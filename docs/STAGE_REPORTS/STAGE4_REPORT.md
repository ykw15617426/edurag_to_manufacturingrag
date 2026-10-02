# Stage 4 — Versioned Ingestion + Incremental Upsert + Delta Delete

## Status

2026-10-02。Implementation: PASS；Validation: PASS（限实测范围）；Stage 4: PASS。Stage 0–3 / Governance: PASS；Stage 5–13: PENDING；Full Integration Readiness: NO。

## Repository Baseline

Repository: https://github.com/ykw15617426/edurag_to_manufacturingrag；Branch: main。
Stage Start HEAD: `0cc3a855653ef20564c089f919517bc1514219d8`。初始工作区 clean，fetch 后 HEAD == origin/main。已读取治理/计划/索引、用户列出的 Stage 1–3 合约与报告、Processor/VectorStore/Schema/Metadata Loader/Fingerprints 真实代码及配置和测试。

## Implemented

Persistent Version Manifest: IMPLEMENTED。
Cross-run Unchanged Skip: IMPLEMENTED。
Metadata Fingerprint: IMPLEMENTED。
Processing Signature: IMPLEMENTED。
Version Transition: IMPLEMENTED。
Incremental Diff: IMPLEMENTED。
Delta Delete: IMPLEMENTED。
Stale Child Cleanup: IMPLEMENTED。
Explicit Document Delete: IMPLEMENTED。
Retry / Recovery: IMPLEMENTED。

以上是代码与自动化控制验证，不表示已写入真实 Milvus。正式合约/字段/调用与限制见 [MANUFACTURING_VERSIONED_INGESTION.md](../MANUFACTURING_VERSIONED_INGESTION.md)。

## Manifest

SQLiteManifestStore、独立 manifest_v1、唯一 document_id active record、opaque active version、两个输入 Hash、processing signature、集合/Schema、provenance、排序 Child JSON/count、revision 与 UTC updated_at。临时 SQLite 实际提交并 reopen 验证；首次 revision=1，成功更新递增，Skip 不修改 revision/time。SQL 参数化、短事务和 revision CAS；陌生/不兼容 DB 失败，不自动修复。仅单 worker / 单 writer，OCR/模型/网络期间无 SQLite 写事务。

配置新增 MANUFACTURING_MANIFEST_DB_PATH / `[ingestion] manufacturing_manifest_db_path`，默认 ignored runtime。没有创建生产 Manifest、修改 config.ini、安装依赖、下载模型或启动容器。

## Fingerprints and Version Policy

业务字段由 Stage 1 模型/to_metadata 归一化后 canonical JSON SHA256，排除 runtime/provenance/Child IDs。sidecar key order 不变 Hash，业务变更会改变。signature 包含显式 processing/fingerprint 版本、实际 Parent/Child size/overlap 与 storage schema，不 Hash 源码、不修改 Stage 2 指纹算法。

document_version 不转数字、不比较大小。同版本 source/Metadata 变更先报冲突；仅 signature 变可 REINDEX；不同版本即使 IDs 不变也 Upsert 全 desired 刷新 scalar。Active 版本只在最终 Manifest 成功提交后生效。

## Skip, Diff and Administrative Methods

Skip 先核对 Manifest 兼容、版本/Hash/signature、实际 Milvus IDs 精确相等，再确认输入静止；Processor/Embedding/Upsert/Delete 零调用。缺失或额外实际 Rows 走 RECONCILE，不能仅凭 Manifest 跳过。

实际集合决定 added/retained/removed。所有 desired Upsert → 查询确认 desired 存在 → 删除实际 removed → 最终 IDs 相等 → Commit Manifest。pymilvus 2.5.4 的本地真实 SDK query_iterator/UNLIMITED/close API 已核对；适配器采用无限总量分页、Strong、安全 JSON filter、finally close、完整 batch PK 校验及分批 delete。Legacy 拒绝管理/删除路径；不增加在线检索过滤能力。

## Failure Recovery and Explicit Delete

