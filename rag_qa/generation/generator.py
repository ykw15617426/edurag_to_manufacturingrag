"""Injectable JSON generation, claim guards and citation rendering, fail closed."""
import json
import re
from .evidence import normalize_evidence, guard_evidence
from .prompts import build_messages
from .schemas import (Citation, GeneratedAnswer, GenerationError, GenerationValidationError,
                      GenerationStatus, GroundedAnswerResult)


INSUFFICIENT_TEXT = "现有知识库证据不足，无法可靠回答该问题。"
ASCII_TOKEN = re.compile(r"[A-Za-z0-9]+(?:[._+-][A-Za-z0-9]+)*")
NUMERIC_TOKEN = re.compile(r"(?<![A-Za-z0-9_.\d])[-+]?\d+(?:[.,]\d+)*(?:[eE][-+]?\d+)?(?:%|[°℃])?")


def parse_answer(payload):
    try:
        if not isinstance(payload, str) or len(payload.encode("utf-8")) > 131072:
            raise ValueError("invalid_response")
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("duplicate_json_key")
                result[key] = value
            return result
        def reject_constant(value):
            raise ValueError("invalid_json_constant")
        raw = json.loads(payload, object_pairs_hook=unique, parse_constant=reject_constant)
        return GeneratedAnswer.model_validate(raw)
    except Exception:
        raise GenerationValidationError("invalid_generation_json_or_schema") from None


def validate_claims(query, answer, records):
    by_id = {record.evidence_id: record for record in records}
    for claim in answer.claims:
        if any(eid not in by_id for eid in claim.evidence_ids):
            raise GenerationValidationError("unknown_citation")
        if re.search(r"\[E[0-9]+\]", claim.text) or re.match(r"\s*\d+[.)、]", claim.text):
            raise GenerationValidationError("claim_contains_renderer_markup")
        # Field values stay separate: do not invent support across concatenated
        # field boundaries or permit score/version routing fields as numeric facts.
        support = [query]
        for eid in claim.evidence_ids:
            record = by_id[eid]
            support.extend(value for key, value in record.facts().items()
                           if key in {"page_content", "title", "equipment_model", "manufacturer", "alarm_code", "part_number", "effective_date"}
                           and isinstance(value, str))
        ascii_allowed = {token for value in support for token in ASCII_TOKEN.findall(value)}
        numeric_allowed = {token for value in support for token in NUMERIC_TOKEN.findall(value)}
        if set(ASCII_TOKEN.findall(claim.text)) - ascii_allowed:
            raise GenerationValidationError("ungrounded_identifier_token")
        if set(NUMERIC_TOKEN.findall(claim.text)) - numeric_allowed:
            raise GenerationValidationError("ungrounded_numeric_literal")


def render_answer(answer, records):
    if answer.status == GenerationStatus.INSUFFICIENT_EVIDENCE:
        # Never echo an unguarded model reason as an operational answer.
        return GroundedAnswerResult(status=answer.status, answer_text=INSUFFICIENT_TEXT,
            claims=(), citations=(), used_evidence_ids=(), warnings=("model_reported_insufficient_evidence",))
    used = {eid for claim in answer.claims for eid in claim.evidence_ids}
    citations = tuple(Citation(**{field: getattr(record, field).value if field == "knowledge_type" else getattr(record, field)
                                  for field in Citation.model_fields}) for record in records if record.evidence_id in used)
    body = "\n\n".join(claim.text + "".join(f"[{eid}]" for eid in claim.evidence_ids) for claim in answer.claims)
    sources = "\n".join(f"[{citation.evidence_id}] " + json.dumps(dict(title=citation.title,
        document_id=citation.document_id, document_version=citation.document_version, source_file=citation.source_file), ensure_ascii=False)
        for citation in citations)
    return GroundedAnswerResult(status=answer.status, answer_text=body + "\n\n来源：\n" + sources,
        claims=answer.claims, citations=citations, used_evidence_ids=tuple(c.evidence_id for c in citations))


class StructuredAnswerGenerator:
    """Completion callable owns SDK, model, finite network timeout and secrets."""
    def __init__(self, completion=None):
        self.completion = completion

    def generate(self, query, analysis, strategy_result):
        if not isinstance(query, str) or not query.strip() or len(query) > 16384:
            raise GenerationError("invalid_query")
        try:
            query.encode("utf-8", errors="strict")
        except UnicodeError:
            raise GenerationError("invalid_query") from None
        if getattr(strategy_result, "original_query", query) != query:
            raise GenerationError("strategy_query_mismatch")
        try:
            documents = (strategy_result.documents if hasattr(strategy_result, "documents")
                         else strategy_result.evidence)
        except Exception:
            raise GenerationError("evidence_result_required") from None
        records = normalize_evidence(documents)
        guard_evidence(records, analysis)
        if not records:
            return GroundedAnswerResult(status="insufficient_evidence", answer_text=INSUFFICIENT_TEXT,
                claims=(), citations=(), used_evidence_ids=(), warnings=("no_evidence",))
        if self.completion is None:
            raise GenerationError("completion_not_configured")
        messages = build_messages(query, analysis, records)
        try:
            payload = self.completion(messages=messages, temperature=0.0, response_format={"type": "json_object"})
        except Exception:
            raise GenerationError("generation_transport_failed") from None
        answer = parse_answer(payload)
        validate_claims(query, answer, records)
        return render_answer(answer, records)
