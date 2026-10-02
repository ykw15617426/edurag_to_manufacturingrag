# 项目维护计划

更新日期：2026-10-02。

Last Completed Stage: Stage 5 — PASS；Active Stage: NONE；Stage 6–13: PENDING。

## 已确认检查点

| 检查点 | 状态 | 依据 |
| --- | --- | --- |
| Stage 0 源码审计与基线准备 | 已完成交付；技术验证 PARTIAL | [Stage 0 报告](../docs/STAGE_REPORTS/STAGE0_REPORT.md)；历史 Smoke 7 passed / 9 skipped |
| Stage 0 Git Commit | PASS | b6db2e8d70f6c701975e24cefd10a04514139d2e |
| Stage 0 GitHub Push | PASS | 该提交已发布到 origin/main |
| Stage 0 Remote Verification | PASS | 本次 git ls-remote 核对为相同 SHA |
| Stage 0 Task Completion | PASS | 审计交付与 Git 发布均已完成；不等于完整集成就绪 |
| Governance Setup | PASS | Commit、Push、Remote Verification 均已通过，验证时工作区 clean |
| Stage 1 | PASS | Schema/Parser 验证、Commit/Push/Remote Verification 完成；集成限制见报告 |
| Stage 2 | PASS | 指纹/稳定身份、验证及 Git 发布完成；集成限制见报告 |
| Stage 3 | PASS | 制造业 Schema/映射、验证及 Git 发布完成；集成限制见报告 |
| Stage 4 | PASS | 版本/增量控制、验证及 Git 发布完成；真实集成限制见报告 |
| Stage 5 | PASS | QueryAnalysis/信任规则、验证及 Git 发布完成；真实 LLM/在线限制见报告 |
| Stage 6–13 | PENDING | 尚未授权实施 |

## 已完成任务：Repository Governance & Documentation Setup

范围：治理约定、工作区说明、计划、正式文档索引与报告归档。保留原审计内容；不修改业务代码、测试、依赖、配置、数据或模型。

- [x] 读取已有 Stage 0 文档并检查工作区。
- [x] 核对本地与远端 Stage 0 SHA。
- [x] 建立 AGENTS.md、.agent/README.md、.agent/PLANS.md、docs/README.md。
- [x] 将 Stage 0 报告移入 STAGE_REPORTS，修正导航和相对链接。
- [x] 更正 Stage 0 Git 发布状态，保留历史审计/测试限制。
- [x] 完成文档链接、内容保留与变更范围检查，记录治理报告。
- [x] Commit、Push、fetch 与远端一致性/工作区检查完成。

交付：[治理设置报告](../docs/STAGE_REPORTS/REPOSITORY_GOVERNANCE_SETUP_REPORT.md)。本次已完成授权的 Commit + Push，fetch 后 Local HEAD == origin/main，工作区 clean；Governance Setup 为 PASS。历史 Stage 0 发布状态保持 PASS。

## 下一步边界

正式任务若产生需保留的仓库文件变化，按 AGENTS.md 默认完成 Commit、Push、Remote Verification 与 clean 检查，无需用户另行要求 Push；无变化不创建空提交。此规则不授权推进后续阶段。

等待后续任务明确范围；不自行进入 Stage 6。未来业务阶段定义统一引用 [MANUFACTURING_MIGRATION_PLAN.md](../docs/MANUFACTURING_MIGRATION_PLAN.md)。完整集成尚未验证等已知限制保留在 Stage 0 报告；本任务不安装完整运行依赖、不重新执行审计或集成测试；可运行已有 Smoke Tests 作最终检查。

## 已完成任务：Stage 1 — Manufacturing Document Schema + YAML Metadata

状态：PASS。开始 HEAD：`64809b23ee507dd50067e91333dc818a5053224e`；main；起始工作区 clean，fetch 后 HEAD == origin/main。

- [x] 读取治理、Stage 0 文档、Loader/Splitter/Processor、配置、依赖和测试。
- [x] 实现独立 Pydantic Schema、安全 YAML Resolver、显式 manufacturing 模式。
- [x] 验证 Schema/Parser、Legacy 兼容和 Metadata 传播；缺依赖明确 SKIPPED。
- [x] 更新架构/迁移计划/Schema 文档与 Stage 1 报告，审阅 Diff。
- [x] Commit、Push、fetch/远端 SHA 与工作区 clean 核对。

不修改旧语料、切分参数、Chunk ID、模型或数据库。Stage 2–13 保持 PENDING。

Stage 1 锁定版本验证：105 passed / 10 skipped（核心 98 passed / 1 skipped；Smoke 7 passed / 9 skipped）。报告：[STAGE1_REPORT.md](../docs/STAGE_REPORTS/STAGE1_REPORT.md)。SKIPPED 不代表真实集成通过。

## 已完成任务：Stage 2 — Parent-Child + Document / Child SHA256 Fingerprints

状态：PASS；开始 HEAD：`86bdc9cb4e4bea3a0aa7f9b9601d1acee57c91cb`；main；初始工作区 clean，fetch 后 HEAD == origin/main。

