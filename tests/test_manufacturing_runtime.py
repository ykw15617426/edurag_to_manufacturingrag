"""Real runtime factory composition with recording adapters, no live services."""
import asyncio
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import pytest
from base.config import Config, config
from test_manufacturing_api import QUERY, bundle
from test_manufacturing_cache import RedisFake
from test_manifest_store import record
from test_manufacturing_bm25 import entry
from rag_qa.ingestion.manifest_store import SQLiteManifestStore
from rag_qa.api.runtime import build_runtime, OpenAICompletionAdapter, OpenAIManufacturingStrategyPlanner, KnowledgeRevisionProvider
from rag_qa.retrieval.fast_path import FastPathCorpus


def test_import_safe_new_process_blocks_all_heavy_dependencies():
    script='''
import sys
class Block:
 def find_spec(self, name, path=None, target=None):
  if name.split('.')[0] in {'openai','redis','pymilvus','milvus_model','sentence_transformers','torch','langchain_core'}:
   raise RuntimeError('heavy module imported')
sys.meta_path.insert(0,Block())
import manufacturing_app
assert not manufacturing_app.app.state.ready
assert manufacturing_app.app.state.runtime is None
'''
    result=subprocess.run([sys.executable,"-c",script],capture_output=True,text=True)
    assert result.returncode == 0,result.stderr


def fake_dependencies(monkeypatch,tmp_path, *, redis_fail=False):
    calls={"clients":[],"vector":[],"llm":[],"closed":[],"redis":[]}
    db=tmp_path/"state.sqlite"
    with SQLiteManifestStore(db) as store: store.commit_snapshot(record(),expected_revision=0)
    monkeypatch.setattr(config,"MANUFACTURING_MANIFEST_DB_PATH",str(db))
    monkeypatch.setattr(config,"MILVUS_MANUFACTURING_COLLECTION_NAME",record().collection_name)
    monkeypatch.setattr(config,"MANUFACTURING_FAST_PATH_SNAPSHOT_PATH","")
    monkeypatch.setattr(config,"DASHSCOPE_API_KEY","synthetic-test-only")
    class Client:
        def __init__(self,**kwargs):
            calls["clients"].append(kwargs)
            self.chat=SimpleNamespace(completions=SimpleNamespace(create=self.create))
        def create(self,**kwargs):
            calls["llm"].append(kwargs)
            return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop",message=SimpleNamespace(content='{"strategy":"direct","reason_code":"default_direct"}'))])
        def close(self): calls["closed"].append("llm")
    class Vector:
        schema_mode="manufacturing"
        def __init__(self,**kwargs):
            calls["vector"].append(kwargs)
            self.client=SimpleNamespace(close=lambda:calls["closed"].append("milvus"))
            self.reranker=SimpleNamespace(predict=lambda pairs:[.5]*len(pairs))
    class Redis(RedisFake):
        def __init__(self,**kwargs):
            if redis_fail: raise ConnectionError("hidden password")
            super().__init__(); calls["redis"].append(kwargs)
        def ping(self): return True
        def close(self): calls["closed"].append("redis")
    monkeypatch.setitem(sys.modules,"openai",SimpleNamespace(OpenAI=Client))
    monkeypatch.setitem(sys.modules,"redis",SimpleNamespace(Redis=Redis))
    monkeypatch.setitem(sys.modules,"rag_qa.core.vector_store",SimpleNamespace(VectorStore=Vector))
    return calls


def test_single_client_finite_timeout_shared_completion_and_shutdown(monkeypatch,tmp_path):
    calls=fake_dependencies(monkeypatch,tmp_path)
    runtime=build_runtime(); service=runtime.service
    assert len(calls["clients"]) == 1 and calls["clients"][0]["max_retries"] == 0
    assert calls["clients"][0]["timeout"] == config.MANUFACTURING_LLM_TIMEOUT_SECONDS
    completion=service.generator.completion
    assert service.analyzer.classifier.completion is completion
    assert service.retriever.planner.completion is completion and service.retriever.fast_path is None
    assert calls["vector"] == [{"schema_mode":"manufacturing"}]
    assert calls["redis"][0]["socket_timeout"] > 0
    assert service.retriever.planner.plan(QUERY, __import__('test_manufacturing_metadata_filters').analysis()).startswith('{')
    assert calls["llm"][-1]["stream"] is False and calls["llm"][-1]["timeout"] > 0
    assert runtime.cache_state() == "ready"
    runtime.close(); assert calls["closed"] == ["redis","milvus","llm"]


