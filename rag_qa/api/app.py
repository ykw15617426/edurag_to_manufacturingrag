"""Dedicated manufacturing routes; all runtime construction belongs to lifespan."""
import asyncio
from contextlib import asynccontextmanager
import uuid
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from .schemas import ManufacturingQueryRequest, ManufacturingQueryResponse, ServiceError, RequestDisconnected
from .sse import stream_response
from .service import check_connected


def create_manufacturing_app(runtime_factory=None, *, cors_origins=None):
    # Config import parses settings only; no SDK/client/model import.
    from base.config import config, validate_manufacturing_origins
    origins = validate_manufacturing_origins(config.MANUFACTURING_CORS_ORIGINS if cors_origins is None else cors_origins)
    @asynccontextmanager
    async def lifespan(app):
        app.state.runtime, app.state.ready, app.state.reason = None, False, "SERVICE_NOT_READY"
        try:
            if runtime_factory is None:
                from .runtime import build_runtime
                factory = build_runtime
            else:
                factory = runtime_factory
            app.state.runtime = await asyncio.to_thread(factory)
            app.state.ready, app.state.reason = True, None
        except Exception:
            app.state.reason = "RUNTIME_INITIALIZATION_FAILED"
        try:
            yield
        finally:
            app.state.ready = False
            if app.state.runtime is not None:
                await asyncio.to_thread(app.state.runtime.close)

    app = FastAPI(lifespan=lifespan)
    app.state.runtime, app.state.ready, app.state.reason = None, False, "SERVICE_NOT_READY"
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                       allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        # Do not echo raw query/Pydantic context or exception objects.
        if request.url.path == "/api/manufacturing/stream":
            from .sse import encode_event
            request_id = str(uuid.uuid4())
            async def invalid_stream():
                if not await request.is_disconnected():
                    yield encode_event("start", {"request_id": request_id})
                if not await request.is_disconnected():
                    yield encode_event("error", {"code":"INVALID_REQUEST", "request_id":request_id})
            return StreamingResponse(invalid_stream(), status_code=422, media_type="text/event-stream")
        return JSONResponse({"code":"INVALID_REQUEST"}, status_code=422)

    @app.get("/health/live")
    async def live(): return {"status":"alive"}

    @app.get("/health/ready")
    async def ready():
        runtime = app.state.runtime
        return JSONResponse(dict(status="ready" if app.state.ready else "not_ready", core=app.state.ready,
            cache=runtime.cache_state() if runtime is not None else "unavailable", reason=app.state.reason),
            status_code=200 if app.state.ready else 503)

    @app.post("/api/manufacturing/query", response_model=ManufacturingQueryResponse)
    async def query(payload: ManufacturingQueryRequest, request: Request):
        request_id = str(uuid.uuid4())
        if not app.state.ready:
            return JSONResponse({"code":"SERVICE_NOT_READY", "request_id":request_id}, status_code=503)
        try:
            outcome = await app.state.runtime.service.query(payload.query, request.is_disconnected)
            await check_connected(request.is_disconnected)
            return ManufacturingQueryResponse(**outcome.answer.model_dump(mode="json"),
                request_id=request_id, session_id=payload.session_id, cache_hit=outcome.cache_hit)
        except RequestDisconnected:
            return JSONResponse({"code":"CLIENT_DISCONNECTED", "request_id":request_id}, status_code=499)
        except ServiceError as exc:
            return JSONResponse({"code":exc.code, "request_id":request_id}, status_code=exc.status_code)
        except Exception:
            return JSONResponse({"code":"INTERNAL_ERROR", "request_id":request_id}, status_code=500)

    @app.post("/api/manufacturing/stream")
    async def stream(payload: ManufacturingQueryRequest, request: Request):
        request_id = str(uuid.uuid4())
        if not app.state.ready:
            async def unavailable():
                from .sse import encode_event
                if not await request.is_disconnected():
                    yield encode_event("start", dict(request_id=request_id, session_id=payload.session_id))
                if not await request.is_disconnected():
                    yield encode_event("error", {"code":"SERVICE_NOT_READY", "request_id":request_id})
            content = unavailable()
        else:
            content = stream_response(app.state.runtime.service, payload.query, request.is_disconnected,
                                      request_id=request_id, session_id=payload.session_id)
        return StreamingResponse(content, media_type="text/event-stream", headers={"Cache-Control":"no-cache", "X-Accel-Buffering":"no"})
    return app
