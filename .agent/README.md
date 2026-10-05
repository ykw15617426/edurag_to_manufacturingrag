# 项目工作区说明

`.agent/` 保存维护过程与当前计划，`docs/` 保存可交付的架构、迁移设计和阶段证据。这里不放运行代码、凭据或模型。

当前最终检查点（2026-10-06）：Stage 0–13: PASS；Last Completed Stage: Stage 13 — PASS；Active Stage: NONE；Full Integration Readiness: YES（仅受控本地 Integration）；Migration: COMPLETE。Production Quality Certification: NO；Production Scale Validation: NO。 验收报告见 [Stage 13](../docs/STAGE_REPORTS/STAGE13_REPORT.md)。历史限制仍按各报告保留。

| 文件 | 用途 |
| --- | --- |
| [AGENTS.md](../AGENTS.md) | 仓库维护约定与阶段边界 |
| [PLANS.md](PLANS.md) | 当前任务、完成情况、待处理事项和下一步边界 |
| [docs/README.md](../docs/README.md) | 正式文档入口及职责索引 |
| [迁移计划](../docs/MANUFACTURING_MIGRATION_PLAN.md) | 业务阶段与模块边界的设计依据，避免在 PLANS 中重复维护 |

开始任务时先核对用户范围和 Git 状态，再更新 PLANS；结束时记录真实验证结果与交付位置。用户未要求下一阶段时只保留待办，不自动实施。

产生需保留文件变化的正式任务，验证及 Diff 审阅后默认自动 Commit、Push、fetch/远端核对并确认 clean，无需单独要求 Push；无仓库变化则无需提交或推送。具体规则见 AGENTS.md，自动同步不扩大业务任务范围。

阶段报告统一放在 `docs/STAGE_REPORTS/`。历史报告保留当时的审计/测试结论；必要的后续状态更正明确注明日期。Stage 0 技术验证仍为 PARTIAL，其 Commit/Push/Remote Verification 已为 PASS，两者分别记录。
