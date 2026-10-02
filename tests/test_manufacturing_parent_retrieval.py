"""Injectable scorers validate controls, not real CrossEncoder model quality."""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from test_parent_aggregation import hit
from test_manufacturing_metadata_filters import analysis
from test_manufacturing_retrieval import Gateway, search_store
from test_manufacturing_milvus_schema import vector_store_unit
from base.config import config
from rag_qa.retrieval import ManufacturingRetriever, ParentAggregationError, RerankerError, aggregate_parents
from rag_qa.retrieval.parent_reranker import rerank_parents


@pytest.fixture
def scorer():
    calls = []
    return SimpleNamespace(predict=lambda pairs: calls.append(pairs) or [0.5] * len(pairs)), calls


def test_crossencoder_input_parent_metadata_and_separate_scores(vector_store_unit, scorer):
    model, calls = scorer
    children = [hit(score=0.81), hit(child="2", score=0.73), hit(parent="b", child="3", score=0.77)]
    parents = aggregate_parents(children)
    documents = rerank_parents("原始查询", parents, model, top_m=5)
    assert calls == [[["原始查询", p.page_content] for p in parents]]
    assert len(documents) == 2 and documents[0].page_content == parents[0].page_content
    metadata = documents[0].metadata
    assert metadata["id"] == metadata["parent_id"] == "a" * 64
    assert metadata["best_retrieval_score"] == 0.81 and metadata["rerank_score"] == 0.5
    assert metadata["child_hit_count"] == 2 and metadata["matched_child_ids"] == ["1" * 64, "2" * 64]
    assert metadata["first_child_rank"] == 1
    assert metadata["matched_children"][1] == dict(child_id="2" * 64, child_content_sha256="2" * 64,
                                                 retrieval_score=0.73, child_rank=2)
    assert {name: metadata[name] for name in parents[0].metadata} == dict(parents[0].metadata)
    assert "child_id" not in metadata and "retrieval_score" not in metadata


def test_rerank_primary_score_and_stable_ties(vector_store_unit):
    parents = aggregate_parents([hit(score=0.81), hit(parent="b", child="2", score=0.77),
                                 hit(parent="c", child="3", score=0.77)])
    model = SimpleNamespace(predict=lambda pairs: [-1.25, 1.9, 1.9])
    docs = rerank_parents("query", reversed(parents), model, top_m=9)
    assert [d.metadata["parent_id"] for d in docs] == ["b" * 64, "c" * 64, "a" * 64]
    assert [d.metadata["rerank_score"] for d in docs] == [1.9, 1.9, -1.25]


def test_parent_id_is_last_tie_breaker(vector_store_unit, scorer):
    model, _ = scorer
    parents = aggregate_parents([hit(parent="b"), hit(parent="a", child="2")])
    tied = [replace(p, first_child_rank=1) for p in parents]
    assert [d.metadata["parent_id"] for d in rerank_parents("query", tied, model, top_m=2)] == ["a" * 64, "b" * 64]


@pytest.mark.parametrize("scores", [[], [0.1, 0.2], [float("nan")], [float("inf")],
                                   [-float("inf")], [True], ["0.8"], [[0.8]], None, 0.8])
def test_invalid_model_output_fail_closed(scores):
    model = SimpleNamespace(predict=lambda pairs: scores)
    with pytest.raises(RerankerError): rerank_parents("query", aggregate_parents([hit()]), model, top_m=2)


def test_model_exception_fail_closed_without_disclosing_query():
    def predict(pairs): raise RuntimeError("secret query or model path")
    with pytest.raises(RerankerError) as error:
        rerank_parents("secret query", aggregate_parents([hit()]), SimpleNamespace(predict=predict), top_m=2)
    assert "secret" not in str(error.value) and error.value.__suppress_context__


def test_empty_skips_model_single_parent_is_scored(vector_store_unit, scorer):
    model, calls = scorer
    assert rerank_parents("query", [], model, top_m=2) == () and not calls
    documents = rerank_parents("query", aggregate_parents([hit()]), model, top_m=2)
    assert len(calls) == len(documents) == 1 and documents[0].metadata["rerank_score"] == 0.5


def test_numpy_scalar_output_supported_without_normalization(vector_store_unit):
    numpy = pytest.importorskip("numpy")
    model = SimpleNamespace(predict=lambda pairs: numpy.array([-1.25], dtype=numpy.float32))
    document = rerank_parents("query", aggregate_parents([hit()]), model, top_m=1)[0]
    assert document.metadata["rerank_score"] == -1.25


def test_multiclass_array_rejected():
    numpy = pytest.importorskip("numpy")
    model = SimpleNamespace(predict=lambda pairs: numpy.array([[0.2, 0.8]]))
    with pytest.raises(RerankerError): rerank_parents("query", aggregate_parents([hit()]), model, top_m=1)


