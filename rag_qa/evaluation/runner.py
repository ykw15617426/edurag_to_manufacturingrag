"""Safe CLI: prepare/preflight is offline; real evaluation requires STAGE12_LIVE=1."""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
from types import SimpleNamespace

from .benchmark import controlled_benchmark
from .schemas import EvaluationProfile, load_dataset, strict_json
from .provenance import environment_snapshot, git_sha, live_preflight, source_snapshot, write_report
from .evaluator import evaluate_retrieval, compare_direct_strategy

BENCHMARK = Path(__file__).parent / "benchmarks" / "controlled_synthetic_v1.json"


def checked_collection(name, production_names=()):
    if not isinstance(name, str) or not re.fullmatch(r"manufacturing_rag_eval_[a-zA-Z0-9_]{1,100}", name) or name in production_names:
        raise ValueError("explicit isolated evaluation collection required")
    return name


def not_run_report(dataset, profile, preflight, collection):
    return dict(metadata=dict(dataset_type=dataset.dataset_type, provenance_note=dataset.provenance_note,
        sample_count=len(dataset.samples), dataset_sha256=dataset.sha256(), knowledge_revision=None,
        git_sha=git_sha(), collection=collection, schema_version="manufacturing_v1", execution_mode="not_run",
        components={"BGE-M3": "NOT RUN", "Milvus": "NOT RUN", "CrossEncoder": "NOT RUN"},
        environment=environment_snapshot(), source_snapshot=source_snapshot(),
        model_snapshot=dict(embedding="local/bge-m3", reranker="local/bge-reranker-large", device="cpu", use_fp16=False), production_quality_claim=False,
        production_tuning="NOT AUTHORIZED BY DATA"),
        config_snapshot=profile.model_dump(mode="json"), retrieval_config_fingerprint=profile.fingerprint(),
        status="NOT RUN", preflight=preflight, aggregate_metrics=None, metrics_by_intent={}, metrics_by_tag={},
        fast_path_metrics=None, strategy_metrics=None, latency_metrics=None,
        ragas=dict(status="NOT RUN", reason="ragas_and_explicit_judges_unavailable"),
        per_sample_results=[dict(sample.model_dump(mode="json"), status="NOT RUN", metrics=None,
                                 returned_child_ids=None, returned_parent_ids=None, returned_document_ids=None)
                            for sample in dataset.samples])


class ControlledPlanner:
    """Controlled strategy exercise, never LLM Planner accuracy."""
    def plan(self, query, analysis):
        from rag_qa.query.rewrite import StrategyDecision
        if "分别" in query and analysis.entities.equipment_model:
            model = analysis.entities.equipment_model
            return StrategyDecision(strategy="subquery", subqueries=[f"设备型号 {model} 维护保养周期是什么？", f"设备型号 {model} 主轴转速参数是多少？"],
                        reason_code="controlled_subquery")
        return StrategyDecision(strategy="direct", reason_code="controlled_direct")


def provision_new_benchmark(vector_store, manifest_path, children):
    """New evaluation resources only; no drop, delete, clear, or existing DB adoption."""
    from rag_qa.ingestion.manifest_store import SQLiteManifestStore, ManifestRecord
    from rag_qa.ingestion.versioned_ingestion import metadata_sha256, canonical_sha256
    from rag_qa.core.milvus_schema import MANUFACTURING_SCHEMA_VERSION
    from base.config import config
    checked_collection(vector_store.collection_name, (config.MILVUS_COLLECTION_NAME, config.MILVUS_MANUFACTURING_COLLECTION_NAME))
    path = Path(manifest_path).resolve()
    if path == Path(config.MANUFACTURING_MANIFEST_DB_PATH).resolve(): raise ValueError("production manifest forbidden")
    if path.exists(): raise ValueError("new evaluation manifest path required")
    groups = {}
    for child in children: groups.setdefault(child.metadata["document_id"], []).append(child)
    with SQLiteManifestStore(path) as manifest:
        for docid, group in groups.items():
            vector_store.add_documents(group)
            ids = tuple(d.metadata["child_id"] for d in group)
            if not vector_store.verify_document_snapshot(docid, ids): raise ValueError("evaluation snapshot verification failed")
            metadata = group[0].metadata
            record = ManifestRecord(docid, metadata["document_version"], metadata["document_sha256"],
                metadata_sha256(metadata), canonical_sha256(dict(processor="controlled_synthetic_authored_segments_v1")),
                vector_store.collection_name, MANUFACTURING_SCHEMA_VERSION, metadata["source_file"], metadata["metadata_source"], ids)
            manifest.commit_snapshot(record, expected_revision=0)


