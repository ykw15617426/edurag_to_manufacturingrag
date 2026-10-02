"""Strict planner contract and conservative identifier-preserving query variants."""
from enum import Enum
import json
import re
from typing import Protocol
from pydantic import BaseModel, ConfigDict, StrictStr, model_validator
from .entities import evidence_spans


class RetrievalStrategy(str, Enum):
    DIRECT = "direct"
    REWRITE = "rewrite"
    SUBQUERY = "subquery"


def validate_query(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 16384:
        raise ValueError("invalid_query")
    value.encode("utf-8", errors="strict")
    return value


class StrategyDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    strategy: RetrievalStrategy
    rewritten_query: StrictStr | None = None
    subqueries: tuple[StrictStr, ...] = ()
    reason_code: StrictStr

    @model_validator(mode="after")
    def contract(self):
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", self.reason_code):
            raise ValueError("invalid_reason_code")
        if self.strategy == RetrievalStrategy.DIRECT:
            if self.rewritten_query is not None or self.subqueries:
                raise ValueError("direct_has_variants")
        elif self.strategy == RetrievalStrategy.REWRITE:
            if self.rewritten_query is None or self.subqueries:
                raise ValueError("rewrite_requires_one_query")
            validate_query(self.rewritten_query)
        else:
            if self.rewritten_query is not None or not 1 <= len(self.subqueries) <= 4:
                raise ValueError("subquery_count")
            for query in self.subqueries:
                validate_query(query)
            unique, seen = [], set()
            for query in self.subqueries:
                key = " ".join(query.split())
                if key not in seen:
                    unique.append(query)
                    seen.add(key)
            object.__setattr__(self, "subqueries", tuple(unique))
        return self


class StructuredStrategyPlanner(Protocol):
    """Caller owns transport timeout; core performs no model/API request."""
    def plan(self, query, analysis) -> str | StrategyDecision: ...


def parse_decision(payload):
    if isinstance(payload, StrategyDecision):
        return StrategyDecision.model_validate(payload.model_dump())
    if not isinstance(payload, str) or len(payload.encode("utf-8")) > 32768:
        raise ValueError("invalid_planner_json")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = value
        return result
    raw = json.loads(payload, object_pairs_hook=unique,
                     parse_constant=lambda _: (_ for _ in ()).throw(ValueError("invalid_json_constant")))
    if not isinstance(raw, dict):
        raise ValueError("invalid_planner_json")
    return StrategyDecision.model_validate(raw)


class VariantError(ValueError):
    pass


def query_variants(original, analysis, decision):
    validate_query(original)
    variants = (() if decision.strategy == RetrievalStrategy.DIRECT else
                (decision.rewritten_query,) if decision.strategy == RetrievalStrategy.REWRITE else decision.subqueries)
    # Unknown ASCII words can also be identifiers. Fail closed instead of guessing
    # an enterprise identifier dictionary, translating case, or stripping zeros.
    token_pattern = r"[A-Za-z0-9][A-Za-z0-9_.-]*"
    original_tokens = set(re.findall(token_pattern, original))
    seen = {" ".join(original.split())}
    accepted = []
    for variant in variants:
        validate_query(variant)
        for field in ("equipment_model", "alarm_code", "part_number"):
            value = getattr(analysis.entities, field)
            if value is not None and not evidence_spans(variant, value):
                raise VariantError("hard_identifier_not_preserved")
        if set(re.findall(token_pattern, variant)) - original_tokens:
            raise VariantError("new_identifier_token")
        key = " ".join(variant.split())
        if key not in seen:
            accepted.append(variant)
            seen.add(key)
    if variants and not accepted:
        raise VariantError("duplicate_query_variant")
    return (original, *accepted)
