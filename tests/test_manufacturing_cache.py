"""Recording Redis and real temporary SQLite; no live network dependencies."""
from dataclasses import replace
import json
import re
import pytest
from test_manufacturing_metadata_filters import analysis
from test_manufacturing_generation import generate, answered
from test_manifest_store import record
from rag_qa.ingestion.manifest_store import SQLiteManifestStore
from rag_qa.api.cache import ManufacturingAnswerCache, build_cache_key
from rag_qa.api.runtime import KnowledgeRevisionProvider


class RedisFake:
    def __init__(self): self.data, self.sets, self.deletes = {}, [], []
    def get(self, key): return self.data.get(key)
    def set(self, key, value, **kwargs):
        self.sets.append((key, value, kwargs)); self.data[key] = value
    def delete(self, key): self.deletes.append(key); self.data.pop(key, None)
    def close(self): pass


def key(query="mZ_0002 ALM-007 00001234", revision="revision", **options):
    return build_cache_key(query, analysis(equipment_model="mZ_0002"), revision,
                          **dict(dict(llm_model="model", retrieval_k=5, candidate_m=2), **options))


def test_key_hash_only_namespace_stable_safe_normalization():
    query = "mZ_0002 ALM-007 00001234"
    assert re.fullmatch(r"manufacturing:answer:v1:[0-9a-f]{64}", key())
    assert query not in key() and "ALM-007" not in key()
    assert key("  mZ_0002\nALM-007\t00001234  ") == key()
    assert key("Cafe\u0301 "+query) == key("Café "+query)


@pytest.mark.parametrize("query", ["MZ_0002 ALM-007 00001234", "mZ-0002 ALM-007 00001234", "mZ_0002 ALM-07 00001234", "mZ_0002 ALM-007 1234"])
def test_identifier_normalization_does_not_merge(query): assert key(query) != key()


@pytest.mark.parametrize("options", [dict(llm_model="other"), dict(retrieval_k=6), dict(candidate_m=3)])
def test_config_changes_namespace(options): assert key(**options) != key()


def test_revision_analysis_and_contract_affect_key(monkeypatch):
    assert key(revision="changed") != key()
    assert build_cache_key("mZ_0002 ALM-007 00001234", analysis(intent="parts", equipment_model="mZ_0002"), "revision", llm_model="model", retrieval_k=5, candidate_m=2) != key()
    import rag_qa.api.cache as module
    before = key(); monkeypatch.setattr(module, "GENERATION_CONTRACT_VERSION", "v2")
    assert key() != before


def test_cache_ttl_validated_roundtrip_no_negative_cache():
    redis = RedisFake(); cache = ManufacturingAnswerCache(redis, 60)
    result, _ = generate(answered())
    assert cache.put(key(), result) and cache.get(key()) == result
    assert redis.sets[0][2] == {"ex":60}
    insufficient, _ = generate(json.dumps(dict(status="insufficient_evidence", insufficient_reason="没有足够证据")))
    assert not cache.put("negative", insufficient) and len(redis.sets) == 1
    assert not cache.put("raw", answered()) and len(redis.sets) == 1


@pytest.mark.parametrize("ttl", [0, -1, True, 1.5, "10"])
def test_invalid_ttl(ttl):
    with pytest.raises(ValueError): ManufacturingAnswerCache(RedisFake(), ttl)


@pytest.mark.parametrize("raw", ["bad", "[]", "{}", '{"status":"answered","status":"answered"}', '"raw answer"'])
def test_corrupt_value_delete_miss(raw):
    redis = RedisFake(); redis.data[key()] = raw
    assert ManufacturingAnswerCache(redis, 60).get(key()) is None and redis.deletes == [key()]


@pytest.mark.parametrize("mutation", ["unknown_citation", "tampered_text", "no_claims", "duplicate_citation", "status"])
def test_structural_cache_validation(mutation):
    redis=RedisFake(); result,_=generate(answered()); data=result.model_dump(mode="json")
    if mutation == "unknown_citation": data["claims"][0]["evidence_ids"] = ["E99"]
    elif mutation == "tampered_text": data["answer_text"] = "RAW unsafe answer"
    elif mutation == "no_claims": data["claims"] = []
    elif mutation == "duplicate_citation": data["citations"].append(data["citations"][0])
    else: data["status"] = "insufficient_evidence"
    redis.data[key()] = json.dumps(data)
    assert ManufacturingAnswerCache(redis,60).get(key()) is None and redis.deletes == [key()]


def test_redis_failure_does_not_leak_or_raise():
    class Broken(RedisFake):
        def get(self, key): raise RuntimeError("secret-host/password")
        def set(self, *args, **kwargs): raise RuntimeError("secret-host/password")
    cache=ManufacturingAnswerCache(Broken(),60)
    assert cache.get(key()) is None and cache.degraded
    assert not cache.put(key(), generate(answered())[0]) and cache.degraded


@pytest.mark.parametrize("change", [dict(active_document_version="v2"), dict(document_sha256="b"*64),
    dict(metadata_sha256="c"*64), dict(processing_signature="d"*64), dict(child_ids=("a"*64,"b"*64,"c"*64)),
    dict(collection_name="other"), dict(storage_schema_version="other"), dict(revision=2)])
def test_manifest_fingerprint_changed_fields(tmp_path, change):
    with SQLiteManifestStore(tmp_path/"state.sqlite") as store:
        committed=store.commit_snapshot(record(),expected_revision=0); before=store.snapshot_fingerprint()
        other=replace(committed, **change)
        # Commit CAS changes revision too; force same revision for independent field coverage.
        store.commit_snapshot(other,expected_revision=1)
        store.connection.execute("UPDATE active_documents SET revision=?", (other.revision,))
        assert store.snapshot_fingerprint() != before


def test_fingerprint_stable_sorted_timestamp_only_add_delete(tmp_path):
    with SQLiteManifestStore(tmp_path/"state.sqlite") as store:
        empty=store.snapshot_fingerprint(); first=store.commit_snapshot(record(),expected_revision=0)
        one=store.snapshot_fingerprint(); assert one != empty and one == store.snapshot_fingerprint()
        store.connection.execute("UPDATE active_documents SET updated_at='different timestamp'")
        assert one == store.snapshot_fingerprint()
        store.commit_snapshot(replace(record(), document_id="OTHER"),expected_revision=0)
        assert store.snapshot_fingerprint() != one
        store.delete("OTHER",expected_revision=1); assert store.snapshot_fingerprint() == one
        store.delete(first.document_id,expected_revision=1); assert store.snapshot_fingerprint() == empty


def test_readonly_provider_fastpath_revision_and_no_db_creation(tmp_path):
    path=tmp_path/"state.sqlite"
    with SQLiteManifestStore(path) as store: store.commit_snapshot(record(),expected_revision=0)
    collection=record().collection_name
    first=KnowledgeRevisionProvider(path,collection,b"approved-v1")
    assert first() == first() and first() != KnowledgeRevisionProvider(path,collection,b"approved-v2")()
    assert first() != KnowledgeRevisionProvider(path,collection)()
    with pytest.raises(Exception): KnowledgeRevisionProvider(tmp_path/"missing.sqlite",collection)()
    assert not (tmp_path/"missing.sqlite").exists()
    with pytest.raises(Exception): KnowledgeRevisionProvider(path,"wrong_collection")()
