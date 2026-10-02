"""Synthetic Stage 6-shaped Child evidence; no LangChain/model dependency."""
from copy import deepcopy
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_manufacturing_milvus_schema import row
from rag_qa.retrieval.parent_aggregation import PARENT_FIELDS, ParentAggregationError, aggregate_parents


def hit(parent="a", child="1", score=0.81, **metadata):
    fields = {name: value for name, value in row().items() if name not in {"text", "dense_vector", "sparse_vector"}}
    fields.update(id=child * 64, child_id=child * 64, parent_id=parent * 64,
                  child_content_sha256=child * 64, retrieval_score=score)
    fields.update(metadata)
    return SimpleNamespace(page_content="Child " + child, metadata=fields)


def test_multiple_children_max_score_ids_ranks_and_metadata():
    children = [hit(score=0.73), hit(child="2", score=0.81), hit(parent="b", child="3", score=0.77)]
    before = deepcopy(children)
    parents = aggregate_parents(children)
    first = parents[0]
    assert first.parent_id == "a" * 64 and first.best_retrieval_score == 0.81
    assert first.child_hit_count == 2 and first.matched_child_ids == ("1" * 64, "2" * 64)
    assert first.first_child_rank == 1
    assert [m.child_rank for m in first.matched_children] == [1, 2]
    assert [m.retrieval_score for m in first.matched_children] == [0.73, 0.81]
    assert first.page_content == children[0].metadata["parent_content"]
    assert dict(first.metadata) == {name: children[0].metadata[name] for name in PARENT_FIELDS}
    assert children == before


def test_same_text_different_parent_ids_remain_separate():
    parents = aggregate_parents([hit(), hit(parent="b", child="2")])
    assert len(parents) == 2 and parents[0].page_content == parents[1].page_content
    assert [p.parent_id for p in parents] == ["a" * 64, "b" * 64]


@pytest.mark.parametrize("field", PARENT_FIELDS)
def test_all_parent_business_and_provenance_conflicts_fail(field):
    first, second = hit(), hit(child="2")
    if field == "parent_id":
        # A different identity is a different group, never a content conflict.
        second.metadata[field] = "b" * 64
        assert len(aggregate_parents([first, second])) == 2
        return
    second.metadata[field] = "conflicting value"
    with pytest.raises(ParentAggregationError, match=field):
        aggregate_parents([first, second])


def test_extra_provenance_preserved_and_checked():
    first, second = hit(batch_label="synthetic"), hit(child="2", batch_label="synthetic")
    assert aggregate_parents([first, second])[0].metadata["batch_label"] == "synthetic"
    second.metadata["batch_label"] = "different"
    with pytest.raises(ParentAggregationError, match="batch_label"):
        aggregate_parents([first, second])


def test_stable_pre_rerank_order_score_then_first_rank():
    children = [hit(parent="c", score=-1.0), hit(parent="b", child="2", score=1.9),
                hit(parent="a", child="3", score=1.9)]
    expected = ["b" * 64, "a" * 64, "c" * 64]
    for _ in range(3):
        parents = aggregate_parents(children)
        assert [p.parent_id for p in parents] == expected
        assert [p.best_retrieval_score for p in parents] == [1.9, 1.9, -1.0]


@pytest.mark.parametrize("score", [None, "0.8", True, float("nan"), float("inf"), -float("inf")])
def test_invalid_retrieval_scores_fail(score):
    with pytest.raises(ParentAggregationError, match="retrieval_score"):
        aggregate_parents([hit(score=score)])


@pytest.mark.parametrize("field", ["parent_content", "document_id", "source_file", "child_id", "retrieval_score"])
def test_missing_contract_fields_fail(field):
    document = hit(); del document.metadata[field]
    with pytest.raises(ParentAggregationError, match=field): aggregate_parents([document])


@pytest.mark.parametrize("field,value", [("parent_id", "P1"), ("child_id", "C1"), ("id", "f" * 64),
                                       ("child_content_sha256", None), ("parent_content", " "), ("parent_content", 42)])
def test_invalid_identity_or_parent_text_fails(field, value):
    with pytest.raises(ParentAggregationError): aggregate_parents([hit(**{field: value})])


def test_duplicate_child_ids_fail_and_child_signals_not_accepted():
    with pytest.raises(ParentAggregationError, match="duplicate"):
        aggregate_parents([hit(), hit(score=0.9)])
    with pytest.raises(ParentAggregationError, match="parent signals"):
        aggregate_parents([hit(rerank_score=0.1)])


def test_empty_input_and_no_metadata_fail():
    assert aggregate_parents([]) == ()
    with pytest.raises(ParentAggregationError): aggregate_parents([SimpleNamespace(metadata=None)])


def test_errors_do_not_disclose_parent_text_or_mutate_inputs():
    first, second = hit(parent_content="sensitive parent text"), hit(child="2", parent_content="other text")
    with pytest.raises(ParentAggregationError) as error: aggregate_parents([first, second])
    assert "sensitive" not in str(error.value) and "other text" not in str(error.value)
