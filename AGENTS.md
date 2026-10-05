# 仓库维护约定

## 项目与当前边界

本项目从 EduRAG 渐进迁移到制造业设备智能运维 RAG。优先复用已有 Loader、Parent-Child、Embedding、Milvus、Reranker 和问答入口；不要创建平行系统绕开原实现。

Stage 0 已提交并推送：`b6db2e8d70f6c701975e24cefd10a04514139d2e`。历史审计与测试限制见 [Stage 0 报告](docs/STAGE_REPORTS/STAGE0_REPORT.md)。Git 发布完成不等于完整集成验证通过。

Stage 0–12: PASS。Last Completed Stage: Stage 12 — PASS；Active Stage: NONE。Stage 12 Completion V2已在隔离Milvus 2.5.4完成真实BGE-M3/CrossEncoder、42 Child与25-query Direct/Strategy受控评估；synthetic结果不代表生产质量。Stage 13为PENDING，readiness: YES；Full Integration Readiness: NO。迁移计划中的 readiness 或 TODO 不构成实施授权。每次工作以用户当次要求的阶段和范围为准，不自动推进后续 Stage。

## 开始工作

1. 读取本文件、[工作区说明](.agent/README.md)、[执行计划](.agent/PLANS.md)和[文档索引](docs/README.md)。
2. 按任务读取相关现有文档和真实源码；采用 read → verify → preserve → minimally update。已有审计不用重做，运行事实需按任务核实。
3. 修改前检查 `git status --short`、`git branch --show-current`、`git log -5 --oneline`。发现用户改动先报告，保留其内容，避免覆盖。

## 改动与数据保护

- 优先最小范围修改；需求、架构、状态和历史报告各归其位，不复制多套计划或实现。
- 未明确包含数据治理的任务，不删除、移动或重新入库旧语料、训练集、demo、RAGAS 输出；不修改数据库/集合来验证文档工作。
- 不提交 `.env`、`config.ini`、实际密钥/密码、模型权重、缓存、日志或意外的大型文件；不在日志和报告输出秘密值。
- 检索权重、切分参数和其他业务配置的修改须属于当前任务，并提供理由与验证依据。记录的问题留到其目标 Stage。
- 已有架构与遗留清单是事实基线；新增事实与历史事实注明时间/来源，不把设计写成已实现。

## 验证与交付

- 仅文档修改：检查相对链接、目标目录、补丁格式和变更范围；无需为此启动模型、数据库或重跑 Stage 0。
- 代码修改：运行与改动相关的现有检查；Smoke 命令为 `python -m pytest tests/test_stage0_smoke.py -q -rs`。该命令会导入配置，但完整 app import 有显式 live 开关。
- 每个验证记录 command、result 和 PASS/FAIL/SKIPPED/NOT RUN。缺依赖或模型只说明实际限制，不能将源码编译、mock 或目录存在当作集成 PASS。
- 修改长任务时维护 `.agent/PLANS.md`；交付报告存入 `docs/STAGE_REPORTS/`，链接回事实文档，避免复制全部历史审计。
- 任何产生需要保留的仓库文件变化的正式任务，在完成任务并通过相应验证后，必须自动 Commit、Push 和 Remote Verification；这是本项目默认授权，不需要用户每个 Stage 再次要求 Push。范围仅限当前任务的合法修改。

用户明确指令优先；本文件只约束仓库维护流程，不扩大任务授权范围。

## 明确治理基线

- Read first, understand second, modify third：阅读现有内容并理解真实调用链后再最小修改。
- Stage-based development：阶段定义以迁移计划为准；只执行用户当前明确的 Stage，Stage 1–13 未开始时标记 PENDING。
- Source of Truth：CURRENT_ARCHITECTURE 只描述当前真实能力；MANUFACTURING_MIGRATION_PLAN 描述未来路线；Stage Report 持久化阶段证据；PLANS 记录当前执行状态。冲突时以实际源码、已执行结果和用户最新要求校正，不把计划当事实。
- 禁止虚构功能、禁止虚构测试、禁止虚构指标；区分任务完成、测试通过范围和 Full Integration Readiness。
- Git Safety：保留用户工作区，限定暂存文件，禁止混入当前任务无关的用户改动或秘密；不 amend/squash 已完成的 Stage 0 提交。禁止 git reset --hard、git clean -fd、git checkout . 等破坏用户已有工作的操作。
- Commit + Push：所有产生需保留文件变化的正式任务必须自动提交并推送到当前已配置的正确远端分支，不以本地修改作为最终交付。
- Remote Verification：推送后 fetch，核对 Local HEAD == origin/<branch>，并确认 Working Tree clean；失败则记录 PARTIAL 与真实错误。
- GitHub 作为已完成阶段的持久状态：已完成的治理/阶段文档须随授权的提交发布；只有 Commit、Push、Remote Verification 和 clean 全满足，发布任务状态才为 PASS。
- Stage Report 持久化规则：报告放在 docs/STAGE_REPORTS/，包含文件变更、源码范围、command/result、状态及限制；最终 SHA 在回复中提供，不预写当前提交自身的哈希。

## 默认 GitHub 同步工作流

For every formal task that changes repository files:

```text
Read
→ Plan when needed
→ Modify
→ Test / Validate
→ Review Diff
→ Update Documentation when applicable
→ Commit
→ Push
→ Fetch / Verify Remote
→ Confirm Working Tree Clean
```

- 只要产生需要保留的仓库文件变化，就必须 Commit；Commit 后默认 Push 到当前已配置的正确远端分支。
- Push 后必须 fetch 并验证 `Local HEAD == origin/<current-branch>`，同时确认 `Working Tree == clean`。
- 审阅后若 `Repository Changes: NONE`，则 `Commit: NOT REQUIRED`、`Push: NOT REQUIRED`；禁止为制造 Git 历史创建空 Commit。
- 若实现和验证已通过但 Push 失败，记录 `Implementation: PASS`、`Validation: PASS`、`GitHub Sync: FAIL`、`Overall Status: PARTIAL`，并提供真实错误；不得虚构同步完成。
- 自动 Commit + Push 不扩大任务权限，不自动推进下一阶段，不借机提交用户无关修改。若用户已有无关改动，保留并报告；只提交本任务修改，不为追求 clean 而删除或覆盖用户工作。
