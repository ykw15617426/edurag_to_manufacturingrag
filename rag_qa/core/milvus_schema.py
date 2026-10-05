"""Strict Stage 3 storage contract; no models, connections or migration state."""
from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from numbers import Integral, Real
from pathlib import Path
import re

from pydantic import ValidationError

from rag_qa.schemas.manufacturing_metadata import ManufacturingDocumentMetadata

MANUFACTURING_SCHEMA_VERSION = "manufacturing_v1"
HASH_LEN = ID_LEN = 64
DOCUMENT_ID_MAX = 256
DOCUMENT_VERSION_MAX = 64
TEXT_MAX = 65535
TITLE_MAX = 1024
MODEL_MAX = 256
PATH_MAX = 4096
LABEL_MAX = 256
SHORT_LABEL_MAX = 128
LANGUAGE_MAX = 32
FAULT_SYMPTOM_MAX = 8192
UNIT_MAX = 16
DATE_MAX = 10
HASH_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class FieldSpec:
    name: str
    datatype: str = "VARCHAR"
    max_length: int | None = None
    nullable: bool = False
    is_primary: bool = False
    dim: int | None = None


def manufacturing_fields(dense_dim):
    if type(dense_dim) is not int or dense_dim <= 0:
        raise ValueError("dense_dim must be a positive integer from the embedding specification")
    return (
        FieldSpec("id", max_length=ID_LEN, is_primary=True),
        FieldSpec("text", max_length=TEXT_MAX),
        FieldSpec("dense_vector", "FLOAT_VECTOR", dim=dense_dim),
        FieldSpec("sparse_vector", "SPARSE_FLOAT_VECTOR"),
        FieldSpec("schema_version", max_length=ID_LEN),
        FieldSpec("child_id", max_length=ID_LEN),
        FieldSpec("parent_id", max_length=ID_LEN),
        FieldSpec("parent_content", max_length=TEXT_MAX),
        FieldSpec("document_id", max_length=DOCUMENT_ID_MAX),
        FieldSpec("document_version", max_length=DOCUMENT_VERSION_MAX),
        *(FieldSpec(name, max_length=HASH_LEN) for name in (
            "document_sha256", "parent_content_sha256", "child_content_sha256")),
        FieldSpec("title", max_length=TITLE_MAX),
        FieldSpec("knowledge_type", max_length=LANGUAGE_MAX),
        FieldSpec("equipment_type", max_length=SHORT_LABEL_MAX, nullable=True),
        FieldSpec("equipment_model", max_length=MODEL_MAX, nullable=True),
        FieldSpec("manufacturer", max_length=LABEL_MAX, nullable=True),
        FieldSpec("alarm_code", max_length=SHORT_LABEL_MAX, nullable=True),
        FieldSpec("fault_type", max_length=LABEL_MAX, nullable=True),
        FieldSpec("fault_symptom", max_length=FAULT_SYMPTOM_MAX, nullable=True),
        FieldSpec("maintenance_type", max_length=LABEL_MAX, nullable=True),
        FieldSpec("maintenance_cycle_value", "DOUBLE", nullable=True),
        FieldSpec("maintenance_cycle_unit", max_length=UNIT_MAX, nullable=True),
        FieldSpec("maintenance_cycle_trigger", max_length=LABEL_MAX, nullable=True),
        FieldSpec("part_number", max_length=LABEL_MAX, nullable=True),
        FieldSpec("effective_date", max_length=DATE_MAX, nullable=True),
        FieldSpec("language", max_length=LANGUAGE_MAX),
        FieldSpec("source_file", max_length=PATH_MAX),
        FieldSpec("metadata_source", max_length=LANGUAGE_MAX),
        FieldSpec("source", max_length=LABEL_MAX, nullable=True),
        FieldSpec("timestamp", max_length=ID_LEN, nullable=True),
    )


def manufacturing_indexes():
    return (
        dict(field_name="dense_vector", index_name="dense_index", index_type="IVF_FLAT",
             metric_type="IP", params={"nlist": 128}),
        dict(field_name="sparse_vector", index_name="sparse_index", index_type="SPARSE_INVERTED_INDEX",
             metric_type="IP", params={"drop_ratio_build": 0.2}),
    )


class ManufacturingRowValidationError(ValueError):
    def __init__(self, child_id, field, reason):
        self.child_id = child_id if isinstance(child_id, str) and HASH_PATTERN.fullmatch(child_id) else "<invalid>"
        self.field, self.reason = field, reason
        super().__init__(f"child_id={self.child_id}; field={field}; reason={reason}")


class ManufacturingSchemaMismatchError(ValueError):
    def __init__(self, collection_name, field, expected, actual):
        self.collection_name, self.field = collection_name, field
        self.expected, self.actual = expected, actual
        super().__init__(f"collection={collection_name}; field={field}; expected={expected!r}; actual={actual!r}; "
                         "migration required; collection was not repaired or dropped")


