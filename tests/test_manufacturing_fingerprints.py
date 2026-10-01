"""Synthetic Stage 2 fixtures; pure hashes and isolated Processor control flow.

Loader/Splitter doubles below do not constitute real LangChain integration.
"""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rag_qa.ingestion import fingerprints
from rag_qa.ingestion.fingerprints import (
    sha256_file, normalize_content_for_hash, sha256_content, build_parent_id, build_child_id,
)
from rag_qa.ingestion.metadata_loader import load_with_metadata, InvalidManufacturingMetadataError, MetadataMergeConflictError
from test_manufacturing_metadata import processor_unit, front_file, valid, text_loader


ABC_SHA256 = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_known_sha256(tmp_path):
    path = tmp_path / "abc.bin"
    path.write_bytes(b"abc")
    assert sha256_file(path) == ABC_SHA256
    assert sha256_content("abc") == ABC_SHA256


@pytest.mark.parametrize("data", [b"", b"abc", bytes(range(256)), b"\x00\xff\xfe\x80\r\n"])
def test_raw_file_fingerprint(tmp_path, data):
    path = tmp_path / "raw.bin"
    path.write_bytes(data)
    digest = sha256_file(path)
    assert digest == sha256_file(path) == hashlib.sha256(data).hexdigest()
    assert re.fullmatch("[0-9a-f]{64}", digest)
    path.write_bytes(data + b"\x01")
    assert sha256_file(path) != digest


def test_streaming_large_file(tmp_path, monkeypatch):
    data = bytes(range(256)) * 20000  # synthetic ~5MB
    path = tmp_path / "large.bin"
    path.write_bytes(data)
    reads = []
    real_open = open

    class BoundedReader:
        def __enter__(self):
            self.file = real_open(path, "rb")
            return self

        def read(self, size=-1):
            assert size > 0, "must use bounded reads, not read()"
            block = self.file.read(size)
            reads.append(len(block))
            return block

        def __exit__(self, *args):
            self.file.close()

    monkeypatch.setattr(fingerprints, "open", lambda *args: BoundedReader(), raising=False)
    assert sha256_file(path) == hashlib.sha256(data).hexdigest()
    assert len(reads) > 2 and sum(reads) == len(data)
    assert max(reads) < len(data)  # no business assertion about block size


@pytest.mark.parametrize("left,right", [
    ("abc\r\ndef", "abc\ndef"), ("abc\rdef", "abc\ndef"),
    ("abc   \n", "abc\n"), ("abc\t\n def\t", "abc\n def"),
    ("\n\t abc \n\n", "abc"), ("Cafe\u0301", "Café"),
])
def test_format_equivalence(left, right):
    assert normalize_content_for_hash(left) == normalize_content_for_hash(right)
    assert sha256_content(left) == sha256_content(right)


@pytest.mark.parametrize("left,right", [
    ("A B", "AB"), ("A  B", "A B"), ("E102", "e102"),
    ("设备。", "设备！"), ("Ａ", "A"), ("a\n b", "a\nb"),
    ("a\n\nb", "a\nb"),
])
def test_meaningful_characters_remain_distinct(left, right):
    assert sha256_content(left) != sha256_content(right)


def ids_for_parents(document_id, texts):
    counts = Counter()
    result = []
    for text in texts:
        digest = sha256_content(text)
        result.append(build_parent_id(document_id, digest, counts[digest]))
        counts[digest] += 1
    return result


def ids_for_children(document_id, parent_id, texts):
    counts = Counter()
    result = []
    for text in texts:
        digest = sha256_content(text)
        result.append(build_child_id(document_id, parent_id, digest, counts[digest]))
        counts[digest] += 1
    return result


def test_parent_identity_stability_and_occurrences():
    original = ids_for_parents("Synthetic:A", ["A", "B", "A"])
    assert original == ids_for_parents("Synthetic:A", ["A", "B", "A"])
    inserted = ids_for_parents("Synthetic:A", ["Unrelated", "A", "B", "A"])
    assert inserted[1:] == original
    assert original[0] != original[2]
    assert original != ids_for_parents("Synthetic:B", ["A", "B", "A"])
    assert all(re.fullmatch("[0-9a-f]{64}", item) for item in original)


