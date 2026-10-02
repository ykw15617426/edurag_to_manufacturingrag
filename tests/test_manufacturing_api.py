"""FastAPI TestClient and real Stage 5/10 with synthetic retrieval/completion."""
import asyncio
from types import SimpleNamespace
import time
import pytest
from fastapi.testclient import TestClient
from test_manufacturing_evidence import document
from test_manufacturing_generation import answered
from test_manufacturing_cache import RedisFake
from rag_qa.query import QueryAnalyzer
from rag_qa.generation import StructuredAnswerGenerator, GenerationError
from rag_qa.query.rewrite import RetrievalStrategy
from rag_qa.api.app import create_manufacturing_app
from rag_qa.api.runtime import ManufacturingRuntime
from rag_qa.api.service import ManufacturingOnlineService
from rag_qa.api.cache import ManufacturingAnswerCache

QUERY="MZ-2000 报警 E102 怎么处理？"


def bundle(*, failure=None, empty=False, redis=None, revision=None):
    calls={"analysis":0,"retrieval":0,"generation":0,"closed":0}
    def analyze(query):
        calls["analysis"]+=1; return QueryAnalyzer().analyze(query)
    def retrieve(query, analysis):
        calls["retrieval"]+=1
        if failure == "retrieval": raise RuntimeError("password/secret-host")
        return SimpleNamespace(strategy=RetrievalStrategy.DIRECT, documents=() if empty else (document(),), original_query=query)
    def complete(**kwargs):
        calls["generation"]+=1
        if failure == "generation": raise GenerationError("password/secret-key")
        return answered()
    cache=ManufacturingAnswerCache(redis,60) if redis is not None else None
    service=ManufacturingOnlineService(SimpleNamespace(analyze=analyze), SimpleNamespace(retrieve=retrieve),
        StructuredAnswerGenerator(complete), revision or (lambda:"r1"), cache=cache,
        llm_model="synthetic", retrieval_k=5, candidate_m=2)
    def close(): calls["closed"]+=1
    runtime=ManufacturingRuntime(service,(SimpleNamespace(close=close),))
    return runtime,calls


def test_lifespan_nonstream_once_complete_and_session_correlation():
    runtime,calls=bundle(); factory_calls=[]
    app=create_manufacturing_app(lambda:factory_calls.append(1) or runtime)
    assert not factory_calls and not app.state.ready
    with TestClient(app) as client:
        assert factory_calls == [1] and client.get("/health/live").json() == {"status":"alive"}
        assert client.get("/health/ready").json()["status"] == "ready"
        response=client.post("/api/manufacturing/query",json={"query":QUERY,"session_id":"group-1"})
        data=response.json()
        assert response.status_code == 200 and data["status"] == "answered"
        assert data["session_id"] == "group-1" and data["request_id"] and "[E1]" in data["answer_text"]
        assert data["citations"][0]["document_version"] == "1.10" and not data["cache_hit"]
        assert calls["generation"] == calls["retrieval"] == calls["analysis"] == 1
    assert calls["closed"] == 1 and not app.state.ready


@pytest.mark.parametrize("payload", [{"query":""},{"query":" "},{"query":"x"*16385},{"query":"\ud800"},
    {"query":12},{"query":QUERY,"source_filter":"ai"},{"query":QUERY,"session_id":""}],
    ids=["empty","blank","long","unicode","type","legacy_filter","session"])
def test_invalid_request_422_no_pipeline(payload):
    runtime,calls=bundle()
    with TestClient(create_manufacturing_app(lambda:runtime)) as client:
        assert client.post("/api/manufacturing/query",json=payload).status_code == 422
        assert calls["analysis"] == 0


def test_empty_evidence_200_not_server_error():
    runtime,calls=bundle(empty=True)
    with TestClient(create_manufacturing_app(lambda:runtime)) as client:
        response=client.post("/api/manufacturing/query",json={"query":QUERY})
        assert response.status_code == 200 and response.json()["status"] == "insufficient_evidence"
        assert calls["retrieval"] == 1 and calls["generation"] == 0


