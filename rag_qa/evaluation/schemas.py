"""Strict labeled datasets and immutable experiment profiles."""
import hashlib
import json
from pathlib import Path
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator, model_validator
from rag_qa.query.schemas import QueryEntities, QueryIntent
from rag_qa.retrieval.settings import RetrievalSettings

Hash = Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
Short = Annotated[StrictStr, Field(min_length=1, max_length=128)]
DocId = Annotated[StrictStr, Field(min_length=1, max_length=256)]


class RetrievalEvaluationSample(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    sample_id: Short
    query: StrictStr = Field(min_length=1, max_length=16384)
    expected_parent_ids: tuple[Hash, ...] = Field(min_length=1, max_length=4096)
    expected_document_ids: tuple[DocId, ...] = Field(min_length=1, max_length=4096)
    expected_child_ids: tuple[Hash, ...] = Field(min_length=1, max_length=4096)
    expected_intent: QueryIntent | None = None
    expected_equipment_model: StrictStr | None = None
    expected_alarm_code: StrictStr | None = None
    expected_part_number: StrictStr | None = None
    reference_answer: StrictStr | None = Field(default=None, min_length=1, max_length=65535)
    tags: tuple[Short, ...] = Field(default=(), max_length=32)
    # Explicit per-channel opportunity labels; fallback match_type cannot infer eligibility.
    fast_path_labels: tuple[Literal["exact_alarm", "exact_faq", "bm25_faq"], ...] = ()

    @field_validator("query", "reference_answer", "sample_id")
    @classmethod
    def bounded_utf8(cls, value, info):
        if value is not None and (not value.strip() or len(value.encode("utf-8")) > {"reference_answer": 65535, "query": 65536, "sample_id": 128}[info.field_name]):
            raise ValueError("nonempty bounded UTF-8 required")
        return value

    @field_validator("expected_parent_ids", "expected_document_ids", "expected_child_ids", "tags", "fast_path_labels")
    @classmethod
    def unique_sorted(cls, values):
        if len(values) != len(set(values)):
            raise ValueError("duplicate labels rejected")
        if any(not value.strip() or len(value.encode("utf-8")) > 256 for value in values):
            raise ValueError("bounded nonblank labels required")
        return tuple(sorted(values))

    @model_validator(mode="after")
    def identifiers(self):
        values = {name: getattr(self, "expected_" + name) for name in ("equipment_model", "alarm_code", "part_number")}
        checked = QueryEntities(**values)
        if any(getattr(checked, name) != value for name, value in values.items()):
            raise ValueError("identifier labels must already be canonical")
        return self


class EvaluationDataset(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["manufacturing_evaluation_v1"] = "manufacturing_evaluation_v1"
    dataset_type: Literal["controlled_synthetic", "approved_manufacturing", "production_replay"]
    provenance_note: StrictStr = Field(min_length=1, max_length=4096)
    samples: tuple[RetrievalEvaluationSample, ...] = Field(min_length=1, max_length=10000)

    @model_validator(mode="after")
    def unique(self):
        if len({s.sample_id for s in self.samples}) != len(self.samples):
            raise ValueError("duplicate sample_id")
        if not self.provenance_note.strip():
            raise ValueError("provenance note required")
        return self

    def canonical_json(self):
        data = self.model_dump(mode="json")
        data["samples"] = sorted(data["samples"], key=lambda s: s["sample_id"])
        return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

    def sha256(self):
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


class EvaluationProfile(RetrievalSettings):
    profile_name: Short = "baseline"

    def retrieval_settings(self):
        return RetrievalSettings(**self.model_dump(exclude={"profile_name"}))

    def fingerprint(self):
        return self.retrieval_settings().fingerprint()


def strict_json(raw):
    def unique(pairs):
        data = {}
        for key, value in pairs:
            if key in data: raise ValueError("duplicate JSON key")
            data[key] = value
        return data
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def load_dataset(path):
    path = Path(path)
    if path.stat().st_size > 32 * 1024 * 1024:
        raise ValueError("dataset exceeds 32MiB")
    raw = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        rows = [strict_json(line) for line in raw.splitlines() if line.strip()]
        if not rows: raise ValueError("empty dataset")
        return EvaluationDataset(**rows[0], samples=rows[1:])
    return EvaluationDataset.model_validate(strict_json(raw))