def test_child_identity_stability_and_occurrences():
    original = ids_for_children("Synthetic:A", "parent-A", ["A", "B", "A"])
    assert original == ids_for_children("Synthetic:A", "parent-A", ["A", "B", "A"])
    inserted = ids_for_children("Synthetic:A", "parent-A", ["Unrelated", "A", "B", "A"])
    assert inserted[1:] == original and original[0] != original[2]
    assert original != ids_for_children("Synthetic:B", "parent-A", ["A", "B", "A"])
    assert original != ids_for_children("Synthetic:A", "parent-B", ["A", "B", "A"])
    assert all(re.fullmatch("[0-9a-f]{64}", item) for item in original)


def test_identity_canonical_json_and_component_boundaries():
    # IDs with delimiters cannot shift the boundaries of the JSON array.
    assert build_parent_id("a:b", "c", 0) != build_parent_id("a", "b:c", 0)
    assert build_child_id("a:b", "c", "d", 0) != build_child_id("a", "b:c", "d", 0)
    expected = hashlib.sha256('["parent","业务:001","abc",0]'.encode("utf-8")).hexdigest()
    assert build_parent_id("业务:001", "abc", 0) == expected
    assert build_parent_id("a", "b", 0) != build_child_id("a", "b", "c", 0)


def test_cross_process_determinism():
    code = "from rag_qa.ingestion.fingerprints import build_child_id; print(build_child_id('业务:001', 'p', 'h', 0))"
    digest = subprocess.check_output([sys.executable, "-c", code], cwd=ROOT, text=True).strip()
    assert digest == build_child_id("业务:001", "p", "h", 0)


@pytest.mark.parametrize("suffix", [".txt", ".md"])
def test_front_matter_original_hash_before_sanitizing(tmp_path, suffix):
    path = front_file(tmp_path, suffix=suffix)
    original = path.read_bytes()
    sanitized_hash = []

    def loader(body_path):
        sanitized_hash.append(sha256_file(body_path))
        return text_loader(body_path)

    doc = load_with_metadata(path, loader)[0]
    assert doc.metadata["document_sha256"] == hashlib.sha256(original).hexdigest()
    assert doc.metadata["document_sha256"] != sanitized_hash[0]
    assert doc.page_content == "Synthetic body.\n" and path.read_bytes() == original


def test_sidecar_change_excluded_from_raw_fingerprint(tmp_path):
    path = tmp_path / "source.pdf"
    path.write_bytes(b"\x00\xffSynthetic binary source")
    sidecar = Path(str(path) + ".yaml")

    def loader(source):
        assert source == str(path)
        return [SimpleNamespace(page_content="Synthetic extracted body", metadata={})]

    sidecar.write_text(yaml.safe_dump(valid()), encoding="utf-8")
    first = load_with_metadata(path, loader)[0]
    data = valid()
    data["document_version"] = "2.0"
    data["title"] = "Changed sidecar metadata"
    sidecar.write_text(yaml.safe_dump(data), encoding="utf-8")
    second = load_with_metadata(path, loader)[0]
    assert first.metadata["document_sha256"] == second.metadata["document_sha256"] == sha256_file(path)
    assert first.metadata["document_version"] != second.metadata["document_version"]


def test_invalid_metadata_fails_before_hash(tmp_path, monkeypatch):
    from rag_qa.ingestion import metadata_loader
    path = front_file(tmp_path, valid("alarm"))
    monkeypatch.setattr(metadata_loader, "sha256_file", lambda p: pytest.fail("invalid metadata reached hash"))
    with pytest.raises(InvalidManufacturingMetadataError):
        load_with_metadata(path, text_loader)


