"""Stage 6: whitelisted conditions and bounded, hard-preserving relaxation."""
from dataclasses import dataclass, field
from enum import Enum
import json
from types import MappingProxyType
from typing import Mapping

from rag_qa.query.schemas import ConfidenceLevel, QueryAnalysis, QueryEntities

HARD_FIELDS = ("equipment_model", "alarm_code", "part_number")
SOFT_FIELDS = ("manufacturer", "equipment_type", "knowledge_type")
INTENT_TYPES = MappingProxyType({
    "alarm_fault": ("alarm", "fault", "case", "manual"),
    "maintenance": ("maintenance", "case", "manual"),
    "parameter": ("parameter", "manual"),
    "parts": ("parts", "manual"),
})
KNOWLEDGE_TYPES = frozenset({"alarm", "fault", "case", "manual", "maintenance", "parameter", "parts"})


class FilterMode(str, Enum):
    STRICT = "STRICT"
    RELAXED = "RELAXED"
    NONE = "NONE"


def _conditions(filters, allowed):
    if not isinstance(filters, Mapping) or filters.keys() - set(allowed):
        raise ValueError("filter fields must belong to the fixed whitelist")
    result = {}
    for name in allowed:
        if name not in filters:
            continue
        value = filters[name]
        if name == "knowledge_type":
            if (not isinstance(value, (tuple, list)) or not value
                    or any(type(v) is not str or v not in KNOWLEDGE_TYPES for v in value)):
                raise ValueError("knowledge_type requires a nonempty list of supported types")
            result[name] = tuple(dict.fromkeys(value))
        else:
            # Reuse Stage 5 validation; no coercion or identifier normalization.
            if type(value) is not str:
                raise ValueError("filter values must be nonempty strings")
            validated = getattr(QueryEntities(**{name: value}), name)
            if validated != value:
                raise ValueError("filter values must already be trimmed")
            result[name] = value
    return MappingProxyType(result)


def build_expression(hard_filters, soft_filters):
    hard = _conditions(hard_filters, HARD_FIELDS)
    soft = _conditions(soft_filters, SOFT_FIELDS)
    clauses = []
    for name, value in (*hard.items(), *soft.items()):
        operator = " in " if name == "knowledge_type" else " == "
        clauses.append(name + operator + json.dumps(value, ensure_ascii=False))
    return " and ".join(clauses)


@dataclass(frozen=True)
class MetadataFilterPlan:
    mode: FilterMode
    hard_filters: Mapping[str, str] = field(default_factory=dict)
    soft_filters: Mapping[str, str | tuple[str, ...]] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    relaxation_reason: str | None = None
    removed_fields: tuple[str, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "mode", FilterMode(self.mode))
        object.__setattr__(self, "hard_filters", _conditions(self.hard_filters, HARD_FIELDS))
        object.__setattr__(self, "soft_filters", _conditions(self.soft_filters, SOFT_FIELDS))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "removed_fields", tuple(self.removed_fields))
        if self.mode == FilterMode.NONE and (self.hard_filters or self.soft_filters):
            raise ValueError("NONE cannot contain filters")
        if self.mode == FilterMode.RELAXED and (self.soft_filters or not self.hard_filters):
            raise ValueError("RELAXED requires hard filters only")
        if self.mode == FilterMode.STRICT and not (self.hard_filters or self.soft_filters):
            raise ValueError("STRICT requires filters")

    @property
    def expression(self):
        # A derived value, never a caller-provided raw expression.
        return build_expression(self.hard_filters, self.soft_filters)

    def relax_after_zero_hits(self):
        if not self.soft_filters:
            return None
        return MetadataFilterPlan(
            FilterMode.RELAXED if self.hard_filters else FilterMode.NONE,
            self.hard_filters, warnings=self.warnings,
            relaxation_reason="zero_hits_drop_soft_filters",
            removed_fields=tuple(self.soft_filters))


def build_filter_plan(analysis):
    if not isinstance(analysis, QueryAnalysis):
        raise TypeError("validated QueryAnalysis required")
    analysis = QueryAnalysis.model_validate(analysis.to_metadata())
    warnings = tuple(analysis.warnings)
    hard = {name: getattr(analysis.entities, name) for name in HARD_FIELDS
            if getattr(analysis.entities, name) is not None and "ambiguous_" + name not in warnings}
    unsafe_soft = any(w.startswith("ambiguous_") or "conflict" in w
                      or w in {"multiple_intent_cues", "semantic_classifier_failed", "invalid_query"}
                      or w.startswith("semantic_entity_rejected_") for w in warnings)
    soft = {}
    strict = analysis.confidence == ConfidenceLevel.HIGH and not unsafe_soft
    if strict:
        soft.update({name: getattr(analysis.entities, name) for name in SOFT_FIELDS[:2]
                     if getattr(analysis.entities, name) is not None})
        if analysis.intent.value in INTENT_TYPES:
            soft["knowledge_type"] = INTENT_TYPES[analysis.intent.value]
    mode = (FilterMode.STRICT if strict else FilterMode.RELAXED) if hard or soft else FilterMode.NONE
    return MetadataFilterPlan(mode, hard, soft, warnings,
                              None if strict else "confidence_or_warnings_disable_soft_filters")
