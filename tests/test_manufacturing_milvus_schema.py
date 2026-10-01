"""Synthetic Schema/Mapper tests. Recording clients never claim Milvus integration."""
from copy import deepcopy
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rag_qa.core.milvus_schema import (
    MANUFACTURING_SCHEMA_VERSION, manufacturing_fields, manufacturing_indexes,
    build_manufacturing_row, validate_manufacturing_document, select_collection,
    build_manufacturing_schema, build_manufacturing_indexes,
    validate_manufacturing_schema, ensure_manufacturing_collection,
    ManufacturingRowValidationError, ManufacturingSchemaMismatchError,
)
from rag_qa.ingestion.fingerprints import sha256_content, build_parent_id, build_child_id
from rag_qa.schemas.manufacturing_metadata import ManufacturingDocumentMetadata, MaintenanceCycle, KnowledgeType


def child(**business):
    body, parent = "Synthetic child", "Synthetic parent: Synthetic child"
    data = dict(document_id="SYNTHETIC-001", document_version="1.10", title="Synthetic fixture", knowledge_type="manual")
    data.update(business)
    metadata = ManufacturingDocumentMetadata(**data).to_metadata()
    parent_hash, child_hash = sha256_content(parent), sha256_content(body)
    parent_id = build_parent_id(metadata["document_id"], parent_hash)
    identifier = build_child_id(metadata["document_id"], parent_id, child_hash)
    metadata.update(id=identifier, child_id=identifier, parent_id=parent_id, parent_content=parent,
                    document_sha256=hashlib.sha256(b"synthetic source bytes").hexdigest(),
                    parent_content_sha256=parent_hash, child_content_sha256=child_hash,
                    source_file="synthetic/manual.txt", metadata_source="front_matter",
                    source="synthetic", timestamp="2026-10-02T00:00:00")
    return SimpleNamespace(page_content=body, metadata=metadata)


def row(document=None, dense=None, sparse=None):
    return build_manufacturing_row(document or child(), [1, 0, 0, 0] if dense is None else dense,
                                   {0: 1} if sparse is None else sparse, 4)


def description(dim=4):
    fields = []
    for spec in manufacturing_fields(dim):
        fields.append(dict(name=spec.name, type=spec.datatype, nullable=spec.nullable,
                           is_primary=spec.is_primary, auto_id=False,
                           params={k: v for k, v in {"max_length": spec.max_length, "dim": spec.dim}.items() if v is not None}))
    return dict(auto_id=False, enable_dynamic_field=False, fields=fields)


def test_field_contract_and_dimension():
    specs = {f.name: f for f in manufacturing_fields(7)}
    assert len(specs) == 32
    assert specs["id"].is_primary and specs["id"].max_length == 64
    assert specs["dense_vector"].datatype == "FLOAT_VECTOR" and specs["dense_vector"].dim == 7
    assert specs["sparse_vector"].datatype == "SPARSE_FLOAT_VECTOR"
    assert specs["maintenance_cycle_value"].datatype == "DOUBLE"
    assert "maintenance_cycle" not in specs
    assert {"document_id", "document_version", "schema_version", "source_file", "source", "timestamp",
            "metadata_source", "document_sha256", "parent_content_sha256", "child_content_sha256"} <= specs.keys()
    assert set(ManufacturingDocumentMetadata.model_fields) - {"maintenance_cycle"} <= specs.keys()
    assert specs["text"].max_length == specs["parent_content"].max_length == 65535
    assert specs["source_file"].max_length == 4096


@pytest.mark.parametrize("dim", [0, -1, True, "1024", 1.5])
def test_invalid_dimension(dim):
    with pytest.raises(ValueError, match="dense_dim"):
        manufacturing_fields(dim)


def test_index_baseline():
    dense, sparse = manufacturing_indexes()
    assert (dense["index_type"], dense["metric_type"], dense["params"]) == ("IVF_FLAT", "IP", {"nlist": 128})
    assert (sparse["index_type"], sparse["metric_type"], sparse["params"]) == ("SPARSE_INVERTED_INDEX", "IP", {"drop_ratio_build": 0.2})


