"""Stage 1 unit tests use synthetic data, no models/databases/runtime services."""
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest
import yaml
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rag_qa.schemas.manufacturing_metadata import ManufacturingDocumentMetadata, MaintenanceCycle
from rag_qa.ingestion.metadata_loader import (
    resolve_metadata, load_with_metadata, MissingMetadataError,
    MetadataSourceConflictError, InvalidYamlMetadataError,
    InvalidManufacturingMetadataError, MetadataMergeConflictError,
)


def valid(kind="manual", **extra):
    return dict(document_id="Synthetic-001", document_version="1.10",
                title="Synthetic test fixture", knowledge_type=kind, **extra)


def front_file(tmp_path, data=None, suffix=".txt", body="Synthetic body.\n"):
    path = tmp_path / ("example" + suffix)
    path.write_text("---\n" + yaml.safe_dump(data or valid()) + "---\n" + body, encoding="utf-8")
    return path


@pytest.mark.parametrize("kind,extra", [
    ("manual", {}), ("alarm", {"alarm_code": "E102"}),
    ("fault", {"fault_symptom": "Synthetic vibration"}),
    ("maintenance", {"maintenance_cycle": {"value": 500, "unit": "hour"}}),
    ("parts", {"part_number": "BRG-6205-ZZ"}), ("parameter", {}), ("case", {}),
])
def test_legal_types(kind, extra):
    metadata = ManufacturingDocumentMetadata(**valid(kind, **extra)).to_metadata()
    assert metadata["knowledge_type"] == kind
    assert metadata["equipment_model"] is None
    assert metadata["language"] == "zh-CN"
    json.dumps(metadata)


@pytest.mark.parametrize("field", ["document_id", "document_version", "title", "knowledge_type"])
@pytest.mark.parametrize("missing", [True, False])
def test_required_fields(field, missing):
    data = valid()
    if missing:
        del data[field]
    else:
        data[field] = " \t "
    with pytest.raises(ValidationError):
        ManufacturingDocumentMetadata(**data)


def test_trim_preserves_business_identity_and_serialization():
    data = valid(" alarm ", alarm_code=" 001-a_B ", equipment_model=" Mz-001 ",
                 equipment_type=" CNC ", manufacturer=" DemoMachinery ",
                 fault_type=" ", effective_date="2026-01-01", language=" en-US ")
    data["document_id"] = " Mixed-001 "
    data["document_version"] = " 1.10 "
    metadata = ManufacturingDocumentMetadata(**data).to_metadata()
    assert metadata["document_id"] == "Mixed-001"
    assert metadata["document_version"] == "1.10"
    assert metadata["alarm_code"] == "001-a_B"
    assert metadata["equipment_model"] == "Mz-001"
    assert metadata["fault_type"] is None
    assert metadata["effective_date"] == "2026-01-01"
    assert metadata["language"] == "en-US"


@pytest.mark.parametrize("field,value", [
    ("document_version", 1.10), ("document_id", 10), ("title", 10),
    ("alarm_code", 7), ("part_number", 7), ("equipment_model", 1),
    ("knowledge_type", "alarms"), ("knowledge_type", "ALARM"),
    ("effective_date", "2026-02-30"), ("effective_date", 0), ("language", " "),
])
def test_bad_types_and_values(field, value):
    data = valid()
    data[field] = value
    with pytest.raises(ValidationError):
        ManufacturingDocumentMetadata(**data)


@pytest.mark.parametrize("kind", ["alarm", "fault", "maintenance", "parts"])
def test_conditional_requirements(kind):
    with pytest.raises(ValidationError):
        ManufacturingDocumentMetadata(**valid(kind))


@pytest.mark.parametrize("kind,extra", [
    ("fault", {"fault_type": "bearing"}),
    ("maintenance", {"maintenance_type": "lubrication"}),
    ("maintenance", {"maintenance_cycle": {"trigger": "condition_based"}}),
])
def test_alternative_requirements(kind, extra):
    ManufacturingDocumentMetadata(**valid(kind, **extra))


