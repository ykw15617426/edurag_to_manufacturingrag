"""Approved FAQ/alarm evidence optimization; unsuccessful searches delegate to Stage 7."""
from dataclasses import dataclass
from enum import Enum
import json
from types import MappingProxyType

from pydantic import ConfigDict, StrictStr, ValidationError, field_validator, model_validator

from rag_qa.core.milvus_schema import HASH_PATTERN, manufacturing_fields
from rag_qa.query.schemas import QueryEntities
from rag_qa.schemas.manufacturing_metadata import ManufacturingDocumentMetadata, MaintenanceCycle
from .filters import HARD_FIELDS, build_filter_plan
from .manufacturing_bm25 import BM25Candidate, ManufacturingBM25, normalize_question, tokenize
from .manufacturing_retriever import validate_search_input


class CorpusValidationError(ValueError):
    """Invalid approved corpus, rejected at initialization rather than silently ignored."""


class FrozenMaintenanceCycle(MaintenanceCycle):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FastPathEntry(ManufacturingDocumentMetadata):
    model_config = ConfigDict(extra="forbid", frozen=True)
    entry_id: StrictStr
    question: StrictStr
    evidence_text: StrictStr
    parent_id: StrictStr
    source_file: StrictStr
    maintenance_cycle: FrozenMaintenanceCycle | None = None

    @field_validator("entry_id", "question", "evidence_text", "source_file")
    @classmethod
    def validate_text(cls, value, info):
        value = normalize_question(value) if info.field_name == "question" else value.strip()
        limit = {"entry_id": 128, "question": 65535, "evidence_text": 65535, "source_file": 4096}[info.field_name]
        if not value or len(value.encode("utf-8")) > limit:
            raise ValueError("nonempty text within field byte capacity required")
        return value

    @field_validator("parent_id")
    @classmethod
    def validate_parent_id(cls, value):
        if not HASH_PATTERN.fullmatch(value):
            raise ValueError("parent_id must be a stable lowercase SHA256")
        return value

    @model_validator(mode="after")
    def validate_storage_metadata(self):
        data = self.model_dump(mode="json")
        QueryEntities(**{name: data[name] for name in QueryEntities.model_fields})
        for spec in manufacturing_fields(1):
            if spec.name in data and data[spec.name] is not None and spec.max_length:
                if len(data[spec.name].encode("utf-8")) > spec.max_length:
                    raise ValueError("metadata exceeds storage byte capacity")
        return self


