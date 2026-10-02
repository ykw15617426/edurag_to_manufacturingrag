"""Recording Milvus tests execute the real VectorStore child-search method."""
from types import SimpleNamespace
import pytest

from test_manufacturing_metadata_filters import analysis
from test_manufacturing_milvus_schema import vector_store_unit, row
from rag_qa.core.milvus_schema import manufacturing_fields
from rag_qa.retrieval import ManufacturingRetriever
from rag_qa.retrieval.filters import build_filter_plan


class Gateway:
    schema_mode = "manufacturing"

    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def hybrid_search_children(self, query, **kwargs):
        self.calls.append((query, kwargs))
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


@pytest.mark.parametrize("hard", [{"equipment_model": "MZ-2000", "alarm_code": "E102"}, {"part_number": "PN-001"}])
def test_strict_zero_relaxes_only_soft_and_stops_empty(hard):
    gateway = Gateway([[], []])
    result = ManufacturingRetriever(gateway).retrieve("原始问题", analysis(manufacturer="ACME", **hard), k=7)
    assert not result.documents and len(result.attempts) == 2
    assert [a.plan.mode for a in result.attempts] == ["STRICT", "RELAXED"]
    assert all(dict(a.plan.hard_filters) == hard for a in result.attempts)
    assert all(call[0] == "原始问题" and call[1]["k"] == 7 for call in gateway.calls)
    assert result.final_plan.removed_fields == ("manufacturer", "knowledge_type")


def test_soft_only_zero_then_none():
    gateway = Gateway([[], ["child"]])
    result = ManufacturingRetriever(gateway).retrieve("ACME 数控机床怎么启动？",
        analysis(intent="knowledge", manufacturer="ACME", equipment_type="数控机床"))
    assert [a.plan.mode for a in result.attempts] == ["STRICT", "NONE"]
    assert result.documents == ("child",) and result.final_plan.expression == ""


@pytest.mark.parametrize("entities", [{}, {"equipment_model": "MZ-2000"}])
def test_general_does_not_bypass_or_repeat_empty_search(entities):
    gateway = Gateway([[]])
    result = ManufacturingRetriever(gateway).retrieve("怎么启动这台设备？", analysis(intent="general", confidence="low", **entities))
    assert len(result.attempts) == len(gateway.calls) == 1
    assert result.final_plan.mode == ("RELAXED" if entities else "NONE")


def test_success_does_not_relax():
    gateway = Gateway([["first", "second"]])
    result = ManufacturingRetriever(gateway).retrieve("报警", analysis())
    assert result.documents == ("first", "second") and len(result.attempts) == 1


def test_errors_do_not_relax():
    gateway = Gateway([RuntimeError("database unavailable")])
    with pytest.raises(RuntimeError):
        ManufacturingRetriever(gateway).retrieve("报警", analysis(equipment_model="MZ-2000"))
    assert len(gateway.calls) == 1


@pytest.mark.parametrize("query,k", [("", 1), ("  ", 1), (None, 1), ("x", 0), ("x", True), ("x", 16385)])
def test_invalid_input_no_calls(query, k):
    gateway = Gateway([])
    with pytest.raises(ValueError):
        ManufacturingRetriever(gateway).retrieve(query, analysis(), k=k)
    assert not gateway.calls


def test_legacy_gateway_rejected():
    with pytest.raises(ValueError):
        ManufacturingRetriever(SimpleNamespace(schema_mode="legacy"))


@pytest.fixture
def search_store(vector_store_unit, monkeypatch):
    module = vector_store_unit
    monkeypatch.setattr(module, "AnnSearchRequest", lambda **kwargs: SimpleNamespace(**kwargs))
    monkeypatch.setattr(module, "WeightedRanker", lambda *weights: weights)
    store = module.VectorStore.__new__(module.VectorStore)
    store.schema_mode, store.collection_name, store.dense_dim = "manufacturing", "stage6_test_fake_v1", 4
    embeddings = []
    store.embedding_function = lambda queries: embeddings.append(queries) or {"dense": [[1, 0, 0, 0]]}
    store.get_sparse_dict = lambda *args: {3: 0.5}
    store.reranker = SimpleNamespace(predict=lambda *args: pytest.fail("child search must not rerank"))
    calls = []
    store.client = SimpleNamespace(hybrid_search=lambda **kwargs: calls.append(kwargs) or [[]])
    return store, calls, embeddings


def test_requests_both_filtered_and_parameters_preserved(search_store):
    store, calls, embeddings = search_store
    plan = build_filter_plan(analysis(equipment_model="MZ-2000", alarm_code="E102"))
    assert store.hybrid_search_children("原 query", filter_plan=plan, k=13) == []
    call = calls[0]; dense, sparse = call["reqs"]
    assert dense.expr == sparse.expr == plan.expression
    assert dense.param == {"metric_type": "IP", "nprobe": 10}
    assert sparse.param == {"metric_type": "IP"}
    assert dense.anns_field == "dense_vector" and sparse.anns_field == "sparse_vector"
    assert dense.data == [[1, 0, 0, 0]] and sparse.data == [{3: 0.5}]
    assert dense.limit == sparse.limit == call["limit"] == 13
    assert call["ranker"] == (0.8, 0.3) and embeddings == [["原 query"]]
    assert call["output_fields"] == [f.name for f in manufacturing_fields(4) if "VECTOR" not in f.datatype]


