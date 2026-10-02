"""Actual Stage 6/7 composition using synthetic hits and recording adapters."""
import json
from types import SimpleNamespace
import pytest
from base.config import config
from test_manufacturing_metadata_filters import analysis
from test_manufacturing_milvus_schema import vector_store_unit
from test_manufacturing_parent_retrieval import scorer
from test_manufacturing_retrieval import Gateway
from test_manufacturing_fast_path import alarm, ParentGateway
from test_parent_aggregation import hit
from rag_qa.retrieval import ManufacturingRetriever
from rag_qa.retrieval.fast_path import ManufacturingFastPath, FastPathCorpus, FastPathEligibility
from rag_qa.retrieval.strategy import ManufacturingStrategyRetriever, fuse_children, ChildFusionError
from rag_qa.retrieval.manufacturing_bm25 import BM25AcceptancePolicy
from rag_qa.retrieval.parent_reranker import RerankerError


def planner(strategy="rewrite", **kwargs):
    return SimpleNamespace(plan=lambda query, parsed: json.dumps(dict(strategy=strategy, reason_code="explicit_plan", **kwargs)))


def setup(responses, scorer, plan=None, fast=None):
    gateway = Gateway(responses)
    gateway.reranker = scorer[0]
    return ManufacturingStrategyRetriever(ManufacturingRetriever(gateway), planner=plan, fast_path=fast), gateway


def test_no_planner_direct(vector_store_unit, scorer):
    engine, gateway = setup([[hit()]], scorer)
    parsed = analysis(equipment_model="MZ-2000")
    result = engine.retrieve("MZ-2000 报警原因", parsed, k=7)
    assert result.strategy == "direct" and result.decision_source == "default" and result.fallback_reason is None
    assert result.query_variants == (result.original_query,) and len(result.retrieval_attempts) == 1
    assert gateway.calls[0][1]["k"] == 7 and len(scorer[1]) == 1


@pytest.mark.parametrize("strategy,kwargs", [("direct", {}), ("rewrite", {"rewritten_query": "MZ-2000 故障原因"}),
    ("subquery", {"subqueries": ["MZ-2000 故障原因", "MZ-2000 处理步骤"]})])
def test_original_analysis_reused_and_rerank_once(vector_store_unit, scorer, monkeypatch, strategy, kwargs):
    count = 1 + len(kwargs.get("subqueries", [])) + bool(kwargs.get("rewritten_query"))
    engine, gateway = setup([[hit(child=str(i+1), score=.5+i/10)] for i in range(count)], scorer, planner(strategy, **kwargs))
    captured = []
    original_retrieve = engine.retriever.retrieve
    engine.retriever.retrieve = lambda query, parsed, k=None: captured.append(parsed) or original_retrieve(query, parsed, k=k)
    monkeypatch.setattr(config, "CANDIDATE_M", 1)
    parsed = analysis(equipment_model="MZ-2000", manufacturer="ACME")
    result = engine.retrieve("MZ-2000 怎么处理", parsed)
    assert result.strategy == strategy and result.decision_source == "planner"
    assert all(item is parsed for item in captured) and len(captured) == count
    assert [call[0] for call in gateway.calls] == list(result.query_variants)
    assert all(call[1]["k"] == config.RETRIEVAL_K for call in gateway.calls)
    assert all(call[1]["filter_plan"].hard_filters == {"equipment_model":"MZ-2000"} for call in gateway.calls)
    assert len(scorer[1]) == 1 and all(pair[0] == result.original_query for pair in scorer[1][0])
    assert result.documents[0].metadata["child_hit_count"] == count


@pytest.mark.parametrize("bad,reason", [
    (TimeoutError(), "planner_timeout"), (RuntimeError("secret"), "planner_error"),
    ("not JSON", "planner_invalid_json"), ('{"strategy":"hyde","reason_code":"x"}', "planner_invalid_schema"),
    (json.dumps(dict(strategy="rewrite", reason_code="x", rewritten_query="E102 处理")), "hard_identifier_not_preserved"),
    (json.dumps(dict(strategy="rewrite", reason_code="x", rewritten_query="MZ-2000 E102 处理")), "new_identifier_token"),
    (json.dumps(dict(strategy="subquery", reason_code="x", subqueries=["MZ-2000 原因", "MZ-2000 E102 处理"])), "new_identifier_token"),
    (json.dumps(dict(strategy="subquery", reason_code="x", subqueries=["MZ-2000 原因"]*5)), "planner_invalid_schema")])
