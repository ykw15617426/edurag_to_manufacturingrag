"""Hand rankings, never measurements of real model quality."""
import pytest
from rag_qa.evaluation.metrics import ranking_metrics, macro_metrics, bm25_threshold_sweep


@pytest.mark.parametrize("relevant,ranking,k,hit,recall,mrr,rank", [
    (["P2"], ["P1", "P2", "P3"], 1, 0, 0, 0, None),
    (["P2"], ["P1", "P2", "P3"], 2, 1, 1, .5, 2),
    (["P2"], ["P1", "P2", "P3"], 3, 1, 1, .5, 2),
    (["P2", "P4"], ["P1", "P4", "P2"], 2, 1, .5, .5, 2),
    (["P2", "P4"], ["P1", "P4", "P2"], 3, 1, 1, .5, 2),
    (["P2"], ["P1", "P1", "P2"], 2, 1, 1, .5, 2),
    (["P2"], [], 5, 0, 0, 0, None),
    (["P2", "P2"], ["P2", "P2"], 2, 1, 1, 1, 1),
])
def test_exact_metrics(relevant, ranking, k, hit, recall, mrr, rank):
    assert ranking_metrics(relevant, ranking, k) == dict(k=k, hit=hit, recall=recall, mrr=mrr, first_relevant_rank=rank)


@pytest.mark.parametrize("k", [0, -1, True, 2.5, "2", None, 16385])
def test_invalid_k(k):
    with pytest.raises(ValueError): ranking_metrics(["P1"], ["P1"], k)


@pytest.mark.parametrize("relevant,ranking", [([], []), ([""], []), (["P1"], [" "]), (["P1"], [1])])
def test_invalid_ids(relevant, ranking):
    with pytest.raises(ValueError): ranking_metrics(relevant, ranking, 2)


def test_macro_and_empty_explicit_null():
    assert macro_metrics([]) == dict(sample_count=0, hit=None, recall=None, mrr=None)
    rows = [ranking_metrics(["P2"], ["P1", "P2"], 2), ranking_metrics(["P2"], [], 2)]
    assert macro_metrics(rows) == dict(sample_count=2, hit=.5, recall=.5, mrr=.25)


def test_raw_bm25_sweep_respects_token_matches_and_false_accepts():
    rows = [dict(raw_score=2., correct=True, matched_token_count=1), dict(raw_score=1., correct=False, matched_token_count=1),
            dict(raw_score=5., correct=False, matched_token_count=0)]
    low, high = bm25_threshold_sweep(rows, [1., 2.])
    assert low["accepted_count"] == 2 and low["precision"] == .5 and low["false_accept_count"] == 1
    assert high["accepted_count"] == 1 and high["precision"] == 1 and high["coverage"] == 1/3
    assert high["relevant_recall"] == 1
    assert bm25_threshold_sweep([], [2.])[0]["precision"] is None


@pytest.mark.parametrize("threshold", [float("nan"), float("inf"), True, "2"])
def test_bad_threshold(threshold):
    with pytest.raises(ValueError): bm25_threshold_sweep([], [threshold])
