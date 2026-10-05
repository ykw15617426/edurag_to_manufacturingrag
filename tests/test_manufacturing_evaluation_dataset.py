import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from rag_qa.evaluation.benchmark import controlled_benchmark, MODELS
from rag_qa.evaluation.schemas import EvaluationDataset, RetrievalEvaluationSample, load_dataset
from rag_qa.evaluation.runner import BENCHMARK
from rag_qa.ingestion.fingerprints import build_parent_id, build_child_id, sha256_content
from rag_qa.core.milvus_schema import validate_manufacturing_document


def sample_data():
    return controlled_benchmark()[0].samples[0].model_dump(mode="json")


def test_fixed_benchmark_real_stage2_id_formulas_and_active_versions():
    dataset, children, corpus = controlled_benchmark()
    assert dataset.dataset_type == "controlled_synthetic" and len(dataset.samples) == 25
    assert len(children) == 42 and len(corpus.entries) == 21
    assert {c.metadata["equipment_model"] for c in children} == set(MODELS)
    for child in children:
        m = child.metadata
        validate_manufacturing_document(child)
        assert m["parent_id"] == build_parent_id(m["document_id"], sha256_content(m["parent_content"]))
        assert m["child_id"] == build_child_id(m["document_id"], m["parent_id"], sha256_content(child.page_content))
        if m["knowledge_type"] == "parameter": assert m["document_version"] == "V2"
    assert load_dataset(BENCHMARK).sha256() == dataset.sha256()
    assert dataset.sha256() == controlled_benchmark()[0].sha256()


def test_canonical_order_and_jsonl_same_sha(tmp_path):
    dataset, _, _ = controlled_benchmark()
    reversed_dataset = EvaluationDataset(**{**dataset.model_dump(exclude={"samples"}), "samples": tuple(reversed(dataset.samples))})
    assert reversed_dataset.sha256() == dataset.sha256()
    path = tmp_path / "data.jsonl"
    header = dataset.model_dump(mode="json", exclude={"samples"})
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in [header, *[s.model_dump(mode="json") for s in dataset.samples]]), encoding="utf-8")
    assert load_dataset(path).sha256() == dataset.sha256()
    changed = dataset.samples[0].model_copy(update={"query": "不同问题"})
    assert dataset.model_copy(update={"samples": (changed, *dataset.samples[1:])}).sha256() != dataset.sha256()


@pytest.mark.parametrize("field,value", [
    ("sample_id", " "), ("query", ""), ("query", "x" * 16385), ("query", "\ud800"),
    ("expected_parent_ids", []), ("expected_child_ids", []), ("expected_document_ids", []),
    ("expected_parent_ids", ["A" * 64]), ("expected_child_ids", ["abc"]),
    ("expected_parent_ids", ["a" * 64, "a" * 64]), ("expected_document_ids", ["D", "D"]),
    ("expected_equipment_model", "bad model"), ("expected_alarm_code", "E102-"),
    ("expected_part_number", " PN-001 "), ("tags", ["x"] * 33), ("tags", ["x", "x"]),
    ("tags", [" "]), ("fast_path_labels", ["unknown"]), ("unexpected", "x")])
def test_strict_sample_rejects(field, value):
    data = sample_data(); data[field] = value
    with pytest.raises((ValidationError, UnicodeError)): RetrievalEvaluationSample.model_validate(data)


def test_empty_duplicate_dataset_and_legacy_isolation(tmp_path):
    data = dict(dataset_type="controlled_synthetic", provenance_note="synthetic", samples=[])
    with pytest.raises(ValidationError): EvaluationDataset(**data)
    data["samples"] = [sample_data(), sample_data()]
    with pytest.raises(ValidationError): EvaluationDataset(**data)
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps([dict(question="教育问题", ground_truth="教育答案")]), encoding="utf-8")
    with pytest.raises(ValidationError): load_dataset(path)
    path.write_text('{"dataset_type":"controlled_synthetic","dataset_type":"production_replay"}', encoding="utf-8")
    with pytest.raises(ValueError): load_dataset(path)


def test_dataset_provenance_nonblank():
    with pytest.raises(ValidationError): EvaluationDataset(dataset_type="controlled_synthetic", provenance_note=" ", samples=[sample_data()])