@pytest.mark.parametrize("unit", ["hour", "day", "week", "month", "year", "cycle"])
def test_cycle_units(unit):
    assert MaintenanceCycle(value=500, unit=unit).model_dump(mode="json")["value"] == 500


def test_cycle_trigger():
    assert MaintenanceCycle(trigger=" condition_based ").trigger == "condition_based"


@pytest.mark.parametrize("cycle", [
    {}, {"value": 500}, {"unit": "hour"}, {"value": 0, "unit": "hour"},
    {"value": -1, "unit": "day"}, {"value": 1, "unit": "minute"},
    {"trigger": " "}, {"value": "500", "unit": "hour"},
    {"value": True, "unit": "hour"}, {"value": float("inf"), "unit": "hour"},
    {"value": 500, "trigger": "condition_based"}, {"trigger": "condition_based", "extra": 1},
])
def test_invalid_cycle(cycle):
    with pytest.raises(ValidationError):
        MaintenanceCycle(**cycle)


@pytest.mark.parametrize("field", ["equipement_model", "document_sha256", "parent_content_sha256", "child_content_sha256",
                                     "parent_id", "child_id", "ingestion_version", "vector_id",
                                     "created_at", "schema_version", "source", "file_path", "timestamp", "metadata_source"])
def test_unknown_or_system_fields(field):
    with pytest.raises(ValidationError):
        ManufacturingDocumentMetadata(**valid(**{field: "spoof"}))


@pytest.mark.parametrize("suffix", [".txt", ".md"])
def test_front_matter_and_body(tmp_path, suffix):
    path = front_file(tmp_path, valid("alarm", alarm_code="E102"), suffix)
    resolved = resolve_metadata(path)
    assert resolved.metadata_source == "front_matter"
    assert resolved.body == "Synthetic body.\n"
    assert resolved.business_metadata["alarm_code"] == "E102"


def test_bom_crlf_front_matter(tmp_path):
    path = tmp_path / "bom.txt"
    path.write_bytes(("\ufeff---\r\n" + yaml.safe_dump(valid()).replace("\n", "\r\n") +
                      "---\r\nSynthetic body.\r\n").encode("utf-8"))
    assert resolve_metadata(path).body == "Synthetic body.\n"


@pytest.mark.parametrize("suffix", [".txt", ".md", ".pdf", ".docx", ".pptx", ".png", ".jpg"])
def test_full_filename_sidecar(tmp_path, suffix):
    path = tmp_path / ("example" + suffix)
    path.write_bytes(b"synthetic document placeholder")
    Path(str(path) + ".yaml").write_text(yaml.safe_dump(valid(effective_date="2026-01-01")), encoding="utf-8")
    resolved = resolve_metadata(path)
    assert resolved.metadata_source == "sidecar" and resolved.body is None
    assert resolved.business_metadata["effective_date"] == "2026-01-01"


def test_wrong_sidecar_name_and_missing(tmp_path):
    path = tmp_path / "manual.pdf"
    path.write_bytes(b"placeholder")
    path.with_suffix(".yaml").write_text(yaml.safe_dump(valid()), encoding="utf-8")
    with pytest.raises(MissingMetadataError, match="manual.pdf"):
        resolve_metadata(path)


@pytest.mark.parametrize("suffix", [".txt", ".md"])
def test_source_conflict(tmp_path, suffix):
    path = front_file(tmp_path, suffix=suffix)
    Path(str(path) + ".yaml").write_text("", encoding="utf-8")
    with pytest.raises(MetadataSourceConflictError):
        resolve_metadata(path)


@pytest.mark.parametrize("text", ["", "null", "{}", "- document_id\n- title", "hello",
                                  "title: [", "!!python/object/apply:os.system ['echo unsafe']",
                                  "document_id: first\ndocument_id: second"])
def test_bad_yaml(tmp_path, text):
    path = tmp_path / "example.pdf"
    path.write_bytes(b"placeholder")
    Path(str(path) + ".yaml").write_text(text, encoding="utf-8")
    with pytest.raises(InvalidYamlMetadataError):
        resolve_metadata(path)


