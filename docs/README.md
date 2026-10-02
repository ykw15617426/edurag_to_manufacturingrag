# 项目文档索引

## 当前状态

Stage 0 已完成基线交付，其 Commit、GitHub Push 与 Remote Verification 均为 PASS，提交为 `b6db2e8d70f6c701975e24cefd10a04514139d2e`。Stage 0 技术验证保留 **PARTIAL（7 passed / 9 skipped）** 的历史结论。Stage 1: PASS；Stage 2: PASS；Stage 3: PASS；Stage 4: PASS；Stage 5: PASS；Stage 6: PASS；Stage 7: PASS；Stage 8: PASS；Stage 9: IN PROGRESS；Stage 10–13: PENDING；Full Integration Readiness: NO。

## 文档职责

| 文档 | 维护内容 |
| --- | --- |
| [CURRENT_ARCHITECTURE.md](CURRENT_ARCHITECTURE.md) | 当前真实代码架构、数据流、能力与配置基线 |
| [MANUFACTURING_MIGRATION_PLAN.md](MANUFACTURING_MIGRATION_PLAN.md) | 制造业目标、阶段划分、模块边界与 Metadata 候选设计 |
| [EDURAG_LEGACY_INVENTORY.md](EDURAG_LEGACY_INVENTORY.md) | 已审计教育遗留定位与历史资产清单 |
| [MANUFACTURING_METADATA_SCHEMA.md](MANUFACTURING_METADATA_SCHEMA.md) | Stage 1 正式字段、来源、校验与调用约定 |
| [MANUFACTURING_FINGERPRINTS.md](MANUFACTURING_FINGERPRINTS.md) | Stage 2 原文件/内容指纹、稳定身份与后续持久化边界 |
| [MANUFACTURING_MILVUS_SCHEMA.md](MANUFACTURING_MILVUS_SCHEMA.md) | Stage 3 字段、NULL、PK、索引、集合隔离与兼容规则 |
| [MANUFACTURING_VERSIONED_INGESTION.md](MANUFACTURING_VERSIONED_INGESTION.md) | Stage 4 Manifest、版本策略、差集清理与恢复合约 |
| [MANUFACTURING_QUERY_ANALYSIS.md](MANUFACTURING_QUERY_ANALYSIS.md) | Stage 5 意图、实体证据、结构化语义边界与降级合约 |
| [MANUFACTURING_RETRIEVAL.md](MANUFACTURING_RETRIEVAL.md) | Stage 6 安全 Metadata 条件、Hard 保留、Soft 放宽与 Child Hybrid Retrieval |
| [MANUFACTURING_PARENT_RETRIEVAL.md](MANUFACTURING_PARENT_RETRIEVAL.md) | Stage 7 Parent 身份/Metadata/分数聚合、稳定重排与配置 Top-M |
| [MANUFACTURING_FAST_PATH.md](MANUFACTURING_FAST_PATH.md) | Stage 8 批准语料、报警/FAQ精确证据、raw BM25与Stage 7 fallback合约 |
| [MANUFACTURING_RETRIEVAL_STRATEGY.md](MANUFACTURING_RETRIEVAL_STRATEGY.md) | Stage 9 严格决策、标识符保护、意图快路径与Child融合/一次重排 |
| [Stage 9 报告](STAGE_REPORTS/STAGE9_REPORT.md) | 策略治理离线测试、真实集成限制与Git发布证据 |
| [Stage 8 报告](STAGE_REPORTS/STAGE8_REPORT.md) | 快路径/真实BM25离线测试、扩容记录、限制与Git发布证据 |
| [Stage 7 报告](STAGE_REPORTS/STAGE7_REPORT.md) | Parent/scorer synthetic 验证、真实模型限制与 Git 发布证据 |
| [Stage 6 报告](STAGE_REPORTS/STAGE6_REPORT.md) | 过滤/检索参数/Metadata synthetic 验证、集成限制与 Git 发布证据 |
| [Stage 5 报告](STAGE_REPORTS/STAGE5_REPORT.md) | 查询分析 synthetic 验证、限制与 Git 发布证据 |
| [Stage 4 报告](STAGE_REPORTS/STAGE4_REPORT.md) | 版本摄取实测、集成限制与 Git 发布证据 |
| [Stage 3 报告](STAGE_REPORTS/STAGE3_REPORT.md) | 严格持久化代码、真实验证范围与发布证据 |
| [Stage 2 报告](STAGE_REPORTS/STAGE2_REPORT.md) | 指纹/身份实现、真实测试与 Git 发布证据 |
| [Stage 1 报告](STAGE_REPORTS/STAGE1_REPORT.md) | 实现范围、真实测试、兼容性和发布证据 |
| [Stage 0 报告](STAGE_REPORTS/STAGE0_REPORT.md) | 历史审计发现、改动、测试证据和 Git 发布状态 |
| [治理设置报告](STAGE_REPORTS/REPOSITORY_GOVERNANCE_SETUP_REPORT.md) | 本次文档/治理调整、保留验证及交付状态 |

## 使用与维护

- [项目 README](../README.md) 提供运行前提和测试命令；[AGENTS.md](../AGENTS.md) 提供维护约定；[.agent/](../.agent/README.md) 跟踪当前工作。
- 正式阶段/维护报告统一放入 `STAGE_REPORTS/`。移动已有报告时更新所有有效导航与相对链接，历史变更表中的原路径可保留为事实。
- 历史报告的实验结论不因后续文档整理而重新标记 PASS；后续发布结果注明更新时间。
- 计划不等于实现，readiness 不等于授权。架构事实、未来设计、历史证据分别维护，避免重复生成。