def test_valid_row_preserves_identity_metadata_and_nulls():
    document = child()
    mapped = row(document)
    assert set(mapped) == {f.name for f in manufacturing_fields(4)}
    assert mapped["id"] == mapped["child_id"] == document.metadata["id"]
    assert mapped["id"] != hashlib.md5(document.metadata["id"].encode()).hexdigest()
    assert mapped["document_version"] == "1.10" and mapped["knowledge_type"] == "manual"
    assert mapped["schema_version"] == MANUFACTURING_SCHEMA_VERSION
    for spec in manufacturing_fields(4):
        if spec.nullable and spec.name not in {"source", "timestamp"}:
            assert mapped[spec.name] is None
    for field in ("document_sha256", "parent_content_sha256", "child_content_sha256", "parent_id", "parent_content"):
        assert mapped[field] == document.metadata[field]
    json.dumps(mapped)


@pytest.mark.parametrize("cycle", [dict(value=500, unit="hour"), dict(trigger="condition_based")])
def test_maintenance_flatten(cycle):
    mapped = row(child(knowledge_type="maintenance", maintenance_cycle=cycle))
    assert mapped["maintenance_cycle_value"] == cycle.get("value")
    assert mapped["maintenance_cycle_unit"] == cycle.get("unit")
    assert mapped["maintenance_cycle_trigger"] == cycle.get("trigger")
    assert "maintenance_cycle" not in mapped


def test_plain_object_serialization():
    document = child(knowledge_type="maintenance", maintenance_cycle=dict(value=500, unit="hour"), effective_date="2026-01-01")
    document.metadata["knowledge_type"] = KnowledgeType.MAINTENANCE
    document.metadata["maintenance_cycle"] = MaintenanceCycle(value=500, unit="hour")
    document.metadata["source_file"] = Path("synthetic/manual.txt")
    document.metadata["timestamp"] = datetime(2026, 10, 2)
    mapped = row(document)
    assert type(mapped["knowledge_type"]) is str
    assert type(mapped["source_file"]) is str and type(mapped["timestamp"]) is str
    assert mapped["effective_date"] == "2026-01-01"
    assert mapped["maintenance_cycle_value"] == 500
    json.dumps(mapped)


@pytest.mark.parametrize("field", ["id", "child_id", "parent_id", "document_sha256", "parent_content_sha256",
                                     "child_content_sha256", "document_id", "document_version", "title",
                                     "knowledge_type", "parent_content", "source_file", "metadata_source"])
def test_required_metadata_fails(field):
    document = child()
    del document.metadata[field]
    with pytest.raises(ManufacturingRowValidationError, match=field):
        row(document)


@pytest.mark.parametrize("field", ["id", "child_id", "parent_id", "document_sha256", "parent_content_sha256", "child_content_sha256"])
@pytest.mark.parametrize("value", ["A" * 64, "a" * 63, "g" * 64, None])
def test_invalid_hash_or_id(field, value):
    document = child()
    document.metadata[field] = value
    with pytest.raises(ManufacturingRowValidationError, match=field):
        row(document)


@pytest.mark.parametrize("field,value", [
    ("child_id", "a" * 64), ("document_version", 1.10), ("knowledge_type", "alarms"),
    ("metadata_source", "guessed"), ("metadata_source", {}), ("schema_version", "manufacturing_v2"),
    ("source", 123), ("effective_date", "invalid"),
])
def test_bad_metadata(field, value):
    document = child()
    document.metadata[field] = value
    with pytest.raises(ManufacturingRowValidationError):
        row(document)


def test_unknown_metadata_not_silently_dropped():
    document = child()
    document.metadata["equipement_model"] = "typo"
    with pytest.raises(ManufacturingRowValidationError, match="equipement_model"):
        row(document)