def test_redis_initialization_failure_degraded_core(monkeypatch,tmp_path):
    fake_dependencies(monkeypatch,tmp_path,redis_fail=True)
    runtime=build_runtime(); assert runtime.cache_state() == "degraded" and runtime.service.cache is None
    runtime.close()


def test_configured_snapshot_validated_no_bm25_threshold(monkeypatch,tmp_path):
    fake_dependencies(monkeypatch,tmp_path)
    path=tmp_path/"approved.json"; path.write_text(FastPathCorpus([entry()]).to_json(),encoding="utf-8")
    monkeypatch.setattr(config,"MANUFACTURING_FAST_PATH_SNAPSHOT_PATH",str(path))
    runtime=build_runtime(); assert runtime.service.retriever.fast_path.acceptance_policy is None
    assert runtime.service.revision_provider.fast_path_hash is not None
    runtime.close()


def test_corrupt_explicit_snapshot_fails_before_models(monkeypatch,tmp_path):
    calls=fake_dependencies(monkeypatch,tmp_path)
    path=tmp_path/"bad.json"; path.write_text("bad",encoding="utf-8")
    monkeypatch.setattr(config,"MANUFACTURING_FAST_PATH_SNAPSHOT_PATH",str(path))
    with pytest.raises(Exception): build_runtime()
    assert not calls["vector"] and not calls["clients"]


@pytest.mark.parametrize("timeout", [None,0,-1,True,float("nan"),float("inf")])
def test_invalid_completion_timeout(timeout):
    with pytest.raises(ValueError): OpenAICompletionAdapter(None,"model",timeout)


def test_planner_prompt_preserves_all_identifiers_and_strict_schema():
    calls=[]
    def complete(**kwargs): calls.append(kwargs); return "bad JSON"
    from test_manufacturing_metadata_filters import analysis
    assert OpenAIManufacturingStrategyPlanner(complete).plan(QUERY,analysis()) == "bad JSON"
    system=calls[0]["messages"][0]["content"]
    for value in ("equipment_model","alarm_code","part_number","最多4","Schema:","identifier"):
        assert value in system
    assert json.loads(calls[0]["messages"][1]["content"])["query"] == QUERY


@pytest.mark.parametrize("finish,content", [("length","{}"),("content_filter",None),("stop",None),("stop","")])
def test_adapter_rejects_partial_or_invalid_response(finish,content):
    client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_:SimpleNamespace(choices=[SimpleNamespace(finish_reason=finish,message=SimpleNamespace(content=content))]))))
    with pytest.raises(ValueError): OpenAICompletionAdapter(client,"model",30)(messages=[],temperature=0,response_format={"type":"json_object"})


def test_config_precedence_defaults_and_origin_validation(monkeypatch,tmp_path):
    file=tmp_path/"config.ini";file.write_text('[manufacturing]\nllm_timeout_seconds=12\ncache_ttl_seconds=45\ncors_origins=["https://example.test"]\n',encoding="utf-8")
    monkeypatch.delenv("MANUFACTURING_LLM_TIMEOUT_SECONDS",raising=False)
    assert Config(file).MANUFACTURING_LLM_TIMEOUT_SECONDS == 12
    monkeypatch.setenv("MANUFACTURING_LLM_TIMEOUT_SECONDS","9")
    assert Config(file).MANUFACTURING_LLM_TIMEOUT_SECONDS == 9
    assert Config(file).MANUFACTURING_CACHE_TTL_SECONDS == 45
    monkeypatch.delenv("MANUFACTURING_LLM_TIMEOUT_SECONDS")
    assert Config(tmp_path/"missing.ini").MANUFACTURING_CORS_ORIGINS == []


