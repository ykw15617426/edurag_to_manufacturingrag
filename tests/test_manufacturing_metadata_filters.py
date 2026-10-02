"""Offline trust-policy and expression safety tests."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag_qa.query import QueryAnalyzer
from rag_qa.query.schemas import QueryAnalysis
from rag_qa.retrieval.filters import FilterMode, MetadataFilterPlan, build_expression, build_filter_plan


def analysis(intent="alarm_fault", confidence="high", warnings=None, **entities):
    return QueryAnalysis(intent=intent, confidence=confidence, entities=entities,
                         analysis_source="rules", warnings=warnings or [])


@pytest.mark.parametrize("intent,types", [
    ("alarm_fault", ("alarm", "fault", "case", "manual")),
    ("maintenance", ("maintenance", "case", "manual")),
    ("parameter", ("parameter", "manual")), ("parts", ("parts", "manual")),
    ("knowledge", None), ("general", None),
])
def test_intent_is_soft_multiple_types(intent, types):
    plan = build_filter_plan(analysis(intent=intent))
    assert plan.soft_filters.get("knowledge_type") == types
    assert plan.mode == (FilterMode.STRICT if types else FilterMode.NONE)


@pytest.mark.parametrize("confidence,mode", [("high", "STRICT"), ("medium", "RELAXED"), ("low", "RELAXED")])
def test_hard_filters_survive_confidence(confidence, mode):
    plan = build_filter_plan(analysis(confidence=confidence, equipment_model="MZ-2000",
                                      alarm_code="E102", part_number="PN-000_A"))
    assert plan.mode == mode
    assert dict(plan.hard_filters) == {"equipment_model": "MZ-2000", "alarm_code": "E102", "part_number": "PN-000_A"}
    assert 'equipment_model == "MZ-2000" and alarm_code == "E102" and part_number == "PN-000_A"' in plan.expression
    assert bool(plan.soft_filters) == (confidence == "high")


@pytest.mark.parametrize("confidence", ["medium", "low"])
def test_no_hard_low_trust_is_none(confidence):
    plan = build_filter_plan(analysis(confidence=confidence, manufacturer="ACME", fault_symptom="振动异常"))
    assert plan.mode == "NONE" and plan.expression == ""


@pytest.mark.parametrize("warning", ["ambiguous_equipment_model", "semantic_entity_conflict_equipment_model",
                                    "multiple_intent_cues", "semantic_classifier_failed",
                                    "semantic_entity_role_conflict_alarm_code"])
def test_warning_disables_soft_but_preserves_unambiguous_hard(warning):
    plan = build_filter_plan(analysis(warnings=[warning], equipment_model="MZ-2000", alarm_code="E102"))
    assert not plan.soft_filters
    assert plan.hard_filters["alarm_code"] == "E102"
    assert ("equipment_model" in plan.hard_filters) == (warning != "ambiguous_equipment_model")
    assert plan.warnings == (warning,)


@pytest.mark.parametrize("query,hard", [
    ("MZ-2000 报警 E102 怎么处理？", {"equipment_model": "MZ-2000", "alarm_code": "E102"}),
    ("MZ-2000 多久润滑一次？", {"equipment_model": "MZ-2000"}),
    ("型号 MZ-2000 或型号 CX-0030 怎么启动？", {}),
    ("怎么启动这台设备？", {}),
])
def test_real_stage5_boundary(query, hard):
    plan = build_filter_plan(QueryAnalyzer().analyze(query))
    assert dict(plan.hard_filters) == hard


def test_symptom_never_equality_and_general_hard_stays():
    plan = build_filter_plan(analysis(intent="general", confidence="low", equipment_model="MZ-2000",
                                      fault_symptom="振动异常"))
    assert plan.mode == "RELAXED" and plan.expression == 'equipment_model == "MZ-2000"'


@pytest.mark.parametrize("value", ['ACME" or alarm_code == "E999', "ACME\\厂", "ACME == []", '中文"\\==[]'])
def test_literal_cannot_escape(value):
    expression = build_expression({}, {"manufacturer": value})
    assert expression == "manufacturer == " + json.dumps(value, ensure_ascii=False)
    assert json.loads(expression.removeprefix("manufacturer == ")) == value


@pytest.mark.parametrize("hard,soft", [
    ({"text": "x"}, {}), ({"manufacturer": "x"}, {}), ({}, {"equipment_model": "MZ-2000"}),
    ({}, {"fault_symptom": "x"}), ({}, {"knowledge_type": ["manual\" or true"]}),
    ({}, {"knowledge_type": "manual"}), ({"alarm_code": 'E102" or true'}, {}),
    ({}, {"manufacturer": 123}), ({}, {"manufacturer": " ACME "}),
])
def test_invalid_conditions_rejected(hard, soft):
    with pytest.raises(ValueError):
        build_expression(hard, soft)


def test_plan_immutable_and_only_soft_removed():
    hard, soft = {"equipment_model": "MZ-2000"}, {"manufacturer": "ACME", "knowledge_type": ["manual"]}
    plan = MetadataFilterPlan(FilterMode.STRICT, hard, soft)
    hard.clear(); soft["knowledge_type"].append("fault")
    assert plan.soft_filters["knowledge_type"] == ("manual",)
    with pytest.raises(TypeError):
        plan.hard_filters["alarm_code"] = "E102"
    relaxed = plan.relax_after_zero_hits()
    assert relaxed.hard_filters == plan.hard_filters and not relaxed.soft_filters
    assert relaxed.mode == "RELAXED" and relaxed.removed_fields == ("manufacturer", "knowledge_type")
    assert relaxed.relaxation_reason == "zero_hits_drop_soft_filters"
    assert relaxed.relax_after_zero_hits() is None


def test_empty_expression_and_no_raw_expression_input():
    assert build_expression({}, {}) == ""
    with pytest.raises(TypeError):
        MetadataFilterPlan("NONE", expression="true")