def validate_live_labels(dataset, vector_store, manifest_path):
    """Labels must exist in the actual active snapshot, not just in JSON fixtures."""
    from rag_qa.ingestion.manifest_store import ManifestRecord
    from rag_qa.core.milvus_schema import MANUFACTURING_SCHEMA_VERSION
    path = Path(manifest_path).resolve()
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute("SELECT * FROM active_documents").fetchall()
    records = {}
    for row in rows:
        data = dict(row)
        count = data.pop("child_count")
        data["child_ids"] = tuple(json.loads(data["child_ids"]))
        record = ManifestRecord(**data)
        if (record.collection_name != vector_store.collection_name or record.storage_schema_version != MANUFACTURING_SCHEMA_VERSION
                or count != len(record.child_ids) or record.revision < 1): raise ValueError("evaluation manifest incompatible")
        actual = set(vector_store.list_document_child_ids(record.document_id))
        if actual != set(record.child_ids): raise ValueError("actual evaluation collection differs from manifest")
        records[record.document_id] = record
    for sample in dataset.samples:
        if not set(sample.expected_document_ids) <= set(records): raise ValueError("missing relevant documents")
        active_children = {cid for did in sample.expected_document_ids for cid in records[did].child_ids}
        if not set(sample.expected_child_ids) <= active_children: raise ValueError("missing relevant children")
        # Read actual parent IDs associated with labels; ground truth never inferred by similarity.
        rows = vector_store.client.query(collection_name=vector_store.collection_name,
            filter="child_id in " + json.dumps(list(sample.expected_child_ids)), output_fields=["parent_id"], limit=16384)
        if set(sample.expected_parent_ids) != {row["parent_id"] for row in rows}: raise ValueError("parent label snapshot mismatch")


