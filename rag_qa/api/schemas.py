"""Strict request and safe public responses; session is correlation only."""
from pydantic import BaseModel, ConfigDict, StrictStr, Field, field_validator
from rag_qa.generation.schemas import GroundedAnswerResult


class ManufacturingQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: StrictStr = Field(min_length=1, max_length=16384)
    session_id: StrictStr | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("query", "session_id")
    @classmethod
    def valid_text(cls, value):
        if value is not None:
            if not value.strip():
                raise ValueError("empty_text")
            value.encode("utf-8", errors="strict")
        return value


class ManufacturingQueryResponse(GroundedAnswerResult):
    request_id: StrictStr
    session_id: StrictStr | None
    cache_hit: bool


class ServiceError(RuntimeError):
    def __init__(self, code, status_code=500):
        self.code, self.status_code = code, status_code
        super().__init__(code)


class RequestDisconnected(Exception):
    pass
