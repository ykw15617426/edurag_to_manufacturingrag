"""Deterministic macro ID metrics; rankings deduplicate before Top-K truncation."""
from math import isfinite


def stable_unique(values):
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError("rankings require nonempty IDs")
    return list(dict.fromkeys(values))


def ranking_metrics(relevant, ranking, k):
    if type(k) is not int or not 1 <= k <= 16384:
        raise ValueError("positive bounded integer K required")
    relevant = set(stable_unique(list(relevant)))
    if not relevant: raise ValueError("nonempty ground truth required")
    top = stable_unique(list(ranking))[:k]
    ranks = [rank for rank, value in enumerate(top, 1) if value in relevant]
    first = min(ranks) if ranks else None
    return dict(k=k, hit=float(bool(ranks)), recall=len(relevant.intersection(top)) / len(relevant),
                mrr=1 / first if first else 0.0, first_relevant_rank=first)


def macro_metrics(rows):
    rows = list(rows)
    if not rows: return dict(sample_count=0, hit=None, recall=None, mrr=None)
    return dict(sample_count=len(rows), **{name: sum(r[name] for r in rows) / len(rows)
                                          for name in ("hit", "recall", "mrr")})


def bm25_threshold_sweep(observations, thresholds):
    """Diagnostic only; raw score plus token match, never changes runtime policy."""
    rows = list(observations)
    result = []
    for threshold in thresholds:
        if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not isfinite(threshold):
            raise ValueError("finite raw threshold required")
        for row in rows:
            if (type(row.get("correct")) is not bool or type(row.get("matched_token_count")) is not int
                    or row["matched_token_count"] < 0 or isinstance(row.get("raw_score"), bool)
                    or not isinstance(row.get("raw_score"), (int, float)) or not isfinite(row["raw_score"])):
                raise ValueError("invalid BM25 observation")
        accepted = [r for r in rows if r["matched_token_count"] > 0 and r["raw_score"] >= threshold]
        correct = sum(r["correct"] for r in accepted)
        result.append(dict(threshold=threshold, eligible_count=len(rows), accepted_count=len(accepted),
            precision=correct / len(accepted) if accepted else None,
            coverage=len(accepted) / len(rows) if rows else None,
            relevant_recall=correct / sum(r["correct"] for r in rows) if any(r["correct"] for r in rows) else None,
            false_accept_count=len(accepted) - correct))
    return result
