"""Normalize both existing evidence shapes and fail closed on conflicting facts."""
from datetime import date
from pydantic import Field, StrictStr, ValidationError, field_validator
from rag_qa.core.milvus_schema import HASH_PATTERN, manufacturing_fields
from rag_qa.query.schemas import QueryAnalysis, QueryEntities
from rag_qa.schemas.manufacturing_metadata import KnowledgeType
from .schemas import StrictRecord, EvidenceID, GenerationError


class EvidenceIntegrityError(GenerationError):
    pass


class EvidenceConflictError(EvidenceIntegrityError):
    pass


class EvidenceGuardError(EvidenceIntegrityError):
    pass


LIMITS = {f.name: f.max_length for f in manufacturing_fields(4) if f.max_length}
OBSERVABILITY = frozenset({"best_retrieval_score", "rerank_score", "match_type", "fast_path_reason"})


class EvidenceRecord(StrictRecord):
    evidence_id: EvidenceID
    page_content: StrictStr
    parent_id: StrictStr
    document_id: StrictStr
    document_version: StrictStr
    title: StrictStr
    knowledge_type: KnowledgeType
    equipment_model: StrictStr | None = None
    manufacturer: StrictStr | None = None
    alarm_code: StrictStr | None = None
    part_number: StrictStr | None = None
    source_file: StrictStr
    effective_date: date | None = None
    language: StrictStr
    best_retrieval_score: float | None = Field(default=None, strict=True, allow_inf_nan=False)
    rerank_score: float | None = Field(default=None, strict=True, allow_inf_nan=False)
    match_type: StrictStr | None = None
    fast_path_reason: StrictStr | None = None

    @field_validator("*")
    @classmethod
    def storage_bounds(cls, value, info):
        limit = LIMITS.get("parent_content" if info.field_name == "page_content" else info.field_name)
        if isinstance(value, str) and limit and len(value.encode("utf-8")) > limit:
            raise ValueError("evidence_field_exceeds_storage_limit")
        return value

    @field_validator("parent_id")
    @classmethod
    def valid_parent(cls, value):
        if not HASH_PATTERN.fullmatch(value):
            raise ValueError("invalid_parent_id")
        return value

    @field_validator("effective_date", mode="before")
    @classmethod
    def calendar_date(cls, value):
        if value is None or type(value) is date:
            return value
        if not isinstance(value, str):
            raise ValueError("invalid_effective_date")
        return date.fromisoformat(value)

    @field_validator("equipment_model", "alarm_code", "part_number", "manufacturer")
    @classmethod
    def validate_entity(cls, value, info):
        QueryEntities.model_validate({info.field_name: value})
        if value is not None and value != value.strip():
            raise ValueError("noncanonical_identifier")
        return value

    def facts(self):
        """Scores/routing reasons are not textual support for generated facts."""
        return self.model_dump(mode="json", exclude=OBSERVABILITY | {"evidence_id"})


def normalize_evidence(documents):
    records, parents, versions = [], {}, {}
    try:
        for index, document in enumerate(documents):
            if index >= 128:
                raise EvidenceIntegrityError("too_many_evidence_records")
            metadata = dict(document.metadata)
            data = {name: metadata[name] for name in EvidenceRecord.model_fields
                    if name not in {"evidence_id", "page_content"} and name in metadata}
            record = EvidenceRecord.model_validate(dict(data, evidence_id=f"E{len(records)+1}", page_content=document.page_content))
            previous = parents.get(record.parent_id)
            if previous is not None:
                if previous.facts() != record.facts():
                    raise EvidenceConflictError("conflicting_parent_evidence")
                continue
            if record.document_id in versions and versions[record.document_id] != record.document_version:
                raise EvidenceConflictError("multiple_document_versions")
            versions[record.document_id] = record.document_version
            parents[record.parent_id] = record
            records.append(record)
    except EvidenceIntegrityError:
        raise
    except Exception:
        raise EvidenceIntegrityError("invalid_evidence_record") from None
    return tuple(records)


def guard_evidence(records, analysis):
    if not isinstance(analysis, QueryAnalysis):
        raise EvidenceGuardError("query_analysis_required")
    try:
        checked = QueryAnalysis.model_validate(analysis.to_metadata())
    except ValidationError:
        raise EvidenceGuardError("invalid_query_analysis") from None
    for record in records:
        for field in ("equipment_model", "alarm_code", "part_number"):
            confirmed = getattr(checked.entities, field)
            if confirmed is not None and getattr(record, field) != confirmed:
                raise EvidenceGuardError("hard_identifier_incompatible")
