# 项目文档索引

## 当前状态

Stage 0 已完成基线交付，其 Commit、GitHub Push 与 Remote Verification 均为 PASS，提交为 `b6db2e8d70f6c701975e24cefd10a04514139d2e`。Stage 0 技术验证保留 **PARTIAL（7 passed / 9 skipped）** 的历史结论。Stage 1: PASS；Stage 2–13: PENDING；Full Integration Readiness: NO。

## 文档职责

| 文档 | 维护内容 |
| --- | --- |
| [CURRENT_ARCHITECTURE.md](CURRENT_ARCHITECTURE.md) | 当前真实代码架构、数据流、能力与配置基线 |
| [MANUFACTURING_MIGRATION_PLAN.md](MANUFACTURING_MIGRATION_PLAN.md) | 制造业目标、阶段划分、模块边界与 Metadata 候选设计 |
| [EDURAG_LEGACY_INVENTORY.md](EDURAG_LEGACY_INVENTORY.md) | 已审计教育遗留定位与历史资产清单 |
| [MANUFACTURING_METADATA_SCHEMA.md](MANUFACTURING_METADATA_SCHEMA.md) | Stage 1 正式字段、来源、校验与调用约定 |
| [Stage 1 报告](STAGE_REPORTS/STAGE1_REPORT.md) | 实现范围、真实测试、兼容性和发布证据 |
| [Stage 0 报告](STAGE_REPORTS/STAGE0_REPORT.md) | 历史审计发现、改动、测试证据和 Git 发布状态 |
| [治理设置报告](STAGE_REPORTS/REPOSITORY_GOVERNANCE_SETUP_REPORT.md) | 本次文档/治理调整、保留验证及交付状态 |

## 使用与维护

- [项目 README](../README.md) 提供运行前提和测试命令；[AGENTS.md](../AGENTS.md) 提供维护约定；[.agent/](../.agent/README.md) 跟踪当前工作。
- 正式阶段/维护报告统一放入 `STAGE_REPORTS/`。移动已有报告时更新所有有效导航与相对链接，历史变更表中的原路径可保留为事实。
- 历史报告的实验结论不因后续文档整理而重新标记 PASS；后续发布结果注明更新时间。
- 计划不等于实现，readiness 不等于授权。架构事实、未来设计、历史证据分别维护，避免重复生成。
