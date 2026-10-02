# Stage 9 — Query Rewrite + Retrieval Strategy Governance

日期：2026-10-02。Repository：ykw15617426/edurag_to_manufacturingrag；branch：main；起始HEAD：`31c21bd01d9482945c8864e4ee2e8d19725153ae`，fetch核对origin/main一致，起始工作区clean。Stage 9: PASS；Implementation/Validation/GitHub Sync: PASS。实现提交正常push/fetch后本地远端一致、工作区clean；完成状态独立提交发布，最终SHA在交付回复提供，不预写本提交自身SHA。

## 文件与实际源码范围

- 新增`rag_qa/query/rewrite.py`：严格Pydantic策略合约、JSON/parser、planner protocol、变体/标识符保护与稳定去重。
- 新增`rag_qa/retrieval/strategy.py`：意图eligibility、策略降级、复用Stage 6原Analysis Child检索、融合、复用Stage 7聚合和一次原query重排、可观察结果。
- 最小扩展`rag_qa/retrieval/fast_path.py`：公开probe/三个eligibility开关，Stage 8公开入口复用probe并保持fallback行为。
- 新增两个Stage 9测试文件；新增[策略合约](../MANUFACTURING_RETRIEVAL_STRATEGY.md)与本报告；增量同步AGENTS/PLANS、README/docs索引、当前架构/迁移计划/快路径合约。不重写历史阶段报告。

实际链路：Original Query + QueryAnalysis → public FastPath probe（仅alarm_fault Exact Alarm eligible）→ structured DIRECT/REWRITE/SUBQUERY → 全部变体验证 → 每变体原Analysis Stage 6 Child retrieval → child_id融合 → Stage 7 Parent聚合 → 原query一次CrossEncoder predict → 配置Top-M Parent Evidence。fast path接受只返回批准Evidence，跳过planner/Child/rerank；不声称经过模型评分。

Metadata/正文冲突及检索/Parent/model错误fail closed，不进行无过滤重试；highest raw score不和rerank score混合。每条变体保留hard ID和original，不能新增ASCII token；该保守策略也会拒绝新英文普通词，未验证企业真实rewrite召回收益。Schema最多4条原始subqueries，空白键稳定去重，非法项整体DIRECT。Planner timeout由注入适配器承担，核心处理TimeoutError但不自行终止阻塞网络调用。

## 验证 command / result

以下python均为仓库ignored验证环境`.venv/stage1-validation/Scripts/python.exe`（Python 3.13.9、pytest 8.4.2）。未新增依赖安装、下载模型或连接数据库。

| Command | Result | Status |
| --- | --- | --- |
| `git status --short`; `git branch --show-current`; `git log -5 --oneline`; `git fetch origin`; `git rev-parse HEAD`; `git rev-parse origin/main` | 初始clean/main，基线本地远端相同 | PASS |
| `python -m pytest tests/test_manufacturing_query_rewrite.py tests/test_manufacturing_strategy.py -q -rs --tb=short` | 83 passed / 0 failed / 0 skipped | PASS |
| Stage 0–9完整回归（下方命令） | 689 passed / 0 failed / 12 skipped | PASS |
| Python AST、治理/文档相对链接目标、`git diff --check`、范围与Diff审阅 | 5文件AST与119相对链接目标通过；Diff/范围无异常 | PASS |
| Real LLM / BGE-M3 / CrossEncoder / Live Milvus / online Generation | 未执行，不当作集成PASS | NOT RUN |
| Commit / Push / Fetch / equal / clean | 实现提交正常Push；fetch后Local HEAD == origin/main，Working Tree clean | PASS |

```powershell
.venv/stage1-validation/Scripts/python.exe -m pytest tests/test_manufacturing_query_rewrite.py tests/test_manufacturing_strategy.py tests/test_manufacturing_bm25.py tests/test_manufacturing_fast_path.py tests/test_parent_aggregation.py tests/test_manufacturing_parent_retrieval.py tests/test_manufacturing_metadata_filters.py tests/test_manufacturing_retrieval.py tests/test_manufacturing_query_analysis.py tests/test_manifest_store.py tests/test_versioned_ingestion.py tests/test_manufacturing_milvus_schema.py tests/test_manufacturing_fingerprints.py tests/test_manufacturing_metadata.py tests/test_stage0_smoke.py -q -rs --tb=short
```

测试覆盖：无planner及三策略、timeout/坏JSON/schema/不支持策略整体验证降级；hard ID大小写/-/_/前导零/边界保护和新编号拒绝；最大4、重复稳定去重、空/非法/混合子查询、original-first；六意图、公共probe不提前回退、FAQ/BM25显式policy和Stage 8旧接口；融合max score、稳定tie/位置/来源、重复计数/冲突/输入不变；原Analysis对象复用、每变体soft-only放宽、先融合再聚合、全部Parent一次原query评分、配置k/Top-M、异常传播。

初轮曾136 passed / 2 errors：超长JSON测试参数默认ID超过Windows环境变量32767字符限制。仅缩短测试ID后解决；未将失败运行记为PASS。此后先前完整回归681 passed / 12 skipped，增加额外边界与稳定去重后最终完整回归689 passed / 0 failed / 12 skipped。12个SKIPPED为既有缺依赖/未启用Live测试，不是集成PASS。

## 保留与限制

Stage 2 stable IDs/指纹、Stage 3 32字段Schema、Stage 4 manifest/版本摄取、Stage 5 QueryAnalysis、Stage 6 filter policy、Stage 7 Parent聚合/重排规则、BM25 threshold/config/权重和Legacy StrategySelector/HyDE/Backtracking/new_rag_system保持。未修改app/new_main，未移动旧数据/删除集合/重跑入库，未提交凭据/模型/缓存。

Manufacturing HyDE / Backtracking：NOT IMPLEMENTED。假设事实/新标识符与硬约束弱化存在风险，缺真实评估收益，不在本阶段试探实现。LLM计划器仅可注入边界和synthetic tests，不能声称真实LLM质量通过；recording scorer不能声称CrossEncoder质量通过。完整线上服务和真实资料未验收。

Full Integration Readiness: NO。Stage 10–13 PENDING；Stage 9发布完成后停止，不开始Generation/Citation/SSE/cache/tuning。

## 发布证据

实现Commit：`66e3b32e64fbde9e14e011fccbed19c9c1d1dba0`（`feat: add manufacturing retrieval strategy governance`）。已执行`git push`、`git fetch origin`、`git rev-parse HEAD`、`git rev-parse origin/main`、`git status --short`，两SHA一致且status为空：PASS。本完成状态以正常独立文档Commit发布，不amend/force push；最终HEAD及clean在交付回复核验。Last Completed Stage: Stage 9 — PASS；Active Stage: NONE；Stage 10–13 PENDING。
