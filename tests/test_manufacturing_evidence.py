"""Evidence integrity over synthetic real Stage 7/8 shapes."""
from types import SimpleNamespace
import pytest
from test_parent_aggregation import hit
from test_manufacturing_metadata_filters import analysis
from test_manufacturing_bm25 import entry
from test_manufacturing_fast_path import ParentGateway
from test_manufacturing_milvus_schema import vector_store_unit
from rag_qa.retrieval.parent_aggregation import aggregate_parents
from rag_qa.retrieval.parent_reranker import rerank_parents
from rag_qa.retrieval.fast_path import FastPathCorpus, ManufacturingFastPath
from rag_qa.generation.evidence import (normalize_evidence, guard_evidence,
    EvidenceIntegrityError, EvidenceConflictError, EvidenceGuardError)


def document(parent="a", body="MZ-2000 报警 E102。检查润滑管路。每500小时维护，压力3.5 MPa，电压220V。", **metadata):
    fields = dict(parent_id=parent*64, document_id="SYNTHETIC-DOC", document_version="1.10",
        title="设备手册", knowledge_type="manual", equipment_model="MZ-2000", manufacturer=None,
        alarm_code="E102", part_number="BRG-6205-ZZ", source_file="synthetic/manual.md",
        effective_date="2026-10-02", language="zh-CN", best_retrieval_score=.8, rerank_score=.6)
    fields.update(metadata)
    return SimpleNamespace(page_content=body, metadata=fields)


def test_real_parent_documents_normalize(vector_store_unit):
    parents = aggregate_parents([hit(), hit(parent="b", child="2")])
    docs = rerank_parents("query", parents, SimpleNamespace(predict=lambda pairs: [.8]*len(pairs)), top_m=3)
    records = normalize_evidence(docs)
    assert [r.evidence_id for r in records] == ["E1", "E2"]
    for record, doc in zip(records, docs):
        assert record.page_content == doc.page_content
        for field in ("parent_id", "document_id", "document_version", "title", "source_file", "equipment_model", "language", "rerank_score"):
            assert getattr(record, field) == doc.metadata[field]


def test_actual_fast_path_normalize():
    approved = entry()
    result = ManufacturingFastPath(FastPathCorpus([approved]), ParentGateway()).probe(approved.question, analysis(intent="knowledge", equipment_model="MZ-2000"))
    record, = normalize_evidence(result.evidence)
    assert record.match_type == "exact_faq" and record.page_content == approved.evidence_text
    assert record.parent_id == approved.parent_id and record.document_version == "1.10"


def test_stable_ids_duplicate_same_parent_dedupe_and_no_input_mutation():
    first, second = document(), document(parent="b")
    before = dict(first.metadata)
    records = normalize_evidence([first, document(rerank_score=.9), second])
    assert [r.evidence_id for r in records] == ["E1", "E2"]
    assert records == normalize_evidence([first, second]) and first.metadata == before
    assert [r.parent_id for r in normalize_evidence([second, first])] == ["b"*64, "a"*64]


@pytest.mark.parametrize("changes", [dict(body="different"), dict(document_id="OTHER"), dict(document_version="2"),
    dict(title="other"), dict(source_file="other.md"), dict(equipment_model="CX-3000"), dict(alarm_code="E103"),
    dict(part_number="OTHER-001"), dict(effective_date="2026-10-03"), dict(language="en")])
def test_same_parent_conflicts(changes):
    with pytest.raises(EvidenceConflictError): normalize_evidence([document(), document(**changes)])


def test_same_document_multi_version_fails_and_distinct_documents_allowed():
    with pytest.raises(EvidenceConflictError): normalize_evidence([document(), document(parent="b", document_version="2")])
    assert len(normalize_evidence([document(), document(parent="b", document_id="OTHER", document_version="2")])) == 2


@pytest.mark.parametrize("field,value", [("parent_id", "wrong"), ("parent_id", "A"*64), ("document_id", ""),
    ("document_version", " "), ("title", ""), ("source_file", 2), ("language", ""), ("knowledge_type", "education"),
    ("alarm_code", "E/102"), ("equipment_model", "MZ 2000"), ("part_number", " 0001"),
    ("effective_date", 123), ("effective_date", "2026-99-99"), ("rerank_score", float("nan")),
    ("best_retrieval_score", True), ("document_id", "x"*513)])
def test_malformed_evidence(field, value):
    with pytest.raises(EvidenceIntegrityError): normalize_evidence([document(**{field:value})])


@pytest.mark.parametrize("body", ["", " ", "\ud800", 2, "x"*65536], ids=["empty", "blank", "unicode", "type", "size"])
def test_malformed_content(body):
    with pytest.raises(EvidenceIntegrityError): normalize_evidence([document(body=body)])


@pytest.mark.parametrize("field", ["parent_id", "document_id", "document_version", "title", "source_file", "language"])
def test_missing_required_metadata(field):
    doc = document(); doc.metadata.pop(field)
    with pytest.raises(EvidenceIntegrityError): normalize_evidence([doc])


@pytest.mark.parametrize("field,wrong", [("equipment_model", "CX-3000"), ("equipment_model", "mz-2000"),
    ("alarm_code", "E103"), ("part_number", "BRG6205"), ("part_number", None)])
def test_hard_identifier_mismatch_or_missing(field, wrong):
    confirmed = dict(equipment_model="MZ-2000", alarm_code="E102", part_number="BRG-6205-ZZ")
    with pytest.raises(EvidenceGuardError): guard_evidence(normalize_evidence([document(**{field:wrong})]), analysis(**confirmed))


def test_empty_and_compatible_and_general():
    assert normalize_evidence([]) == ()
    guard_evidence(normalize_evidence([document()]), analysis(intent="general", equipment_model="MZ-2000"))
    with pytest.raises(EvidenceGuardError): guard_evidence((), None)


def test_evidence_count_bound():
    with pytest.raises(EvidenceIntegrityError): normalize_evidence([document()]*129)
