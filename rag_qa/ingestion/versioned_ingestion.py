"""Single-worker, retryable ingestion; SQLite and Milvus are not one transaction."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

from rag_qa.core.milvus_schema import MANUFACTURING_SCHEMA_VERSION, validate_manufacturing_document
from rag_qa.ingestion.fingerprints import sha256_file
from rag_qa.ingestion.manifest_store import (
    ManifestRecord, ManifestCompatibilityError, MANIFEST_SCHEMA_VERSION,
)
from rag_qa.ingestion.metadata_loader import resolve_metadata
from rag_qa.schemas.manufacturing_metadata import ManufacturingDocumentMetadata


class DocumentVersionConflictError(ValueError):
    pass


class SourceChangedDuringIngestionError(RuntimeError):
    pass


class DuplicateDocumentIdError(ValueError):
    pass


class SnapshotVerificationError(RuntimeError):
    pass


def canonical_sha256(value):
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def metadata_sha256(metadata):
    """Business fields only; revalidate and normalize through the Stage 1 model."""
    business = {k: metadata[k] for k in ManufacturingDocumentMetadata.model_fields if k in metadata}
    return canonical_sha256(ManufacturingDocumentMetadata.model_validate(business).to_metadata())


@dataclass(frozen=True)
class ProcessingContract:
    parent_chunk_size: int
    parent_chunk_overlap: int
    child_chunk_size: int
    child_chunk_overlap: int
    processing_contract_version: str = "manufacturing_processing_v1"
    fingerprint_contract_version: str = "manufacturing_fingerprints_v1"
    storage_schema_version: str = MANUFACTURING_SCHEMA_VERSION

    def __post_init__(self):
        for prefix in ("parent", "child"):
            size, overlap = getattr(self, prefix + "_chunk_size"), getattr(self, prefix + "_chunk_overlap")
            if type(size) is not int or type(overlap) is not int or not 0 <= overlap < size:
                raise ValueError(f"{prefix}: integer size > overlap >= 0 required")
        for name in ("processing_contract_version", "fingerprint_contract_version"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name}: nonempty contract version required")
        if self.storage_schema_version != MANUFACTURING_SCHEMA_VERSION:
            raise ManifestCompatibilityError("processing contract requires the unchanged Stage 3 storage schema")

    @classmethod
    def from_config(cls):
        from base.config import config
        return cls(config.PARENT_CHUNK_SIZE, config.PARENT_CHUNK_OVERLAP,
                   config.CHILD_CHUNK_SIZE, config.CHILD_CHUNK_OVERLAP)

    @property
    def signature(self):
        return canonical_sha256(asdict(self))

    def chunk_options(self):
        return {key: value for key, value in asdict(self).items() if "chunk" in key}


@dataclass(frozen=True)
class SourceSnapshot:
    path: Path
    business: dict
    document_sha256: str
    metadata_sha256: str
    metadata_source: str

    @property
    def document_id(self):
        return self.business["document_id"]


@dataclass(frozen=True)
class IngestionResult:
    document_id: str
    status: str
    revision: int
    added: tuple[str, ...] = ()
    retained: tuple[str, ...] = ()
    removed: tuple[str, ...] = ()


def preflight_source(source_file):
    path = Path(source_file).resolve(strict=True)
    before = sha256_file(path)
    resolved = resolve_metadata(path)
    if sha256_file(path) != before:
        raise SourceChangedDuringIngestionError(f"document source changed during preflight: {path}")
    return SourceSnapshot(path, resolved.business_metadata, before,
                          metadata_sha256(resolved.business_metadata), resolved.metadata_source)


def _process_file(path, **chunk_options):
    # Reuse the real loader/Stage 2 splitter; keep imports and processing off the skip path.
    from rag_qa.core.document_processor import process_document_file
    return process_document_file(path, metadata_mode="manufacturing", **chunk_options)


class VersionedIngestion:
    """Caller owns gateway/store lifetime and serializes all ingest/delete calls.

    Use one manifest DB for one collection. No automatic directory pruning.
    """
    SUPPORTED_EXTENSIONS = frozenset({".txt", ".md", ".pdf", ".docx", ".ppt", ".pptx", ".jpg", ".png"})

    def __init__(self, manifest_store, vector_gateway, *, processing_contract=None, processor=None):
        if getattr(vector_gateway, "schema_mode", None) != "manufacturing":
            raise ValueError("versioned ingestion requires a manufacturing gateway")
        self.manifest = manifest_store
        self.gateway = vector_gateway
        self.contract = processing_contract or ProcessingContract.from_config()
        self.processor = processor or _process_file

    def _compatible(self, record):
        if record and (record.collection_name != self.gateway.collection_name
                       or record.storage_schema_version != self.contract.storage_schema_version
                       or record.manifest_schema_version != MANIFEST_SCHEMA_VERSION):
            raise ManifestCompatibilityError("manifest collection/schema incompatible; explicit migration required")

    def ingest_file(self, source_file):
        return self._ingest(preflight_source(source_file))

    def _confirm_source(self, before):
        try:
            after = preflight_source(before.path)
        except (OSError, ValueError) as exc:
            raise SourceChangedDuringIngestionError(f"source or metadata no longer valid: {before.path}") from exc
        if (after.document_sha256, after.metadata_sha256, after.metadata_source) != (
                before.document_sha256, before.metadata_sha256, before.metadata_source):
            raise SourceChangedDuringIngestionError(f"source or metadata changed: {before.path}")

    def _actual_ids(self, document_id):
        # Validate IDs before passing them to a destructive administrative method.
        from rag_qa.core.milvus_schema import HASH_PATTERN
        values = list(self.gateway.list_document_child_ids(document_id))
        if any(not isinstance(i, str) or not HASH_PATTERN.fullmatch(i) for i in values):
            raise SnapshotVerificationError("actual document snapshot contains invalid stable PKs")
        if len(values) != len(set(values)):
            raise SnapshotVerificationError("actual document snapshot contains duplicate PKs")
        return set(values)

    def _ingest(self, source):
        document_id, version = source.document_id, source.business["document_version"]
        old = self.manifest.get(document_id)
        self._compatible(old)
        revision = old.revision if old else 0
        status = "INGEST" if old is None else "UPDATE"
        if old and version == old.active_document_version:
            if (old.document_sha256, old.metadata_sha256) != (source.document_sha256, source.metadata_sha256):
                raise DocumentVersionConflictError(f"document={document_id}; same version has changed source/metadata; bump document_version")
            status = "REINDEX"
            if old.processing_signature == self.contract.signature:
                actual = self._actual_ids(document_id)
                self._confirm_source(source)
                if actual == set(old.child_ids):
                    return IngestionResult(document_id, "SKIP_UNCHANGED", revision)
                status = "RECONCILE"

        children = list(self.processor(str(source.path), **self.contract.chunk_options()))
        self._confirm_source(source)  # before any mutation, including failures after OCR
        if not children:
            raise SnapshotVerificationError("empty processor snapshot; use explicit delete_document instead")
        desired = set()
        for child in children:
            scalar = validate_manufacturing_document(child)
            if (scalar["document_id"] != document_id or scalar["document_version"] != version
                    or scalar["document_sha256"] != source.document_sha256
                    or metadata_sha256(child.metadata) != source.metadata_sha256
                    or scalar["source_file"] != str(source.path)
                    or scalar["metadata_source"] != source.metadata_source):
                raise SourceChangedDuringIngestionError("processor output does not match the authoritative source snapshot")
            if scalar["id"] in desired:
                raise SnapshotVerificationError("processor returned duplicate stable child IDs")
            desired.add(scalar["id"])
        actual = self._actual_ids(document_id)
        added, retained, removed = desired - actual, desired & actual, actual - desired
        if children:
            self.gateway.add_documents(children)  # all retained scalars are refreshed as well
        if not desired <= self._actual_ids(document_id):
            raise SnapshotVerificationError("desired children missing after upsert; stale delete forbidden")
        if removed:
            self.gateway.delete_child_ids(sorted(removed))
        if not self.gateway.verify_document_snapshot(document_id, sorted(desired)):
            raise SnapshotVerificationError("final document snapshot does not equal desired IDs")
        record = ManifestRecord(
            document_id=document_id, active_document_version=version,
            document_sha256=source.document_sha256, metadata_sha256=source.metadata_sha256,
            processing_signature=self.contract.signature, collection_name=self.gateway.collection_name,
            storage_schema_version=self.contract.storage_schema_version, source_file=str(source.path),
            metadata_source=source.metadata_source, child_ids=tuple(desired))
        committed = self.manifest.commit_snapshot(record, expected_revision=revision)
        return IngestionResult(document_id, status, committed.revision,
                               tuple(sorted(added)), tuple(sorted(retained)), tuple(sorted(removed)))

    def delete_document(self, document_id):
        # Validate through the business contract; quotes are legal and gateway encoding handles them.
        document_id = ManufacturingDocumentMetadata(document_id=document_id, document_version="delete",
                                                     title="delete", knowledge_type="manual").document_id
        old = self.manifest.get(document_id)
        self._compatible(old)
        actual = self._actual_ids(document_id)
        if actual:
            self.gateway.delete_child_ids(sorted(actual))
        if not self.gateway.verify_document_snapshot(document_id, []):
            raise SnapshotVerificationError("document is not empty after explicit delete")
        if old:
            self.manifest.delete(document_id, expected_revision=old.revision)
        return IngestionResult(document_id, "DELETED" if actual or old else "NOOP", 0,
                               removed=tuple(sorted(actual)))

    def ingest_directory(self, directory):
        root = Path(directory).resolve(strict=True)
        if not root.is_dir():
            raise ValueError("ingest_directory requires a directory")
        sources = [preflight_source(p) for p in sorted(root.rglob("*"))
                   if p.is_file() and p.suffix.lower() in self.SUPPORTED_EXTENSIONS]
        seen = set()
        for source in sources:
            if source.document_id in seen:
                raise DuplicateDocumentIdError(f"duplicate document_id in batch: {source.document_id}")
            seen.add(source.document_id)
        return [self._ingest(source) for source in sources]