@pytest.mark.parametrize("name,value", [("MANUFACTURING_CACHE_TTL_SECONDS","0"),("MANUFACTURING_CACHE_TTL_SECONDS","1.5"),
    ("MANUFACTURING_LLM_TIMEOUT_SECONDS","nan"),("MANUFACTURING_REDIS_TIMEOUT_SECONDS","inf"),
    ("MANUFACTURING_CORS_ORIGINS",'["*"]'),("MANUFACTURING_CORS_ORIGINS",'["https://example.test/path"]'),
    ("MANUFACTURING_CORS_ORIGINS",'"https://example.test"')])
def test_invalid_runtime_config(monkeypatch,tmp_path,name,value):
    monkeypatch.setenv(name,value)
    with pytest.raises(ValueError): Config(tmp_path/"missing.ini")


def test_manifest_v2_cache_namespace_forces_new_pipeline(tmp_path):
    async def run():
        db=tmp_path/"manifest.sqlite"
        with SQLiteManifestStore(db) as store:
            current=store.commit_snapshot(record(),expected_revision=0)
            provider=KnowledgeRevisionProvider(db,current.collection_name)
            redis=RedisFake(); runtime,calls=bundle(redis=redis,revision=provider)
            async def connected(): return False
            first=await runtime.service.query(QUERY,connected)
            assert not first.cache_hit and len(redis.sets) == 1
            assert (await runtime.service.query(QUERY,connected)).cache_hit
            store.commit_snapshot(replace(current,active_document_version="2"),expected_revision=1)
            changed=await runtime.service.query(QUERY,connected)
            assert not changed.cache_hit and len(redis.sets) == 2 and calls["generation"] == 2
            assert redis.sets[0][0] != redis.sets[1][0] and redis.sets[0][0] in redis.data
    asyncio.run(run())


def test_factory_actual_stage5_stage9_stage10_end_to_end_recording(monkeypatch,tmp_path):
    from fastapi.testclient import TestClient
    from rag_qa.api.app import create_manufacturing_app
    from test_parent_aggregation import hit
    from test_manufacturing_generation import answered
    calls=fake_dependencies(monkeypatch,tmp_path)
    vector=sys.modules['rag_qa.core.vector_store'].VectorStore
    searches=[]
    def search(self,query,**kwargs):
        searches.append((query,kwargs))
        return [hit(equipment_model="MZ-2000",alarm_code="E102",parent_content="MZ-2000 报警 E102。检查润滑管路。")]
    monkeypatch.setattr(vector,'hybrid_search_children',search,raising=False)
    monkeypatch.setitem(sys.modules,'langchain_core',SimpleNamespace())
    monkeypatch.setitem(sys.modules,'langchain_core.documents',SimpleNamespace(Document=SimpleNamespace))
    client=sys.modules['openai'].OpenAI
    def create(self,**kwargs):
        calls['llm'].append(kwargs)
        system=kwargs['messages'][0]['content']
        if '语义分类器' in system:
            content=json.dumps(dict(intent='alarm_fault',confidence='high',entities=dict(equipment_model='MZ-2000',alarm_code='E102')))
        elif '只返回严格JSON策略' in system:
            content=json.dumps(dict(strategy='direct',reason_code='direct_plan'))
        else: content=answered()
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason='stop',message=SimpleNamespace(content=content))])
    monkeypatch.setattr(client,'create',create)
    with TestClient(create_manufacturing_app(build_runtime)) as http:
        first=http.post('/api/manufacturing/query',json={'query':QUERY})
        assert first.status_code==200 and first.json()['status']=='answered'
        assert len(calls['llm'])==3 and len(searches)==1
        assert searches[0][1]['filter_plan'].hard_filters=={'equipment_model':'MZ-2000','alarm_code':'E102'}
        second=http.post('/api/manufacturing/query',json={'query':QUERY})
        assert second.json()['cache_hit'] and len(searches)==1 and len(calls['llm'])==4
        assert calls['clients'][0]['timeout']>0 and len(calls['clients'])==1
