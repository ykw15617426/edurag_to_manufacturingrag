# 项目维护计划

更新日期：2026-10-01。

## 已确认检查点

| 检查点 | 状态 | 依据 |
| --- | --- | --- |
| Stage 0 源码审计与基线准备 | 已完成交付；技术验证 PARTIAL | [Stage 0 报告](../docs/STAGE_REPORTS/STAGE0_REPORT.md)；历史 Smoke 7 passed / 9 skipped |
| Stage 0 Git Commit | PASS | b6db2e8d70f6c701975e24cefd10a04514139d2e |
| Stage 0 GitHub Push | PASS | 该提交已发布到 origin/main |
| Stage 0 Remote Verification | PASS | 本次 git ls-remote 核对为相同 SHA |
| Stage 0 Task Completion | PASS | 审计交付与 Git 发布均已完成；不等于完整集成就绪 |
| Governance Setup | PASS | Commit、Push、Remote Verification 均已通过，验证时工作区 clean |
| Stage 1–13 | PENDING | 本次用户明确禁止开始 Stage 1 |

## 当前任务：Repository Governance & Documentation Setup

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

等待后续任务明确范围；不自行进入 Stage 1。未来业务阶段定义统一引用 [MANUFACTURING_MIGRATION_PLAN.md](../docs/MANUFACTURING_MIGRATION_PLAN.md)。完整集成尚未验证等已知限制保留在 Stage 0 报告；本任务不安装完整运行依赖、不重新执行审计或集成测试；可运行已有 Smoke Tests 作最终检查。
