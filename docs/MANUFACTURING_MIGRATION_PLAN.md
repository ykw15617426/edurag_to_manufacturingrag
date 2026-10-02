# 制造业设备智能运维 RAG 渐进迁移计划

## Stage 0 决策

面向企业内部设备运维、维修与技术人员，覆盖操作手册、型号参数、报警、故障、维保、备件、历史案例。本阶段建立代码与测试基线，不向现有运行链路注入制造业业务。

**采用现有目录内渐进迁移，不新建平行 manufacturing_rag 系统。** Loader、Parent/Child、BGE-M3、Milvus、Reranker 是可复用核心；新建整套引擎会复制依赖与缺陷、使两套运行入口分叉。Stage 0 只建立设计边界，待相应阶段再添加有实现需求的模块；不创建无调用的空包来制造完成度。

| 目标边界 | 现有复用点 | 最小扩展位置（schemas/ingestion 已在 Stage 1 创建，其余为设计） |
| --- | --- | --- |
| schemas | API Pydantic 模型经验 | rag_qa/schemas：文档 Metadata 合约 |
| ingestion | edu_document_loaders、document_processor | rag_qa/ingestion：sidecar metadata、身份、版本编排；复用原解析器 |
| retrieval | vector_store | rag_qa/retrieval：过滤/聚合策略；基础 Milvus adapter 留原模块并分步迁移 |
| query | query_classifier、strategy_selector | rag_qa/query：制造业意图与实体；不把教育分类器当制造业分类器 |
| generation | prompts、new_rag_system | rag_qa/generation：工业 Prompt；在线编排仍接 new_main |
| evaluation | rag_assessment | rag_qa/evaluation：检索标注/回放，历史教育结果隔离保留 |
| infrastructure | base、mysql_qa clients | 先复用 clients，后续按需求拆 adapter；不复制数据库层 |
| api | app.py | 保留现有入口，Stage 11 才演进协议/生命周期 |

移动/重命名可复用 edu_* 文件时要保留过渡导入或同时修所有引用，并先跑回归；原逻辑与入口不会在 Stage 0 被绕开。

## 阶段与验收边界

用户已明确以下 Stage 0–13 正式路线；Stage 1–8 已完成；2026-10-02 正按授权执行 Stage 9，后续阶段不自动推进。

```text
Stage 0: PASS
Governance Setup: PASS
Stage 1: PASS
Stage 2: PASS
Stage 3: PASS
Stage 4: PASS
Stage 5: PASS
Stage 6: PASS
Stage 7: PASS
Stage 8: PASS
Stage 9: IN PROGRESS
Stage 10-13: PENDING
```

| Stage | 目标 | 入口/复用 | 验收重点 |
| --- | --- | --- | --- |
| 0 | Project Baseline Audit & Manufacturing Migration Preparation | 原目录 | 逐项证据；未验证项明确 SKIPPED；单提交 |
| 1 | Manufacturing Document Schema + YAML Metadata | Processor 前的元数据适配，复用原 Loader | 合法/非法字段、缺失 sidecar、文件映射、错误定位；不创建最终 Milvus Schema |
| 2 | Parent-Child + Document / Child SHA256 Fingerprints | process_documents / add_documents | 原文件/Parent/Child 指纹；document_id 命名空间、重复 occurrence 与版本无关身份；不持久化切分版本状态 |
| 3 | Milvus Manufacturing Schema | VectorStore adapter | 新旧集合隔离、字段/索引确认、Schema 版本与迁移回滚 |
| 4 | Versioned Ingestion + Incremental Upsert + Delta Delete | 离线 orchestration | V1 A/B/C → V2 A/B/D 无 stale C；失败后可重试恢复；文档删除/版本切换 |
| 5 | Query Analysis: Intent Recognition + Entity Extraction | 原分类与策略边界 | 型号/报警/维保意图、实体抽取与兜底；不继承教育“通用知识”绕检索的假设 |
| 6 | Metadata Filter + Hybrid Retrieval | hybrid_search source expr | 型号/制造商/知识类型隔离，表达式安全构造，未抽到字段的策略 |
| 7 | Parent Aggregation + Reranker Refactor | _doc_from_hit / _get_unique_parent_docs | parent_id、metadata、score、child_hit_count、排序稳定；子查询统一融合 |
| 8 | Alarm Code / FAQ / BM25 Fast Path | mysql_qa.retrieval / preprocess | 冷启动/热启动一致，型号/报警码不破坏，语料规模影响可测，source 过滤 |
| 9 | Query Rewrite + Retrieval Strategy Governance | query_classifier / strategy_selector / new_rag_system | 改写与策略有边界、可观测、可回退，避免改写丢失型号/报警实体 |
| 10 | Answer Generation + Citations + Evidence Guard | prompts / new_rag_system | 答案来源、版本引用与证据约束；缺知识时不编造处理步骤 |
| 11 | FastAPI + SSE + Redis Cache Governance | app/new_main/RedisClient | 不重复生成；取消/错误/流完成；真实依赖 readiness；旧 WebSocket 兼容方案 |
| 12 | Retrieval Evaluation + Hit@K + MRR + RAGAS | 独立 retrieval evaluator | 带期望 Document/Child/Parent ID 的标注集；隔离型号/报警；留原始召回与配置快照 |
| 13 | Docker + Integration Tests + README + Final Acceptance | Docker / Compose / README / 现有测试 | 完整依赖约定、集成测试、启动/停止与最终验收 |