测试真实观察部分 Upsert 后旧 C 仍在且 Manifest 不推进；部分 Delete 后旧 Manifest 保持，重试仅删除实际余留 stale；SQLite trigger 注入实际提交失败，Milvus 合成快照已正确但控制面仍旧，移除 trigger 后重试收敛。最终存在性/精确集合查询失败同样禁止提交。不是跨系统 ACID，不回滚已经写入的 Rows。

显式 delete_document 按实际 PK 清理、验证 empty 后才删 Manifest；实际数据已空而 Manifest delete 失败也可重试，第二次成功删除后返回 NOOP。其他业务文档 Rows/Manifest 保持。目录先全量 Metadata/ID 预检，duplicate 在首个 mutation 前失败；忽略 sidecar、不自动 prune、目录 batch 不原子。

## Legacy / Existing Contracts

Stage 2 原文件/内容 Hash、稳定 Parent/Child ID 算法未修改。Stage 3 Manufacturing Schema/Row Mapping、Legacy Schema、PK、索引、retrieval weights、nprobe 和切分 defaults 未修改。Processor 原切分体抽为共享 helper，新增单文件 manufacturing 入口，目录/Legacy 仍复用原逻辑。回归与单文件/目录 ID 一致测试通过。

## Changed Files

共 17 文件：

- 新控制代码：`rag_qa/ingestion/manifest_store.py`、`rag_qa/ingestion/versioned_ingestion.py`。
- 现有入口：`rag_qa/core/document_processor.py`、`rag_qa/core/vector_store.py`。
- 配置/忽略：`base/config.py`、`config.example.ini`、`.gitignore`。
- 新测试：`tests/test_manifest_store.py`、`tests/test_versioned_ingestion.py`。
- 新正式文档：`docs/MANUFACTURING_VERSIONED_INGESTION.md`、本报告。
- 增量治理/导航：`AGENTS.md`、`.agent/PLANS.md`、`README.md`、`docs/README.md`、`docs/CURRENT_ARCHITECTURE.md`、`docs/MANUFACTURING_MIGRATION_PLAN.md`。

Stage 0–3 报告、Legacy Inventory、Stage 1 business schema/loader、Stage 2 fingerprints、Stage 3 milvus_schema、requirements、Compose、旧数据、模型、本地配置/凭据未修改。

## Tests

Windows / Python 3.13.9，沿用 Git 忽略的 `.venv/stage1-validation`（已有 Pydantic 2.12.5 / PyYAML 6.0.3 / pytest 8.4.2 / pymilvus 2.5.4）。未为 Stage 4 安装依赖。

| Command | Result | Scope |
| --- | --- | --- |
| `.venv/stage1-validation/Scripts/python.exe -m pytest tests/test_manifest_store.py tests/test_versioned_ingestion.py -q --tb=short` | 56 passed / 0 failed | 真实临时 SQLite、业务解析/指纹、状态网关、适配器/Processor 控制接线 |
| `.venv/stage1-validation/Scripts/python.exe -m pytest tests/test_manifest_store.py tests/test_versioned_ingestion.py tests/test_manufacturing_milvus_schema.py tests/test_manufacturing_fingerprints.py tests/test_manufacturing_metadata.py tests/test_stage0_smoke.py -q -rs` | 300 passed / 0 failed / 12 skipped | Stage 4 56/0；Stage 3 103/1；Stage 2 34/1；Stage 1 100/1；Smoke 7/9 |
| `python -m pytest tests/test_manifest_store.py tests/test_versioned_ingestion.py -q -rs` | NOT RUN | 当前默认 Python 为 hermes 环境，缺 pytest；使用上方已有验证 venv，不安装全局依赖 |
| 下述 import blocker 脚本，经 `.venv/stage1-validation/Scripts/python.exe -` 执行 | 56 passed / 0 failed | 阻断真实 SDK/模型/数据库/Loader 依赖后核心仍通过；保留 Pydantic/PyYAML/pytest，适配器 fixture 使用替身 |

阻断脚本（本次已执行）：

