"""Produce evidence-checked QueryAnalysis, never retrieval or answer decisions."""
import json
import re

from rag_qa.query.entities import extract_entities, evidence_spans, valid_identifier
from rag_qa.query.schemas import (
    QueryAnalysis, QueryEntities, QueryIntent, ConfidenceLevel, AnalysisSource,
    SemanticClassification, IDENTIFIER_FIELDS,
)

MAX_QUERY_CHARS = 16384
MAX_CLASSIFIER_CHARS = 32768
RULE_INTENTS = (
    (QueryIntent.ALARM_FAULT, r"报警|故障|报错|异常|振动|异响|\balarm\b|\bfault\b"),
    (QueryIntent.MAINTENANCE, r"保养|检修|维护|润滑|维保|\bmaintenance\b|\blubricat\w*\b"),
    (QueryIntent.PARAMETER, r"参数|规格|技术指标|转速|额定|功率|精度|\bparameter\w*\b|\bspecifications?\b"),
    (QueryIntent.PARTS, r"备件|配件|零件|物料号|\bparts?\b"),
    (QueryIntent.KNOWLEDGE, r"操作|手册|说明书|启动|停机|设备知识|\bmanual\b|\boperate\b"),
)


def _rules_intent(query):
    matches = [intent for intent, pattern in RULE_INTENTS if re.search(pattern, query, re.I)]
    if len(matches) == 1:
        return matches[0], ConfidenceLevel.MEDIUM, []
    if matches:
        return matches[0], ConfidenceLevel.LOW, ["multiple_intent_cues"]
    return QueryIntent.GENERAL, ConfidenceLevel.LOW, ["no_reliable_intent_cue"]


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate classifier JSON key")
        result[key] = value
    return result


def _reject_json_constant(value):
    raise ValueError("non-finite classifier JSON")


def _classification(raw):
    if not isinstance(raw, str) or len(raw) > MAX_CLASSIFIER_CHARS:
        raise ValueError("classifier must return bounded JSON text")
    value = json.loads(raw, object_pairs_hook=_unique_json_object,
                       parse_constant=_reject_json_constant)
    return SemanticClassification.model_validate(value)


class QueryAnalyzer:
    def __init__(self, classifier=None):
        self.classifier = classifier

    def analyze(self, query):
        valid_query = isinstance(query, str) and bool(query.strip()) and len(query) <= MAX_QUERY_CHARS
        if valid_query:
            try:
                query.encode("utf-8")
            except UnicodeEncodeError:
                valid_query = False
        if not valid_query:
            return QueryAnalysis(intent=QueryIntent.GENERAL, confidence=ConfidenceLevel.LOW,
                                 analysis_source=AnalysisSource.FALLBACK, warnings=["invalid_query"])
        extracted = extract_entities(query)
        warnings = list(extracted.warnings)
        if self.classifier is None:
            intent, confidence, cues = _rules_intent(query)
            if extracted.ambiguous_fields:
                confidence = ConfidenceLevel.LOW
            return QueryAnalysis(intent=intent, confidence=confidence, entities=extracted.entities,
                                 analysis_source=AnalysisSource.RULES,
                                 warnings=list(dict.fromkeys(warnings + cues)))
        try:
            semantic = _classification(self.classifier.classify(query))
        except Exception:
            # Intentionally do not echo arbitrary classifier exceptions, query or API secrets.
            intent, confidence, cues = _rules_intent(query)
            if extracted.ambiguous_fields:
                confidence = ConfidenceLevel.LOW
            return QueryAnalysis(intent=intent, confidence=confidence, entities=extracted.entities,
                                 analysis_source=AnalysisSource.FALLBACK,
                                 warnings=list(dict.fromkeys(warnings + ["semantic_classifier_failed"] + cues)))

        values = extracted.entities.model_dump()
        for field, proposed in semantic.entities.model_dump().items():
            if proposed is None:
                continue
            if field in extracted.ambiguous_fields:
                continue  # singular output cannot silently pick one of multiple models/codes
            if values[field] is not None:
                if values[field] != proposed:
                    warnings.append("semantic_entity_conflict_" + field)
                continue  # deterministic values are authoritative
            if field in IDENTIFIER_FIELDS:
                if any(other != field and getattr(extracted.entities, other) == proposed
                       for other in IDENTIFIER_FIELDS):
                    warnings.append("semantic_entity_role_conflict_" + field)
                    continue  # an evidenced alarm code is not also an inferred model/part
                spans = evidence_spans(query, proposed)
                valid = any(valid_identifier(proposed, query, m.span()) for m in spans)
            else:
                valid = proposed in query  # even descriptive labels require literal source evidence
            if valid:
                values[field] = proposed
            else:
                warnings.append("semantic_entity_rejected_" + field)
        confidence = semantic.confidence
        if semantic.intent == QueryIntent.GENERAL or extracted.ambiguous_fields:
            confidence = ConfidenceLevel.LOW
        elif warnings and confidence == ConfidenceLevel.HIGH:
            confidence = ConfidenceLevel.MEDIUM
        source = AnalysisSource.HYBRID if (extracted.warnings or any(
            v is not None for v in extracted.entities.model_dump().values())) else AnalysisSource.LLM
        return QueryAnalysis(intent=semantic.intent, confidence=confidence, entities=QueryEntities(**values),
                             analysis_source=source, warnings=list(dict.fromkeys(warnings)))