def select_collection(schema_mode, collection_name, legacy_name, manufacturing_name):
    if schema_mode not in {"legacy", "manufacturing"}:
        raise ValueError("schema_mode must be legacy or manufacturing")
    if legacy_name == manufacturing_name:
        raise ValueError("Legacy and Manufacturing collection names must differ")
    selected = collection_name if collection_name is not None else (
        legacy_name if schema_mode == "legacy" else manufacturing_name)
    if not isinstance(selected, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,254}", selected):
        raise ValueError("invalid collection name")
    if schema_mode == "manufacturing" and selected in {legacy_name, "edurag"}:
        raise ValueError("Manufacturing cannot use the Legacy collection")
    if schema_mode == "legacy" and selected == manufacturing_name:
        raise ValueError("Legacy cannot use the configured Manufacturing collection")
    return selected


def validate_manufacturing_document(document):
    """Preflight before embedding; unknown metadata cannot disappear silently."""
    metadata = document.metadata
    child_id = metadata.get("id")

    def fail(field, reason):
        raise ManufacturingRowValidationError(child_id, field, reason)

    allowed = set(ManufacturingDocumentMetadata.model_fields) | {
        "id", "child_id", "parent_id", "parent_content", "document_sha256",
        "parent_content_sha256", "child_content_sha256", "source_file", "metadata_source",
        "source", "timestamp", "file_path", "schema_version",
    }
    unknown = metadata.keys() - allowed
    if unknown:
        fail(",".join(sorted(map(str, unknown))), "unknown metadata; explicit storage mapping required")

    for field in ("id", "child_id", "parent_id", "document_sha256", "parent_content_sha256", "child_content_sha256"):
        value = metadata.get(field)
        if not isinstance(value, str) or not HASH_PATTERN.fullmatch(value):
            fail(field, "required lowercase 64-char SHA256 hex")
    if metadata["id"] != metadata["child_id"]:
        fail("child_id", "must equal id without rehashing")
    if "schema_version" in metadata and metadata["schema_version"] != MANUFACTURING_SCHEMA_VERSION:
        fail("schema_version", "reserved system schema version")
    try:
        business = ManufacturingDocumentMetadata.model_validate({
            name: metadata[name] for name in ManufacturingDocumentMetadata.model_fields if name in metadata
        }).to_metadata()
    except ValidationError as exc:
        error = exc.errors(include_input=False, include_context=False, include_url=False)[0]
        fail(".".join(map(str, error["loc"])) or "<business>", error["msg"])
    cycle = business.pop("maintenance_cycle")
    row = dict(business, id=metadata["id"], child_id=metadata["child_id"], parent_id=metadata["parent_id"],
               text=document.page_content, parent_content=metadata.get("parent_content"),
               schema_version=MANUFACTURING_SCHEMA_VERSION,
               document_sha256=metadata["document_sha256"],
               parent_content_sha256=metadata["parent_content_sha256"],
               child_content_sha256=metadata["child_content_sha256"],
               maintenance_cycle_value=cycle["value"] if cycle else None,
               maintenance_cycle_unit=cycle["unit"] if cycle else None,
               maintenance_cycle_trigger=cycle["trigger"] if cycle else None)
    row["source_file"] = str(metadata["source_file"]) if isinstance(metadata.get("source_file"), Path) else metadata.get("source_file")
    row["metadata_source"] = metadata.get("metadata_source")
    if not isinstance(row["metadata_source"], str) or row["metadata_source"] not in {"front_matter", "sidecar"}:
        fail("metadata_source", "required front_matter or sidecar")
    for field in ("source", "timestamp"):
        value = metadata.get(field)
        if field == "timestamp" and isinstance(value, datetime):
            value = value.isoformat()
        if isinstance(value, str):
            value = value.strip() or None
        row[field] = value
    for field in manufacturing_fields(1):  # vector dimension unused for scalar validation
        if field.datatype != "VARCHAR":
            continue
        value = row[field.name]
        if value is None and field.nullable:
            continue
        if not isinstance(value, str) or (not field.nullable and not value.strip()):
            fail(field.name, "required string" if not field.nullable else "string or None required")
        if len(value.encode("utf-8")) > field.max_length:
            fail(field.name, f"UTF-8 byte length exceeds {field.max_length}; no truncation")
        row[field.name] = str(value)
    return row


def build_manufacturing_row(document, dense_vector, sparse_vector, dense_dim):
    row = validate_manufacturing_document(document)
    manufacturing_fields(dense_dim)
    try:
        dense = list(dense_vector)
    except TypeError:
        dense = []
    if len(dense) != dense_dim or any(isinstance(v, bool) or not isinstance(v, Real) or not isfinite(v) for v in dense):
        raise ManufacturingRowValidationError(row["id"], "dense_vector", "finite numeric vector with expected dimension required")
    if not isinstance(sparse_vector, dict) or not sparse_vector:
        raise ManufacturingRowValidationError(row["id"], "sparse_vector", "nonempty index-to-value mapping required")
    sparse = {}
    for index, value in sparse_vector.items():
        if (isinstance(index, bool) or not isinstance(index, Integral) or not 0 <= index < 2**32
                or isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value)):
            raise ManufacturingRowValidationError(row["id"], "sparse_vector", "uint32 indices and finite numeric values required")
        sparse[int(index)] = float(value)
    row.update(dense_vector=[float(v) for v in dense], sparse_vector=sparse)
    return row


