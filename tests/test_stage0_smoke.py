"""Stage 0 smoke checks. Missing optional runtime dependencies are explicit skips.

No fake models or databases are substituted. Live app import is opt-in because
the existing module creates clients, loads models and writes a MySQL table.
"""
import importlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture
def clean_environment(monkeypatch):
    prefixes = ("MYSQL_", "REDIS_", "MILVUS_", "DASHSCOPE_", "LLM_",
                "PARENT_", "CHILD_", "RETRIEVAL_", "CANDIDATE_")
    for key in list(os.environ):
        if key.startswith(prefixes) or key in {"VALID_SOURCES", "CUSTOMER_SERVICE_PHONE"}:
            monkeypatch.delenv(key)


def config_from_example():
    from base.config import Config
    return Config(str(ROOT / "config.example.ini"))


def test_config_example_reads(clean_environment):
    cfg = config_from_example()
    assert (cfg.PARENT_CHUNK_SIZE, cfg.CHILD_CHUNK_SIZE) == (512, 128)
    assert (cfg.PARENT_CHUNK_OVERLAP, cfg.CHILD_CHUNK_OVERLAP) == (120, 30)
    assert cfg.RETRIEVAL_K == 5 and cfg.CANDIDATE_M == 2
    assert cfg.DASHSCOPE_API_KEY == ""
    assert cfg.VALID_SOURCES == ["ai", "java", "test", "ops", "bigdata"]


def test_config_blank_redis_password(clean_environment):
    assert config_from_example().REDIS_PASSWORD == ""


def test_config_nonnumeric_redis_password(clean_environment, tmp_path):
    from base.config import Config
    path = tmp_path / "config.ini"
    path.write_text("[redis]\npassword = smoke-password\n", encoding="utf-8")
    assert Config(str(path)).REDIS_PASSWORD == "smoke-password"


def test_config_environment_overrides(clean_environment, monkeypatch):
    monkeypatch.setenv("PARENT_CHUNK_SIZE", "768")
    monkeypatch.setenv("REDIS_PASSWORD", "env-smoke-password")
    monkeypatch.setenv("VALID_SOURCES", '["smoke"]')
    cfg = config_from_example()
    assert cfg.PARENT_CHUNK_SIZE == 768
    assert cfg.REDIS_PASSWORD == "env-smoke-password"
    assert cfg.VALID_SOURCES == ["smoke"]


def test_config_sources_reject_executable_expression(clean_environment, monkeypatch):
    monkeypatch.setenv("VALID_SOURCES", "__import__('os').getcwd()")
    with pytest.raises((ValueError, SyntaxError)):
        config_from_example()


def test_config_fallbacks_without_local_file(clean_environment, tmp_path):
    from base.config import Config
    cfg = Config(str(tmp_path / "missing.ini"))
    assert cfg.DASHSCOPE_API_KEY == ""
    assert (cfg.PARENT_CHUNK_SIZE, cfg.CHILD_CHUNK_SIZE) == (1000, 200)
    assert isinstance(cfg.REDIS_PASSWORD, str)


def require_modules(names):
    missing = [name for name in names if importlib.util.find_spec(name) is None]
    if missing:
        pytest.skip("Missing dependencies: " + ", ".join(missing))


def import_real_module(name):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:
        # Internal path mistakes must fail rather than be hidden as skips.
        internal = {"base", "rag_qa", "mysql_qa", "core", "db", "cache", "retrieval"}
        if (exc.name or "").split(".")[0] in internal:
            raise
        pytest.skip("Missing transitive dependency: " + str(exc.name))


@pytest.mark.parametrize("module,symbol,dependencies", [
    ("rag_qa.core.document_processor", "process_documents",
     ["langchain_core", "langchain_community", "langchain_text_splitters", "docx", "pptx", "fitz", "cv2"]),
    ("rag_qa.core.vector_store", "VectorStore",
     ["milvus_model", "pymilvus", "sentence_transformers", "langchain_core"]),
    ("rag_qa.core.new_rag_system", "RAGSystem",
     ["langchain_core", "transformers", "torch", "openai", "sklearn"]),
    ("rag_qa.core.rag_system", "RAGSystem",
     ["langchain_core", "transformers", "torch", "openai", "sklearn"]),
    ("rag_qa.rag_main", "main",
     ["langchain_core", "langchain_community", "langchain_text_splitters", "milvus_model",
      "pymilvus", "sentence_transformers", "transformers", "docx", "pptx", "fitz", "cv2"]),
    ("mysql_qa.sql_main", "MySQLQASystem", ["pymysql", "pandas", "redis", "rank_bm25", "jieba"]),
    ("new_main", "IntegratedQASystem", ["pymysql", "redis", "rank_bm25", "jieba", "milvus_model",
                                         "pymilvus", "sentence_transformers", "langchain_core", "transformers"]),
])
def test_core_import(module, symbol, dependencies):
    require_modules(dependencies)
    assert callable(getattr(import_real_module(module), symbol))


def test_document_processor_initialization_and_text_pipeline(tmp_path):
    require_modules(["langchain_core", "langchain_community", "langchain_text_splitters",
                     "docx", "pptx", "fitz", "cv2"])
    processor = import_real_module("rag_qa.core.document_processor")
    # The processor is a module with functions, not a DocumentProcessor class.
    splitter = processor.ChineseRecursiveTextSplitter(chunk_size=64, chunk_overlap=8)
    assert splitter.split_text("设备运行正常。请按计划检查。")
    path = tmp_path / "smoke.txt"
    path.write_text("设备运行正常。请按计划检查。", encoding="utf-8")
    loader = processor.document_loaders[".txt"](str(path), encoding="utf-8")
    assert loader.load()[0].page_content
    chunks = processor.process_documents(str(tmp_path), 64, 32, 8, 4)
    assert chunks and all(c.metadata["parent_content"] for c in chunks)
    assert all(c.metadata["parent_id"] and c.metadata["id"] for c in chunks)


def test_fastapi_app_import():
    require_modules(["fastapi", "pymysql", "redis", "rank_bm25", "jieba", "milvus_model",
                     "pymilvus", "sentence_transformers", "langchain_core", "transformers"])
    if os.getenv("STAGE0_LIVE_SMOKE") != "1":
        pytest.skip("Live app import requires STAGE0_LIVE_SMOKE=1, provisioned models, "
                    "MySQL/Redis/Milvus, existing jpkb table, and configured API key")
    completed = subprocess.run(
        [sys.executable, "-c", "from app import app; assert callable(app); "
         "assert any(getattr(r, 'path', '') == '/api/query' for r in app.routes)"],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    # Raw output can contain user queries/configuration; do not print it.
    assert completed.returncode == 0, "Real app import failed; inspect local runtime configuration"


def test_project_python_sources_compile():
    paths = list(ROOT.glob("*.py"))
    for folder in ("base", "rag_qa/core", "rag_qa/edu_document_loaders", "rag_qa/edu_text_spliter",
                   "mysql_qa", "tests"):
        paths.extend((ROOT / folder).rglob("*.py"))
    paths.append(ROOT / "rag_qa/rag_main.py")
    for path in paths:
        compile(path.read_text(encoding="utf-8-sig"), str(path), "exec")