- [x] 读取治理、阶段报告、架构、Stage 1 合约与 Processor/Loader/VectorStore 和测试。
- [x] 实现流式原文件 Hash、内容规范化、稳定 Parent/Child ID，保留 Legacy。
- [x] 核心与隔离 Processor 测试，真实 Loader/分块缺依赖明确 SKIPPED。
- [x] 增量更新文档、Stage 2 报告与审阅 Diff。
- [x] Commit、Push、fetch/远端验证与 clean 检查。

不实施 Milvus Schema/PK、Manifest、跨运行 Skip、增量编排或删除。Stage 3–13 PENDING。

Stage 2 回归验证：140 passed / 11 skipped（Stage 2 34/1；Stage 1 99/1；Smoke 7/9），缺依赖的真实集成未通过。报告：[STAGE2_REPORT.md](../docs/STAGE_REPORTS/STAGE2_REPORT.md)。

## 已完成任务：Stage 3 — Milvus Manufacturing Schema

状态：PASS；开始 HEAD：`53608eac4ba86f558e85a6be840fbdb45bb56400`；main；初始工作区 clean，fetch 后 HEAD == origin/main。

- [x] 读取治理、文档、Stage 1/2 报告及存储/配置/依赖/测试，核对 SDK 版本。
- [x] 实现独立集合配置、严格 Schema/Row Mapper、现有集合兼容检查。
- [x] Schema/Mapper/Legacy/隔离控制验证，回归 Stage 0–2；Live 缺环境明确 SKIPPED。
- [x] 更新文档与 Stage 3 报告，审阅 Diff。
- [x] Commit、Push、fetch/远端与 clean 核对。

Stage 3 交付时：Last Completed Stage: Stage 3 — PASS；Active Stage: NONE；Stage 4–13: PENDING。当前状态以上方检查点及最新任务为准。

不改 Stage 2 身份/切分/检索参数，不做 Manifest、跨运行 Skip 或删除编排。Stage 4–13 PENDING。

Stage 3 锁定 SDK 回归：244 passed / 12 skipped（Stage 3 103/1；Stage 2 34/1；Stage 1 100/1；Smoke 7/9）。原轻量环境核心：101 passed / 3 skipped。真实 Milvus 未执行；报告：[STAGE3_REPORT.md](../docs/STAGE_REPORTS/STAGE3_REPORT.md)。

## 已完成任务：Stage 4 — Versioned Ingestion + Incremental Upsert + Delta Delete

状态：PASS；开始 HEAD：`0cc3a855653ef20564c089f919517bc1514219d8`；main；初始工作区 clean，fetch 后 HEAD == origin/main。

- [x] 读取治理、Stage 1–3 合约和真实代码，核对远端基线。
- [x] 实现 SQLite Manifest、业务 Metadata Hash、Processing Signature 与摄取/删除控制层。
- [x] 验证有状态快照、失败重试、跨运行 Skip、真实适配器控制与 Stage 0–3 回归。
- [x] 增量更新事实/计划/报告，审阅 Diff。
- [x] Commit、Push、fetch/远端与 clean 核对。

仅支持单 worker / 单 writer，不修改 Stage 2 身份、Stage 3 Schema、Legacy 或检索/切分默认值。Stage 5–13 PENDING。

Stage 4 回归：300 passed / 0 failed / 12 skipped（Stage 4 56/0；Stage 3 103/1；Stage 2 34/1；Stage 1 100/1；Smoke 7/9）。阻断真实 SDK/模型/应用运行依赖后核心 56 passed。语法、链接、Diff 与既有合约保留 PASS；真实 Milvus/OCR/BGE NOT RUN。报告：[STAGE4_REPORT.md](../docs/STAGE_REPORTS/STAGE4_REPORT.md)。

## 已完成任务：Stage 5 — Query Analysis: Intent Recognition + Entity Extraction

状态：PASS；开始 HEAD：`11f82044861f7b9eb8efa543e17e4d797be13790`；main；初始工作区 clean，fetch 后 HEAD == origin/main。

- [x] 读取治理、当前架构、Stage 4 报告及教育查询/制造业字段真实代码。
- [x] 实现轻量 QueryAnalysis、保守规则实体、注入 JSON 语义分类边界与 fallback。
- [x] 核心 synthetic 测试及 Stage 0–4 回归；验证不导入 Legacy/模型/API。
- [x] 增量文档、报告与 Diff 审阅。
- [x] Commit、Push、fetch/远端与 clean 核对。

只产出结构化分析；不调用教育 BERT、StrategySelector 或修改 new_rag_system，不实现 Stage 6 Filter/Hybrid Retrieval 或后续业务。

Stage 5 回归：400 passed / 0 failed / 12 skipped（Stage 5 100/0；Stage 4 56/0；Stage 3 103/1；Stage 2 34/1；Stage 1 100/1；Smoke 7/9）。独立进程无 Legacy/SDK/模型导入验证通过；语法/链接/历史保留与 Diff PASS。真实 LLM/API/在线集成 NOT RUN；报告：[STAGE5_REPORT.md](../docs/STAGE_REPORTS/STAGE5_REPORT.md)。
