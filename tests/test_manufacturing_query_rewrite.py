"""Planner schema and exact identifier invariants; no real LLM calls."""
import json
import pytest
from pydantic import ValidationError
from test_manufacturing_metadata_filters import analysis
from rag_qa.query.rewrite import StrategyDecision, parse_decision, query_variants, VariantError


ORIGINAL = "mZ_0002 报警 E-001 配件 00001234 如何检查？"
PARSED = analysis(equipment_model="mZ_0002", alarm_code="E-001", part_number="00001234")


def decision(strategy="rewrite", **kwargs):
    return StrategyDecision(strategy=strategy, reason_code="explicit_plan", **kwargs)


@pytest.mark.parametrize("strategy,kwargs", [
    ("direct", {}), ("rewrite", {"rewritten_query": "mZ_0002 E-001 00001234 检查步骤"}),
    ("subquery", {"subqueries": ["mZ_0002 E-001 00001234 原因", "mZ_0002 E-001 00001234 处理"]})])
def test_valid_contract_original_first(strategy, kwargs):
    plan = parse_decision(json.dumps(dict(strategy=strategy, reason_code="explicit_plan", **kwargs)))
    variants = query_variants(ORIGINAL, PARSED, plan)
    assert variants[0] == ORIGINAL and len(variants) == (1 if strategy == "direct" else 2 if strategy == "rewrite" else 3)


@pytest.mark.parametrize("kwargs", [
    dict(strategy="hyde"), dict(strategy="DIRECT"), dict(strategy="direct", rewritten_query="text"),
    dict(strategy="direct", subqueries=["text"]), dict(strategy="rewrite"),
    dict(strategy="rewrite", rewritten_query=""), dict(strategy="rewrite", rewritten_query="  "),
    dict(strategy="rewrite", rewritten_query=12), dict(strategy="rewrite", rewritten_query="x" * 16385),
    dict(strategy="rewrite", rewritten_query="\ud800"), dict(strategy="rewrite", rewritten_query="text", subqueries=["text"]),
    dict(strategy="subquery"), dict(strategy="subquery", subqueries=["a"] * 5),
    dict(strategy="subquery", subqueries=[""]),
    dict(strategy="subquery", subqueries=["ok", 2]), dict(strategy="direct", extra="injected"),
    dict(strategy="direct", reason_code="free form explanation")])
def test_strict_schema_rejects_invalid_payload(kwargs):
    with pytest.raises(ValidationError):
        StrategyDecision.model_validate(dict(dict(reason_code="explicit_plan"), **kwargs))


@pytest.mark.parametrize("payload", ["direct", "```json\n{}\n```", "[]", "null", "{} trailing",
    '{"strategy":"direct","strategy":"rewrite","reason_code":"x"}',
    '{"strategy":"direct","reason_code":"x","extra":NaN}', " " * 32769],
    ids=["text", "fence", "array", "null", "trailing", "duplicate_key", "nan", "oversize"])
def test_strict_json(payload):
    with pytest.raises(ValueError): parse_decision(payload)


@pytest.mark.parametrize("variant", [
    "mZ_0002 E-001 检查", "MZ_0002 E-001 00001234 检查", "mZ-0002 E-001 00001234 检查",
    "mZ_0002 E-001 1234 检查", "XmZ_0002 E-001 00001234 检查", "mZ_0002 E-0012 00001234 检查",
    "mZ_0002 E-001 00001234 PN-001 检查", "mZ_0002 E-001 00001234 E102 检查",
    "mZ_0002 E-001 00001234 型号 ABC 检查", "mZ_0002 E-001 00001234 causes 检查",
    ORIGINAL, " "+ORIGINAL+" "])
def test_rejects_loss_mutation_new_ascii_and_duplicate(variant):
    with pytest.raises(VariantError):
        query_variants(ORIGINAL, PARSED, decision(rewritten_query=variant))


def test_one_invalid_subquery_rejects_whole_decision():
    plan = decision("subquery", subqueries=["mZ_0002 E-001 00001234 原因", "mZ_0002 E999 00001234 处理"])
    with pytest.raises(VariantError): query_variants(ORIGINAL, PARSED, plan)


def test_unassigned_identifier_not_added_and_original_not_mutated():
    original = "MZ-2000 主轴振动"
    with pytest.raises(VariantError):
        query_variants(original, analysis(equipment_model="MZ-2000"), decision(rewritten_query="MZ-2000 E102 振动原因"))
    assert query_variants(original, analysis(equipment_model="MZ-2000"), decision(rewritten_query="MZ-2000 主轴振动原因")) == (original, "MZ-2000 主轴振动原因")


def test_stable_subquery_dedup_including_original():
    variant = "mZ_0002 E-001 00001234 原因"
    plan = decision("subquery", subqueries=[ORIGINAL, variant, " "+variant+" "])
    assert plan.subqueries == (ORIGINAL, variant)
    assert query_variants(ORIGINAL, PARSED, plan) == (ORIGINAL, variant)