def test_whole_decision_fallback(vector_store_unit, scorer, bad, reason):
    def plan(*args):
        if isinstance(bad, Exception): raise bad
        return bad
    engine, gateway = setup([[hit()]], scorer, SimpleNamespace(plan=plan))
    result = engine.retrieve("MZ-2000 怎么处理", analysis(equipment_model="MZ-2000"))
    assert result.strategy == "direct" and result.fallback_reason == reason and result.decision_source == "fallback"
    assert len(gateway.calls) == 1 and result.query_variants == (result.original_query,)


def test_fusion_max_score_tie_and_provenance():
    results = [SimpleNamespace(documents=[hit(child="2", score=.7), hit(child="1", score=.6)]),
               SimpleNamespace(documents=[hit(child="1", score=.9), hit(child="3", score=.7), hit(child="2", score=.7)])]
    fused, signals = fuse_children(results)
    assert [d.metadata["child_id"] for d in fused] == ["1"*64, "2"*64, "3"*64]
    assert [d.metadata["retrieval_score"] for d in fused] == [.9, .7, .7]
    assert signals[0].variant_indices == (1, 2) and signals[0].winning_variant_index == 2
    assert signals[1].winning_variant_index == 1
    assert results[0].documents[1].metadata["retrieval_score"] == .6


@pytest.mark.parametrize("changes", [dict(parent_id="b"*64), dict(document_version="2"), dict(custom="new")])
def test_fusion_conflicting_metadata_fails(changes):
    with pytest.raises(ChildFusionError):
        fuse_children([SimpleNamespace(documents=[hit()]), SimpleNamespace(documents=[hit(**changes)])])


def test_fusion_conflicting_content_fails():
    other = hit(); other.page_content = "different child"
    with pytest.raises(ChildFusionError): fuse_children([SimpleNamespace(documents=[hit(), other])])


@pytest.mark.parametrize("score", [float("nan"), float("inf"), True, "0.8"])
def test_fusion_invalid_scores(score):
    with pytest.raises(ChildFusionError): fuse_children([SimpleNamespace(documents=[hit(score=score)])])


def test_fused_duplicates_aggregate_once_and_top_m_after_all_scored(vector_store_unit, scorer, monkeypatch):
    engine, gateway = setup([[hit(score=.6), hit(parent="b", child="2")], [hit(score=.9), hit(parent="c", child="3")]], scorer,
                            planner(rewritten_query="MZ-2000 故障原因"))
    monkeypatch.setattr(config, "CANDIDATE_M", 1)
    result = engine.retrieve("MZ-2000 怎么处理", analysis(equipment_model="MZ-2000"))
    assert len(result.documents) == 1 and len(scorer[1]) == 1 and len(scorer[1][0]) == 3
    assert result.documents[0].metadata["child_hit_count"] == 1 and result.documents[0].metadata["best_retrieval_score"] == .9
    assert len(result.fusion_signals) == 3 and len(gateway.calls) == 2


@pytest.mark.parametrize("intent", ["alarm_fault", "parts", "maintenance", "parameter", "knowledge", "general"])
def test_intent_governance_public_probe_and_legacy_compatibility(vector_store_unit, scorer, intent):
    parent = ParentGateway()
    fast = ManufacturingFastPath(FastPathCorpus([alarm()]), parent)
    engine, gateway = setup([[hit()]], scorer, fast=fast)
    parsed = analysis(intent=intent, equipment_model="MZ-2000", alarm_code="E102")
    result = engine.retrieve("MZ-2000 E102 处理所需工具", parsed)
    if intent == "alarm_fault":
        assert result.fast_path_attempt.match_type == "exact_alarm" and not gateway.calls and not scorer[1]
    else:
        assert result.fast_path_attempt.status == "FALLBACK" and len(gateway.calls) == 1
    assert not parent.calls
    # Stage 8's pre-existing public entry retains its original behavior.
    assert fast.retrieve_with_fast_path("MZ-2000 E102 处理所需工具", parsed).match_type == "exact_alarm"


def test_disabled_all_fast_paths_and_no_parent_fallback():
    parent = ParentGateway(); fast = ManufacturingFastPath(FastPathCorpus([alarm()]), parent)
    result = fast.probe(alarm().question, analysis(equipment_model="MZ-2000", alarm_code="E102"),
                        eligibility=FastPathEligibility(False, False, False))
    assert result.status == "FALLBACK" and not result.evidence and result.parent_result is None and not parent.calls


