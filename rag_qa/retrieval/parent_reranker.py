"""Fail-closed Parent CrossEncoder scoring; both score sources remain observable."""
from .parent_aggregation import finite_score, parent_order


class RerankerError(RuntimeError):
    """The model failed or did not produce one finite scalar per parent."""


def validate_top_m(top_m):
    if type(top_m) is not int or top_m <= 0:
        raise ValueError("CANDIDATE_M must be a positive integer")


def rerank_parents(query, parents, reranker, *, top_m):
    validate_top_m(top_m)
    if not isinstance(query, str) or not query.strip():
        raise ValueError("rerank query must be nonempty text")
    parents = tuple(sorted(parents, key=parent_order))
    if not parents:
        return ()
    pairs = [[query, parent.page_content] for parent in parents]
    try:
        scores = tuple(reranker.predict(pairs))
        if len(scores) != len(parents):
            raise RerankerError("score count must equal parent count")
        for score in scores:
            finite_score(score, RerankerError, "rerank_score")
    except Exception:
        # Do not expose model exceptions containing input text; never fallback silently.
        raise RerankerError("reranker must return one finite scalar per parent") from None
    ranked = sorted(zip(scores, parents), key=lambda pair: (-pair[0], *parent_order(pair[1])))
    from langchain_core.documents import Document

    return tuple(Document(page_content=parent.page_content, metadata={
        **dict(parent.metadata), "id": parent.parent_id,
        "best_retrieval_score": parent.best_retrieval_score, "rerank_score": score,
        "child_hit_count": len(parent.matched_children),
        "matched_child_ids": [m.child_id for m in parent.matched_children],
        "first_child_rank": parent.first_child_rank,
        "matched_children": [dict(child_id=m.child_id, child_content_sha256=m.child_content_sha256,
                                  retrieval_score=m.retrieval_score, child_rank=m.child_rank)
                             for m in parent.matched_children],
    }) for score, parent in ranked[:top_m])
