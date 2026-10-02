# Stage 5 — Query Analysis: Intent Recognition + Entity Extraction

## Status

2026-10-02。Implementation: PASS；Validation: PASS（限实际验证范围）；Stage 5: PASS。Stage 0–4 / Governance: PASS；Stage 6–13: PENDING；Full Integration Readiness: NO。

## Repository Baseline

Repository: https://github.com/ykw15617426/edurag_to_manufacturingrag；Branch: main。
Stage Start HEAD: `11f82044861f7b9eb8efa543e17e4d797be13790`。初始工作区 clean，fetch 后 HEAD == origin/main。已读取 AGENTS/.agent/docs index、当前架构/迁移计划/Stage 4 报告、Legacy query_classifier/strategy_selector/new_rag_system 和 ManufacturingDocumentMetadata/Milvus Schema。

Legacy QueryClassifier 为教育 BERT 二分类；StrategySelector 为四种检索增强策略；new_rag_system 仍属于旧在线调用链。本 Stage 不复用其模型/标签、不改写线上分支，不把制造业 general 解释成绕过 RAG。

## Implemented

Manufacturing Intent Enum: IMPLEMENTED（六意图）。
Validated QueryAnalysis / QueryEntities / ConfidenceLevel: IMPLEMENTED。
Deterministic Entity Extraction: IMPLEMENTED（上下文优先，保留 token）。
Structured Semantic Classifier Boundary: IMPLEMENTED（注入 JSON classifier 与 completion Prompt 适配器）。
Exact Identifier Evidence / Rule Priority / Role Protection: IMPLEMENTED。
Confidence / Explainable Failure Fallback: IMPLEMENTED。
Education BERT Reuse: NONE。
General Bypass-RAG Behavior: NONE。

实装的语义分类内容为可注入的结构化边界/Prompt/JSON 校验，不是已训练或已验收的真实制造业语义模型。未配置 classifier 的默认入口仅 rules。正式合约见 [MANUFACTURING_QUERY_ANALYSIS.md](../MANUFACTURING_QUERY_ANALYSIS.md)。

## Schema and Entity Trust

输出 intent/confidence/entities/analysis_source/warnings；全部六实体 Optional。StrictStr/枚举/extra=forbid，未知字段、教育标签、数值概率或非法实体失败。输出 JSON 不含策略、Filter、答案或 bypass 开关。实体同名字段容量与 Stage 3 按 UTF-8 bytes 对齐；存储 Schema 未修改。

规则显式 label 优先；附近制造业词和狭窄 token 形状可提取示例 MZ-2000/E102/ALM-007/BRG-6205-ZZ。大小写/连字符/下划线/前导零保留，日期/量值拒绝，没有企业词典时无上下文 token 不猜。多个不同值在单字段下返回 None + ambiguous warning/low。

语义值不能覆盖规则；填充 exact identifier 必须是原 query 的区分大小写完整 token，不能截取 XE1029 中的 E102 或改变 ALM-007 为 ALM-07。规则已定角色的 token 不能被补为另一 ID 字段；描述实体也须原文证据。拒绝/冲突明确 warning，high 降为 medium；general/歧义 low。置信度不是概率，不宣称校准过。

## Semantic Boundary and Failure Fallback

SemanticIntentClassifier.classify(query) 返回 JSON str，经严格 JSON parser（重复 key/non-finite 拒绝）与 SemanticClassification Pydantic 校验。JSONSemanticClassifier 传递原始 query、system 合约/Schema、temperature=0.0、JSON response_format；无 SDK/凭据/网络初始化，completion 由调用方负责模型/API、content 提取与有限 timeout。

timeout/network/invalid JSON/unsupported intent/Schema 异常返回 fallback，保留规则实体，warning code 可解释，不回显异常秘密值。唯一关键词意图 cue medium；多 cue 固定优先顺序且 low；无可靠 cue general/low。无规则 classifier 时 analysis_source=rules；成功 semantic 为 llm/hybrid，失败 fallback。无检索选择或 confidence 控制 Filter 的代码。

## Changed Files

共 14 文件：

- 新代码 `rag_qa/query/__init__.py`、`schemas.py`、`entities.py`、`classifier.py`、`analyzer.py`。
- 新测试 `tests/test_manufacturing_query_analysis.py`。
- 新文档 `docs/MANUFACTURING_QUERY_ANALYSIS.md`、本报告。
- 增量治理/导航 `AGENTS.md`、`.agent/PLANS.md`、`README.md`、`docs/README.md`、`docs/CURRENT_ARCHITECTURE.md`、`docs/MANUFACTURING_MIGRATION_PLAN.md`。

旧 QueryClassifier/StrategySelector/new_rag_system、Processor/VectorStore、Stage 1–4 business Schema/Metadata/Fingerprints/Milvus Schema/Manifest/摄取、历史阶段报告、Legacy Inventory、配置/依赖/数据/模型均未修改。