@pytest.mark.parametrize("hard", [True, False])
def test_retriever_and_real_adapter_relax_together(search_store, hard):
    store, calls, embeddings = search_store
    result = ManufacturingRetriever(store).retrieve("不改写原问题", analysis(
        manufacturer='ACME"\\[]', **({"equipment_model": "MZ-2000"} if hard else {})), k=6)
    assert len(calls) == len(result.attempts) == 2 and not result.documents
    for call, attempt in zip(calls, result.attempts):
        assert call["reqs"][0].expr == call["reqs"][1].expr == attempt.plan.expression
        assert call["ranker"] == (0.8, 0.3) and call["limit"] == 6
    assert calls[1]["reqs"][0].expr == ('equipment_model == "MZ-2000"' if hard else "")
    assert embeddings == [["不改写原问题"], ["不改写原问题"]]


def test_legacy_search_still_aggregates_and_reranks(search_store):
    store, _, _ = search_store
    store.schema_mode = "legacy"
    store.client.hybrid_search = lambda **kwargs: [[
        {"entity": {"id": "old1", "text": "child1", "parent_id": "p1", "parent_content": "first parent", "source": "ai", "timestamp": "old"}},
        {"entity": {"id": "old2", "text": "child2", "parent_id": "p2", "parent_content": "second parent", "source": "ai", "timestamp": "old"}}]]
    pairs = []
    store.reranker.predict = lambda values: pairs.extend(values) or [0.9 if v[1] == "second parent" else 0.1 for v in values]
    documents = store.hybrid_search_with_rerank("legacy query", k=3, source_filter="ai")
    assert documents[0].page_content == "second parent"
    assert {pair[1] for pair in pairs} == {"first parent", "second parent"}


@pytest.mark.parametrize("score_key,score", [("distance", -1.25), ("score", 1.9)])
def test_all_scalar_metadata_score_order_and_same_parent_preserved(search_store, score_key, score):
    store, _, _ = search_store
    original = {name: value for name, value in row().items() if not name.endswith("vector")}
    second = dict(original, id="a" * 64, child_id="a" * 64, text="Second child")
    first_entity = dict(original); del first_entity["id"]
    store.client.hybrid_search = lambda **kwargs: [[
        {"id": original["id"], "entity": first_entity, score_key: score},
        {"id": second["id"], "entity": second, score_key: score - 0.25}]]
    docs = store.hybrid_search_children("报警")
    assert len(docs) == 2 and docs[0].page_content == original["text"] and docs[1].page_content == "Second child"
    assert docs[0].metadata == {**{k: v for k, v in original.items() if k != "text"}, "retrieval_score": score}
    assert docs[0].metadata["parent_id"] == docs[1].metadata["parent_id"]
    assert docs[1].metadata["retrieval_score"] == score - 0.25


@pytest.mark.parametrize("mode,plan,error", [("legacy", None, ValueError), ("manufacturing", "true", TypeError),
                                            ("manufacturing", {"expr": "true"}, TypeError)])
def test_mode_and_raw_expression_rejected_before_models(search_store, mode, plan, error):
    store, calls, embeddings = search_store; store.schema_mode = mode
    with pytest.raises(error):
        store.hybrid_search_children("报警", filter_plan=plan)
    assert not calls and not embeddings


@pytest.mark.parametrize("mutation", ["missing_field", "conflicting_pk", "bad_child_id", "no_score", "nan_score"])
def test_invalid_hits_fail_instead_of_silent_metadata_loss(search_store, mutation):
    store, _, _ = search_store
    entity = {name: value for name, value in row().items() if not name.endswith("vector")}
    hit = {"id": entity["id"], "entity": entity, "distance": 0.8}
    if mutation == "missing_field": del entity["manufacturer"]
    if mutation == "conflicting_pk": hit["id"] = "a" * 64
    if mutation == "bad_child_id": entity["child_id"] = "a" * 64
    if mutation == "no_score": del hit["distance"]
    if mutation == "nan_score": hit["distance"] = float("nan")
    store.client.hybrid_search = lambda **kwargs: [[hit]]
    with pytest.raises(ValueError): store.hybrid_search_children("报警")


def test_real_sdk_requests_offline():
    pymilvus = pytest.importorskip("pymilvus")
    expr = build_filter_plan(analysis(equipment_model="MZ-2000")).expression
    request = pymilvus.AnnSearchRequest(data=[[1, 0]], anns_field="dense_vector",
        param={"metric_type": "IP", "nprobe": 10}, limit=5, expr=expr)
    assert request.expr == expr and request.limit == 5 and request.param["nprobe"] == 10
    assert pymilvus.WeightedRanker(0.8, 0.3).dict()["params"]["weights"] == [0.8, 0.3]