def execute_live(dataset, profile, args):
    if os.getenv("STAGE12_LIVE") != "1": raise ValueError("STAGE12_LIVE=1 required")
    from base.config import config
    collection = checked_collection(args.collection, (config.MILVUS_COLLECTION_NAME, config.MILVUS_MANUFACTURING_COLLECTION_NAME))
    if not args.manifest: raise ValueError("explicit evaluation manifest required")
    manifest = Path(args.manifest).resolve()
    if manifest == Path(config.MANUFACTURING_MANIFEST_DB_PATH).resolve(): raise ValueError("production manifest forbidden")
    if args.mode != "direct" and profile.candidate_m != config.CANDIDATE_M:
        raise ValueError("Stage 9 paired/strategy evaluation requires current M; select --mode direct for M experiments")
    if not live_preflight()["ready"]: raise ValueError("live dependencies or weights missing")
    from pymilvus import MilvusClient
    with closing(MilvusClient(uri=f"http://{config.MILVUS_HOST}:{config.MILVUS_PORT}", db_name=config.MILVUS_DATABASE_NAME)) as probe:
        exists = probe.has_collection(collection_name=collection)
    if args.provision and (exists or manifest.exists()): raise ValueError("provision requires absent evaluation collection and manifest")
    if not args.provision and (not exists or not manifest.is_file()): raise ValueError("existing evaluation resources required")
    baseline, children, corpus = controlled_benchmark()
    if args.provision and dataset.sha256() != baseline.sha256(): raise ValueError("provision only supports fixed controlled benchmark")
    # Profile is scoped to this VectorStore, not production config.ini/global config.
    from rag_qa.core.vector_store import VectorStore
    from rag_qa.query import QueryAnalyzer
    from rag_qa.api.runtime import KnowledgeRevisionProvider
    from .adapters import ComponentEvaluationAdapter
    vector = VectorStore(schema_mode="manufacturing", collection_name=collection, retrieval_settings=profile.retrieval_settings())
    llm = None
    try:
        if args.provision: provision_new_benchmark(vector, manifest, children)
        validate_live_labels(dataset, vector, manifest)
        if args.fast_path_snapshot:
            from rag_qa.retrieval.fast_path import FastPathCorpus
            snapshot = Path(args.fast_path_snapshot).read_bytes()
            corpus = FastPathCorpus.from_json(snapshot.decode("utf-8"))
        elif dataset.sha256() == baseline.sha256():
            snapshot = corpus.to_json().encode("utf-8")
        else: corpus, snapshot = None, None
        revision_provider = KnowledgeRevisionProvider(manifest, collection, snapshot)
        revision = revision_provider()
        planner = None
        if args.planner == "scripted": planner = ControlledPlanner()
        if args.planner == "llm":
            from openai import OpenAI
            from rag_qa.api.runtime import OpenAICompletionAdapter, OpenAIManufacturingStrategyPlanner
            llm = OpenAI(api_key=config.DASHSCOPE_API_KEY, base_url=config.DASHSCOPE_BASE_URL,
                         timeout=config.MANUFACTURING_LLM_TIMEOUT_SECONDS, max_retries=0)
            planner = OpenAIManufacturingStrategyPlanner(OpenAICompletionAdapter(llm, config.LLM_MODEL, config.MANUFACTURING_LLM_TIMEOUT_SECONDS))
        metadata = dict(execution_mode="real_components", git_sha=git_sha(), source_snapshot=source_snapshot(), knowledge_revision=revision,
            collection=collection, schema_version="manufacturing_v1", environment=environment_snapshot(),
            components={"BGE-M3": "REAL", "Milvus": "REAL", "CrossEncoder": "REAL"},
            model_snapshot=dict(embedding="local/bge-m3", reranker="local/bge-reranker-large", device="cpu", use_fp16=False),
            analyzer_type="Stage5_rules_fallback", planner_type="LLM_planner" if llm else "controlled_strategy_test" if planner else "none",
            planner_model=config.LLM_MODEL if llm else None,
            fast_path_snapshot_sha256=hashlib.sha256(snapshot).hexdigest() if snapshot else None)
        analyzer = QueryAnalyzer()
        direct = (evaluate_retrieval(dataset, ComponentEvaluationAdapter(vector, analyzer, profile), profile=profile, metadata=dict(metadata, mode="direct"))
                  if args.mode in {"direct", "paired"} else None)
        strategy = (evaluate_retrieval(dataset, ComponentEvaluationAdapter(vector, analyzer, profile, mode="strategy", planner=planner, corpus=corpus),
                                      profile=profile, metadata=dict(metadata, mode="strategy")) if args.mode in {"strategy", "paired"} else None)
        if revision_provider() != revision: raise ValueError("knowledge changed during paired evaluation")
        if args.mode != "paired":
            report = direct if direct is not None else strategy
            report["status"] = "PARTIAL" if report["aggregate_metrics"]["error_count"] else "PASS"
            return report
        failed = direct["aggregate_metrics"]["error_count"] + strategy["aggregate_metrics"]["error_count"]
        return dict(status="PARTIAL" if failed else "PASS", metadata=metadata, direct=direct, strategy=strategy,
                    comparison=compare_direct_strategy(direct, strategy))
    finally:
        try: vector.client.close()
        finally:
            if llm is not None: llm.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true", help="write fixed canonical synthetic dataset, offline")
    parser.add_argument("--dataset", default=str(BENCHMARK))
    parser.add_argument("--output", default=".venv/stage12-evaluation/evaluation_results.json")
    parser.add_argument("--profile")
    parser.add_argument("--collection", default="manufacturing_rag_eval_v1")
    parser.add_argument("--manifest")
    parser.add_argument("--fast-path-snapshot")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--provision", action="store_true", help="create absent isolated eval resources; never clean them automatically")
    parser.add_argument("--planner", choices=("none", "scripted", "llm"), default="none")
    parser.add_argument("--mode", choices=("paired", "direct", "strategy"), default="paired")
    args = parser.parse_args(argv)
    if args.prepare:
        dataset, _, _ = controlled_benchmark()
        if args.live or args.provision: parser.error("prepare is offline only")
        path = Path(args.dataset)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dataset.canonical_json() + "\n", encoding="utf-8")
        print(json.dumps(dict(dataset_type=dataset.dataset_type, sample_count=len(dataset.samples), dataset_sha256=dataset.sha256())))
        return 0
    dataset = load_dataset(args.dataset)
    profile = EvaluationProfile.model_validate(strict_json(Path(args.profile).read_text(encoding="utf-8"))) if args.profile else EvaluationProfile()
    checked_collection(args.collection)
    preflight = live_preflight()
    report = not_run_report(dataset, profile, preflight, args.collection)
    if args.live:
        try: report = execute_live(dataset, profile, args)
        except Exception as exc:
            report["status"] = "PARTIAL"
            report["live_failure"] = type(exc).__name__  # never emit dependency exception secrets
    elif args.provision: parser.error("provision requires live opt-in")
    write_report(args.output, report)
    print(json.dumps(dict(status=report["status"], output=str(Path(args.output)), dataset_sha256=dataset.sha256())))
    return 0 if report["status"] in {"PASS", "NOT RUN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
