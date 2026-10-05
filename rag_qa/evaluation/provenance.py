"""Nonsecret environment provenance and deterministic artifact output."""
import importlib.metadata
import importlib.util
import json
import platform
from pathlib import Path
import subprocess


def git_sha():
    root = Path(__file__).resolve().parents[2]
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def environment_snapshot():
    names = ("pymilvus", "milvus-model", "sentence-transformers", "FlagEmbedding", "torch", "ragas")
    versions = {}
    for name in names:
        try: versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: versions[name] = None
    return dict(python=platform.python_version(), platform=platform.platform(), packages=versions)


def source_snapshot():
    """Record actual source bytes when measuring a dirty checkout, not just HEAD."""
    import hashlib
    root = Path(__file__).resolve().parents[2]
    files = sorted((root / "rag_qa/evaluation").glob("*.py")) + [root / name for name in (
        "rag_qa/retrieval/settings.py", "rag_qa/core/vector_store.py", "rag_qa/api/cache.py", "rag_qa/api/service.py", "rag_qa/api/runtime.py")]
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode("utf-8") + b"\0" + path.read_bytes() + b"\0")
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=normal"], cwd=root, text=True).strip())
    return dict(source_tree_dirty=dirty, evaluated_code_sha256=digest.hexdigest())


def live_preflight():
    missing = [n for n in ("milvus_model", "sentence_transformers", "torch", "langchain_core", "pymilvus")
               if importlib.util.find_spec(n) is None]
    from base.config import config
    models = {name: (Path(config.MODELS_DIR) / name / "pytorch_model.bin").is_file()
              for name in ("bge-m3", "bge-reranker-large")}
    return dict(ready=not missing and all(models.values()), missing_dependencies=missing, model_weights_present=models,
                service_connectivity="NOT RUN")


def write_report(path, report):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Refuse NaN: optional failed metrics are null, never invented valid scores.
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