```python
import importlib.abc
import sys
class NoRuntimeDependencies(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'pymilvus','milvus_model','sentence_transformers','langchain_core','langchain_community','langchain_text_splitters','torch','redis','pymysql'}:
            raise ModuleNotFoundError('Stage 4 core verification blocks runtime dependency: ' + fullname)
sys.meta_path.insert(0, NoRuntimeDependencies())
import pytest
raise SystemExit(pytest.main(['tests/test_manifest_store.py','tests/test_versioned_ingestion.py','-q','-rs']))
```

12 skipped：Stage 3 opt-in Live Milvus 1；真实 Stage 1/2 Loader/分块各 1；Smoke 缺应用/模型/数据库依赖 9。Stage 4 没有对真实服务执行摄取/删除；Live Milvus/OCR/BGE: NOT RUN。核心不需服务器/模型；SDK 离线 PASS 属于保留的 Stage 3 验证，不是 Stage 4 Live PASS。

自动化场景含：Manifest reopen/唯一 active/revision CAS、跨运行 exact skip、opaque version 与 retained scalar 刷新、同版本 source/Metadata 冲突、signature reindex、sidecar bump、缺块恢复、无 Manifest orphan 收敛、A/B/C → A/B/D 且 C absent、部分失败和 SQL trigger、输入在处理期间改变/失效、其他文档隔离、显式 delete 幂等/失败重试、目录重复/no prune、2501 IDs 完整读取/安全编码/close/分批删除、Legacy 拒绝管理、共享 Processor 接线。Fake 只证明控制逻辑/合成状态，不证明 RPC 或实际模型质量。

`git diff --check`: PASS。7 个变更/新增 Python 文件 ast.parse(feature_version=(3,10)) 与 compile: PASS（Python 3.13 实际执行，3.10 只验证语法）。8 个变更/新增 Markdown 的相对链接: PASS。脚本比较 HEAD 原文件与当前内容，确认 business Schema/Metadata Loader/Fingerprints/Milvus Schema/requirements/Compose 不变；Processor 原切分体从 parent_splitter 初始化到原文件末尾原样保留: PASS。`git diff --cached --check`: PASS（含所有新增文件）；17 文件范围审阅完成，runtime DB 忽略检查 PASS。

## Known Risks

- 只支持调用方串行单 worker；SQLite CAS 不是分布式数据面锁。不具备 SQLite + Milvus 分布式 ACID。
- 摄取期间在线查询可见混合/部分快照；active Manifest 最后推进，不提供在线版本过滤或历史自动 rollback。
- 真实服务器 Strong iterator/upsert/delete、OCR/BGE 与全量应用依赖未验证；Python 3.10 runtime 未验证。
- 输入双校验不是文件系统锁，ABA 或最终校验后的写入仍需业务侧静止源文件。
- Skip 核对 IDs，不审计既有 scalar/向量内容；模型/OCR资产变更需显式 bump processing contract。
- 一个 Manifest DB 固定绑定同一 endpoint/database/collection，运行 DB 需持久化；路径移动不触发完全未变快照的 provenance 刷新。
- 空 Processor 快照失败，须显式删除；目录不自动 prune，不保证全 batch 原子。大批量 Upsert/模型吞吐尚未验收。

## Deferred

Distributed Multi-worker Ingestion: NOT IMPLEMENTED。
Intent Recognition / Entity Extraction: NOT IMPLEMENTED — Stage 5。
Metadata Retrieval Filter: NOT IMPLEMENTED — Stage 6。
Parent Aggregation、BM25、SSE、Evaluation 及历史版本 rollback 未实施。
Full Integration Readiness: NO。

## Git

Commit / Push / Remote Verification: PASS。消息：`feat: add versioned incremental ingestion`。仅暂存本任务 17 文件，已 Commit/Push/fetch 并核对 HEAD == origin/main 与 Working Tree clean；最终状态回写并入刚创建的本阶段提交，再做远端/clean 核验，最终 SHA 在用户回复提供，不预写本报告自身哈希。Last Completed Stage: Stage 4 — PASS；Active Stage: NONE；Stage 5–13: PENDING。

## Stage 5 Readiness

YES（限定已版本化知识快照的查询分析设计）；不是完整集成 PASS 或实施授权。Stage 5–13 PENDING；完成 Stage 4 发布核验后停止。