def test_loader_cannot_override_document_hash(tmp_path):
    path = front_file(tmp_path)
    with pytest.raises(MetadataMergeConflictError, match="document_sha256"):
        load_with_metadata(path, lambda p: [SimpleNamespace(metadata={"document_sha256": "spoof"})])


@pytest.fixture
def identity_processor(processor_unit, monkeypatch):
    class ControlledSplitter:
        """Predetermined boundaries isolate identity bookkeeping from LangChain."""
        def __init__(self, chunk_size, chunk_overlap):
            self.parent = chunk_size == 100

        def split_documents(self, documents):
            delimiter = "\n---P---\n" if self.parent else "|"
            return [SimpleNamespace(page_content=text, metadata=deepcopy(doc.metadata))
                    for doc in documents for text in doc.page_content.split(delimiter)]

    monkeypatch.setattr(processor_unit, "ChineseRecursiveTextSplitter", ControlledSplitter)
    monkeypatch.setattr(processor_unit, "MarkdownTextSplitter", ControlledSplitter)
    return processor_unit


def run_pipeline(processor, directory, mode="manufacturing"):
    return processor.process_documents(str(directory), 100, 10, 0, 0, metadata_mode=mode)


def test_legacy_positional_ids_and_no_fingerprint(identity_processor, tmp_path):
    (tmp_path / "legacy.txt").write_text("A|B\n---P---\nC|D", encoding="utf-8")
    chunks = run_pipeline(identity_processor, tmp_path, "legacy")
    assert [c.metadata["id"] for c in chunks] == ["doc_0_parent_0_child_0", "doc_0_parent_0_child_1",
                                                  "doc_0_parent_1_child_0", "doc_0_parent_1_child_1"]
    assert [c.metadata["parent_id"] for c in chunks] == ["doc_0_parent_0"] * 2 + ["doc_0_parent_1"] * 2
    assert all("document_sha256" not in c.metadata and "child_id" not in c.metadata for c in chunks)


def test_processor_identity_version_independence_and_metadata(identity_processor, tmp_path):
    data = valid("alarm", alarm_code="E102", equipment_model="MZ-2000")
    path = front_file(tmp_path, data, body="A|B\n---P---\nC|D")
    first = run_pipeline(identity_processor, tmp_path)
    data["document_version"] = "2.0"
    front_file(tmp_path, data, body="A|B\n---P---\nC|D")
    second = run_pipeline(identity_processor, tmp_path)
    assert [c.metadata["id"] for c in first] == [c.metadata["id"] for c in second]
    assert [c.metadata["parent_id"] for c in first] == [c.metadata["parent_id"] for c in second]
    assert first[0].metadata["document_sha256"] != second[0].metadata["document_sha256"]
    for child in second:
        m = child.metadata
        assert m["document_version"] == "2.0" and m["document_id"] == data["document_id"]
        assert m["equipment_model"] == "MZ-2000" and m["alarm_code"] == "E102"
        assert m["id"] == m["child_id"]
        assert m["document_sha256"] == sha256_file(path)
        assert m["parent_content_sha256"] == sha256_content(m["parent_content"])
        assert m["child_content_sha256"] == sha256_content(child.page_content)
        assert m["parent_id"] == build_parent_id(data["document_id"], m["parent_content_sha256"])
        assert m["id"] == build_child_id(data["document_id"], m["parent_id"], m["child_content_sha256"])
        json.dumps(m)


def test_processor_parent_insertions_and_duplicates(identity_processor, tmp_path):
    front_file(tmp_path, body="A|A\n---P---\nB|C\n---P---\nA|A")
    original = run_pipeline(identity_processor, tmp_path)
    assert len({c.metadata["id"] for c in original}) == len(original) == 6
    front_file(tmp_path, body="X|Y\n---P---\nA|A\n---P---\nB|C\n---P---\nA|A")
    inserted = run_pipeline(identity_processor, tmp_path)
    assert [c.metadata["id"] for c in inserted[2:]] == [c.metadata["id"] for c in original]
    assert [c.page_content for c in original] == ["A", "A", "B", "C", "A", "A"]  # no dedup


