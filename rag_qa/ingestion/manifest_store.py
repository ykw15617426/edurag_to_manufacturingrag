"""Persistent control plane for a single ingestion worker, never a Milvus row."""
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
import hashlib

MANIFEST_SCHEMA_VERSION = "manifest_v1"
_HASH = re.compile(r"[0-9a-f]{64}")


class ManifestCompatibilityError(ValueError):
    pass


class ManifestRevisionConflictError(RuntimeError):
    pass


@dataclass(frozen=True)
class ManifestRecord:
    document_id: str
    active_document_version: str
    document_sha256: str
    metadata_sha256: str
    processing_signature: str
    collection_name: str
    storage_schema_version: str
    source_file: str
    metadata_source: str
    child_ids: tuple[str, ...]
    revision: int = 0
    updated_at: str = ""
    manifest_schema_version: str = MANIFEST_SCHEMA_VERSION

    @property
    def child_count(self):
        return len(self.child_ids)

    def __post_init__(self):
        for name in ("document_id", "active_document_version", "collection_name",
                     "storage_schema_version", "source_file"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name}: nonempty string required")
        for name in ("document_sha256", "metadata_sha256", "processing_signature"):
            if not isinstance(getattr(self, name), str) or not _HASH.fullmatch(getattr(self, name)):
                raise ValueError(f"{name}: lowercase SHA256 required")
        ids = tuple(self.child_ids)
        if any(not isinstance(i, str) or not _HASH.fullmatch(i) for i in ids) or len(ids) != len(set(ids)):
            raise ValueError("child_ids: unique stable SHA256 IDs required")
        object.__setattr__(self, "child_ids", tuple(sorted(ids)))
        if self.manifest_schema_version != MANIFEST_SCHEMA_VERSION:
            raise ManifestCompatibilityError("unsupported manifest schema version")
        if self.metadata_source not in {"front_matter", "sidecar"}:
            raise ValueError("metadata_source: front_matter or sidecar required")
        if type(self.revision) is not int or self.revision < 0:
            raise ValueError("revision: nonnegative integer required")


class SQLiteManifestStore:
    """Short SQLite transactions only. Caller must serialize the entire ingestion.

    Revision CAS detects stale control writes; it is not a distributed worker lock.
    """

    def __init__(self, db_path=None):
        if db_path is None:
            from base.config import config
            db_path = config.MANUFACTURING_MANIFEST_DB_PATH
        self.db_path = str(db_path)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        try:
            version = self.connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise ManifestCompatibilityError(f"unsupported SQLite manifest version: {version}")
            tables = {row[0] for row in self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            if (version == 0 and tables) or (version == 1 and tables != {"active_documents"}):
                raise ManifestCompatibilityError("not an initialized manifest_v1 database; no automatic adoption/repair")
            if version == 1:
                info = list(self.connection.execute("PRAGMA table_info(active_documents)"))
                expected = set(ManifestRecord.__dataclass_fields__) | {"child_count"}
                if ({r[1] for r in info} != expected
                        or any(r[2] != ("INTEGER" if r[1] in {"revision", "child_count"} else "TEXT") for r in info)
                        or [r[1] for r in info if r[5]] != ["document_id"]):
                    raise ManifestCompatibilityError("incompatible active_documents fields/types/PK; no automatic repair")
            with self._write():
                self.connection.execute("""CREATE TABLE IF NOT EXISTS active_documents (
                    document_id TEXT PRIMARY KEY, active_document_version TEXT NOT NULL,
                    document_sha256 TEXT NOT NULL, metadata_sha256 TEXT NOT NULL,
                    processing_signature TEXT NOT NULL, collection_name TEXT NOT NULL,
                    storage_schema_version TEXT NOT NULL, source_file TEXT NOT NULL,
                    metadata_source TEXT NOT NULL, child_ids TEXT NOT NULL,
                    revision INTEGER NOT NULL CHECK(revision > 0), updated_at TEXT NOT NULL,
                    manifest_schema_version TEXT NOT NULL, child_count INTEGER NOT NULL
                )""")
                self.connection.execute("PRAGMA user_version=1")
            expected = set(ManifestRecord.__dataclass_fields__) | {"child_count"}
            actual = {r[1] for r in self.connection.execute("PRAGMA table_info(active_documents)")}
            if actual != expected:
                raise ManifestCompatibilityError("incompatible active_documents fields; no automatic repair")
        except BaseException:
            self.connection.close()
            raise

    @contextmanager
    def _write(self):
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.connection.execute("COMMIT")
        except BaseException:
            self.connection.execute("ROLLBACK")
            raise

    def get(self, document_id):
        row = self.connection.execute("SELECT * FROM active_documents WHERE document_id=?", (document_id,)).fetchone()
        if row is None:
            return None
        values = dict(row)
        count = values.pop("child_count")
        values["child_ids"] = tuple(json.loads(values["child_ids"]))
        record = ManifestRecord(**values)
        if count != record.child_count or record.revision < 1:
            raise ManifestCompatibilityError("invalid persisted manifest count/revision")
        return record

    def _check_revision(self, document_id, expected_revision):
        current = self.get(document_id)
        revision = current.revision if current else 0
        if revision != expected_revision:
            raise ManifestRevisionConflictError(f"document={document_id}; expected revision={expected_revision}; actual={revision}")

    def commit_snapshot(self, record, *, expected_revision):
        from dataclasses import replace
        # No loader/embedding/network callback is executed inside this transaction.
        with self._write():
            self._check_revision(record.document_id, expected_revision)
            committed = replace(record, revision=expected_revision + 1,
                                updated_at=datetime.now(timezone.utc).isoformat())
            values = asdict(committed)
            values["child_ids"] = json.dumps(committed.child_ids, ensure_ascii=False, separators=(",", ":"))
            values["child_count"] = committed.child_count
            columns = list(values)
            updates = ",".join(f"{c}=excluded.{c}" for c in columns if c != "document_id")
            self.connection.execute(
                f"INSERT INTO active_documents ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)}) "
                f"ON CONFLICT(document_id) DO UPDATE SET {updates}", tuple(values.values()))
        return committed

    def delete(self, document_id, *, expected_revision):
        with self._write():
            self._check_revision(document_id, expected_revision)
            self.connection.execute("DELETE FROM active_documents WHERE document_id=?", (document_id,))

    def close(self):
        self.connection.close()

    def snapshot_fingerprint(self, collection_name=None):
        """One read snapshot; exclude timestamp noise, preserve mutation semantics."""
        return manifest_snapshot_fingerprint(self.connection, collection_name)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def manifest_snapshot_fingerprint(connection, collection_name=None):
    """Also usable with a mode=ro SQLite connection in online worker threads."""
    if connection.execute("PRAGMA user_version").fetchone()[0] != 1:
        raise ManifestCompatibilityError("initialized manifest_v1 required")
    cursor = connection.execute("SELECT * FROM active_documents ORDER BY document_id")
    names = [item[0] for item in cursor.description]
    rows = cursor.fetchall()
    records = []
    for row in rows:
        values = dict(zip(names, row))
        count = values.pop("child_count")
        values["child_ids"] = tuple(json.loads(values["child_ids"]))
        record = ManifestRecord(**values)
        if record.revision < 1 or count != record.child_count:
            raise ManifestCompatibilityError("invalid manifest record")
        if collection_name is not None and record.collection_name != collection_name:
            raise ManifestCompatibilityError("manifest collection mismatch")
        values = asdict(record)
        values.pop("updated_at")
        records.append(values)
    payload = json.dumps(dict(manifest_schema_version=MANIFEST_SCHEMA_VERSION, active_documents=records),
                         sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