def test_existing_fallback_values_unchanged(monkeypatch, tmp_path):
    from base.config import Config
    monkeypatch.delenv("RETRIEVAL_K", raising=False)
    monkeypatch.delenv("CANDIDATE_M", raising=False)
    defaults = Config(config_file=str(tmp_path / "not_present.ini"))
    assert defaults.RETRIEVAL_K == 5 and defaults.CANDIDATE_M == 2


@pytest.mark.parametrize("top_m", [0, -1, True, 1.5, "2"])
def test_invalid_top_m_no_search_or_model(monkeypatch, top_m):
    monkeypatch.setattr(config, "CANDIDATE_M", top_m)
    gateway = Gateway([])
    with pytest.raises(ValueError): ManufacturingRetriever(gateway).retrieve_parents("query", analysis())
    assert not gateway.calls


def test_default_k_reads_config_and_explicit_k_overrides(monkeypatch):
    gateway = Gateway([[], [], []]); retriever = ManufacturingRetriever(gateway)
    monkeypatch.setattr(config, "RETRIEVAL_K", 7)
    retriever.retrieve("query", analysis(intent="general"))
    monkeypatch.setattr(config, "RETRIEVAL_K", 9)
    retriever.retrieve("query", analysis(intent="general"))
    retriever.retrieve("query", analysis(intent="general"), k=3)
    assert [kwargs["k"] for _, kwargs in gateway.calls] == [7, 9, 3]


@pytest.mark.parametrize("top_m", [1, 3])
def test_pipeline_uses_existing_scorer_and_config_top_m(vector_store_unit, monkeypatch, top_m):
    monkeypatch.setattr(config, "CANDIDATE_M", top_m)
    monkeypatch.setattr(config, "RETRIEVAL_K", 8)
    children = [hit(parent=p, child=c, score=0.9 - i * 0.1)
                for i, (p, c) in enumerate(zip("abcd", "1234"))]
    gateway = Gateway([children]); calls = []
    gateway.reranker = SimpleNamespace(predict=lambda pairs: calls.append(pairs) or [0.1, 0.4, 0.3, 0.2])
    result = ManufacturingRetriever(gateway).retrieve_parents("query", analysis(equipment_model="MZ-2000"))
    assert len(result.documents) == top_m and result.documents[0].metadata["parent_id"] == "b" * 64
    assert gateway.calls[0][1]["k"] == 8 and len(calls[0]) == 4
    assert result.attempts[0].hit_count == 4 and result.final_plan.hard_filters["equipment_model"] == "MZ-2000"


def test_pipeline_preserves_soft_relaxation_and_stops_on_hard_zero(monkeypatch):
    monkeypatch.setattr(config, "RETRIEVAL_K", 6)
    gateway = Gateway([[], []])
    gateway.reranker = SimpleNamespace(predict=lambda pairs: pytest.fail("empty retrieval must not rerank"))
    result = ManufacturingRetriever(gateway).retrieve_parents("query", analysis(equipment_model="MZ-2000"))
    assert not result.documents and [a.plan.mode for a in result.attempts] == ["STRICT", "RELAXED"]
    assert all(a.plan.hard_filters["equipment_model"] == "MZ-2000" for a in result.attempts)
    assert [kwargs["k"] for _, kwargs in gateway.calls] == [6, 6]


def test_aggregation_conflict_never_reaches_model():
    gateway = Gateway([[hit(), hit(child="2", document_version="2")]])
    gateway.reranker = SimpleNamespace(predict=lambda pairs: pytest.fail("conflict reached model"))
    with pytest.raises(ParentAggregationError): ManufacturingRetriever(gateway).retrieve_parents("query", analysis())


def test_actual_child_adapter_through_top_m(search_store, monkeypatch):
    store, calls, _ = search_store
    monkeypatch.setattr(config, "CANDIDATE_M", 2)
    children = [hit(score=0.81), hit(child="2", score=0.73), hit(parent="b", child="3", score=0.77)]
    def search(**kwargs):
        calls.append(kwargs)
        return [[dict(id=c.metadata["id"], distance=c.metadata["retrieval_score"],
                      entity={**{k: v for k, v in c.metadata.items() if k != "retrieval_score"}, "text": c.page_content})
                 for c in children]]
    store.client.hybrid_search = search
    pairs = []
    store.reranker.predict = lambda values: pairs.extend(values) or [0.1, 0.9]
    result = ManufacturingRetriever(store).retrieve_parents("原 query", analysis(equipment_model="MZ-2000"), k=7)
    assert [d.metadata["parent_id"] for d in result.documents] == ["b" * 64, "a" * 64]
    assert result.documents[1].metadata["child_hit_count"] == 2
    assert calls[0]["reqs"][0].expr == calls[0]["reqs"][1].expr == result.final_plan.expression
    assert calls[0]["ranker"] == (0.8, 0.3) and calls[0]["limit"] == 7
    assert all(pair == ["原 query", children[0].metadata["parent_content"]] for pair in pairs)
