"""Bounded retrieval orchestration; errors propagate without unfiltered retries."""
from dataclasses import dataclass
from .filters import MetadataFilterPlan, build_filter_plan


def validate_search_input(query, k):
    if not isinstance(query, str) or not query.strip() or len(query) > 16384:
        raise ValueError("query must be a nonempty string of at most 16384 characters")
    if type(k) is not int or not 1 <= k <= 16384:
        raise ValueError("k must be an integer between 1 and 16384")


@dataclass(frozen=True)
class RetrievalAttempt:
    plan: MetadataFilterPlan
    hit_count: int


@dataclass(frozen=True)
class RetrievalResult:
    documents: tuple
    attempts: tuple[RetrievalAttempt, ...]

    @property
    def final_plan(self):
        return self.attempts[-1].plan


class ManufacturingRetriever:
    def __init__(self, vector_store):
        if vector_store.schema_mode != "manufacturing":
            raise ValueError("ManufacturingRetriever requires manufacturing schema_mode")
        self.vector_store = vector_store

    def retrieve(self, query, analysis, k=None):
        if k is None:
            # Resolve lazily so importing the lightweight package needs no config/runtime.
            from base.config import config
            k = config.RETRIEVAL_K
        validate_search_input(query, k)
        plan = build_filter_plan(analysis)
        documents = self.vector_store.hybrid_search_children(query, filter_plan=plan, k=k)
        attempts = [RetrievalAttempt(plan, len(documents))]
        if not documents:
            relaxed = plan.relax_after_zero_hits()
            if relaxed is not None:
                documents = self.vector_store.hybrid_search_children(query, filter_plan=relaxed, k=k)
                attempts.append(RetrievalAttempt(relaxed, len(documents)))
        return RetrievalResult(tuple(documents), tuple(attempts))

    def retrieve_parents(self, query, analysis, k=None):
        """Stage 6 child retrieval followed by identity aggregation and Parent rerank."""
        from base.config import config
        from .parent_aggregation import aggregate_parents
        from .parent_reranker import rerank_parents, validate_top_m

        top_m = config.CANDIDATE_M
        validate_top_m(top_m)
        children = self.retrieve(query, analysis, k=k)
        parents = aggregate_parents(children.documents)
        documents = rerank_parents(query, parents, self.vector_store.reranker, top_m=top_m) if parents else ()
        return RetrievalResult(documents, children.attempts)