class FastPathCorpus:
    SNAPSHOT_VERSION = "manufacturing_fast_path_v1"

    def __init__(self, approved_entries):
        entries = []
        try:
            for item in approved_entries:
                data = item.model_dump(mode="json") if isinstance(item, FastPathEntry) else item
                entries.append(FastPathEntry.model_validate(data))
        except (ValidationError, ValueError, TypeError):
            raise CorpusValidationError("invalid FastPathEntry metadata or representation") from None
        if len({e.entry_id for e in entries}) != len(entries):
            raise CorpusValidationError("duplicate entry_id")
        self.entries = tuple(sorted(entries, key=lambda e: e.entry_id))
        try:
            self.bm25 = ManufacturingBM25(self.entries)
        except ValueError:
            raise CorpusValidationError("invalid FAQ question tokenization") from None

    def to_json(self):
        return json.dumps({"schema_version": self.SNAPSHOT_VERSION,
                           "entries": [e.model_dump(mode="json") for e in self.entries]}, ensure_ascii=False)

    @classmethod
    def from_json(cls, snapshot):
        def unique_object(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("duplicate snapshot key")
                result[key] = value
            return result

        try:
            data = json.loads(snapshot, object_pairs_hook=unique_object)
            if (not isinstance(data, dict) or set(data) != {"schema_version", "entries"}
                    or data["schema_version"] != cls.SNAPSHOT_VERSION or not isinstance(data["entries"], list)):
                raise ValueError("invalid snapshot contract")
        except (ValueError, TypeError):
            raise CorpusValidationError("invalid corpus snapshot") from None
        return cls(data["entries"])


class MatchType(str, Enum):
    EXACT_ALARM = "exact_alarm"
    EXACT_FAQ = "exact_faq"
    BM25_FAQ = "bm25_faq"
    FALLBACK = "fallback"


@dataclass(frozen=True)
class FastPathEvidence:
    page_content: str
    metadata: object


@dataclass(frozen=True)
class FastPathResult:
    status: str
    match_type: MatchType
    evidence: tuple
    matched_entry: FastPathEntry | None
    bm25_score: float | None
    rank: int | None
    corpus_size: int
    reason: str
    candidates: tuple[BM25Candidate, ...] = ()
    warnings: tuple[str, ...] = ()
    parent_result: object | None = None


class ManufacturingFastPath:
    def __init__(self, corpus, parent_retriever, *, acceptance_policy=None):
        if type(corpus) is not FastPathCorpus:
            raise TypeError("validated approved FastPathCorpus required")
        if acceptance_policy is not None and not callable(getattr(acceptance_policy, "accepts", None)):
            raise TypeError("acceptance_policy must provide accepts(candidate)")
        self.corpus, self.parent_retriever, self.acceptance_policy = corpus, parent_retriever, acceptance_policy

    def _search(self, query, analysis, plan):
        if any("ambiguous_" + name in plan.warnings for name in HARD_FIELDS):
            return None, MatchType.FALLBACK, "ambiguous_hard_identifier", ()
        # Guard a corpus-known alarm token that Stage 5 could not safely assign.
        # This does not add an entity/filter or choose a model on Stage 5's behalf.
        known_codes = {e.alarm_code for e in self.corpus.entries if e.alarm_code is not None}
        unresolved_codes = (set(tokenize(query)) & known_codes) - {plan.hard_filters.get("alarm_code")}
        if unresolved_codes:
            return None, MatchType.FALLBACK, "unresolved_alarm_identifier", ()
        compatible = tuple(e for _, e in self.corpus.bm25.compatible_entries(plan.hard_filters))
        alarm_code = plan.hard_filters.get("alarm_code")
        if alarm_code:
            alarms = tuple(e for e in compatible if e.alarm_code == alarm_code)
            if len(alarms) > 1:
                # Do not let a later exact-FAQ/BM25 decision bypass ambiguous alarm meanings.
                return None, MatchType.FALLBACK, "ambiguous_alarm_evidence", ()
            if len(alarms) == 1 and alarms[0].knowledge_type.value == "alarm":
                reason = "unique_alarm_with_hard_identifiers" if "equipment_model" in plan.hard_filters else "unique_alarm_meaning_in_approved_corpus"
                return alarms[0], MatchType.EXACT_ALARM, reason, ()
        exact = tuple(e for e in compatible if e.question == normalize_question(query))
        if len(exact) > 1:
            return None, MatchType.FALLBACK, "ambiguous_exact_faq", ()
        if len(exact) == 1:
            return exact[0], MatchType.EXACT_FAQ, "unique_normalized_exact_faq", ()
        candidates = self.corpus.bm25.rank(query, plan.hard_filters)
        if not candidates:
            return None, MatchType.FALLBACK, "no_compatible_entries", ()
        if self.acceptance_policy is None:
            return None, MatchType.FALLBACK, "bm25_policy_not_enabled", candidates
        accepted = self.acceptance_policy.accepts(candidates[0])
        if type(accepted) is not bool:
            raise ValueError("acceptance policy must return bool")
        if accepted:
            return candidates[0].entry, MatchType.BM25_FAQ, "bm25_accepted_by_explicit_policy", candidates
        return None, MatchType.FALLBACK, "bm25_rejected_by_policy", candidates

    def retrieve_with_fast_path(self, query, analysis, k=None):
        validate_search_input(query, 1 if k is None else k)
        plan = build_filter_plan(analysis)
        warnings, candidates = (), ()
        try:
            entry, match_type, reason, candidates = self._search(query, analysis, plan)
        except Exception:
            entry, match_type, reason = None, MatchType.FALLBACK, "fast_path_error"
            warnings = ("fast_path_error",)
        top = candidates[0] if candidates else None
        if entry is not None:
            metadata = entry.model_dump(mode="json")
            metadata.pop("evidence_text")
            metadata.update(id=entry.parent_id, match_type=match_type.value, fast_path_reason=reason)
            evidence = FastPathEvidence(entry.evidence_text, MappingProxyType(metadata))
            return FastPathResult("ACCEPTED", match_type, (evidence,), entry,
                                  top.raw_score if top else None, top.rank if top else None,
                                  len(self.corpus.entries), reason, candidates)
        # Outside the optimization try/except: Stage 7 errors propagate unchanged.
        parents = self.parent_retriever.retrieve_parents(query, analysis, k=k)
        return FastPathResult("FALLBACK", MatchType.FALLBACK, parents.documents, None,
                              top.raw_score if top else None, top.rank if top else None,
                              len(self.corpus.entries), reason, candidates, warnings, parents)
