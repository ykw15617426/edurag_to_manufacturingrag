from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from rag_qa.retrieval.settings import RetrievalSettings, baseline_settings
from rag_qa.evaluation.schemas import EvaluationProfile
from rag_qa.api.cache import build_cache_key
from test_manufacturing_metadata_filters import analysis
from test_manufacturing_retrieval import search_store
from test_manufacturing_milvus_schema import vector_store_unit


@pytest.mark.parametrize("updates", [dict(dense_weight=.7), dict(sparse_weight=.4), dict(nprobe=11), dict(retrieval_k=6),
    dict(candidate_m=3), dict(bm25_acceptance_mode="raw_score", bm25_threshold=2.),
    dict(retrieval_contract_version="manufacturing_retrieval_v2")])
def test_fingerprint_and_answer_key_change(updates):
    first = baseline_settings()
    second = RetrievalSettings(**{**first.model_dump(), **updates})
    assert first.fingerprint() == RetrievalSettings(**first.model_dump()).fingerprint()
    assert second.fingerprint() != first.fingerprint()
    def key(s): return build_cache_key("型号 MZ-2000 报警码 E102", analysis(equipment_model="MZ-2000", alarm_code="E102"), "revision",
        llm_model="test", retrieval_k=s.retrieval_k, candidate_m=s.candidate_m, retrieval_settings=s)
    assert key(first) != key(second) and "E102" not in key(second)
    assert key(first) == key(RetrievalSettings())


def test_profile_name_not_retrieval_semantics_and_baseline_unchanged():
    first = EvaluationProfile(); other = EvaluationProfile(profile_name="experiment_label")
    assert first.fingerprint() == other.fingerprint() == baseline_settings().fingerprint()
    assert (first.retrieval_k, first.candidate_m, first.dense_weight, first.sparse_weight, first.nprobe) == (5, 2, .8, .3, 10)
    assert first.bm25_acceptance_mode == "disabled" and first.bm25_threshold is None


@pytest.mark.parametrize("updates", [dict(retrieval_k=True), dict(candidate_m=0), dict(nprobe=0), dict(dense_weight=float("nan")),
    dict(sparse_weight=-1.), dict(dense_weight=0., sparse_weight=0.), dict(bm25_threshold=1.), dict(bm25_acceptance_mode="raw_score")])
def test_bad_config(updates):
    with pytest.raises(ValidationError): RetrievalSettings(**updates)


def test_cache_rejects_mismatched_k():
    with pytest.raises(ValueError): build_cache_key("query", analysis(), "revision", llm_model="test", retrieval_k=6, candidate_m=2,
                                                 retrieval_settings=RetrievalSettings())


def test_real_child_method_uses_instance_experiment_only(search_store):
    store, calls, _ = search_store
    store.retrieval_settings = RetrievalSettings(dense_weight=.7, sparse_weight=.2, nprobe=12)
    store.hybrid_search_children("问题", k=5)
    assert calls[0]["ranker"] == (.7, .2)
    assert calls[0]["reqs"][0].param["nprobe"] == 12
    assert baseline_settings().dense_weight == .8
