"""Validated Stage 5 contracts. Confidence is ordinal, not a calibrated probability."""
from enum import Enum
import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator


class QueryIntent(str, Enum):
    ALARM_FAULT = "alarm_fault"
    MAINTENANCE = "maintenance"
    PARAMETER = "parameter"
    PARTS = "parts"
    KNOWLEDGE = "knowledge"
    GENERAL = "general"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnalysisSource(str, Enum):
    RULES = "rules"
    LLM = "llm"
    HYBRID = "hybrid"
    FALLBACK = "fallback"


IDENTIFIER_FIELDS = frozenset({"equipment_model", "alarm_code", "part_number"})
IDENTIFIER_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*\Z")
ENTITY_BYTE_LIMITS = {"equipment_model": 256, "alarm_code": 128, "part_number": 256,
                      "manufacturer": 256, "equipment_type": 128, "fault_symptom": 8192}


class QueryEntities(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    equipment_model: StrictStr | None = None
    alarm_code: StrictStr | None = None
    part_number: StrictStr | None = None
    manufacturer: StrictStr | None = None
    equipment_type: StrictStr | None = None
    fault_symptom: StrictStr | None = None

    @field_validator("*", mode="before")
    @classmethod
    def trim_outer_space(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("*")
    @classmethod
    def validate_entity(cls, value, info):
        if value is None:
            return value
        if not value or len(value.encode("utf-8")) > ENTITY_BYTE_LIMITS[info.field_name]:
            raise ValueError("nonempty entity within storage byte capacity required")
        if info.field_name in IDENTIFIER_FIELDS and (
                not IDENTIFIER_PATTERN.fullmatch(value) or value.endswith(("-", "_"))):
            raise ValueError("exact ASCII identifier required; preserve case/hyphens/underscores/zeros")
        return value


WarningCode = Annotated[StrictStr, Field(min_length=1, max_length=128)]


class SemanticClassification(BaseModel):
    """Only these fields are accepted from the injected semantic classifier."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    intent: QueryIntent
    confidence: ConfidenceLevel
    entities: QueryEntities = Field(default_factory=QueryEntities)


class QueryAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    intent: QueryIntent
    confidence: ConfidenceLevel
    entities: QueryEntities = Field(default_factory=QueryEntities)
    analysis_source: AnalysisSource
    warnings: list[WarningCode] = Field(default_factory=list, max_length=64)

    def to_metadata(self):
        return self.model_dump(mode="json")
