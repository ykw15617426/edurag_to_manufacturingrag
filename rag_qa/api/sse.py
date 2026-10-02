"""SSE over validated results, never raw LLM chunks."""
import json
from .schemas import ServiceError, RequestDisconnected
from .service import check_connected


def encode_event(event, value):
    return f"event: {event}\ndata: {json.dumps(value, ensure_ascii=False, allow_nan=False)}\n\n"


async def stream_response(service, query, disconnected, *, request_id, session_id):
    try:
        await check_connected(disconnected)
        yield encode_event("start", dict(request_id=request_id, session_id=session_id))
        async for event, value in service.events(query, disconnected):
            await check_connected(disconnected)
            if event != "result":
                yield encode_event(event, value)
                continue
            answer = value.answer
            for offset in range(0, len(answer.answer_text), 256):
                await check_connected(disconnected)
                yield encode_event("answer", {"text": answer.answer_text[offset:offset+256]})
            await check_connected(disconnected)
            yield encode_event("citations", [c.model_dump(mode="json") for c in answer.citations])
            await check_connected(disconnected)
            yield encode_event("done", dict(request_id=request_id, session_id=session_id, status=answer.status.value,
                cache_hit=value.cache_hit, used_evidence_ids=list(answer.used_evidence_ids), warnings=list(answer.warnings)))
            return
        raise ServiceError("INTERNAL_ERROR")
    except RequestDisconnected:
        return
    except ServiceError as exc:
        if not await disconnected(): yield encode_event("error", {"code":exc.code, "request_id":request_id})
    except Exception:
        if not await disconnected(): yield encode_event("error", {"code":"INTERNAL_ERROR", "request_id":request_id})