def test_processor_child_insertion_for_same_parent(identity_processor, tmp_path, monkeypatch):
    front_file(tmp_path, body="Unchanged synthetic parent")
    supplied = ["A", "B", "A"]

    class ControlledChildSplitter:
        def split_documents(self, parents):
            return [SimpleNamespace(page_content=text, metadata=deepcopy(parents[0].metadata)) for text in supplied]

    old_splitter = identity_processor.ChineseRecursiveTextSplitter
    monkeypatch.setattr(identity_processor, "ChineseRecursiveTextSplitter",
                        lambda chunk_size, chunk_overlap: old_splitter(chunk_size, chunk_overlap)
                        if chunk_size == 100 else ControlledChildSplitter())
    original = run_pipeline(identity_processor, tmp_path)
    supplied.insert(0, "Unrelated")
    inserted = run_pipeline(identity_processor, tmp_path)
    assert [c.metadata["id"] for c in inserted[1:]] == [c.metadata["id"] for c in original]


def test_path_and_walk_order_independence(identity_processor, tmp_path, monkeypatch):
    first_dir, moved_dir = tmp_path / "first", tmp_path / "moved"
    first_dir.mkdir()
    moved_dir.mkdir()
    path = front_file(first_dir, body="A|B")
    # A second distinct business document with identical body must have different IDs.
    text = path.read_text(encoding="utf-8")
    (first_dir / "other.txt").write_text(text.replace("Synthetic-001", "Synthetic-002"), encoding="utf-8")
    first = run_pipeline(identity_processor, first_dir)
    for source in first_dir.iterdir():
        (moved_dir / source.name).write_bytes(source.read_bytes())
    # Isolate the processor's traversal; tempfile cleanup also uses global os.walk.
    monkeypatch.setattr(identity_processor, "os", SimpleNamespace(
        path=identity_processor.os.path,
        walk=lambda directory: [(str(directory), [], ["other.txt", "example.txt"])],
    ))
    second = run_pipeline(identity_processor, moved_dir)
    assert {c.metadata["id"] for c in first} == {c.metadata["id"] for c in second}
    assert len({c.metadata["id"] for c in first}) == 4
    assert len({c.metadata["child_content_sha256"] for c in first}) == 2


def test_parent_occurrences_span_loader_outputs(identity_processor, tmp_path):
    front_file(tmp_path)

    class MultiDocumentLoader:
        def __init__(self, *args, **kwargs):
            pass

        def load(self):
            return [SimpleNamespace(page_content="Repeated", metadata={}) for _ in range(2)]

    identity_processor.document_loaders[".txt"] = MultiDocumentLoader
    children = run_pipeline(identity_processor, tmp_path)
    assert len(children) == 2 and children[0].metadata["parent_id"] != children[1].metadata["parent_id"]
    assert len({c.metadata["id"] for c in children}) == 2


def test_real_manufacturing_fingerprint_pipeline(tmp_path):
    from test_stage0_smoke import require_modules, import_real_module
    require_modules(["langchain_core", "langchain_community", "langchain_text_splitters",
                     "docx", "pptx", "fitz", "cv2"])
    processor = import_real_module("rag_qa.core.document_processor")
    path = front_file(tmp_path, valid("alarm", alarm_code="E102"), body="Synthetic alarm.\nCheck equipment.\n" * 20)
    children = processor.process_documents(str(tmp_path), 64, 32, 8, 4, metadata_mode="manufacturing")
    assert children
    assert len({c.metadata["id"] for c in children}) == len(children)
    for child in children:
        assert child.metadata["document_sha256"] == sha256_file(path)
        assert child.metadata["parent_content_sha256"] == sha256_content(child.metadata["parent_content"])
        assert child.metadata["child_content_sha256"] == sha256_content(child.page_content)
        assert re.fullmatch("[0-9a-f]{64}", child.metadata["id"])
        assert re.fullmatch("[0-9a-f]{64}", child.metadata["parent_id"])
        assert child.metadata["alarm_code"] == "E102"
