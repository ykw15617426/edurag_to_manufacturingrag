# Stage 6 — Metadata Filter + Hybrid Retrieval

2026-10-02。开始 main / `545124c9acb7b2918b4c424a5de4af16cd9a2156`，初始 Working Tree clean；fetch 后 HEAD == origin/main。用户授权范围仅 Stage 6。

Implementation: PASS。Validation: PASS。GitHub Sync: PENDING。Overall Status: IN PROGRESS。Full Integration Readiness: NO。

## Changes and source scope

- 新增 `rag_qa/retrieval/{__init__,filters,manufacturing_retriever}.py`：固定字段/安全表达式、immutable plan、STRICT/RELAXED/NONE、最多两次 soft-only 放宽，原 query/k 保留，general 不绕检索。
- 扩展 `rag_qa/core/vector_store.py`：manufacturing-only child search；同表达式两路 ANN、IP/nprobe10、WeightedRanker 0.8/0.3，完整 scalar Metadata 和原始 retrieval_score；原方法保留。
- 新增 `tests/test_manufacturing_metadata_filters.py`、`tests/test_manufacturing_retrieval.py`，复用现有 Stage 3 recording fixture 隔离重依赖，执行真实新方法。
- 新增 [检索合约](../MANUFACTURING_RETRIEVAL.md) 和本报告；最小更新 AGENTS、PLANS、README、文档索引、当前架构与迁移计划。

不修改 Stage 2 stable IDs、Stage 3 Schema、Stage 4 Manifest/版本摄取、Stage 5 QueryAnalysis contract；Legacy 分类、策略、检索方法与在线 new_rag_system 保留。未修改历史报告、Legacy Inventory、依赖、配置、旧数据或模型；没有 Parent 聚合/Reranker 改造、BM25、Rewrite 或 Generation。

## Tests

Windows / Python 3.13.9，沿用 ignored `.venv/stage1-validation` 的 Pydantic 2.12.5 / pytest 8.4.2 / PyMilvus 2.5.4；无新增安装或模型下载。Synthetic/fake 只验证控制与参数，不证明 Live Milvus。

| Command | Result | Scope |
| --- | --- | --- |
| `.venv/stage1-validation/Scripts/python.exe -m pytest tests/test_manufacturing_metadata_filters.py tests/test_manufacturing_retrieval.py -q -rs` | 首轮 62 passed / 0 failed / 0 skipped | 初始 Stage 6 core；后续增加 3 项联动/Legacy 验证 |
| `.venv/stage1-validation/Scripts/python.exe -m pytest tests/test_manufacturing_metadata_filters.py tests/test_manufacturing_retrieval.py tests/test_manufacturing_query_analysis.py tests/test_manifest_store.py tests/test_versioned_ingestion.py tests/test_manufacturing_milvus_schema.py tests/test_manufacturing_fingerprints.py tests/test_manufacturing_metadata.py tests/test_stage0_smoke.py -q -rs` | 465 passed / 0 failed / 12 skipped | Stage 6 65/0；Stage 0–5 400/12，保留所有历史跳过原因 |

覆盖 hard/soft/none、高中低 confidence、意图多类型映射、fault_symptom 不过滤、原 Stage 5 报警/润滑/多型号输入、安全 literal 与白名单、immutable plan、warnings/放宽原因、strict→hard-only、soft-only→NONE、hard 零召回不删除、NONE 不重复、general 必须检索、异常不放宽。Recording client 检查 Dense/Sparse 相同 expr、IP/nprobe/权重/k、全部 scalar 输出、负数/大于1原始 score、同 Parent 多 Child 不合并、缺 Metadata/PK 冲突失败、manufacturing-only/raw expression 拒绝；联动执行 Retriever + 真实 VectorStore 新方法；旧方法父聚合与 CrossEncoder 路径仍可执行。真实 SDK 离线 AnnSearchRequest/WeightedRanker 对象测试通过。

12 skipped：Stage 3 live 开关未启用 1；Stage 1/2 真实 Loader/分块各 1；Smoke 缺完整模型/API/应用/数据库依赖 9。Stage 6 Live Milvus: NOT RUN；STAGE6_LIVE_MILVUS 未启用，未提供或宣称执行 live harness。真实 BGE/Reranker、真实语义服务、在线/答案/端到端业务评估: NOT RUN。未连接/修改真实 edurag 或 manufacturing_rag_v1 集合。

`git diff --check`: PASS。6 个新增/修改 Python 文件 ast.parse(feature_version=(3,10)) 与 compile: PASS（3.10 仅语法，实际运行 3.13）。8 个变更/新增 Markdown 相对链接: PASS。原 VectorStore 全部 11 个方法 AST 与开始 HEAD 完全一致: PASS；Stage 2–5 合约、Legacy/配置/数据/历史报告的变更范围保留检查 PASS。独立进程导入新 retrieval package 未导入 SDK/模型/Legacy/config: PASS。Git 发布后回写实际证据。

## Limits and deferred work

品牌/设备类型没有企业别名词典，精确 soft 值可能零召回；低信任直接 hard-only，soft 放宽后保留原 query 向量信号。Hard 误识别仍可得到空，不允许悄悄去掉型号/报警/备件号。两次尝试目前分别 embedding，未做缓存优化。查询分析与 query 的对应由调用方保证，合约不新增 query 字段。严格请求所有 scalar，服务端若返回缺字段则报错；真实 parser/NULL/ANN 行为尚未验证。

新入口复用已有 VectorStore，其 constructor 仍初始化 CrossEncoder；child 方法不调用重排。在线仍 Legacy，Stage 7 Parent Aggregation/Reranker、Stage 8 BM25、Stage 9 Rewrite/Strategy、Stage 10 Generation 未实施；Stage 7–13 PENDING，Full Integration Readiness: NO。

## Git and handoff

Commit message: `feat: add manufacturing filtered retrieval`。限定本阶段文件；Commit / Push / Remote Verification / Working Tree 检查待完成。最终 SHA 在回复提供，不预写报告自身哈希。

Stage 7 Readiness: YES（限定已保留 Child Metadata、parent_id/parent_content 与排序信号的设计输入）。不是 Stage 7 实施授权；Stage 6 发布核验后停止。