@pytest.mark.parametrize("text", ["---\n---\nbody", "---\ntitle: x\nbody"])
def test_empty_or_unterminated_front_matter(tmp_path, text):
    path = tmp_path / "example.txt"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(InvalidYamlMetadataError):
        resolve_metadata(path)


def test_readable_validation_error_without_values(tmp_path):
    data = valid()
    data["document_version"] = 1.10
    data["equipement_model"] = "SENSITIVE_VALUE"
    path = front_file(tmp_path, data)
    with pytest.raises(InvalidManufacturingMetadataError) as caught:
        resolve_metadata(path)
    message = str(caught.value)
    assert str(path) in message and "front_matter" in message
    assert "document_version" in message and "equipement_model" in message
    assert "reason=" in message and "SENSITIVE_VALUE" not in message


def test_yaml_date_and_unquoted_version(tmp_path):
    path = front_file(tmp_path)
    text = path.read_text(encoding="utf-8")
    text = text.replace("document_version: '1.10'", 'document_version: "1.10"')
    text = text.replace("title:", "effective_date: 2026-01-01\ntitle:")
    path.write_text(text, encoding="utf-8")
    assert resolve_metadata(path).business_metadata["effective_date"] == "2026-01-01"
    path.write_text(text.replace('document_version: "1.10"', 'document_version: 1.10'), encoding="utf-8")
    with pytest.raises(InvalidManufacturingMetadataError):
        resolve_metadata(path)


def text_loader(path):
    """Loader test double; does not claim LangChain/OCR integration coverage."""
    return [SimpleNamespace(page_content=Path(path).read_text(encoding="utf-8"), metadata={"source": path})]


def test_adapter_attaches_metadata_and_cleans_temp_file(tmp_path):
    path = front_file(tmp_path, valid("alarm", alarm_code="E102", equipment_model="MZ-2000"))
    original = path.read_bytes()
    opened = []

    def loader(sanitized):
        opened.append(sanitized)
        return text_loader(sanitized)

    doc = load_with_metadata(path, loader)[0]
    assert doc.page_content == "Synthetic body.\n"
    assert doc.metadata["source"] == str(path)
    assert doc.metadata["equipment_model"] == "MZ-2000"
    assert doc.metadata["alarm_code"] == "E102"
    assert doc.metadata["source_file"] == str(path.resolve())
    assert not Path(opened[0]).exists() and path.read_bytes() == original
    json.dumps(doc.metadata)


def test_adapter_cleans_temp_on_loader_failure(tmp_path):
    path = front_file(tmp_path)
    opened = []

    def broken(sanitized):
        opened.append(sanitized)
        raise RuntimeError("loader failed")

    with pytest.raises(RuntimeError, match="loader failed"):
        load_with_metadata(path, broken)
    assert not Path(opened[0]).exists()


def test_invalid_metadata_never_calls_loader(tmp_path):
    path = front_file(tmp_path, valid("alarm"))

    def forbidden(path):
        pytest.fail("invalid metadata reached loader")

    with pytest.raises(InvalidManufacturingMetadataError):
        load_with_metadata(path, forbidden)


def test_loader_metadata_conflict(tmp_path):
    path = front_file(tmp_path)
    with pytest.raises(MetadataMergeConflictError, match="title"):
        load_with_metadata(path, lambda p: [SimpleNamespace(metadata={"title": "loader title"})])


