"""Bounded query planning, Child fusion, then one original-query Parent rerank."""
from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType
import math
from numbers import Real
from pydantic import ValidationError
from rag_qa.query.rewrite import (RetrievalStrategy, StrategyDecision, StructuredStrategyPlanner,
                                VariantError, parse_decision, query_variants, validate_query)
from .fast_path import FastPathEligibility
from .filters import build_filter_plan
from .manufacturing_retriever import validate_search_input
from .parent_aggregation import aggregate_parents
from .parent_reranker import rerank_parents, validate_top_m


class ChildFusionError(ValueError):
    pass


@dataclass(frozen=True)
class FusedChild:
    page_content: str
    metadata: object


@dataclass(frozen=True)
class ChildFusionSignal:
    child_id: str
    winning_variant_index: int
    child_rank: int
    variant_indices: tuple[int, ...]


def fuse_children(results):
    """Highest raw score wins; positions are one-based and ties remain stable."""
    children, positions, sources = {}, {}, {}
    for variant_index, result in enumerate(results, 1):
        for rank, document in enumerate(result.documents, 1):
            metadata = deepcopy(dict(document.metadata))
            child_id = metadata.get("child_id")
            score = metadata.get("retrieval_score")
            if not isinstance(child_id, str) or not child_id or isinstance(score, bool) or not isinstance(score, Real) or not math.isfinite(score):
                raise ChildFusionError("invalid_child_identity_or_score")
            prior = children.get(child_id)
            if prior is not None:
                old = {k: v for k, v in prior.metadata.items() if k != "retrieval_score"}
                new = {k: v for k, v in metadata.items() if k != "retrieval_score"}
                if old != new or prior.page_content != document.page_content:
                    raise ChildFusionError("conflicting_child_metadata")
            sources.setdefault(child_id, set()).add(variant_index)
            if prior is None or score > prior.metadata["retrieval_score"]:
                children[child_id] = FusedChild(document.page_content, MappingProxyType(metadata))
                positions[child_id] = (variant_index, rank)
    ordered = sorted(children, key=lambda cid: (-children[cid].metadata["retrieval_score"], *positions[cid], cid))
    return (tuple(children[cid] for cid in ordered),
            tuple(ChildFusionSignal(cid, *positions[cid], tuple(sorted(sources[cid]))) for cid in ordered))


@dataclass(frozen=True)
class VariantRetrievalAttempt:
    query: str
    attempts: tuple
    hit_count: int


@dataclass(frozen=True)
class StrategyRetrievalResult:
    strategy: RetrievalStrategy
    original_query: str
    query_variants: tuple[str, ...]
    decision_source: str
    fallback_reason: str | None
    fast_path_attempt: object | None
    retrieval_attempts: tuple[VariantRetrievalAttempt, ...]
    documents: tuple
    reason_code: str
    fusion_signals: tuple[ChildFusionSignal, ...] = ()


class ManufacturingStrategyRetriever:
    def __init__(self, retriever, *, planner: StructuredStrategyPlanner | None = None, fast_path=None):
        if retriever.vector_store.schema_mode != "manufacturing":
            raise ValueError("manufacturing retriever required")
        self.retriever, self.planner, self.fast_path = retriever, planner, fast_path

    def retrieve(self, query, analysis, k=None):
        from base.config import config
        validate_query(query)
        validate_search_input(query, config.RETRIEVAL_K if k is None else k)
        validate_top_m(config.CANDIDATE_M)
        build_filter_plan(analysis)  # Validate original contract before calling any planner.
        fast = None
        if self.fast_path is not None:
            fast = self.fast_path.probe(query, analysis, k=k,
                eligibility=FastPathEligibility(allow_exact_alarm=analysis.intent.value == "alarm_fault"))
            if fast.status == "ACCEPTED":
                return StrategyRetrievalResult(RetrievalStrategy.DIRECT, query, (query,), "fast_path",
                    None, fast, (), fast.evidence, "fast_path_accepted")
        decision = StrategyDecision(strategy="direct", reason_code="no_planner")
        source, fallback = "default", None
        if self.planner is not None:
            try:
                decision = parse_decision(self.planner.plan(query, analysis))
                variants = query_variants(query, analysis, decision)
                source = "planner"
            except TimeoutError:
                fallback = "planner_timeout"
            except ValidationError:
                fallback = "planner_invalid_schema"
            except VariantError as exc:
                fallback = str(exc)
            except ValueError:
                fallback = "planner_invalid_json"
            except Exception:
                fallback = "planner_error"
            if fallback is not None:
                source = "fallback"
                decision = StrategyDecision(strategy="direct", reason_code=fallback)
        variants = query_variants(query, analysis, decision)
        results = tuple(self.retriever.retrieve(variant, analysis, k=k) for variant in variants)
        children, signals = fuse_children(results)
        parents = aggregate_parents(children)
        documents = rerank_parents(query, parents, self.retriever.vector_store.reranker,
                                  top_m=config.CANDIDATE_M) if parents else ()
        attempts = tuple(VariantRetrievalAttempt(variant, result.attempts, len(result.documents))
                         for variant, result in zip(variants, results))
        return StrategyRetrievalResult(decision.strategy, query, variants, source, fallback,
                                       fast, attempts, documents, decision.reason_code, signals)
