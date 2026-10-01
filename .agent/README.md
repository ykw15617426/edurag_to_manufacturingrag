# 项目工作区说明

`.agent/` 保存维护过程与当前计划，`docs/` 保存可交付的架构、迁移设计和阶段证据。这里不放运行代码、凭据或模型。

| 文件 | 用途 |
| --- | --- |
| [AGENTS.md](../AGENTS.md) | 仓库维护约定与阶段边界 |
| [PLANS.md](PLANS.md) | 当前任务、完成情况、待处理事项和下一步边界 |
| [docs/README.md](../docs/README.md) | 正式文档入口及职责索引 |
| [迁移计划](../docs/MANUFACTURING_MIGRATION_PLAN.md) | 业务阶段与模块边界的设计依据，避免在 PLANS 中重复维护 |

开始任务时先核对用户范围和 Git 状态，再更新 PLANS；结束时记录真实验证结果与交付位置。用户未要求下一阶段时只保留待办，不自动实施。

阶段报告统一放在 `docs/STAGE_REPORTS/`。历史报告保留当时的审计/测试结论；必要的后续状态更正明确注明日期。Stage 0 技术验证仍为 PARTIAL，其 Commit/Push/Remote Verification 已为 PASS，两者分别记录。
