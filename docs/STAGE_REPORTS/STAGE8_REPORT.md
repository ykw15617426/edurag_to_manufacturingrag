# Stage 8 — Alarm Code / FAQ / BM25 Fast Path

2026-10-02。main / 起始 `13dfecfc2d773f7445c1ad0cd1794d5d881dbfd8`；Working Tree clean，fetch后HEAD == origin/main。只执行当前授权Stage 8。

Implementation: PASS。Validation: PASS。GitHub Sync: PASS。Overall Status: PASS。Full Integration Readiness: NO。

## Changes and scope

- 新增 `rag_qa/retrieval/fast_path.py`：strict approved FastPathEntry/Corpus、canonical JSON snapshot、Exact Alarm/FAQ、歧义/未确认code拒绝短路、结构化Evidence结果、runtime error回退Stage 7。
- 新增 `manufacturing_bm25.py`：标识符保护tokenizer、真实BM25Okapi raw ranking、hard范围预筛、corpus/rank统计、显式可注入acceptance policy；默认不短路。
- 包 `__init__.py` 仅增量导出Stage 8类型；新增两个核心测试文件；[快路径合约](../MANUFACTURING_FAST_PATH.md)、本报告及治理/架构/导航最小更新。

Legacy `mysql_qa/retrieval/bm25_search.py`、preprocess、Redis/MySQL clients、new_main.py、new_rag_system.py保留。Stage 6 filters、Stage 7 Parent retrieval/aggregation/reranker、VectorStore、Stage 2–5合约与所有历史报告、配置/依赖文件、旧数据/模型不改；无生产表或教育jpkb迁移，无Stage 9+实现。

## Validation

Windows / Python3.13.9，沿用ignored `.venv/stage1-validation`。执行 `.venv/stage1-validation/Scripts/python.exe -m pip install --no-deps rank-bm25==0.2.2`：PASS；仅验证venv安装项目requirements已锁定版本，复用已存在NumPy，未改依赖声明、未安装完整运行栈或下载模型。

| Command | Result | Scope |
| --- | --- | --- |
| `.venv/stage1-validation/Scripts/python.exe -m pytest tests/test_manufacturing_bm25.py tests/test_manufacturing_fast_path.py -q -rs` | 首轮59 passed / 0 failed / 0 skipped | Stage 8核心；随后增加3项低信任hard/默认k/policy输出保护 |
| `.venv/stage1-validation/Scripts/python.exe -m pytest tests/test_manufacturing_bm25.py tests/test_manufacturing_fast_path.py tests/test_parent_aggregation.py tests/test_manufacturing_parent_retrieval.py tests/test_manufacturing_metadata_filters.py tests/test_manufacturing_retrieval.py tests/test_manufacturing_query_analysis.py tests/test_manifest_store.py tests/test_versioned_ingestion.py tests/test_manufacturing_milvus_schema.py tests/test_manufacturing_fingerprints.py tests/test_manufacturing_metadata.py tests/test_stage0_smoke.py -q -rs` | 606 passed / 0 failed / 12 skipped | Stage 8 62/0；Stage 0–7 544/12，全部通过范围保持 |
| `.venv/stage1-validation/Scripts/python.exe -m pytest tests/test_manufacturing_bm25.py::test_expansion_records_real_scores_and_scope -q -s` | 1 passed | 真实raw score/rank/size扩容记录，不要求分数不变 |

扩容 synthetic 2→202条：目标raw score **0.0→34.081873562810806**，rank **1→1**，hard-compatible scope **1→1**。Exact Alarm/Exact FAQ另外各验证200条无关FAQ扩容，决策/证据不变。不是生产业务效果指标，不能拿raw score当置信度。

覆盖大小写/-/_/前导零、NFC/whitespace精确匹配、同码异型号不得跨设备短路、单一批准含义/多条FAQ歧义、Stage 5未确认code保护、所有hard范围/低confidence保留、真实库raw score一致且无softmax、默认policy无短路/显式接受拒绝、稳定rank、冷热entries/tokens/Metadata/排名一致、坏Corpus/Snapshot/duplicate ID fail-fast、冻结嵌套cycle、runtime exception/policy错误回退、原query/analysis/k不变、Stage 7错误向上传播、真实Stage 7控制层联动和Evidence无answer。

12 skipped：Stage 3 Live未启用1；Stage 1/2真实Loader/分块各1；Smoke缺完整模型/API/应用/数据库依赖9。安装rank-bm25只消除了该缺包名称，其余缺包保留，Smoke仍7/9。真实MySQL/Redis、Milvus/BGE/CrossEncoder/LLM、线上/端到端 NOT RUN；Stage 7 scorer/Document fixture仍仅隔离控制证明。

`git diff --check`: PASS。5个Python文件ast.parse(feature_version=(3,10))/compile PASS（3.10仅语法，实际运行3.13）；8个Markdown相对链接PASS。38个Legacy/Stage 2–7/配置/依赖/历史报告文件与起始HEAD内容一致PASS，`git diff --cached --check`: PASS，限定暂存13个文件；任务变更范围与Diff审阅PASS。新进程package import不导入Legacy/外部BM25库/模型/数据库/config PASS；索引依赖延迟到Corpus初始化。不将synthetic或真实BM25离线算法测试当作Full Integration PASS。

## Limits and deferred work

批准真实性/语义/版本有效期由调用方治理；本阶段只验证结构与引用字段。中文char/bigram tokenizer、case-sensitive自然语言和词典缺失限制召回；重复/不明确alarm或FAQ宁可回退。BM25全语料IDF随扩容变化，生产阈值未调优；custom policy必须自行承担质量依据。未实现cache读写/TTL、生产FAQ表、最终answer/citation或Stage 9+策略。

## Git and handoff

实现Commit: `0ee768337902fb1100f6afe0d23b18aa4880bc74`；message: `feat: add manufacturing faq fast path`。限定13个本Stage文件，Commit/Push/Remote Verification: PASS；`git push origin main`、`git fetch origin`成功，`git rev-parse HEAD` == `git rev-parse origin/main`，`git status` 为Working Tree clean。完成状态通过独立文档提交正常发布，不amend/force push；最终SHA在回复中提供，不预写当前状态提交自身哈希。Last Completed Stage: Stage 8 — PASS；Active Stage: NONE；Stage 9–13 PENDING。

Stage 9 Readiness: YES（限定已有统一Evidence/快路径决策与Parent fallback接口供设计）。Stage 9–13 PENDING，不自动实施；Full Integration Readiness: NO。发布核验后停止。