@pytest.fixture
def processor_unit(monkeypatch):
    """Execute the real processor functions with isolated loader/import doubles.

    This covers dispatch/legacy behavior, not real LangChain propagation.
    """
    class TextLoader:
        def __init__(self, path, encoding=None):
            self.path = path

        def load(self):
            return text_loader(self.path)

    modules = {
        "rag_qa.edu_document_loaders.edu_docloader": {"OCRDOCLoader": TextLoader},
        "rag_qa.edu_document_loaders.edu_imgloader": {"OCRIMGLoader": TextLoader},
        "rag_qa.edu_document_loaders.edu_pdfloader": {"OCRPDFLoader": TextLoader},
        "rag_qa.edu_document_loaders.edu_pptloader": {"OCRPPTLoader": TextLoader},
        "rag_qa.edu_text_spliter.edu_chinese_recursive_text_splitter": {"ChineseRecursiveTextSplitter": object},
        "langchain_community": {},
        "langchain_community.document_loaders": {"TextLoader": TextLoader},
        "langchain_community.document_loaders.markdown": {"UnstructuredMarkdownLoader": TextLoader},
        "langchain_text_splitters": {"MarkdownTextSplitter": object},
    }
    for name, symbols in modules.items():
        module = ModuleType(name)
        module.__dict__.update(symbols)
        monkeypatch.setitem(sys.modules, name, module)
    spec = importlib.util.spec_from_file_location("_stage1_processor_unit", ROOT / "rag_qa/core/document_processor.py")
    processor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(processor)
    return processor


def test_processor_default_legacy_ignores_yaml(processor_unit, tmp_path):
    directory = tmp_path / "manufacturing_ai_data"
    directory.mkdir()
    path = directory / "legacy.txt"
    path.write_text("No YAML required", encoding="utf-8")
    doc = processor_unit.load_documents_from_directory(str(directory))[0]
    assert doc.page_content == "No YAML required"
    assert set(doc.metadata) == {"source", "file_path", "timestamp"}
    assert doc.metadata["source"] == "manufacturing_ai"
    assert doc.metadata["file_path"] == str(path)
    front_file(directory)  # legacy must leave front matter as body, without schema validation
    docs = processor_unit.load_documents_from_directory(str(directory))
    assert any(doc.page_content.startswith("---") for doc in docs)


def test_processor_manufacturing_requires_metadata(processor_unit, tmp_path):
    (tmp_path / "legacy.txt").write_text("body", encoding="utf-8")
    with pytest.raises(MissingMetadataError):
        processor_unit.load_documents_from_directory(str(tmp_path), metadata_mode="manufacturing")


def test_processor_explicit_manufacturing(processor_unit, tmp_path):
    front_file(tmp_path, valid("alarm", alarm_code="E102"))
    doc = processor_unit.load_documents_from_directory(str(tmp_path), metadata_mode="manufacturing")[0]
    assert doc.metadata["alarm_code"] == "E102"
    assert {"source", "file_path", "timestamp"} <= doc.metadata.keys()
    assert doc.page_content == "Synthetic body.\n"


def test_processor_unknown_mode(processor_unit, tmp_path):
    with pytest.raises(ValueError, match="metadata_mode"):
        processor_unit.load_documents_from_directory(str(tmp_path), metadata_mode="guess")


def test_real_parent_child_metadata(tmp_path):
    from test_stage0_smoke import require_modules, import_real_module
    require_modules(["langchain_core", "langchain_community", "langchain_text_splitters",
                     "docx", "pptx", "fitz", "cv2"])
    processor = import_real_module("rag_qa.core.document_processor")
    path = front_file(tmp_path, valid("alarm", alarm_code="E102", equipment_model="MZ-2000"),
                      body="Synthetic alarm.\nCheck equipment.\n" * 20)
    doc = processor.load_documents_from_directory(str(tmp_path), metadata_mode="manufacturing")[0]
    parents = processor.ChineseRecursiveTextSplitter(chunk_size=64, chunk_overlap=8).split_documents([doc])
    assert parents and all(p.metadata["equipment_model"] == "MZ-2000" for p in parents)
    children = processor.process_documents(str(tmp_path), 64, 32, 8, 4, metadata_mode="manufacturing")
    assert children
    for child in children:
        assert child.metadata["equipment_model"] == "MZ-2000"
        assert child.metadata["alarm_code"] == "E102"
        assert len(child.metadata["id"]) == 64
        assert len(child.metadata["parent_id"]) == 64
        assert child.metadata["child_id"] == child.metadata["id"]
        assert "document_id:" not in child.page_content
        assert child.metadata["file_path"] == str(path)
