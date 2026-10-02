"""Evidence decisions and unchanged Stage 7 fallback using synthetic approved data."""
from types import SimpleNamespace
import pytest

from test_manufacturing_bm25 import entry
from test_manufacturing_metadata_filters import analysis
from test_manufacturing_parent_retrieval import scorer
from test_manufacturing_milvus_schema import vector_store_unit
from test_parent_aggregation import hit
from test_manufacturing_retrieval import Gateway
from rag_qa.query import QueryAnalyzer
from rag_qa.retrieval import ManufacturingRetriever
from rag_qa.retrieval.fast_path import FastPathCorpus, ManufacturingFastPath, MatchType
from rag_qa.retrieval.manufacturing_bm25 import BM25AcceptancePolicy


class ParentGateway:
    def __init__(self): self.calls = []
    def retrieve_parents(self, query, analysis, k=None):
        self.calls.append((query, analysis, k))
        return SimpleNamespace(documents=("synthetic parent",), attempts=("filter attempt",))


def alarm(entry_id="alarm1", **values):
    return entry(entry_id, **dict(dict(knowledge_type="alarm", alarm_code="E102", question="MZ-2000 报警 E102 怎么处理？"), **values))


def test_unique_exact_alarm_hard_conjunction_returns_evidence_only():
    corpus = FastPathCorpus([alarm(), alarm("other", equipment_model="CX-3000")])
    parent = ParentGateway()
    result = ManufacturingFastPath(corpus, parent).retrieve_with_fast_path(
        "MZ-2000 报警 E102 怎么处理？", analysis(equipment_model="MZ-2000", alarm_code="E102"))
    assert result.status == "ACCEPTED" and result.match_type == MatchType.EXACT_ALARM
    assert result.evidence[0].page_content == alarm().evidence_text and result.matched_entry.entry_id == "alarm1"
    assert result.evidence[0].metadata["document_version"] == "1.10"
    assert not parent.calls and result.bm25_score is None and result.rank is None
    assert not hasattr(result, "answer") and "answer" not in result.evidence[0].metadata


def test_cross_model_alarm_ambiguity_cannot_bypass_via_faq_or_bm25():
    query = "E102 怎么处理？"
    corpus = FastPathCorpus([alarm(question=query), alarm("other", equipment_model="CX-3000", evidence_text="Different meaning")])
    parent = ParentGateway(); parsed = analysis(alarm_code="E102")
    result = ManufacturingFastPath(corpus, parent, acceptance_policy=BM25AcceptancePolicy(-100)).retrieve_with_fast_path(query, parsed, k=4)
    assert result.match_type == "fallback" and result.reason == "ambiguous_alarm_evidence"
    assert parent.calls == [(query, parsed, 4)] and parent.calls[0][1] is parsed


def test_single_approved_alarm_meaning_without_model():
    result = ManufacturingFastPath(FastPathCorpus([alarm()]), ParentGateway()).retrieve_with_fast_path("E102 怎么处理？", analysis(alarm_code="E102"))
    assert result.match_type == "exact_alarm" and result.reason == "unique_alarm_meaning_in_approved_corpus"


def test_actual_stage5_unresolved_alarm_token_does_not_guess():
    query = "E102 怎么处理？"
    parent = ParentGateway()
    result = ManufacturingFastPath(FastPathCorpus([alarm(), alarm("other", equipment_model="CX-3000")]), parent,
        acceptance_policy=BM25AcceptancePolicy(-100)).retrieve_with_fast_path(query, QueryAnalyzer().analyze(query))
    assert result.match_type == "fallback" and result.reason == "unresolved_alarm_identifier"


def test_exact_faq_normalization_and_identifier_case():
    corpus = FastPathCorpus([entry(question="Café mZ_0002 00001234 启动", equipment_model="mZ_0002")])
    parent = ParentGateway(); fast = ManufacturingFastPath(corpus, parent)
    result = fast.retrieve_with_fast_path("  Cafe\u0301 \n mZ_0002\t00001234 启动 ", analysis(intent="knowledge", equipment_model="mZ_0002"))
    assert result.match_type == "exact_faq"
    rejected = fast.retrieve_with_fast_path("Café MZ_0002 00001234 启动", analysis(intent="knowledge", equipment_model="MZ_0002"))
    assert rejected.match_type == "fallback" and rejected.reason == "no_compatible_entries"


def test_duplicate_exact_questions_are_not_arbitrarily_selected():
    query = "怎么启动设备？"
    result = ManufacturingFastPath(FastPathCorpus([entry(question=query), entry("second", question=query)]), ParentGateway()).retrieve_with_fast_path(query, analysis(intent="knowledge"))
    assert result.reason == "ambiguous_exact_faq" and result.status == "FALLBACK"


@pytest.mark.parametrize("policy,reason,accepted", [(None, "bm25_policy_not_enabled", False),
    (BM25AcceptancePolicy(-100), "bm25_accepted_by_explicit_policy", True),
    (BM25AcceptancePolicy(10000), "bm25_rejected_by_policy", False)])
def test_similar_faq_policy_raw_score_rank_and_fallback(policy, reason, accepted):
    parent = ParentGateway()
    corpus = FastPathCorpus([entry(), entry("other", question="冷却泵检查", equipment_model="CX-3000")])
    result = ManufacturingFastPath(corpus, parent, acceptance_policy=policy).retrieve_with_fast_path("MZ-2000 主轴如何润滑？", analysis(intent="maintenance", equipment_model="MZ-2000"))
    assert result.reason == reason and len(result.candidates) == 1
    assert result.bm25_score == result.candidates[0].raw_score and result.rank == 1 and result.corpus_size == 2
    assert result.status == ("ACCEPTED" if accepted else "FALLBACK")
    assert bool(parent.calls) == (not accepted)
    assert result.match_type == ("bm25_faq" if accepted else "fallback")


