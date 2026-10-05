"""Hashed versioned keys, bounded TTL, and structural cache validation."""
import hashlib
import json
import unicodedata
import re
from rag_qa.generation.schemas import GroundedAnswerResult

CACHE_CONTRACT_VERSION = "manufacturing_answer_v1"
GENERATION_CONTRACT_VERSION = "manufacturing_generation_v1"


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def build_cache_key(query, analysis, revision, *, llm_model, retrieval_k, candidate_m, retrieval_settings=None):
    from rag_qa.retrieval.settings import RetrievalSettings, baseline_settings
    settings = retrieval_settings or baseline_settings(retrieval_k, candidate_m)
    if type(settings) is not RetrievalSettings or (settings.retrieval_k, settings.candidate_m) != (retrieval_k, candidate_m):
        raise ValueError("cache retrieval settings mismatch")
    normalized = " ".join(unicodedata.normalize("NFC", query).split())
    return "manufacturing:answer:v1:" + canonical_hash(dict(cache_contract_version=CACHE_CONTRACT_VERSION,
        generation_contract_version=GENERATION_CONTRACT_VERSION, knowledge_revision=revision,
        query=normalized, analysis=analysis.to_metadata(), llm_model=llm_model,
        retrieval_k=retrieval_k, candidate_m=candidate_m,
        retrieval_config_fingerprint=settings.fingerprint(),
        retrieval_contract_version=settings.retrieval_contract_version))


def validate_cached_answer(payload):
    result = GroundedAnswerResult.model_validate(payload)
    if result.status.value != "answered" or not result.claims or not result.citations:
        raise ValueError("only_answered_cache")
    ids = tuple(c.evidence_id for c in result.citations)
    if len(ids) != len(set(ids)) or ids != result.used_evidence_ids:
        raise ValueError("invalid_cached_citations")
    used = {eid for claim in result.claims for eid in claim.evidence_ids}
    if used != set(ids):
        raise ValueError("invalid_cached_claim_links")
    from rag_qa.schemas.manufacturing_metadata import KnowledgeType
    for citation in result.citations:
        if not re.fullmatch(r"[0-9a-f]{64}", citation.parent_id):
            raise ValueError("invalid_cached_parent_id")
        KnowledgeType(citation.knowledge_type)
    for claim in result.claims:
        if re.search(r"\[E[0-9]+\]", claim.text) or re.match(r"\s*\d+[.)、]", claim.text):
            raise ValueError("invalid_cached_claim_markup")
    # Reconstruct exact Stage 10 rendering to reject tampered/free answer_text.
    body = "\n\n".join(c.text + "".join(f"[{eid}]" for eid in c.evidence_ids) for c in result.claims)
    sources = "\n".join(f"[{c.evidence_id}] " + json.dumps(dict(title=c.title,
        document_id=c.document_id, document_version=c.document_version, source_file=c.source_file), ensure_ascii=False) for c in result.citations)
    if result.answer_text != body + "\n\n来源：\n" + sources:
        raise ValueError("invalid_cached_rendering")
    return result


class ManufacturingAnswerCache:
    def __init__(self, client, ttl_seconds):
        if type(ttl_seconds) is not int or ttl_seconds <= 0:
            raise ValueError("positive_cache_ttl_required")
        self.client, self.ttl_seconds = client, ttl_seconds
        self.degraded = False

    def get(self, key):
        try:
            raw = self.client.get(key)
            self.degraded = False
        except Exception:
            self.degraded = True
            return None
        if raw is None:
            return None
        try:
            if len(raw) > 1024 * 1024:
                raise ValueError("oversized_cache")
            def unique(pairs):
                result = {}
                for k, v in pairs:
                    if k in result: raise ValueError("duplicate_key")
                    result[k] = v
                return result
            return validate_cached_answer(json.loads(raw, object_pairs_hook=unique))
        except Exception:
            try: self.client.delete(key)
            except Exception: self.degraded = True
            return None

    def put(self, key, result):
        if not isinstance(result, GroundedAnswerResult) or result.status.value != "answered":
            return False
        checked = validate_cached_answer(result.model_dump(mode="json"))
        try:
            self.client.set(key, checked.model_dump_json(), ex=self.ttl_seconds)
            self.degraded = False
            return True
        except Exception:
            self.degraded = True
            return False