## Tests

Windows / Python 3.13.9，沿用 ignored `.venv/stage1-validation` 的 Pydantic 2.12.5 / pytest 8.4.2；没有安装新依赖或下载模型。所有本阶段 query/classifier 数据均 synthetic，不是实际企业语料；测试验证接口、控制和确定性规则，不证明真实 LLM 意图质量。

| Command | Result | Scope |
| --- | --- | --- |
| `.venv/stage1-validation/Scripts/python.exe -m pytest tests/test_manufacturing_query_analysis.py tests/test_manifest_store.py tests/test_versioned_ingestion.py tests/test_manufacturing_milvus_schema.py tests/test_manufacturing_fingerprints.py tests/test_manufacturing_metadata.py tests/test_stage0_smoke.py -q -rs` | 400 passed / 0 failed / 12 skipped | Stage 5 100/0；Stage 4 56/0；Stage 3 103/1；Stage 2 34/1；Stage 1 100/1；Smoke 7/9 |

覆盖六意图 Enum/JSON/规则例子；MZ-2000、E102/ALM-007、BRG-6205-ZZ、大小写/underscore/前导零；日期/量值/no-context/错误 token 边界；规则覆盖优先/grounding/角色冲突/描述证据/多实体歧义；bad JSON、fenced prose、duplicate key、unknown intent、数字 confidence、Schema/长度错误、Exception、empty/overlong/invalid Unicode；general 无 bypass 字段；JSON adapter Prompt/temperature/原 query；新进程阻断 Legacy/core/ingestion/config/torch/transformers/openai/pymilvus 等导入仍分析通过。

12 skipped 保留环境事实：Stage 3 Live 开关未启用 1；Stage 1/2 真实 Loader/分块各 1；Stage 0 Smoke 缺完整模型/API/应用/数据库依赖 9。Stage 5 Real LLM/API、线上 RAG 接入、真实业务评估: NOT RUN；真实 Milvus/OCR/BGE 同样未执行。不把保留的 SDK 离线测试算作 Stage 5 Live 集成。

`git diff --check`: PASS。6 个新增 Python 文件 ast.parse(feature_version=(3,10)) 与 compile: PASS（Python 3.13 实际测试，3.10 仅语法）。8 个变更/新增 Markdown 相对链接: PASS。22 个 Legacy/Stage 1–4/配置/依赖/历史文件与起始 HEAD 内容比较原样保留: PASS；14 文件范围与 core 不导入 Legacy/runtime 的检查 PASS。`git diff --cached --check`: PASS（含全部新增文件）；限定暂存 14 文件，未混入无关修改，不重新生成历史审计。

## Known Risks

- 没有企业词典，狭窄上下文规则会漏掉未知前缀、其他格式/非 ASCII ID；多实体单值合约不能直接表达比较查询。
- Keyword fallback 不能完整理解否定/语义或所有非制造业上下文，不作为真实生产分类质量证据。
- 真实 LLM/JSON 服务支持、响应延迟和有限 timeout 未验证；temperature=0 不保证完全确定性。
- 模块不主动终止永久阻塞的注入 callable；调用方须配置传输超时。没有真实模型或评估数据，confidence 未校准。
- 原文证据仅证明 token 出现，不证明企业设备/报警/备件词典合法性；品牌/设备/症状不做自动同义归一化。
- 在线仍 Legacy；没有制造业 Filter/Hybrid Retrieval 或低置信度去过滤行为。Full Integration Readiness: NO。

## Deferred

Milvus Metadata Filter / Hybrid Retrieval Changes: NOT IMPLEMENTED — Stage 6。
Parent Aggregation: NOT IMPLEMENTED — Stage 7。
BM25 Fast Path: NOT IMPLEMENTED — Stage 8。
Query Rewrite / Retrieval Strategy: NOT IMPLEMENTED — Stage 9。
Manufacturing Answer Generation: NOT IMPLEMENTED — Stage 10。
真实语义模型部署/企业词典/置信度校准尚未验收。

## Git

Commit / Push / Remote Verification: PASS。消息：`feat: add manufacturing query analysis`。限定本阶段 14 文件，已 Commit/Push/fetch，验证 HEAD == origin/main 与 Working Tree clean。完成状态回写并入刚创建的本阶段提交，再核验最终远端/clean；最终 SHA 在用户回复提供，不预写本报告自身哈希。Last Completed Stage: Stage 5 — PASS；Active Stage: NONE；Stage 6–13: PENDING。

## Stage 6 Readiness

YES（限定 Metadata Filter 的结构化输入与可信边界设计）。后续可依据 confidence/warnings 设计严格、放宽或不加 Filter；本 Stage 不执行该决策。Stage 6–13 PENDING；完成 Stage 5 发布核验后停止。
