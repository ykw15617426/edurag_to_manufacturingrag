"""Identifier-preserving FAQ ranking using the existing pinned BM25Okapi algorithm."""
from dataclasses import dataclass
from math import isfinite
from numbers import Real
import re
import unicodedata

from .filters import build_expression


def normalize_question(text):
    if not isinstance(text, str):
        raise ValueError("question must be text")
    text = unicodedata.normalize("NFC", text)
    text.encode("utf-8")
    return " ".join(text.split())


def tokenize(text):
    # ASCII words/numbers/identifier segments remain one case-sensitive token.
    # Remaining Chinese spans use deterministic characters + adjacent bigrams.
    tokens = []
    for match in re.finditer(r"[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*|[\u3400-\u9fff]+", normalize_question(text)):
        value = match.group()
        if re.fullmatch(r"[\u3400-\u9fff]+", value):
            tokens.extend(value)
            tokens.extend(value[i:i + 2] for i in range(len(value) - 1))
        else:
            tokens.append(value)
    return tuple(tokens)


@dataclass(frozen=True)
class BM25Candidate:
    entry: object
    raw_score: float
    rank: int
    corpus_size: int
    candidate_scope_size: int
    matched_token_count: int


@dataclass(frozen=True)
class BM25AcceptancePolicy:
    minimum_raw_score: float

    def __post_init__(self):
        value = self.minimum_raw_score
        if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
            raise ValueError("minimum_raw_score must be an explicit finite number")

    def accepts(self, candidate):
        return candidate.matched_token_count > 0 and candidate.raw_score >= self.minimum_raw_score


class ManufacturingBM25:
    def __init__(self, entries):
        from rank_bm25 import BM25Okapi

        self.entries = tuple(entries)
        self.tokens = tuple(tokenize(e.question) for e in self.entries)
        if any(not tokens for tokens in self.tokens):
            raise ValueError("FAQ question requires indexable tokens")
        self.index = BM25Okapi(self.tokens) if self.entries else None

    def compatible_entries(self, hard_filters):
        build_expression(hard_filters, {})  # Fixed hard-field whitelist and Stage 5 value validation.
        return tuple((i, e) for i, e in enumerate(self.entries)
                     if all(getattr(e, field) == value for field, value in hard_filters.items()))

    def rank(self, query, hard_filters):
        scope = self.compatible_entries(hard_filters)
        if not scope:
            return ()
        query_tokens = tokenize(query)
        scores = self.index.get_batch_scores(query_tokens, [i for i, _ in scope])
        if len(scores) != len(scope) or any(not isfinite(score) for score in scores):
            raise ValueError("BM25 must return one finite raw score per scoped entry")
        ranked = sorted(zip(scope, scores), key=lambda item: (-item[1], item[0][1].entry_id))
        return tuple(BM25Candidate(e, float(score), rank, len(self.entries), len(scope),
                                   len(set(query_tokens) & set(self.tokens[i])))
                     for rank, ((i, e), score) in enumerate(ranked, start=1))
