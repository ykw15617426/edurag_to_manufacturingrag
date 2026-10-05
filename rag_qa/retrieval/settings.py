"""One immutable manufacturing retrieval contract; no production tuning."""
import hashlib
import json
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, model_validator

DENSE_WEIGHT = 0.8
SPARSE_WEIGHT = 0.3
DENSE_NPROBE = 10
MANUFACTURING_RETRIEVAL_CONTRACT_VERSION = "manufacturing_retrieval_v1"


class RetrievalSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    retrieval_contract_version: StrictStr = MANUFACTURING_RETRIEVAL_CONTRACT_VERSION
    retrieval_k: StrictInt = Field(default=5, ge=1, le=16384)
    candidate_m: StrictInt = Field(default=2, ge=1, le=16384)
    dense_weight: float = Field(default=DENSE_WEIGHT, strict=True, ge=0, allow_inf_nan=False)
    sparse_weight: float = Field(default=SPARSE_WEIGHT, strict=True, ge=0, allow_inf_nan=False)
    nprobe: StrictInt = Field(default=DENSE_NPROBE, ge=1, le=65536)
    bm25_acceptance_mode: Literal["disabled", "raw_score"] = "disabled"
    bm25_threshold: float | None = Field(default=None, strict=True, allow_inf_nan=False)

    @model_validator(mode="after")
    def consistent(self):
        if not self.retrieval_contract_version.strip() or self.dense_weight + self.sparse_weight <= 0:
            raise ValueError("nonempty contract and positive total weight required")
        if (self.bm25_acceptance_mode == "raw_score") != (self.bm25_threshold is not None):
            raise ValueError("threshold required only for enabled BM25")
        return self

    def fingerprint(self):
        raw = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def baseline_settings(retrieval_k=5, candidate_m=2):
    return RetrievalSettings(retrieval_k=retrieval_k, candidate_m=candidate_m)
