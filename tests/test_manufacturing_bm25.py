"""Real pinned BM25 scores over synthetic approved FAQ, not production quality."""
from pathlib import Path
import sys
import math

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag_qa.retrieval.fast_path import FastPathCorpus, FastPathEntry, CorpusValidationError
from rag_qa.retrieval.manufacturing_bm25 import BM25AcceptancePolicy, tokenize, normalize_question


def entry(entry_id="faq1", **values):
    data = dict(entry_id=entry_id, question="MZ-2000 主轴润滑怎么操作？", evidence_text="Synthetic approved evidence only",
                document_id="SYNTHETIC-DOC", document_version="1.10", parent_id="a" * 64,
                title="Synthetic manual", knowledge_type="manual", equipment_model="MZ-2000",
                source_file="synthetic/manual.md")
    data.update(values)
    return FastPathEntry(**data)


@pytest.mark.parametrize("identifier", ["MZ-2000", "mZ_0002", "ALM-007", "E102", "BRG-6205-ZZ", "P_0003_A", "00001234"])
def test_preserves_identifier_tokens(identifier):
    tokens = tokenize("设备 " + identifier + " 如何操作")
    assert identifier in tokens and tokens.count(identifier) == 1


def test_normalization_conservative_and_deterministic():
    assert normalize_question("  Cafe\u0301 \n MZ-2000\t 00001234  ") == "Café MZ-2000 00001234"
    assert tokenize("mZ_0002 润滑") == ("mZ_0002", "润", "滑", "润滑")
    assert "MZ-2000" in tokenize("MZ-2000") and "mz-2000" not in tokenize("MZ-2000")


def test_real_raw_scores_equal_library_no_softmax():
    from rank_bm25 import BM25Okapi
    corpus = FastPathCorpus([entry(), entry("other", question="CX-3000 冷却泵检查", equipment_model="CX-3000"),
                             entry("third", question="机床轴承更换步骤", equipment_model=None)])
    query = "MZ-2000 主轴润滑"
    ranked = corpus.bm25.rank(query, {})
    scores = BM25Okapi([tokenize(e.question) for e in corpus.entries]).get_scores(tokenize(query))
    expected = dict(zip([e.entry_id for e in corpus.entries], scores))
    assert {c.entry.entry_id: c.raw_score for c in ranked} == expected
    assert all(c.corpus_size == c.candidate_scope_size == 3 for c in ranked)
    assert [c.rank for c in ranked] == [1, 2, 3]


@pytest.mark.parametrize("field,value", [("equipment_model", "MZ-2000"), ("alarm_code", "E102"), ("part_number", "P_0003_A")])
def test_hard_scope_before_scoring(field, value, monkeypatch):
    a, b = entry(**{field: value}), entry("wrong", **{field: None})
    corpus = FastPathCorpus([a, b])
    recorded = []
    original = corpus.bm25.index.get_batch_scores
    monkeypatch.setattr(corpus.bm25.index, "get_batch_scores", lambda tokens, ids: recorded.append(ids) or original(tokens, ids))
    result = corpus.bm25.rank("主轴润滑", {field: value})
    assert len(result) == 1 and result[0].entry.entry_id == a.entry_id
    assert recorded == [[0]] and result[0].candidate_scope_size == 1 and result[0].corpus_size == 2
    assert corpus.bm25.rank("主轴润滑", {field: "UNKNOWN"}) == ()


def test_conjunction_and_stable_ties():
    corpus = FastPathCorpus([entry("b", alarm_code="E102"), entry("a", alarm_code="E999"),
                             entry("c", alarm_code="E102", equipment_model="CX-3000")])
    assert [c.entry.entry_id for c in corpus.bm25.rank("未知", {})] == ["a", "b", "c"]
    assert [c.entry.entry_id for c in corpus.bm25.rank("主轴", {"equipment_model": "MZ-2000", "alarm_code": "E102"})] == ["b"]
    with pytest.raises(ValueError): corpus.bm25.rank("主轴", {"source_file": "any"})


def test_canonical_cold_hot_metadata_tokens_and_ranking():
    cold = FastPathCorpus([entry("m", knowledge_type="maintenance", maintenance_cycle=dict(value=500, unit="hour")), entry()])
    hot = FastPathCorpus.from_json(cold.to_json())
    assert hot.entries == cold.entries and hot.bm25.tokens == cold.bm25.tokens
    assert hot.bm25.rank("润滑操作", {}) == cold.bm25.rank("润滑操作", {})
    assert cold.to_json() == hot.to_json()
    with pytest.raises(ValueError): hot.entries[0].equipment_model = "other"
    with pytest.raises(ValueError): hot.entries[1].maintenance_cycle.value = 100


def test_expansion_records_real_scores_and_scope():
    base = FastPathCorpus([entry(), entry("other", question="冷却水泵", equipment_model=None)])
    expanded = FastPathCorpus([*base.entries, *[entry(f"unrelated{i:03}", question=f"QX-{i:04} 电柜温度记录", equipment_model=None) for i in range(200)]])
    before = base.bm25.rank("MZ-2000 主轴润滑", {"equipment_model": "MZ-2000"})[0]
    after = expanded.bm25.rank("MZ-2000 主轴润滑", {"equipment_model": "MZ-2000"})[0]
    assert (before.rank, after.rank, before.corpus_size, after.corpus_size) == (1, 1, 2, 202)
    assert math.isfinite(before.raw_score) and math.isfinite(after.raw_score)
    print(dict(before_score=before.raw_score, after_score=after.raw_score, rank=1, before_size=2, after_size=202))


@pytest.mark.parametrize("value", [None, True, "0.85", float("nan"), float("inf")])
def test_explicit_policy_invalid_threshold(value):
    with pytest.raises(ValueError): BM25AcceptancePolicy(value)


def test_empty_corpus_and_no_overlap_never_accepted():
    assert FastPathCorpus([]).bm25.rank("query", {}) == ()
    corpus = FastPathCorpus([entry()])
    candidate = corpus.bm25.rank("UNRELATED", {})[0]
    assert candidate.raw_score == 0 and not BM25AcceptancePolicy(-100).accepts(candidate)


@pytest.mark.parametrize("data", [{}, ("question",), {"entry_id": "faq", "answer": "unsafe"}])
def test_bad_cold_shapes_fail_fast(data):
    with pytest.raises(CorpusValidationError): FastPathCorpus([data])


@pytest.mark.parametrize("field,value", [("parent_id", "P1"), ("equipment_model", "MZ 2000"), ("alarm_code", 102),
                                       ("part_number", "P/001"), ("document_version", 1.10), ("knowledge_type", "faq"),
                                       ("evidence_text", ""), ("source_file", ""), ("title", "字" * 400)])
def test_invalid_metadata_fail_fast(field, value):
    data = entry().model_dump(mode="json"); data[field] = value
    with pytest.raises(CorpusValidationError): FastPathCorpus([data])


def test_duplicate_ids_and_empty_tokens_fail_fast():
    with pytest.raises(CorpusValidationError, match="duplicate"): FastPathCorpus([entry(), entry()])
    with pytest.raises(CorpusValidationError): FastPathCorpus([entry(question="？？？")])


@pytest.mark.parametrize("snapshot", ['{}', '[]', '{"schema_version":"wrong","entries":[]}',
                                      '{"schema_version":"manufacturing_fast_path_v1","entries":[],"entries":[]}',
                                      '{"schema_version":"manufacturing_fast_path_v1","entries":[["question"]]}'])
def test_invalid_snapshot_fails(snapshot):
    with pytest.raises(CorpusValidationError): FastPathCorpus.from_json(snapshot)
