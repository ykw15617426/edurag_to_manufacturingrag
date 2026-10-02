"""Real temporary SQLite; no live Milvus or model dependency."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag_qa.ingestion.manifest_store import (
    SQLiteManifestStore, ManifestRecord, ManifestRevisionConflictError, ManifestCompatibilityError,
)


def record(document_id="DOC-1", **overrides):
    digest = hashlib.sha256(b"fixture").hexdigest()
    values = dict(document_id=document_id, active_document_version="1.10",
                  document_sha256=digest, metadata_sha256=digest, processing_signature=digest,
                  collection_name="test_manufacturing_v1", storage_schema_version="manufacturing_v1",
                  source_file="synthetic.txt", metadata_source="sidecar", child_ids=("b" * 64, "a" * 64))
    values.update(overrides)
    return ManifestRecord(**values)


def test_manifest_survives_reopen_and_one_active_record(tmp_path):
    path = tmp_path / "control" / "manifest.sqlite3"
    with SQLiteManifestStore(path) as store:
        first = store.commit_snapshot(record(), expected_revision=0)
        assert first.revision == 1 and first.child_count == 2 and first.updated_at
        assert first.child_ids == ("a" * 64, "b" * 64)
        second = store.commit_snapshot(replace(first, active_document_version="release-A"), expected_revision=1)
        assert second.revision == 2
        raw = store.connection.execute("SELECT child_ids,child_count FROM active_documents").fetchone()
        assert raw[0] == json.dumps(first.child_ids, separators=(",", ":")) and raw[1] == 2
        assert not store.connection.in_transaction
    with SQLiteManifestStore(path) as reopened:
        assert reopened.get("DOC-1") == second
        assert reopened.connection.execute("SELECT count(*) FROM active_documents").fetchone()[0] == 1


def test_stale_revision_cannot_overwrite_or_delete(tmp_path):
    with SQLiteManifestStore(tmp_path / "manifest.db") as store:
        first = store.commit_snapshot(record(), expected_revision=0)
        with pytest.raises(ManifestRevisionConflictError):
            store.commit_snapshot(record(active_document_version="2"), expected_revision=0)
        with pytest.raises(ManifestRevisionConflictError):
            store.delete("DOC-1", expected_revision=0)
        assert store.get("DOC-1") == first
        assert not store.connection.in_transaction


def test_real_sql_commit_failure_rolls_back(tmp_path):
    with SQLiteManifestStore(tmp_path / "manifest.db") as store:
        first = store.commit_snapshot(record(), expected_revision=0)
        store.connection.execute("CREATE TRIGGER fail_update BEFORE UPDATE ON active_documents BEGIN SELECT RAISE(ABORT, 'synthetic commit failure'); END")
        with pytest.raises(sqlite3.IntegrityError):
            store.commit_snapshot(record(active_document_version="2"), expected_revision=1)
        assert store.get("DOC-1") == first
        assert not store.connection.in_transaction


def test_explicit_manifest_delete_is_idempotent_and_scoped(tmp_path):
    with SQLiteManifestStore(tmp_path / "manifest.db") as store:
        store.commit_snapshot(record(), expected_revision=0)
        other = store.commit_snapshot(record("OTHER"), expected_revision=0)
        store.delete("DOC-1", expected_revision=1)
        store.delete("DOC-1", expected_revision=0)
        assert store.get("DOC-1") is None and store.get("OTHER") == other


@pytest.mark.parametrize("overrides", [
    {"child_ids": ("a" * 64, "a" * 64)}, {"child_ids": ("invalid",)},
    {"document_sha256": "x" * 64}, {"revision": -1}, {"revision": True},
    {"active_document_version": 1.10}, {"document_id": ""}, {"metadata_source": "runtime"},
])
def test_invalid_records_rejected(overrides):
    with pytest.raises(ValueError):
        record(**overrides)


def test_unknown_manifest_versions_fail(tmp_path):
    with pytest.raises(ManifestCompatibilityError):
        record(manifest_schema_version="manifest_v2")
    path = tmp_path / "future.db"
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA user_version=2")
    with pytest.raises(ManifestCompatibilityError):
        SQLiteManifestStore(path)


def test_unrelated_database_is_not_adopted_or_modified(tmp_path):
    path = tmp_path / "unrelated.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE unrelated (value TEXT)")
    with pytest.raises(ManifestCompatibilityError):
        SQLiteManifestStore(path)
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 0
        assert connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == [("unrelated",)]


def test_missing_v1_table_is_not_silently_recreated(tmp_path):
    path = tmp_path / "corrupt.db"
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA user_version=1")
    with pytest.raises(ManifestCompatibilityError):
        SQLiteManifestStore(path)


def test_corrupt_count_fails_closed(tmp_path):
    with SQLiteManifestStore(tmp_path / "manifest.db") as store:
        store.commit_snapshot(record(), expected_revision=0)
        store.connection.execute("UPDATE active_documents SET child_count=999")
        with pytest.raises(ManifestCompatibilityError):
            store.get("DOC-1")


def test_document_id_sql_injection_is_literal(tmp_path):
    identifier = "DOC'; DROP TABLE active_documents; --"
    with SQLiteManifestStore(tmp_path / "manifest.db") as store:
        stored = store.commit_snapshot(record(identifier), expected_revision=0)
        assert store.get(identifier) == stored and store.get("DOC") is None


def test_manifest_config_precedence(tmp_path, monkeypatch):
    from base.config import Config
    ini = tmp_path / "example.ini"
    ini.write_text("[ingestion]\nmanufacturing_manifest_db_path = local.db\n", encoding="utf-8")
    monkeypatch.delenv("MANUFACTURING_MANIFEST_DB_PATH", raising=False)
    assert Config(ini).MANUFACTURING_MANIFEST_DB_PATH == "local.db"
    monkeypatch.setenv("MANUFACTURING_MANIFEST_DB_PATH", "override.db")
    assert Config(ini).MANUFACTURING_MANIFEST_DB_PATH == "override.db"
    monkeypatch.delenv("MANUFACTURING_MANIFEST_DB_PATH")
    assert Path(Config(tmp_path / "missing.ini").MANUFACTURING_MANIFEST_DB_PATH).parts[-2:] == ("runtime", "manufacturing_manifest.sqlite3")