def build_manufacturing_schema(client, dense_dim):
    # Deferred import: pure field specifications and row tests need no SDK/server.
    from pymilvus import DataType
    schema = client.create_schema(auto_id=False, enable_dynamic_field=False,
                                  description=MANUFACTURING_SCHEMA_VERSION)
    for field in manufacturing_fields(dense_dim):
        options = {"nullable": field.nullable}
        if field.max_length is not None:
            options["max_length"] = field.max_length
        if field.dim is not None:
            options["dim"] = field.dim
        if field.is_primary:
            options.update(is_primary=True, auto_id=False)
        schema.add_field(field_name=field.name, datatype=getattr(DataType, field.datatype), **options)
    return schema


def build_manufacturing_indexes(client):
    indexes = client.prepare_index_params()
    for spec in manufacturing_indexes():
        indexes.add_index(**spec)
    return indexes


def validate_manufacturing_schema(description, collection_name, dense_dim):
    def check(field, expected, actual):
        if actual != expected:
            raise ManufacturingSchemaMismatchError(collection_name, field, expected, actual)

    check("auto_id", False, description.get("auto_id"))
    check("enable_dynamic_field", False, description.get("enable_dynamic_field"))
    check("functions", [], description.get("functions", []))
    fields = {field["name"]: field for field in description.get("fields", [])}
    expected = {field.name: field for field in manufacturing_fields(dense_dim)}
    check("fields", sorted(expected), sorted(fields))
    check("field_count", len(expected), len(description["fields"]))
    type_codes = {11: "DOUBLE", 21: "VARCHAR", 101: "FLOAT_VECTOR", 104: "SPARSE_FLOAT_VECTOR"}
    for name, spec in expected.items():
        actual = fields[name]
        datatype = actual.get("type")
        datatype = getattr(datatype, "name", type_codes.get(datatype, datatype))
        check(f"{name}.type", spec.datatype, datatype)
        check(f"{name}.is_primary", spec.is_primary, actual.get("is_primary", False))
        check(f"{name}.auto_id", False, actual.get("auto_id", False))
        check(f"{name}.nullable", spec.nullable, actual.get("nullable", False))
        check(f"{name}.default_value", None, actual.get("default_value"))
        for flag in ("is_partition_key", "is_clustering_key", "is_dynamic", "is_function_output"):
            check(f"{name}.{flag}", False, actual.get(flag, False))
        for key, value in (("max_length", spec.max_length), ("dim", spec.dim)):
            if value is not None:
                parameter = actual.get("params", {}).get(key)
                check(f"{name}.{key}", str(value), str(parameter))


def validate_manufacturing_indexes(client, collection_name):
    names = client.list_indexes(collection_name=collection_name)
    for spec in manufacturing_indexes():
        index_name = spec["index_name"]
        if index_name not in names:
            raise ManufacturingSchemaMismatchError(collection_name, "indexes", index_name, names)
        actual = client.describe_index(collection_name=collection_name, index_name=index_name) or {}
        for key in ("field_name", "index_type", "metric_type"):
            if actual.get(key) != spec[key]:
                raise ManufacturingSchemaMismatchError(collection_name, f"{index_name}.{key}", spec[key], actual.get(key))
        # SDK 2.5.4 describes server parameters either at top level or in params.
        # Verify every representation when both exist; conflicting values fail closed.
        parameters = actual.get("params", {})
        if not isinstance(parameters, dict):
            raise ManufacturingSchemaMismatchError(collection_name, f"{index_name}.params", "mapping", parameters)
        for key, expected in spec["params"].items():
            values = ([parameters[key]] if key in parameters else []) + ([actual[key]] if key in actual else [])
            for value in values or [None]:
                try:
                    equal = float(value) == expected
                except (TypeError, ValueError):
                    equal = False
                if not equal:
                    raise ManufacturingSchemaMismatchError(collection_name, f"{index_name}.{key}", expected, value)


def ensure_manufacturing_collection(client, collection_name, dense_dim):
    if not client.has_collection(collection_name):
        client.create_collection(collection_name=collection_name,
                                 schema=build_manufacturing_schema(client, dense_dim),
                                 index_params=build_manufacturing_indexes(client))
    # Inspect new collections as well: unsupported server semantics must fail closed.
    validate_manufacturing_schema(client.describe_collection(collection_name=collection_name), collection_name, dense_dim)
    validate_manufacturing_indexes(client, collection_name)
    client.load_collection(collection_name=collection_name)