@pytest.mark.parametrize("failure,code", [("retrieval","RETRIEVAL_ERROR"),("generation","GENERATION_ERROR")])
def test_safe_error_response_no_cache(failure, code):
    redis=RedisFake(); runtime,calls=bundle(failure=failure,redis=redis)
    with TestClient(create_manufacturing_app(lambda:runtime)) as client:
        response=client.post("/api/manufacturing/query",json={"query":QUERY})
        assert response.status_code == 500 and response.json()["code"] == code
        assert "password" not in response.text and "secret" not in response.text and not redis.sets


def test_startup_failure_sanitized_readiness_and_unavailable_query():
    def fail(): raise RuntimeError("host/password details")
    with TestClient(create_manufacturing_app(fail)) as client:
        assert client.get("/health/live").status_code == 200
        ready=client.get("/health/ready")
        assert ready.status_code == 503 and ready.json()["core"] is False and "password" not in ready.text
        assert client.post("/api/manufacturing/query",json={"query":QUERY}).json()["code"] == "SERVICE_NOT_READY"


def test_cache_hit_skips_retrieval_generation_and_session_not_memory():
    redis=RedisFake(); runtime,calls=bundle(redis=redis)
    with TestClient(create_manufacturing_app(lambda:runtime)) as client:
        first=client.post("/api/manufacturing/query",json={"query":QUERY,"session_id":"one"}).json()
        second=client.post("/api/manufacturing/query",json={"query":QUERY,"session_id":"two"}).json()
        assert not first["cache_hit"] and second["cache_hit"] and second["session_id"] == "two"
        assert calls["analysis"] == 2 and calls["retrieval"] == calls["generation"] == 1


def test_redis_failure_pipeline_and_degraded_readiness():
    class Broken(RedisFake):
        def get(self,*args): raise ConnectionError("password")
        def set(self,*args,**kwargs): raise ConnectionError("password")
    runtime,calls=bundle(redis=Broken())
    with TestClient(create_manufacturing_app(lambda:runtime)) as client:
        assert client.post("/api/manufacturing/query",json={"query":QUERY}).json()["status"] == "answered"
        ready=client.get("/health/ready")
        assert ready.status_code == 200 and ready.json()["cache"] == "degraded"


def test_event_loop_schedules_during_sync_work():
    async def run():
        runtime,calls=bundle(); entered=__import__('threading').Event(); released=__import__('threading').Event()
        old=runtime.service.retriever.retrieve
        def blocking(*args):
            entered.set(); assert released.wait(2); return old(*args)
        runtime.service.retriever.retrieve=blocking
        async def connected(): return False
        task=asyncio.create_task(runtime.service.query(QUERY,connected))
        for _ in range(100):
            if entered.is_set(): break
            await asyncio.sleep(.001)
        assert entered.is_set() and not task.done()
        # If sync work ran on the event loop, this cannot release the thread in time.
        released.set(); result=await task
        assert result.answer.status.value == "answered"
    asyncio.run(run())


def test_cors_default_none_explicit_list_no_credentials():
    runtime,_=bundle()
    for origins, expected in [([],None),(["https://example.test"],"https://example.test")]:
        with TestClient(create_manufacturing_app(lambda:runtime,cors_origins=origins)) as client:
            response=client.get("/health/live",headers={"Origin":"https://example.test"})
            assert response.headers.get("access-control-allow-origin") == expected
            assert "access-control-allow-credentials" not in response.headers


@pytest.mark.parametrize("origins", [["*"],["https://bad.test:abc"],["https://bad.test/path"],["https:// bad.test"],"https://test"])
def test_app_factory_invalid_explicit_origins(origins):
    with pytest.raises(ValueError): create_manufacturing_app(cors_origins=origins)
