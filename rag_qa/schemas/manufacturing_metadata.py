"""Stage 1 business metadata; system identity and persistence belong to later stages."""
from datetime import date
from enum import Enum
from typing import Annotated, Literal

from pydantic import (
    BaseModel, BeforeValidator, ConfigDict, Field, StrictStr,
    StringConstraints, field_validator, model_validator,
)


def _trim(value):
    return value.strip() if isinstance(value, str) else value


def _optional_trim(value):
    value = _trim(value)
    return None if value == "" else value


RequiredString = Annotated[StrictStr, BeforeValidator(_trim), StringConstraints(min_length=1)]
OptionalString = Annotated[RequiredString | None, BeforeValidator(_optional_trim)]


class KnowledgeType(str, Enum):
    MANUAL = "manual"
    ALARM = "alarm"
    FAULT = "fault"
    MAINTENANCE = "maintenance"
    PARAMETER = "parameter"
    PARTS = "parts"
    CASE = "case"


class MaintenanceCycle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: Annotated[float, Field(strict=True, gt=0, allow_inf_nan=False)] | None = None
    unit: Literal["hour", "day", "week", "month", "year", "cycle"] | None = None
    trigger: OptionalString = None

    @field_validator("unit", mode="before")
    @classmethod
    def trim_unit(cls, value):
        return _optional_trim(value)

    @model_validator(mode="after")
    def validate_expression(self):
        if (self.value is None) != (self.unit is None):
            raise ValueError("maintenance_cycle.value and unit must be supplied together")
        if self.value is None and self.trigger is None:
            raise ValueError("maintenance_cycle requires value + unit or trigger")
        return self


class ManufacturingDocumentMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: RequiredString
    document_version: RequiredString
    title: RequiredString
    knowledge_type: KnowledgeType
    equipment_type: OptionalString = None
    equipment_model: OptionalString = None
    manufacturer: OptionalString = None
    alarm_code: OptionalString = None
    fault_type: OptionalString = None
    fault_symptom: OptionalString = None
    maintenance_type: OptionalString = None
    maintenance_cycle: MaintenanceCycle | None = None
    part_number: OptionalString = None
    effective_date: date | None = None
    language: RequiredString = "zh-CN"

    @field_validator("knowledge_type", mode="before")
    @classmethod
    def trim_knowledge_type(cls, value):
        return _trim(value)

    @field_validator("effective_date", mode="before")
    @classmethod
    def validate_date_input(cls, value):
        # Reject Unix timestamps and datetime objects; dates have calendar semantics.
        value = _optional_trim(value)
        if value is not None and type(value) is not date:
            if not isinstance(value, str):
                raise ValueError("effective_date must be an ISO date")
            try:
                return date.fromisoformat(value)
            except ValueError:
                raise ValueError("effective_date must be an ISO date") from None
        return value

    @model_validator(mode="after")
    def validate_knowledge_requirements(self):
        if self.knowledge_type == KnowledgeType.ALARM and self.alarm_code is None:
            raise ValueError("alarm_code is required for alarm")
        if self.knowledge_type == KnowledgeType.FAULT and not (self.fault_type or self.fault_symptom):
            raise ValueError("fault_type or fault_symptom is required for fault")
        if self.knowledge_type == KnowledgeType.MAINTENANCE and not (self.maintenance_type or self.maintenance_cycle):
            raise ValueError("maintenance_type or maintenance_cycle is required for maintenance")
        if self.knowledge_type == KnowledgeType.PARTS and self.part_number is None:
            raise ValueError("part_number is required for parts")
        return self

    def to_metadata(self):
        """Plain JSON-compatible metadata; retain optional null values explicitly."""
        return self.model_dump(mode="json")