def test_varchar_utf8_limit_no_truncation_or_body_disclosure():
    document = child()
    document.metadata["title"] = "秘" * 400
    with pytest.raises(ManufacturingRowValidationError) as caught:
        row(document)
    assert "title" in str(caught.value) and "UTF-8" in str(caught.value)
    assert "秘" not in str(caught.value) and document.page_content not in str(caught.value)


@pytest.mark.parametrize("dense", [[], [1, 2], [1, 0, 0, float("nan")], [1, 0, 0, True], [1, 0, 0, "0"]])
def test_invalid_dense(dense):
    with pytest.raises(ManufacturingRowValidationError, match="dense_vector"):
        row(dense=dense)


@pytest.mark.parametrize("sparse", [{}, {-1: 1}, {2**32: 1}, {"0": 1}, {0: float("inf")}, {True: 1}])
def test_invalid_sparse(sparse):
    with pytest.raises(ManufacturingRowValidationError, match="sparse_vector"):
        row(sparse=sparse)


def test_collection_isolation():
    assert select_collection("legacy", None, "edurag", "manufacturing_rag_v1") == "edurag"
    assert select_collection("manufacturing", None, "edurag", "manufacturing_rag_v1") == "manufacturing_rag_v1"
    assert select_collection("manufacturing", "site_docs_v1", "edurag", "manufacturing_rag_v1") == "site_docs_v1"


@pytest.mark.parametrize("mode,target,legacy,manufacturing", [
    ("manufacturing", None, "same", "same"), ("manufacturing", "edurag", "old", "new_v1"),
    ("manufacturing", "old", "old", "new_v1"), ("legacy", "new_v1", "old", "new_v1"),
    ("guess", None, "old", "new_v1"), ("manufacturing", " ", "old", "new_v1"),
])
def test_collection_collision_or_invalid_mode(mode, target, legacy, manufacturing):
    with pytest.raises(ValueError):
        select_collection(mode, target, legacy, manufacturing)


def test_config_priority_and_legacy_default(tmp_path, monkeypatch):
    from base.config import Config
    monkeypatch.delenv("MILVUS_COLLECTION_NAME", raising=False)
    monkeypatch.delenv("MILVUS_MANUFACTURING_COLLECTION_NAME", raising=False)
    assert Config(str(tmp_path / "missing.ini")).MILVUS_COLLECTION_NAME == "edurag"
    assert Config(str(tmp_path / "missing.ini")).MILVUS_MANUFACTURING_COLLECTION_NAME == "manufacturing_rag_v1"
    path = tmp_path / "config.ini"
    path.write_text("[milvus]\nmanufacturing_collection_name = file_v1\n", encoding="utf-8")
    assert Config(str(path)).MILVUS_MANUFACTURING_COLLECTION_NAME == "file_v1"
    monkeypatch.setenv("MILVUS_MANUFACTURING_COLLECTION_NAME", "env_v1")
    assert Config(str(path)).MILVUS_MANUFACTURING_COLLECTION_NAME == "env_v1"


def test_matching_schema_and_numeric_sdk_types():
    data = description()
    codes = {"DOUBLE": 11, "VARCHAR": 21, "FLOAT_VECTOR": 101, "SPARSE_FLOAT_VECTOR": 104}
    for field in data["fields"]:
        field["type"] = codes[field["type"]]
    validate_manufacturing_schema(data, "synthetic_v1", 4)


@pytest.mark.parametrize("change", ["missing", "extra", "pk", "dimension", "type", "dynamic", "auto_id", "nullable", "length", "default"])
def test_schema_mismatch(change):
    data = description()
    fields = {f["name"]: f for f in data["fields"]}
    if change == "missing": data["fields"].pop()
    elif change == "extra": data["fields"].append(dict(name="extra", type="VARCHAR"))
    elif change == "pk": fields["id"]["is_primary"] = False
    elif change == "dimension": fields["dense_vector"]["params"]["dim"] = 1024
    elif change == "type": fields["document_version"]["type"] = "DOUBLE"
    elif change == "dynamic": data["enable_dynamic_field"] = True
    elif change == "auto_id": data["auto_id"] = True
    elif change == "nullable": fields["equipment_model"]["nullable"] = False
    elif change == "length": fields["id"]["params"]["max_length"] = 100
    elif change == "default": fields["equipment_model"]["default_value"] = "N/A"
    with pytest.raises(ManufacturingSchemaMismatchError) as caught:
        validate_manufacturing_schema(data, "synthetic_v1", 4)
    assert "synthetic_v1" in str(caught.value) and "expected=" in str(caught.value) and "actual=" in str(caught.value)


