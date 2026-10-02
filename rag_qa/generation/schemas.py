"""Strict manufacturing generation contracts; no API/model dependencies."""
from enum import Enum
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator, model_validator


class GenerationError(RuntimeError):
    """System/contract failure, never an evidence-insufficiency response."""


class GenerationValidationError(GenerationError):
    pass


class GenerationStatus(str, Enum):
    ANSWERED = "answered"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


Text = Annotated[StrictStr, Field(min_length=1, max_length=4096)]
EvidenceID = Annotated[StrictStr, Field(pattern=r"^E[1-9][0-9]{0,5}$")]


class StrictRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    @field_validator("*", mode="after", check_fields=False)
    @classmethod
    def valid_text(cls, value):
        if isinstance(value, str):
            if not value.strip():
                raise ValueError("empty_text")
            value.encode("utf-8", errors="strict")
        return value


class GeneratedClaim(StrictRecord):
    text: Text
    evidence_ids: tuple[EvidenceID, ...] = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def unique_citations(self):
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("duplicate_citation")
        return self


class GeneratedAnswer(StrictRecord):
    status: GenerationStatus
    claims: tuple[GeneratedClaim, ...] = Field(default=(), max_length=64)
    insufficient_reason: Text | None = None

    @model_validator(mode="after")
    def status_contract(self):
        if self.status == GenerationStatus.ANSWERED:
            if not self.claims or self.insufficient_reason is not None:
                raise ValueError("answered_requires_claims_only")
        elif self.claims or self.insufficient_reason is None:
            raise ValueError("insufficient_requires_reason_without_claims")
        return self


class Citation(StrictRecord):
    evidence_id: EvidenceID
    title: StrictStr
    document_id: StrictStr
    document_version: StrictStr
    parent_id: StrictStr
    knowledge_type: StrictStr
    source_file: StrictStr


class GroundedAnswerResult(StrictRecord):
    status: GenerationStatus
    answer_text: StrictStr
    claims: tuple[GeneratedClaim, ...]
    citations: tuple[Citation, ...]
    used_evidence_ids: tuple[EvidenceID, ...]
    warnings: tuple[StrictStr, ...] = ()
