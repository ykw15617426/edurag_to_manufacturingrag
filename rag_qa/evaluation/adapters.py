"""Reuse actual Stage 5/6/7/8/9 components; capture observations without extra searches."""
from time import perf_counter
from types import SimpleNamespace
from rag_qa.retrieval.manufacturing_retriever import ManufacturingRetriever
from rag_qa.retrieval.parent_aggregation import aggregate_parents
from rag_qa.retrieval.parent_reranker import rerank_parents
from rag_qa.retrieval.strategy import ManufacturingStrategyRetriever, fuse_children
from rag_qa.retrieval.fast_path import ManufacturingFastPath
from rag_qa.retrieval.manufacturing_bm25 import BM25AcceptancePolicy
from .evaluator import RetrievalObservation


def describe_attempt(query, attempt):
    plan = attempt.plan
    return dict(query=query, hit_count=attempt.hit_count, mode=plan.mode.value, expression=plan.expression,
                hard_filters=dict(plan.hard_filters), soft_filters=dict(plan.soft_filters),
                removed_fields=list(plan.removed_fields), warnings=list(plan.warnings))


class RecordingChildRetriever(ManufacturingRetriever):
    def __init__(self, vector_store):
        super().__init__(vector_store)
        self.results = []
        self.attempts = []
        self.elapsed_ms = 0.0

    def retrieve(self, query, analysis, k=None):
        start = perf_counter()
        result = super().retrieve(query, analysis, k=k)
        self.elapsed_ms += (perf_counter() - start) * 1000
        self.results.append(result)
        self.attempts.extend(describe_attempt(query, a) for a in result.attempts)
        return result


class TimedReranker:
    def __init__(self, reranker):
        self.reranker, self.elapsed_ms = reranker, 0.0

    def predict(self, pairs):
        start = perf_counter()
        try: return self.reranker.predict(pairs)
        finally: self.elapsed_ms += (perf_counter() - start) * 1000


class ComponentEvaluationAdapter:
    def __init__(self, vector_store, analyzer, profile, *, mode="direct", planner=None, corpus=None):
        if mode not in {"direct", "strategy"}: raise ValueError("unknown evaluation mode")
        if vector_store.schema_mode != "manufacturing": raise ValueError("manufacturing required")
        if getattr(vector_store, "retrieval_settings", None) != profile.retrieval_settings():
            raise ValueError("profile must match effective vector settings")
        if mode == "strategy":
            from base.config import config
            # Stage 9 intentionally still owns its production Top-M. Never mutate global config for an experiment.
            if profile.candidate_m != config.CANDIDATE_M:
                raise ValueError("Stage 9 paired evaluation requires current CANDIDATE_M; use DIRECT for M experiments")
        self.vector_store, self.analyzer, self.profile = vector_store, analyzer, profile
        self.mode, self.planner, self.corpus = mode, planner, corpus

    def retrieve(self, query):
        analysis = self.analyzer.analyze(query)
        timed = TimedReranker(self.vector_store.reranker)
        # Local observation wrapper: no reassignment of a shared production model/config.
        observed_store = SimpleNamespace(schema_mode="manufacturing", reranker=timed,
            hybrid_search_children=self.vector_store.hybrid_search_children)
        child = RecordingChildRetriever(observed_store)
        if self.mode == "direct":
            result = child.retrieve(query, analysis, k=self.profile.retrieval_k)
            start = perf_counter()
            aggregated = aggregate_parents(result.documents)
            parents = rerank_parents(query, aggregated, timed,
                                     top_m=self.profile.candidate_m) if aggregated else ()
            return RetrievalObservation(result.documents, parents, filter_attempts=tuple(child.attempts), analysis=analysis,
                timings=dict(child_retrieval=child.elapsed_ms, rerank=timed.elapsed_ms, aggregation_and_rerank=(perf_counter() - start) * 1000))
        policy = (BM25AcceptancePolicy(self.profile.bm25_threshold) if self.profile.bm25_acceptance_mode == "raw_score" else None)
        fast = ManufacturingFastPath(self.corpus, child, acceptance_policy=policy) if self.corpus else None
        result = ManufacturingStrategyRetriever(child, planner=self.planner, fast_path=fast).retrieve(
            query, analysis, k=self.profile.retrieval_k)
        children, _ = fuse_children(child.results)
        return RetrievalObservation(children, result.documents, result.strategy.value, result.decision_source,
            result.fallback_reason, tuple(child.attempts), result.fast_path_attempt, analysis,
            dict(child_retrieval=child.elapsed_ms, rerank=timed.elapsed_ms))