def test_other_intent_can_exact_faq_without_alarm_shortcut(vector_store_unit, scorer):
    fast = ManufacturingFastPath(FastPathCorpus([alarm()]), ParentGateway())
    engine, gateway = setup([], scorer, SimpleNamespace(plan=lambda *_: pytest.fail("planner bypassed")), fast)
    result = engine.retrieve(alarm().question, analysis(intent="parts", equipment_model="MZ-2000", alarm_code="E102"))
    assert result.fast_path_attempt.match_type == "exact_faq" and not gateway.calls


def test_zero_hits_relax_only_soft_for_each_variant(vector_store_unit, scorer):
    engine, gateway = setup([[], [], [], []], scorer, planner(rewritten_query="MZ-2000 故障原因"))
    result = engine.retrieve("MZ-2000 怎么处理", analysis(equipment_model="MZ-2000", manufacturer="ACME"))
    assert not result.documents and not scorer[1]
    assert [len(a.attempts) for a in result.retrieval_attempts] == [2, 2]
    assert all(c[1]["filter_plan"].hard_filters == {"equipment_model":"MZ-2000"} for c in gateway.calls)


def test_child_failure_propagates_without_unfiltered_retry(vector_store_unit, scorer):
    engine, gateway = setup([RuntimeError("child failure")], scorer)
    with pytest.raises(RuntimeError, match="child failure"):
        engine.retrieve("MZ-2000 怎么处理", analysis(equipment_model="MZ-2000"))
    assert len(gateway.calls) == 1


def test_four_subqueries_bounded_and_stable(vector_store_unit, scorer):
    queries = ["MZ-2000 原因", "MZ-2000 步骤", "MZ-2000 检查", "MZ-2000 注意事项"]
    engine, gateway = setup([[hit()]] * 5, scorer, planner("subquery", subqueries=queries))
    result = engine.retrieve("MZ-2000 怎么处理", analysis(equipment_model="MZ-2000"))
    assert result.query_variants == (result.original_query, *queries) and len(gateway.calls) == 5
    assert result.fusion_signals[0].variant_indices == (1, 2, 3, 4, 5)
    assert len(scorer[1]) == 1 and result.documents[0].metadata["child_hit_count"] == 1


def test_other_intent_bm25_requires_explicit_policy(vector_store_unit, scorer):
    fast = ManufacturingFastPath(FastPathCorpus([alarm()]), ParentGateway(), acceptance_policy=BM25AcceptancePolicy(-100))
    engine, gateway = setup([], scorer, fast=fast)
    result = engine.retrieve("MZ-2000 E102 需要更换哪个备件", analysis(intent="parts", equipment_model="MZ-2000", alarm_code="E102"))
    assert result.fast_path_attempt.match_type == "bm25_faq" and not gateway.calls


def test_fast_runtime_failure_continues_to_planner(vector_store_unit, scorer, monkeypatch):
    parent = ParentGateway(); fast = ManufacturingFastPath(FastPathCorpus([alarm()]), parent)
    def broken(*args): raise RuntimeError("hidden error")
    monkeypatch.setattr(fast.corpus.bm25, "rank", broken)
    engine, gateway = setup([[hit()], [hit()]], scorer, planner(rewritten_query="MZ-2000 E102 备件清单"), fast)
    result = engine.retrieve("MZ-2000 E102 更换哪个备件", analysis(intent="parts", equipment_model="MZ-2000", alarm_code="E102"))
    assert result.fast_path_attempt.reason == "fast_path_error" and result.strategy == "rewrite"
    assert len(gateway.calls) == 2 and not parent.calls


def test_rerank_failure_does_not_try_other_query(vector_store_unit, scorer):
    scorer[0].predict = lambda _: [float("nan")]
    engine, gateway = setup([[hit()]], scorer)
    with pytest.raises(RerankerError):
        engine.retrieve("MZ-2000 怎么处理", analysis(equipment_model="MZ-2000"))
    assert len(gateway.calls) == 1


@pytest.mark.parametrize("original", ["", " ", "\ud800", "x" * 16385], ids=["empty", "space", "unicode", "length"])
def test_invalid_original_no_planner_or_search(vector_store_unit, scorer, original):
    engine, gateway = setup([], scorer, SimpleNamespace(plan=lambda *_: pytest.fail("invalid input planner")))
    with pytest.raises(ValueError): engine.retrieve(original, analysis())
    assert not gateway.calls
