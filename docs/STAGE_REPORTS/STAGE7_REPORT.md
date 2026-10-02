# Stage 7 — Parent Aggregation + Reranker Refactor

2026-10-02。开始 main / `c8d20a703dd98a6f8c8ccab05aaf5ffc54596da6`；初始 Working Tree clean，fetch 后 HEAD == origin/main。用户仅授权 Stage 7。

Implementation: PASS。Validation: PASS。GitHub Sync: PASS。Overall Status: PASS。Full Integration Readiness: NO。

## Changes and source scope

- 新增 `rag_qa/retrieval/parent_aggregation.py`：parent_id 分组、全部公共 Parent/Document Metadata 一致性检查、max score、Child IDs/数量/首 rank 与每个 Child 的 provenance；相同正文不同 ID 不合并。
- 新增 `rag_qa/retrieval/parent_reranker.py`：现有 scorer.predict(query,parent_content)、两个独立分数、稳定 tie 排序、Top-M、fail-closed RerankerError。
- 最小修改 `manufacturing_retriever.py`：默认 k 统一延迟读取 config.RETRIEVAL_K，新增 retrieve_parents 调用 Stage 6 child → aggregate → 已有 vector_store.reranker → config.CANDIDATE_M；保留过滤 attempts。更新包 exports。
- 新增 `tests/test_parent_aggregation.py`、`tests/test_manufacturing_parent_retrieval.py`；新建 [Parent 检索合约](../MANUFACTURING_PARENT_RETRIEVAL.md) 和本报告，最小同步 README/index、架构/迁移、AGENTS/PLANS 与当前 Stage 6 默认 k 文档。

VectorStore 全文、Stage 6 filters、Legacy 检索/分类/策略/在线 new_rag_system、Stage 2 身份、Stage 3 Schema、Stage 4 ingestion、Stage 5 contract、base/config.py、配置/依赖/数据/模型、历史报告和 Legacy Inventory 未修改。RETRIEVAL_K fallback5、CANDIDATE_M fallback2、Dense/Sparse 参数及权重不调优；没有 Stage 8+ 实施。

## Validation

沿用 Windows / Python 3.13.9、ignored `.venv/stage1-validation`；pytest8.4.2/Pydantic2.12.5/PyMilvus2.5.4 环境未增加安装或模型下载。所有 Child/scorer 数据为 synthetic。LangChain Document 通过现有 fixture 替身验证参数和元数据，未宣称真实运行成功。

| Command | Result | Scope |
| --- | --- | --- |
| `.venv/stage1-validation/Scripts/python.exe -m pytest tests/test_parent_aggregation.py tests/test_manufacturing_parent_retrieval.py -q -rs` | 首轮 76 passed / 0 failed / 0 skipped | Stage 7 控制；随后增加 NumPy scalar/多分类 guard 和配置 fallback 验证 |
| `.venv/stage1-validation/Scripts/python.exe -m pytest tests/test_parent_aggregation.py tests/test_manufacturing_parent_retrieval.py tests/test_manufacturing_metadata_filters.py tests/test_manufacturing_retrieval.py tests/test_manufacturing_query_analysis.py tests/test_manifest_store.py tests/test_versioned_ingestion.py tests/test_manufacturing_milvus_schema.py tests/test_manufacturing_fingerprints.py tests/test_manufacturing_metadata.py tests/test_stage0_smoke.py -q -rs` | 最终完整回归 544 passed / 0 failed / 12 skipped | Stage 7 79/0；Stage 0–6 465/12；含 NumPy 输出和配置 fallback 实测 |

覆盖同父多子/同文异父、所有公共 metadata 冲突与 provenance、max 原始分数、Child ids/rank/count、缺字段/非法 ID/重复 Child guard、不改输入；预排序/最终排序/tie、CrossEncoder 输入 Parent 文本、分别保留分数、空不调模型/单 Parent 评分/全部评分后截断；exception、非法 count、非 scalar/NaN/inf fail closed；默认 k 从 config 读取/显式覆盖、Top-M config1/3、Stage 6 hard 零召回保持/soft 放宽、实际 Child adapter 到 Parent 的 recording 联动、原 Legacy 回归。

12 skipped 为历史环境限制：Stage 3 live 未启用 1；Stage 1/2 真 Loader/分块各 1；Smoke 缺完整模型/API/应用/数据库依赖 9。真实 `bge-reranker-large`/CrossEncoder: NOT RUN；Live Milvus/BGE-M3、LLM、LangChain真实运行与在线/端到端业务评估: NOT RUN。未访问/修改真实集合；假分数不是质量指标。

`git diff --check`: PASS。6 个 Python 文件 ast.parse(feature_version=(3,10)) 与 compile: PASS（3.10 仅语法，实际运行3.13）。9 个 Markdown 文件相对链接 PASS；25 个 VectorStore/filters/Schema/ingestion/query/配置/历史报告与开始 HEAD 内容完全一致 PASS。Stage 6 retrieve 除默认 k 的 lazy resolution 外，原 body AST 完全一致 PASS。独立进程 package import + explicit-k retrieval 无 SDK/模型/LangChain/config imports PASS。`git diff --cached --check`: PASS；限定暂存15个文件，变更范围与 Diff 审阅 PASS；不将 source/mock 当作 Full Integration PASS。

## Limits and deferred work

严格一致性检查会对同 parent_id 下混合版本或不同来源属性报错；输入必须符合 Stage 6 完整 hit 合约。first_child_rank 为1-based，重复 Child ID 报错。ranker 故障 fail closed，无隐藏 fallback；不选择最佳 k/M/权重，不声明真实检索/重排质量。

在线仍 Legacy。Stage 8–13 PENDING；BM25/报警 fast path、Rewrite/HyDE/subquery、Answer/Citations、SSE、evaluation tuning 未实现。

## Git and handoff

实现 Commit: `3427cc372f0accab7ec92b82b92c56fafa7ce660`；message: `feat: add manufacturing parent reranking`。仅本阶段15个文件，Commit / Push / Remote Verification: PASS；`git push origin main` 与 `git fetch origin` 成功，`git rev-parse HEAD` == `git rev-parse origin/main`，`git status` 为 Working Tree clean。完成状态通过独立文档提交正常发布，不 amend/force push；最终 SHA 在回复中提供，不预写当前状态提交自身哈希。Last Completed Stage: Stage 7 — PASS；Active Stage: NONE；Stage 8–13 PENDING。

Stage 8 Readiness: YES（限定已有制造业 Parent Evidence 输出接口供后续设计）；不构成 Stage 8 实施授权。Full Integration Readiness: NO；本阶段发布核验后停止。