class RecordingSchema:
    def __init__(self, **options):
        self.data = dict(options, fields=[])

    def add_field(self, field_name, datatype, **options):
        self.data["fields"].append(dict(name=field_name, type=datatype,
                                       params={key: options[key] for key in ("dim", "max_length") if key in options},
                                       **{key: value for key, value in options.items() if key not in {"dim", "max_length"}}))

    def to_dict(self):
        return deepcopy(self.data)


class RecordingIndexes:
    def __init__(self): self.specs = []
    def add_index(self, **spec): self.specs.append(spec)


class RecordingClient:
    """Control flow only; no networking or persistent Milvus storage."""
    def __init__(self, exists=True, **kwargs):
        self.exists = exists
        self.schema = description()
        self.indexes = {spec["index_name"]: deepcopy(spec) for spec in manufacturing_indexes()}
        self.events, self.upserts = [], []

    def has_collection(self, name): return self.exists
    def create_schema(self, **options): return RecordingSchema(**options)
    def prepare_index_params(self): return RecordingIndexes()
    def create_collection(self, collection_name, schema, index_params):
        self.events.append("create")
        self.schema = schema.to_dict()
        self.indexes = {spec["index_name"]: spec for spec in index_params.specs}
        self.exists = True
    def describe_collection(self, collection_name):
        self.events.append("inspect")
        return self.schema
    def list_indexes(self, collection_name): return list(self.indexes)
    def describe_index(self, collection_name, index_name): return self.indexes[index_name]
    def load_collection(self, collection_name): self.events.append("load")
    def upsert(self, collection_name, data): self.upserts.append((collection_name, deepcopy(data)))
    def drop_collection(self, *args, **kwargs): pytest.fail("automatic collection deletion is forbidden")


def test_existing_schema_checked_before_load():
    client = RecordingClient()
    ensure_manufacturing_collection(client, "synthetic_v1", 4)
    assert client.events == ["inspect", "load"]


def test_mismatch_never_loads_or_repairs():
    client = RecordingClient()
    client.schema["fields"].pop()
    with pytest.raises(ManufacturingSchemaMismatchError):
        ensure_manufacturing_collection(client, "synthetic_v1", 4)
    assert client.events == ["inspect"]


@pytest.mark.parametrize("change", ["missing", "field_name", "index_type", "metric_type", "nlist", "drop_ratio_build"])
def test_index_mismatch_never_loads(change):
    client = RecordingClient()
    if change == "missing": del client.indexes["dense_index"]
    elif change in {"nlist", "drop_ratio_build"}:
        name = "dense_index" if change == "nlist" else "sparse_index"
        client.indexes[name]["params"][change] = 999
    else: client.indexes["dense_index"][change] = "wrong"
    with pytest.raises(ManufacturingSchemaMismatchError):
        ensure_manufacturing_collection(client, "synthetic_v1", 4)
    assert "load" not in client.events and "create" not in client.events