@pytest.mark.parametrize("field,value", [("equipment_model", "MZ-2000"), ("alarm_code", "E102"), ("part_number", "PN-001")])
def test_missing_or_wrong_hard_metadata_not_compatible(field, value):
    query = "如何润滑？"
    parent = ParentGateway()
    corpus = FastPathCorpus([entry(**{field: None}), entry("wrong", **{field: "WRONG"})])
    result = ManufacturingFastPath(corpus, parent, acceptance_policy=BM25AcceptancePolicy(-100)).retrieve_with_fast_path(query, analysis(**{field: value}))
    assert result.reason == "no_compatible_entries" and len(parent.calls) == 1


def test_ambiguous_stage5_hard_warning_forces_parent():
    parsed = analysis(equipment_model=None, warnings=["ambiguous_equipment_model"])
    result = ManufacturingFastPath(FastPathCorpus([entry()]), ParentGateway()).retrieve_with_fast_path(entry().question, parsed)
    assert result.reason == "ambiguous_hard_identifier" and result.match_type == "fallback"


@pytest.mark.parametrize("stage", ["search", "policy"])
def test_runtime_errors_fallback_without_disclosing_exception(monkeypatch, stage):
    parent = ParentGateway(); corpus = FastPathCorpus([entry()])
    fast = ManufacturingFastPath(corpus, parent, acceptance_policy=SimpleNamespace(accepts=lambda c: (_ for _ in ()).throw(RuntimeError("private details"))))
    if stage == "search": monkeypatch.setattr(corpus.bm25, "rank", lambda *args: (_ for _ in ()).throw(RuntimeError("private details")))
    parsed = analysis(equipment_model="MZ-2000")
    result = fast.retrieve_with_fast_path("主轴润滑方法", parsed, k=8)
    assert result.reason == "fast_path_error" and result.warnings == ("fast_path_error",)
    assert parent.calls == [("主轴润滑方法", parsed, 8)] and "private" not in repr(result)


def test_stage7_errors_propagate():
    class FailedParent:
        def retrieve_parents(self, *args, **kwargs): raise RuntimeError("Stage 7 failed")
    with pytest.raises(RuntimeError, match="Stage 7 failed"):
        ManufacturingFastPath(FastPathCorpus([]), FailedParent()).retrieve_with_fast_path("query", analysis())


@pytest.mark.parametrize("mode", ["alarm", "faq"])
def test_unrelated_corpus_expansion_does_not_change_exact_decision(mode):
    target = alarm() if mode == "alarm" else entry()
    expanded = [entry(f"unrelated{i:03}", question=f"QX-{i:04} 电柜检查", equipment_model=None) for i in range(200)]
    parsed = analysis(equipment_model="MZ-2000", **({"alarm_code": "E102"} if mode == "alarm" else {}))
    small = ManufacturingFastPath(FastPathCorpus([target]), ParentGateway()).retrieve_with_fast_path(target.question, parsed)
    big = ManufacturingFastPath(FastPathCorpus([target, *expanded]), ParentGateway()).retrieve_with_fast_path(target.question, parsed)
    assert small.match_type == big.match_type and small.evidence == big.evidence and small.reason == big.reason
    assert (small.corpus_size, big.corpus_size) == (1, 201)


def test_hot_rebuild_same_exact_and_bm25_decisions():
    cold = FastPathCorpus([entry(), alarm("alarm")])
    hot = FastPathCorpus.from_json(cold.to_json())
    for query, parsed in [(entry().question, analysis()), ("MZ-2000 润滑步骤", analysis(equipment_model="MZ-2000"))]:
        assert ManufacturingFastPath(cold, ParentGateway()).retrieve_with_fast_path(query, parsed) == ManufacturingFastPath(hot, ParentGateway()).retrieve_with_fast_path(query, parsed)


def test_real_stage7_fallback_interface_keeps_parent_signals(vector_store_unit, scorer):
    gateway = Gateway([[hit(), hit(child="2")]])
    gateway.reranker = scorer[0]
    parents = ManufacturingRetriever(gateway)
    result = ManufacturingFastPath(FastPathCorpus([]), parents).retrieve_with_fast_path("原 query", analysis(equipment_model="MZ-2000"), k=6)
    assert result.status == "FALLBACK" and result.evidence[0].metadata["child_hit_count"] == 2
    assert result.parent_result.final_plan.hard_filters["equipment_model"] == "MZ-2000"
    assert gateway.calls[0][1]["k"] == 6


def test_low_confidence_hard_identifier_still_scopes_and_general_does_not_skip():
    parent = ParentGateway()
    fast = ManufacturingFastPath(FastPathCorpus([entry(equipment_model="CX-3000")]), parent,
                                 acceptance_policy=BM25AcceptancePolicy(-100))
    result = fast.retrieve_with_fast_path("主轴润滑", analysis(intent="general", confidence="low", equipment_model="MZ-2000"))
    assert result.reason == "no_compatible_entries" and len(parent.calls) == 1


def test_default_k_none_is_forwarded_to_stage7_config_source():
    parent = ParentGateway()
    ManufacturingFastPath(FastPathCorpus([]), parent).retrieve_with_fast_path("query", analysis())
    assert parent.calls[0][2] is None


def test_nonboolean_policy_output_is_runtime_error_fallback():
    result = ManufacturingFastPath(FastPathCorpus([entry()]), ParentGateway(),
        acceptance_policy=SimpleNamespace(accepts=lambda c: "accept")).retrieve_with_fast_path("主轴润滑", analysis())
    assert result.reason == "fast_path_error"
