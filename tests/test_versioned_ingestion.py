"""Stateful gateway + real SQLite/metadata/IDs; no claim of live Milvus integration."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import sqlite3
import sys
from types import SimpleNamespace

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag_qa.core.milvus_schema import build_manufacturing_row
from rag_qa.ingestion.fingerprints import sha256_content, build_parent_id, build_child_id
from rag_qa.ingestion.manifest_store import SQLiteManifestStore, ManifestCompatibilityError
from rag_qa.ingestion.metadata_loader import load_with_metadata
from rag_qa.ingestion.versioned_ingestion import (
    VersionedIngestion, ProcessingContract, metadata_sha256, canonical_sha256,
    DocumentVersionConflictError, SourceChangedDuringIngestionError, DuplicateDocumentIdError,
    SnapshotVerificationError,
)
from test_manufacturing_milvus_schema import vector_store_unit
from test_manufacturing_fingerprints import identity_processor
from test_manufacturing_metadata import processor_unit


def source_file(root, version="V1", body="A\nB\nC", *, document_id="DOC-1", title="Synthetic manual", name="manual.txt"):
    path = root / name
    path.write_text(body, encoding="utf-8")
    metadata = dict(document_id=document_id, document_version=version, title=title, knowledge_type="manual")
    Path(str(path) + ".yaml").write_text(yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


class Processor:
    def __init__(self):
        self.calls = 0
        self.options = []
        self.hook = None
        self.store = None

    def __call__(self, path, **options):
        self.calls += 1
        self.options.append(options)
        assert not self.store.connection.in_transaction
        loaded = load_with_metadata(path, lambda p: [SimpleNamespace(page_content=Path(p).read_text(encoding="utf-8"), metadata={})])
        children = []
        for token in loaded[0].page_content.splitlines():
            if not token.strip():
                continue
            metadata = deepcopy(loaded[0].metadata)
            parent_hash = child_hash = sha256_content(token)
            parent_id = build_parent_id(metadata["document_id"], parent_hash)
            identifier = build_child_id(metadata["document_id"], parent_id, child_hash)
            metadata.update(parent_id=parent_id, parent_content=token, id=identifier, child_id=identifier,
                            parent_content_sha256=parent_hash, child_content_sha256=child_hash)
            children.append(SimpleNamespace(page_content=token, metadata=metadata))
        if self.hook:
            self.hook(path, children)
        return children


class Gateway:
    schema_mode = "manufacturing"
    collection_name = "synthetic_manufacturing_v1"

    def __init__(self, store):
        self.store = store
        self.rows = {}
        self.events = []
        self.embeddings = 0
        self.fail_upsert = False
        self.fail_delete = False
        self.drop_upsert = False
        self.ignore_delete = False
        self.fail_verify = False

    def check(self, event):
        assert not self.store.connection.in_transaction
        self.events.append(event)

    def list_document_child_ids(self, document_id):
        self.check("query")
        return sorted(i for i, row in self.rows.items() if row["document_id"] == document_id)

    def add_documents(self, documents):
        self.check("upsert")
        self.embeddings += 1
        for doc in documents:
            row = build_manufacturing_row(doc, [1, 0, 0, 0], {0: 1}, 4)
            if not self.drop_upsert:
                self.rows[row["id"]] = row
            if self.fail_upsert:
                raise RuntimeError("synthetic partial upsert failure")

    def delete_child_ids(self, ids):
        self.check("delete")
        for identifier in ids:
            if not self.ignore_delete:
                self.rows.pop(identifier, None)
            if self.fail_delete:
                raise RuntimeError("synthetic partial delete failure")

    def verify_document_snapshot(self, document_id, desired_ids):
        self.check("verify")
        return not self.fail_verify and set(self.list_document_child_ids(document_id)) == set(desired_ids)

    def snapshot(self, document_id="DOC-1"):
        return {row["text"] for row in self.rows.values() if row["document_id"] == document_id}


@pytest.fixture
def setup(tmp_path):
    store = SQLiteManifestStore(tmp_path / "manifest.db")
    gateway, processor = Gateway(store), Processor()
    processor.store = store
    contract = ProcessingContract(512, 120, 128, 30)
    runner = VersionedIngestion(store, gateway, processing_contract=contract, processor=processor)
    yield SimpleNamespace(store=store, gateway=gateway, processor=processor, runner=runner, root=tmp_path, contract=contract)
    store.close()


def test_first_ingestion_and_cross_run_skip_before_processing(setup):
    s = setup
    path = source_file(s.root)
    first = s.runner.ingest_file(path)
    assert first.status == "INGEST" and first.revision == 1 and len(first.added) == 3
    assert s.gateway.snapshot() == {"A", "B", "C"}
    record = s.store.get("DOC-1")
    assert record.child_count == 3 and record.active_document_version == "V1"
    # Reopen SQLite and replace processor with a fresh instance: this is a cross-run check.
    with SQLiteManifestStore(s.root / "manifest.db") as reopened:
        processor = Processor(); processor.store = reopened
        s.gateway.store = reopened
        runner = VersionedIngestion(reopened, s.gateway, processing_contract=s.contract, processor=processor)
        s.gateway.events.clear()
        result = runner.ingest_file(path)
        assert result.status == "SKIP_UNCHANGED" and result.revision == 1
        assert processor.calls == 0 and s.gateway.embeddings == 1
        assert s.gateway.events == ["query"] and reopened.get("DOC-1") == record


def test_v1_abc_to_v2_abd_removes_c_and_preserves_other_document(setup):
    s = setup
    path = source_file(s.root)
    other_path = source_file(s.root, document_id="OTHER", body="C\nE", name="other.txt")
    s.runner.ingest_file(path); s.runner.ingest_file(other_path)
    other_rows = deepcopy({k: v for k, v in s.gateway.rows.items() if v["document_id"] == "OTHER"})
    old_ids = set(s.store.get("DOC-1").child_ids)
    source_file(s.root, version="V2", body="A\nB\nD", title="Updated manual")
    s.gateway.events.clear()
    result = s.runner.ingest_file(path)
    assert result.status == "UPDATE" and result.revision == 2
    assert (len(result.added), len(result.retained), len(result.removed)) == (1, 2, 1)
    assert s.gateway.snapshot() == {"A", "B", "D"} and "C" not in s.gateway.snapshot()
    assert old_ids - set(s.store.get("DOC-1").child_ids) == set(result.removed)
    assert s.gateway.events.index("upsert") < s.gateway.events.index("delete") < s.gateway.events.index("verify")
    assert all(row["document_version"] == "V2" and row["title"] == "Updated manual"
               for row in s.gateway.rows.values() if row["document_id"] == "DOC-1")
    assert {k: v for k, v in s.gateway.rows.items() if v["document_id"] == "OTHER"} == other_rows


def test_opaque_version_transition_refreshes_all_retained_scalars(setup):
    s = setup
    path = source_file(s.root, version="9.99")
    s.runner.ingest_file(path)
    ids = set(s.store.get("DOC-1").child_ids)
    source_file(s.root, version="1.01-beta", title="New scalars")
    result = s.runner.ingest_file(path)
    assert set(result.retained) == ids and not result.added and not result.removed
    assert all(r["document_version"] == "1.01-beta" and r["title"] == "New scalars" for r in s.gateway.rows.values())
    assert s.store.get("DOC-1").active_document_version == "1.01-beta"


@pytest.mark.parametrize("change", ["source", "metadata"])
def test_same_version_changed_source_or_metadata_conflicts_without_mutation(setup, change):
    s = setup
    path = source_file(s.root); s.runner.ingest_file(path)
    previous = s.store.get("DOC-1"); rows = deepcopy(s.gateway.rows)
    source_file(s.root, body="A\nchanged" if change == "source" else "A\nB\nC",
                title="Changed title" if change == "metadata" else "Synthetic manual")
    s.gateway.events.clear()
    with pytest.raises(DocumentVersionConflictError):
        s.runner.ingest_file(path)
    assert s.processor.calls == 1 and not s.gateway.events
    assert s.store.get("DOC-1") == previous and s.gateway.rows == rows


@pytest.mark.parametrize("field,value", [("child_chunk_size", 129), ("parent_chunk_overlap", 119),
                                         ("processing_contract_version", "processing_v2"),
                                         ("fingerprint_contract_version", "fingerprints_v2")])
def test_processing_signature_only_change_reindexes_same_version(setup, field, value):
    s = setup
    path = source_file(s.root); s.runner.ingest_file(path)
    contract = replace(s.contract, **{field: value})
    runner = VersionedIngestion(s.store, s.gateway, processing_contract=contract, processor=s.processor)
    result = runner.ingest_file(path)
    assert result.status == "REINDEX" and result.revision == 2 and s.gateway.embeddings == 2
    assert s.store.get("DOC-1").processing_signature == contract.signature != s.contract.signature
    assert s.processor.options[-1] == contract.chunk_options()


def test_metadata_hash_normalization_and_runtime_exclusion():
    business = dict(document_id="工艺-001", document_version="V1", title="合成材料", knowledge_type="manual")
    reversed_keys = dict(reversed(list(business.items())))
    assert metadata_sha256(business) == metadata_sha256(reversed_keys)
    assert metadata_sha256(dict(business, source_file="other", file_path="other", timestamp="later",
                                id="x", child_id="y", document_sha256="z")) == metadata_sha256(business)
    assert metadata_sha256(dict(business, title="changed")) != metadata_sha256(business)
    assert canonical_sha256({"b": 2, "a": "中文"}) == canonical_sha256({"a": "中文", "b": 2})


def test_sidecar_key_order_skip_then_bumped_business_update(setup):
    s = setup
    path = source_file(s.root); s.runner.ingest_file(path)
    sidecar = Path(str(path) + ".yaml")
    data = yaml.safe_load(sidecar.read_text(encoding="utf-8"))
    sidecar.write_text(yaml.safe_dump(dict(reversed(list(data.items()))), sort_keys=False), encoding="utf-8")
    assert s.runner.ingest_file(path).status == "SKIP_UNCHANGED"
    data.update(document_version="release-X", manufacturer="Fixture Co")
    sidecar.write_text(yaml.safe_dump(data), encoding="utf-8")
    assert s.runner.ingest_file(path).status == "UPDATE"
    assert all(r["manufacturer"] == "Fixture Co" for r in s.gateway.rows.values())


def test_missing_manifest_child_reconciles_not_skip(setup):
    s = setup
    path = source_file(s.root); s.runner.ingest_file(path)
    s.gateway.rows.pop(next(iter(s.gateway.rows)))
    result = s.runner.ingest_file(path)
    assert result.status == "RECONCILE" and result.revision == 2 and len(result.added) == 1
    assert s.gateway.snapshot() == {"A", "B", "C"}


def test_no_manifest_and_orphan_state_recovered_from_authoritative_input(setup):
    s = setup
    path = source_file(s.root, body="A\nOLD")
    s.gateway.add_documents(s.processor(str(path)))
    source_file(s.root, version="V2", body="A\nB\nD")
    result = s.runner.ingest_file(path)
    assert result.status == "INGEST" and result.revision == 1 and len(result.removed) == 1
    assert s.gateway.snapshot() == {"A", "B", "D"}


def test_upsert_partial_failure_cannot_delete_or_advance_and_retry_converges(setup):
    s = setup
    path = source_file(s.root); s.runner.ingest_file(path)
    previous = s.store.get("DOC-1")
    source_file(s.root, version="V2", body="D\nA\nB")
    s.gateway.fail_upsert = True; s.gateway.events.clear()
    with pytest.raises(RuntimeError, match="upsert"):
        s.runner.ingest_file(path)
    assert "delete" not in s.gateway.events and s.store.get("DOC-1") == previous
    assert s.gateway.snapshot() == {"A", "B", "C", "D"}
    s.gateway.fail_upsert = False
    assert s.runner.ingest_file(path).revision == 2
    assert s.gateway.snapshot() == {"A", "B", "D"}


def test_partial_delete_failure_keeps_manifest_and_retry_uses_actual_state(setup):
    s = setup
    path = source_file(s.root, body="A\nB\nC\nE"); s.runner.ingest_file(path)
    previous = s.store.get("DOC-1")
    source_file(s.root, version="V2", body="A\nB\nD")
    s.gateway.fail_delete = True
    with pytest.raises(RuntimeError, match="delete"):
        s.runner.ingest_file(path)
    assert s.store.get("DOC-1") == previous and len(s.gateway.snapshot()) == 4
    s.gateway.fail_delete = False
    result = s.runner.ingest_file(path)
    assert len(result.removed) == 1 and s.gateway.snapshot() == {"A", "B", "D"}
    assert s.store.get("DOC-1").revision == 2


def test_manifest_sql_commit_failure_after_correct_milvus_retries(setup):
    s = setup
    path = source_file(s.root); s.runner.ingest_file(path)
    previous = s.store.get("DOC-1")
    source_file(s.root, version="V2", body="A\nB\nD")
    s.store.connection.execute("CREATE TRIGGER fail_update BEFORE UPDATE ON active_documents BEGIN SELECT RAISE(ABORT, 'failure'); END")
    with pytest.raises(sqlite3.IntegrityError):
        s.runner.ingest_file(path)
    assert s.store.get("DOC-1") == previous and s.gateway.snapshot() == {"A", "B", "D"}
    s.store.connection.execute("DROP TRIGGER fail_update")
    result = s.runner.ingest_file(path)
    assert result.revision == 2 and len(result.retained) == 3 and not result.removed


@pytest.mark.parametrize("failure", ["drop_upsert", "ignore_delete", "fail_verify"])
def test_snapshot_verification_prevents_manifest_commit(setup, failure):
    s = setup
    path = source_file(s.root); s.runner.ingest_file(path)
    previous = s.store.get("DOC-1")
    source_file(s.root, version="V2", body="A\nB\nD")
    setattr(s.gateway, failure, True); s.gateway.events.clear()
    with pytest.raises(SnapshotVerificationError):
        s.runner.ingest_file(path)
    assert s.store.get("DOC-1") == previous
    if failure == "drop_upsert":
        assert "delete" not in s.gateway.events and "C" in s.gateway.snapshot()


@pytest.mark.parametrize("change", ["source", "sidecar", "invalid_sidecar", "missing_source"])
def test_input_changes_during_processing_fail_before_any_milvus_mutation(setup, change):
    s = setup
    path = source_file(s.root)
    def mutate(path, children):
        if change == "source":
            Path(path).write_text("changed", encoding="utf-8")
        elif change == "missing_source":
            Path(path).unlink()
        else:
            sidecar = Path(path + ".yaml")
            data = yaml.safe_load(sidecar.read_text(encoding="utf-8"))
            data["title"] = "changed"
            sidecar.write_text("[invalid" if change == "invalid_sidecar" else yaml.safe_dump(data), encoding="utf-8")
    s.processor.hook = mutate
    with pytest.raises(SourceChangedDuringIngestionError):
        s.runner.ingest_file(path)
    assert not s.gateway.events and not s.gateway.rows and s.store.get("DOC-1") is None


def test_invalid_processor_snapshot_fails_before_mutation(setup):
    s = setup
    path = source_file(s.root)
    s.processor.hook = lambda path, docs: docs[0].metadata.update(document_id="OTHER")
    with pytest.raises(SourceChangedDuringIngestionError):
        s.runner.ingest_file(path)
    assert not s.gateway.events and not s.gateway.rows


def test_duplicate_or_empty_children_fail_closed(setup):
    s = setup
    path = source_file(s.root, body="A\nA")
    with pytest.raises(SnapshotVerificationError, match="duplicate"):
        s.runner.ingest_file(path)
    source_file(s.root, body="")
    with pytest.raises(SnapshotVerificationError, match="empty"):
        s.runner.ingest_file(path)
    assert not s.gateway.rows and not s.gateway.events


def test_explicit_delete_idempotent_and_other_rows_untouched(setup):
    s = setup
    s.runner.ingest_file(source_file(s.root))
    s.runner.ingest_file(source_file(s.root, document_id="OTHER", name="other.txt"))
    other_rows = deepcopy({k: r for k, r in s.gateway.rows.items() if r["document_id"] == "OTHER"})
    assert s.runner.delete_document("DOC-1").status == "DELETED"
    assert not s.gateway.snapshot() and s.store.get("DOC-1") is None
    assert s.runner.delete_document("DOC-1").status == "NOOP"
    assert {k: r for k, r in s.gateway.rows.items() if r["document_id"] == "OTHER"} == other_rows
    assert s.store.get("OTHER").revision == 1


def test_explicit_delete_failure_keeps_manifest_and_retries(setup):
    s = setup
    s.runner.ingest_file(source_file(s.root))
    previous = s.store.get("DOC-1")
    s.gateway.fail_delete = True
    with pytest.raises(RuntimeError):
        s.runner.delete_document("DOC-1")
    assert s.store.get("DOC-1") == previous
    s.gateway.fail_delete = False
    assert s.runner.delete_document("DOC-1").status == "DELETED"
    assert not s.gateway.snapshot() and s.store.get("DOC-1") is None


def test_explicit_delete_manifest_failure_retries_when_data_already_empty(setup):
    s = setup
    s.runner.ingest_file(source_file(s.root))
    previous = s.store.get("DOC-1")
    s.store.connection.execute("CREATE TRIGGER fail_delete BEFORE DELETE ON active_documents BEGIN SELECT RAISE(ABORT, 'failure'); END")
    with pytest.raises(sqlite3.IntegrityError):
        s.runner.delete_document("DOC-1")
    assert not s.gateway.snapshot() and s.store.get("DOC-1") == previous
    s.store.connection.execute("DROP TRIGGER fail_delete")
    assert s.runner.delete_document("DOC-1").status == "DELETED"
    assert s.runner.delete_document("DOC-1").status == "NOOP"


def test_directory_duplicate_preflight_before_first_mutation(setup):
    s = setup
    source_file(s.root)
    source_file(s.root, name="duplicate.txt")
    with pytest.raises(DuplicateDocumentIdError):
        s.runner.ingest_directory(s.root)
    assert not s.gateway.events and s.processor.calls == 0


def test_directory_sidecars_ignored_and_missing_sources_do_not_prune(setup):
    s = setup
    path = source_file(s.root)
    assert len(s.runner.ingest_directory(s.root)) == 1
    path.unlink()
    assert s.runner.ingest_directory(s.root) == []
    assert s.gateway.snapshot() == {"A", "B", "C"} and s.store.get("DOC-1") is not None


def test_manifest_collection_incompatibility_rejected_and_legacy_refused(setup):
    s = setup
    path = source_file(s.root); s.runner.ingest_file(path)
    s.gateway.collection_name = "other_collection_v1"; s.gateway.events.clear()
    with pytest.raises(ManifestCompatibilityError):
        s.runner.ingest_file(path)
    with pytest.raises(ManifestCompatibilityError):
        s.runner.delete_document("DOC-1")
    assert not s.gateway.events
    s.gateway.schema_mode = "legacy"
    with pytest.raises(ValueError, match="manufacturing"):
        VersionedIngestion(s.store, s.gateway)


def admin_store(vector_store_unit, client, mode="manufacturing"):
    store = vector_store_unit.VectorStore.__new__(vector_store_unit.VectorStore)
    store.schema_mode = mode; store.collection_name = "synthetic_v1"; store.client = client
    return store


def test_real_vector_admin_iterator_complete_safe_filter_and_close(vector_store_unit):
    identifier = 'DOC"\\\n or document_id != "'
    ids = [f"{i:064x}" for i in range(2501)]
    class Iterator:
        def __init__(self): self.offset = 0; self.closed = False
        def next(self):
            page = ids[self.offset:self.offset + 1000]; self.offset += 1000
            return [dict(id=i, child_id=i, document_id=identifier) for i in page]
        def close(self): self.closed = True
    iterator = Iterator()
    calls = []
    client = SimpleNamespace(query_iterator=lambda **kwargs: (calls.append(kwargs), iterator)[1])
    store = admin_store(vector_store_unit, client)
    assert store.list_document_child_ids(identifier) == ids and iterator.closed
    assert calls[0]["limit"] == -1 and calls[0]["consistency_level"] == "Strong"
    assert json.loads(calls[0]["filter"].split(" == ", 1)[1]) == identifier


@pytest.mark.parametrize("failure", ["rpc", "row"])
def test_real_vector_admin_closes_iterator_on_error(vector_store_unit, failure):
    class Iterator:
        closed = False
        def next(self):
            if failure == "rpc": raise RuntimeError("RPC failure")
            return [dict(id="a" * 64, child_id="a" * 64, document_id="OTHER")]
        def close(self): self.closed = True
    iterator = Iterator()
    store = admin_store(vector_store_unit, SimpleNamespace(query_iterator=lambda **k: iterator))
    with pytest.raises((RuntimeError, ValueError)):
        store.list_document_child_ids("DOC-1")
    assert iterator.closed


def test_real_vector_admin_delete_validates_whole_batch_and_batches_pk(vector_store_unit):
    calls = []
    store = admin_store(vector_store_unit, SimpleNamespace(delete=lambda **k: calls.append(k)))
    with pytest.raises(ValueError):
        store.delete_child_ids(["a" * 64, "malicious"])
    assert not calls
    ids = [f"{i:064x}" for i in range(2501)]
    store.delete_child_ids(ids)
    assert [len(c["ids"]) for c in calls] == [1000, 1000, 501]
    assert {i for c in calls for i in c["ids"]} == set(ids)


def test_real_vector_legacy_rejects_all_admin_paths(vector_store_unit):
    store = admin_store(vector_store_unit, SimpleNamespace(), mode="legacy")
    for call in (lambda: store.list_document_child_ids("DOC-1"), lambda: store.delete_child_ids([]),
                 lambda: store.verify_document_snapshot("DOC-1", [])):
        with pytest.raises(ValueError, match="Legacy"):
            call()


def test_single_file_entry_reuses_existing_processor(identity_processor, tmp_path):
    from test_manufacturing_metadata import front_file, valid
    module = identity_processor
    path = front_file(tmp_path, valid())
    single = module.process_document_file(path)
    directory = module.process_documents(tmp_path, metadata_mode="manufacturing")
    assert [d.metadata["id"] for d in single] == [d.metadata["id"] for d in directory]
    assert [d.page_content for d in single] == [d.page_content for d in directory]
    assert all(d.metadata["source_file"] == str(path.resolve()) for d in single)


def test_coordinator_wires_real_processor_and_vector_methods_with_stateful_client(
        identity_processor, vector_store_unit, tmp_path, monkeypatch):
    """Real coordinator/processor/row/admin methods; loaders, splitters and network are doubles."""
    class Client:
        def __init__(self): self.rows = {}; self.upserts = 0; self.deletes = 0
        def upsert(self, collection_name, data):
            self.upserts += 1
            self.rows.update({r["id"]: deepcopy(r) for r in data})
        def delete(self, collection_name, ids):
            self.deletes += 1
            for i in ids: self.rows.pop(i, None)
        def query_iterator(self, **kwargs):
            document_id = json.loads(kwargs["filter"].split(" == ", 1)[1])
            rows = [r for r in self.rows.values() if r["document_id"] == document_id]
            class Iterator:
                def next(self):
                    batch = rows[:]; rows.clear(); return batch
                def close(self): pass
            return Iterator()
    class Sparse:
        def __init__(self, count): self.count = count
        def tocsr(self): return self
        def __getitem__(self, key):
            assert 0 <= key[0][0] < self.count
            return SimpleNamespace(indices=[0], data=[1.0])
    embedding_calls = []
    def embedding(texts):
        embedding_calls.append(texts)
        return {"dense": [[1, 0, 0, 0] for t in texts], "sparse": Sparse(len(texts))}
    monkeypatch.setitem(sys.modules, "rag_qa.core.document_processor", identity_processor)
    client = Client()
    gateway = admin_store(vector_store_unit, client)
    gateway.dense_dim = 4; gateway.embedding_function = embedding
    path = source_file(tmp_path, body="A\n---P---\nB\n---P---\nC")
    with SQLiteManifestStore(tmp_path / "wired.db") as store:
        runner = VersionedIngestion(store, gateway, processing_contract=ProcessingContract(100, 0, 10, 0))
        assert runner.ingest_file(path).revision == 1
        assert runner.ingest_file(path).status == "SKIP_UNCHANGED"
        assert client.upserts == 1 and len(embedding_calls) == 1
        source_file(tmp_path, version="V2", body="A\n---P---\nB\n---P---\nD")
        assert runner.ingest_file(path).revision == 2
        assert {r["text"] for r in client.rows.values()} == {"A", "B", "D"}
        assert client.deletes == 1 and all(r["document_version"] == "V2" for r in client.rows.values())
        assert runner.delete_document("DOC-1").status == "DELETED" and not client.rows