Dense/Sparse 权重保持 `0.8 / 0.3`；Dense param 的 nprobe 字面值保持 10。Parent/Child 本地示例与 Docker 当前有配置漂移。此阶段不选择“最佳值”，Stage 12 用制造业检索回放决定。Stage 1 开始前记录实际运行配置和已有入库参数；旧集合不可直接用新切分参数覆盖。

## 制造业术语与 Metadata 候选合约

以下保留 Stage 0 候选设计。Stage 1 已实现单文档 Pydantic 合约与安全 YAML Parser，具体约束以 [MANUFACTURING_METADATA_SCHEMA.md](MANUFACTURING_METADATA_SCHEMA.md) 为准；不等于最终 Milvus Schema。

| 字段 | 候选类型 | 语义/约束 |
| --- | --- | --- |
| equipment_type | string | 企业约定设备类型词典；不能从教育 source 直接映射 |
| equipment_model | string | 完整型号，保留前导零、符号；规范化别名须可追溯 |
| manufacturer | string | 制造商规范名，品牌/别名规则另定 |
| knowledge_type | enum string | manual / alarm / fault / maintenance / parameter / parts / case |
| alarm_code | optional string | 报警码按字符串保留；同一码在不同设备可能含义不同 |
| fault_type | optional string | 故障分类词典待真实文档确认，不先编造封闭枚举 |
| fault_symptom | optional string | 原始故障现象；不可替代正文 |
| maintenance_type | optional string | 保养/检修类型，按实际材料确定规范值 |
| maintenance_cycle | optional object（候选） | value/unit/trigger，支持运行小时、日历、状态触发；Stage 1 已实现 value+unit 或 trigger |
| part_number | optional string | 备件号，保留前导零、连字符与制造商语义 |

建议增加 `document_id`、`document_version`、`source_path`、`title`、`effective_date`、`language`，区分业务版本和摄取时间。`document_sha256`、`child_content_sha256`、chunk/parent ID、ingestion_version 属系统生成字段，Stage 2/4 实现，不能让用户 YAML 伪造已入库状态。

单一 sidecar 初步描述一个文档的型号/知识类型；跨多个型号、多知识类型手册不能直接无损压成一个标签。Stage 1 仅支持单个型号/知识类型，不实现列表或节级覆盖；多型号材料需后续真实资料设计。fault/maintenance/parts 的条件必填与企业词典由实际设备资料验证，不在 Stage 0 猜成最终规范。

knowledge_type 定义：manual 操作/说明；alarm 报警码；fault 现象/原因/处置；maintenance 周期/步骤；parameter 技术参数；parts 配件/备件；case 历史事件。case 需区分事实记录和推荐处理，禁止将教学数据或示例案例声称真实维修记录。

## 教育内容的隔离和保留

- 当前 `rag_qa/data/`、`mysql_qa/data/`、`rag_qa/classify_data/`、`rag_qa/rag_assessment/` 标记为教育历史基线。完整路径与命中行见 EDURAG_LEGACY_INVENTORY.md；本阶段零删除、零移动。
- 暂不物理重命名数据目录，避免破坏 `VALID_SOURCES`、脚本路径与现有入库方式。新制造业资料应使用独立、明确批准的根目录和集合，后续再建立归档策略。
- `demo/` 保留为教学参考，不从 app 导入，不把示例 Agent、Chroma、SSE React 草稿记为在线能力。
- 教育类别、客服模板、品牌 UI、训练标签语义、jpkb 教育表是后续替换对象。loader/splitter/logger 等通用实现可保留并择机重命名。
- 须在部署使用前移除旧软件激活示例和未接入原型；“必须删除”是后续生产内容要求，本阶段不批量删除历史数据。