@pytest.fixture
def vector_store_unit(monkeypatch):
    # Isolate heavy imports while executing the repository's real VectorStore methods.
    types = SimpleNamespace(VARCHAR="VARCHAR", DOUBLE="DOUBLE", FLOAT_VECTOR="FLOAT_VECTOR", SPARSE_FLOAT_VECTOR="SPARSE_FLOAT_VECTOR")
    modules = {
        "milvus_model": {}, "milvus_model.hybrid": {"BGEM3EmbeddingFunction": lambda **k: SimpleNamespace(dim={"dense": 4})},
        "sentence_transformers": {"CrossEncoder": lambda *a, **k: object()},
        "langchain_core": {}, "langchain_core.documents": {"Document": SimpleNamespace},
        "pymilvus": {"MilvusClient": RecordingClient, "DataType": types, "AnnSearchRequest": object, "WeightedRanker": object},
    }
    for name, symbols in modules.items():
        module = ModuleType(name); module.__dict__.update(symbols)
        monkeypatch.setitem(sys.modules, name, module)
    spec = importlib.util.spec_from_file_location("_stage3_vector_store_unit", ROOT / "rag_qa/core/vector_store.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module.config, "MILVUS_COLLECTION_NAME", "edurag")
    monkeypatch.setattr(module.config, "MILVUS_MANUFACTURING_COLLECTION_NAME", "manufacturing_rag_v1")
    return module


def test_vector_store_mode_and_early_collision(vector_store_unit, monkeypatch):
    legacy = vector_store_unit.VectorStore()
    assert legacy.schema_mode == "legacy" and legacy.collection_name == "edurag"
    assert legacy.client.events == ["load"]  # preserve existing Legacy behavior
    store = vector_store_unit.VectorStore(schema_mode="manufacturing")
    assert store.collection_name == "manufacturing_rag_v1" and store.dense_dim == 4
    monkeypatch.setattr(vector_store_unit, "CrossEncoder", lambda *a, **k: pytest.fail("collision reached model loading"))
    with pytest.raises(ValueError, match="Legacy"):
        vector_store_unit.VectorStore(collection_name="edurag", schema_mode="manufacturing")


def test_new_collection_strict_builder_and_inspection(vector_store_unit):
    client = RecordingClient(exists=False)
    ensure_manufacturing_collection(client, "synthetic_v1", 7)
    assert client.events == ["create", "inspect", "load"]
    assert client.schema["auto_id"] is False and client.schema["enable_dynamic_field"] is False
    fields = {f["name"]: f for f in client.schema["fields"]}
    assert fields["dense_vector"]["params"]["dim"] == 7 and fields["id"]["is_primary"]
    assert fields["equipment_model"]["nullable"] is True


def test_legacy_schema_and_pk_unchanged(vector_store_unit):
    store = vector_store_unit.VectorStore.__new__(vector_store_unit.VectorStore)
    store.schema_mode, store.collection_name, store.dense_dim = "legacy", "edurag", 4
    store.client = RecordingClient(exists=False)
    store._create_or_load_collection()
    assert store.client.schema["enable_dynamic_field"] is True
    fields = {f["name"]: f for f in store.client.schema["fields"]}
    assert fields["id"]["params"]["max_length"] == 100
    assert "document_id" not in fields and len(fields) == 9
    doc = SimpleNamespace(page_content="Synthetic legacy", metadata=dict(id="doc_0_parent_0_child_0", parent_id="doc_0_parent_0", parent_content="parent"))
    store.embedding_function = lambda texts: dict(dense=[[1, 0, 0, 0]], sparse=None)
    store.get_sparse_dict = lambda embeddings, i: {0: 1}
    store.add_documents([doc])
    name, rows = store.client.upserts[0]
    assert name == "edurag"
    assert rows[0]["id"] == hashlib.md5(doc.metadata["id"].encode()).hexdigest()
    assert rows[0]["child_id"] == doc.metadata["id"]
    assert "document_sha256" not in rows[0]


def test_manufacturing_batch_preflight_and_stable_upsert(vector_store_unit):
    store = vector_store_unit.VectorStore(schema_mode="manufacturing")
    calls = []
    store.embedding_function = lambda texts: calls.append(texts) or dict(dense=[[1, 0, 0, 0]] * len(texts), sparse=None)
    store.get_sparse_dict = lambda embeddings, i: {0: 1}
    invalid = child(); del invalid.metadata["document_sha256"]
    with pytest.raises(ManufacturingRowValidationError): store.add_documents([child(), invalid])
    assert not calls and not store.client.upserts
    first = child()
    store.add_documents([first]); second = child(document_version="2.0"); store.add_documents([second])
    assert store.client.upserts[0][1][0]["id"] == store.client.upserts[1][1][0]["id"] == first.metadata["id"]
    assert store.client.upserts[1][1][0]["document_version"] == "2.0"
    calls.clear(); store.add_documents([]); assert not calls


def test_manufacturing_sparse_uses_requested_row(vector_store_unit):
    class SparseRows:
        def tocsr(self): return self
        def __getitem__(self, key):
            indices, columns = key
            return SimpleNamespace(indices=[0], data=[float(indices[0] + 1)])
    store = vector_store_unit.VectorStore(schema_mode="manufacturing")
    assert store.get_sparse_dict({"sparse": SparseRows()}, 0) == {0: 1.0}
    assert store.get_sparse_dict({"sparse": SparseRows()}, 1) == {0: 2.0}


def test_real_sdk_schema_serialization_without_server():
    sdk = pytest.importorskip("pymilvus", reason="SDK not installed; pure contract tests still run")
    schema = build_manufacturing_schema(sdk.MilvusClient, 7)
    schema.verify()
    validate_manufacturing_schema(schema.to_dict(), "offline_sdk_v1", 7)
    assert schema.auto_id is False
    indexes = list(build_manufacturing_indexes(sdk.MilvusClient))
    assert indexes == list(manufacturing_indexes())


def test_real_sdk_upsert_serializes_native_nulls_without_server():
    sdk = pytest.importorskip("pymilvus")
    from pymilvus.client.prepare import Prepare
    fields = build_manufacturing_schema(sdk.MilvusClient, 4).to_dict()["fields"]
    request = Prepare.row_upsert_param("offline_sdk_v1", [row()], "", fields, enable_dynamic=False)
    data = {field.field_name: field for field in request.fields_data}
    assert request.num_rows == 1 and len(data) == 32
    assert list(data["equipment_model"].valid_data) == [False]
    assert list(data["maintenance_cycle_value"].valid_data) == [False]
    assert list(data["id"].scalars.string_data.data) == [child().metadata["id"]]


def test_live_milvus_synthetic_collection(tmp_path):
    if os.getenv("STAGE3_LIVE_MILVUS") != "1":
        pytest.skip("Requires STAGE3_LIVE_MILVUS=1 and an explicitly prepared Milvus service; no models downloaded")
    sdk = pytest.importorskip("pymilvus")
    client = sdk.MilvusClient(uri=os.getenv("STAGE3_MILVUS_URI", "http://localhost:19530"),
                              db_name=os.getenv("STAGE3_MILVUS_DATABASE", "default"), timeout=10)
    name = "stage3_test_" + uuid4().hex + "_v1"
    assert name.startswith("stage3_test_") and name not in {"edurag", "manufacturing_rag_v1"}
    if client.has_collection(name): pytest.fail("refuse to use an existing test collection")
    created = False
    try:
        client.create_collection(collection_name=name, schema=build_manufacturing_schema(client, 4),
                                 index_params=build_manufacturing_indexes(client))
        created = True
        ensure_manufacturing_collection(client, name, 4)
        first = row(child(effective_date="2026-01-01"))
        client.upsert(collection_name=name, data=[first])
        updated = dict(first, document_version="2.0")
        client.upsert(collection_name=name, data=[updated])
        columns = [f.name for f in manufacturing_fields(4) if f.name not in {"dense_vector", "sparse_vector"}]
        rows = client.get(collection_name=name, ids=[first["id"]], output_fields=columns, consistency_level="Strong")
        assert len(rows) == 1
        for column in columns: assert rows[0][column] == updated[column]
    finally:
        if created:
            # Only the randomly named collection successfully created by THIS test.
            client.drop_collection(collection_name=name)
        client.close()
