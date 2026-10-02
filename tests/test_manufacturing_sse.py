"""Actual StreamingResponse and controlled disconnection without live providers."""
import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from test_manufacturing_api import bundle, QUERY
from test_manufacturing_cache import RedisFake
from rag_qa.api.app import create_manufacturing_app
from rag_qa.api.sse import stream_response


def events(text):
    return [(block.splitlines()[0][7:], json.loads(block.splitlines()[1][6:]))
            for block in text.strip().split("\n\n")]


def test_stream_validated_only_order_citations_single_terminal():
    runtime,calls=bundle()
    with TestClient(create_manufacturing_app(lambda:runtime)) as client:
        response=client.post("/api/manufacturing/stream",json={"query":QUERY})
        assert response.headers["content-type"].startswith("text/event-stream")
        parsed=events(response.text); names=[name for name,_ in parsed]
        assert names[:4] == ["start","analysis","retrieval","generation"]
        assert names.count("done") == 1 and "error" not in names and names[-2:] == ["citations","done"]
        text="".join(data["text"] for name,data in parsed if name == "answer")
        assert "[E1]" in text and calls["generation"] == 1
        assert next(data for name,data in parsed if name == "citations")[0]["document_version"] == "1.10"
        assert not any(word in response.text for word in ["messages", "raw_model_output", "SYSTEM_INSTRUCTION", "secret-key", "chain_of_thought"])


@pytest.mark.parametrize("failure", ["retrieval","generation"])
def test_single_error_no_done_and_no_answer(failure):
    runtime,_=bundle(failure=failure)
    with TestClient(create_manufacturing_app(lambda:runtime)) as client:
        parsed=events(client.post("/api/manufacturing/stream",json={"query":QUERY}).text)
        names=[name for name,_ in parsed]
        assert names[0] == "start" and names.count("error") == 1 and "done" not in names and "answer" not in names
        assert "secret" not in str(parsed) and "password" not in str(parsed)


def test_cache_hit_real_path_no_fake_generation_events():
    runtime,calls=bundle(redis=RedisFake())
    with TestClient(create_manufacturing_app(lambda:runtime)) as client:
        client.post("/api/manufacturing/query",json={"query":QUERY})
        parsed=events(client.post("/api/manufacturing/stream",json={"query":QUERY}).text)
        names=[name for name,_ in parsed]
        assert names[0] == "start" and names[-2:] == ["citations","done"]
        assert not set(names)&{"analysis","retrieval","generation"} and parsed[-1][1]["cache_hit"]
        assert calls["generation"] == 1


@pytest.mark.parametrize("stage", ["analysis","retrieval","generation"])
def test_disconnect_prevents_downstream_and_cache(stage):
    async def run():
        redis=RedisFake(); runtime,calls=bundle(redis=redis); state={"disconnected":False}
        target = runtime.service.analyzer if stage == "analysis" else runtime.service.retriever if stage == "retrieval" else runtime.service.generator
        method = "analyze" if stage == "analysis" else "retrieve" if stage == "retrieval" else "generate"
        previous=getattr(target,method)
        def disconnecting(*args):
            result=previous(*args); state["disconnected"]=True; return result
        setattr(target,method,disconnecting)
        async def disconnected(): return state["disconnected"]
        chunks=[chunk async for chunk in stream_response(runtime.service,QUERY,disconnected,request_id="request",session_id=None)]
        assert not redis.sets and not any("event: answer" in chunk or "event: done" in chunk or "event: error" in chunk for chunk in chunks)
        if stage == "analysis": assert calls["retrieval"] == calls["generation"] == 0
        if stage == "retrieval": assert calls["generation"] == 0
    asyncio.run(run())


def test_disconnect_before_analysis_sends_nothing():
    async def run():
        runtime,calls=bundle()
        async def disconnected(): return True
        assert [chunk async for chunk in stream_response(runtime.service,QUERY,disconnected,request_id="r",session_id=None)] == []
        assert calls["analysis"] == 0
    asyncio.run(run())


def test_startup_failure_sse_safe_terminal():
    def fail(): raise RuntimeError("hidden")
    with TestClient(create_manufacturing_app(fail)) as client:
        parsed=events(client.post("/api/manufacturing/stream",json={"query":QUERY}).text)
        assert [name for name,_ in parsed] == ["start","error"] and parsed[-1][1]["code"] == "SERVICE_NOT_READY"


def test_invalid_stream_request_single_error_terminal():
    runtime,calls=bundle()
    with TestClient(create_manufacturing_app(lambda:runtime)) as client:
        response=client.post("/api/manufacturing/stream",json={"query":""})
        parsed=events(response.text)
        assert response.status_code == 422 and [name for name,_ in parsed] == ["start","error"]
        assert parsed[-1][1]["code"] == "INVALID_REQUEST" and calls["analysis"] == 0


def test_no_answer_sent_before_generation_validation_completes():
    async def run():
        import threading
        runtime,_=bundle(); entered=threading.Event(); released=threading.Event()
        old=runtime.service.generator.generate
        def blocking(*args):
            entered.set(); assert released.wait(2); return old(*args)
        runtime.service.generator.generate=blocking
        async def connected(): return False
        received=[]
        async def collect():
            async for chunk in stream_response(runtime.service,QUERY,connected,request_id="r",session_id=None):
                received.append(chunk)
        task=asyncio.create_task(collect())
        for _ in range(100):
            if entered.is_set(): break
            await asyncio.sleep(.001)
        assert entered.is_set() and not any("event: answer" in chunk for chunk in received)
        released.set(); await task
        assert any("event: answer" in chunk for chunk in received)
    asyncio.run(run())