## Stage 1 readiness

**YES：可以进入限定的 Schema/YAML 设计与离线单元实现。** 现有调用边界、复用点、后续 TODO 和最小检查命令已明确。

这不代表完整运行 readiness。运行环境当前缺 FastAPI/LangChain/Milvus 等依赖；模型只确认目录存在；服务连通性与 API 模型可用性未验证。完整集成、现有生产检索无损验证仍是阻碍项，应在需要实际入库/在线验证前补齐。不得把这些问题带着“全部测试通过”的标签进入下一阶段。

## Stage 1 交付与当时的 Stage 2 依赖

实现及测试证据见 [Stage 1 报告](STAGE_REPORTS/STAGE1_REPORT.md)。Stage 1 交付时 Stage 2: PENDING、Readiness: YES（限定身份/指纹设计）；当前状态以上方阶段表为准，不构成后续阶段实施授权。后续应基于已校验业务字段设计文档与子块指纹，保留当前位置 ID 的兼容边界。Milvus 持久化业务字段属于 Stage 3，版本与增量属于 Stage 4；本次未访问数据库或写入集合。

## Stage 2 交付与当时的 Stage 3 依赖

Stage 2 仅生成指纹与稳定身份，算法以 [MANUFACTURING_FINGERPRINTS.md](MANUFACTURING_FINGERPRINTS.md) 为准，实测见 [Stage 2 报告](STAGE_REPORTS/STAGE2_REPORT.md)。原文件 Hash 不含 sidecar；业务版本判断不能仅用 document_sha256，需在 Stage 4 考虑 document_id、document_version、validated metadata / manifest state。

Stage 2 交付时 Stage 3: PENDING、Readiness: YES（限定制造业持久化设计）；当前状态以上方阶段表为准。当时 VectorStore 不完整持久化业务字段/指纹，Schema、PK 和集合未修改。Manifest、跨运行 Skip、增量编排和 Delta Delete 均留 Stage 4。

## Stage 3 交付与当时的 Stage 4 依赖

存储规则见 [MANUFACTURING_MILVUS_SCHEMA.md](MANUFACTURING_MILVUS_SCHEMA.md)，代码与实测见 [Stage 3 报告](STAGE_REPORTS/STAGE3_REPORT.md)。独立集合、严格 32 字段、稳定 Child PK、业务/指纹 row 映射和现有 Schema/Index 检查已实现；真实服务/BGE 持久化仍需 Live 验证。

Stage 3 交付时 Stage 4: PENDING；Readiness: YES（限定版本/增量设计），当前状态以上方阶段表为准。Stable PK enables Stage 4; it does not replace Stage 4。当时后续需设计 Manifest、业务版本/Metadata 状态、跨运行判断、差异与删除；不能只依赖不含 sidecar 的主文件 Hash。Milvus 新旧集合不自动迁移，Schema mismatch 需明确迁移方案，Stage 3 没有版本激活/回滚或删除。

## Stage 4 交付与当时的 Stage 5 依赖

版本摄取控制层、持久 SQLite Manifest、Metadata/Processing 指纹、实际快照 Skip/Diff、先 Upsert 后 Delete、最终验证后提交、幂等显式删除及失败重试已实现。仍限单 worker / 单 writer；版本不做大小排序；目录不自动 prune。Stage 2 算法、Stage 3 Schema 与检索/切分默认值保持。

合约见 [MANUFACTURING_VERSIONED_INGESTION.md](MANUFACTURING_VERSIONED_INGESTION.md)，证据见 [Stage 4 报告](STAGE_REPORTS/STAGE4_REPORT.md)。Stage 5 Readiness: YES（限定已版本化知识快照的查询分析设计）；真实服务/模型端到端未验证，Full Integration Readiness: NO。Stage 4 交付时 Stage 5–13 PENDING；当前状态以上方阶段表为准，不自动推进。

## Stage 5 交付与 Stage 6 依赖

独立 QueryAnalysis、六意图/定性置信度、保守规则实体、可注入 JSON 语义分类边界、原文证据/规则优先/角色保护与 fallback 已实现。规则 synthetic 验证不是实际企业语义准确率；真实 LLM 尚未验收，旧教育 BERT/StrategySelector/new_rag_system 保留。

合约见 [MANUFACTURING_QUERY_ANALYSIS.md](MANUFACTURING_QUERY_ANALYSIS.md)，实测见 [Stage 5 报告](STAGE_REPORTS/STAGE5_REPORT.md)。Stage 6 Readiness: YES（限定 Filter 设计输入）；应结合 confidence/warnings 决定严格/放宽/无 Metadata Filter。此处记录 Stage 5 交付时的设计边界，当时不执行过滤/Hybrid Retrieval，Stage 6–13 PENDING；当前状态以上方阶段表为准。general 不授权绕检索；Full Integration Readiness: NO。

## Stage 6 交付与 Stage 7 依赖

实现 QueryAnalysis → immutable MetadataFilterPlan → safe expression → 制造业 Dense/Sparse Child 检索；零召回最多一次移除 soft，hard 型号/报警/备件号不移除。现有权重 0.8/0.3 与 nprobe10 保持，完整 Child Metadata/原始 score 已为 Stage 7 保留；不聚合 Parent、不调用 CrossEncoder 重排，不接入 Legacy 在线编排。

合约见 [MANUFACTURING_RETRIEVAL.md](MANUFACTURING_RETRIEVAL.md)，证据见 [Stage 6 报告](STAGE_REPORTS/STAGE6_REPORT.md)。Stage 7 Readiness: YES（限定 Parent 聚合设计输入）；Stage 6 交付时 Stage 7–13 PENDING，当前状态以上方阶段表为准。真实 Milvus/模型/线上未验证，Full Integration Readiness: NO；readiness 不自动授权下一阶段。


## Stage 7 交付与 Stage 8 边界

按 parent_id 聚合 Child，保留全部 Parent/业务/来源属性并检查冲突，max 检索分数、命中统计与稳定 rank 不丢失。现有 CrossEncoder 对 Parent 正文评分，分别保留两个分数，稳定排序后按 config.CANDIDATE_M 返回 Parent Evidence；模型错误 fail closed。k默认统一 config.RETRIEVAL_K，不调配置值，Stage 6 hard/soft控制和 Legacy 原样保留。

合约见 [MANUFACTURING_PARENT_RETRIEVAL.md](MANUFACTURING_PARENT_RETRIEVAL.md)，证据见 [Stage 7 报告](STAGE_REPORTS/STAGE7_REPORT.md)。Stage 8 Readiness: YES（限定 Parent Evidence 接口设计输入）；Stage 7交付时Stage 8–13 PENDING，当前状态以上方阶段表为准。未实现 BM25/报警 fast path、Rewrite/策略/生成/SSE/tuning；真实模型/服务未验证，Full Integration Readiness: NO。


## Stage 8 交付与 Stage 9 边界

批准制造业FAQ/alarm Entry与canonical snapshot、标识符保护tokenizer、Exact Alarm/FAQ与歧义拒绝、raw BM25/hard范围/显式接受policy已实现。默认BM25只给候选，接受只给Evidence；失败/拒绝回退现有Stage 7 Parent检索，不接入在线最终答案，不复用教育BM25业务语义。

合约见 [MANUFACTURING_FAST_PATH.md](MANUFACTURING_FAST_PATH.md)，证据见 [Stage 8 报告](STAGE_REPORTS/STAGE8_REPORT.md)。Stage 9 Readiness: YES（限定统一Evidence/决策与fallback接口设计）；Stage 8交付时Stage 9–13 PENDING，当前状态以上方阶段表为准；当时Query Rewrite/HyDE/subquery/backtracking/strategy、Generation/Citations、Redis TTL/SSE和阈值tuning均未实施。Full Integration Readiness: NO。


## Stage 9 交付与 Stage 10 边界

严格DIRECT/REWRITE/SUBQUERY、可注入planner和整体DIRECT降级、原query保留、硬标识符/新增token保护、稳定去重与最多4子查询已实现。公共fast path probe不提前回退；Exact Alarm限定alarm_fault，旧Stage 8接口兼容。多query复用Stage 6原Analysis的Child检索，按child_id/max score稳定融合及冲突拒绝，再Stage 7聚合与原query一次重排，不改配置/权重/Schema/IDs。

合约见 [MANUFACTURING_RETRIEVAL_STRATEGY.md](MANUFACTURING_RETRIEVAL_STRATEGY.md)，证据见 [Stage 9 报告](STAGE_REPORTS/STAGE9_REPORT.md)。Generation/Citation由Stage 10处理，当前未实现/未接入在线。Manufacturing HyDE/Backtracking未实施，Legacy保留；Stage 10–13 PENDING，Full Integration Readiness: NO。readiness不等于实施授权。
