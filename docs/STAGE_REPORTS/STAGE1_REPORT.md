# Stage 1 — Manufacturing Document Schema + YAML Metadata

## Status

Implementation: PASS。Validation: PASS（限定以下实测范围）。Stage 1: PASS（Commit/Push/Remote Verification 已完成）；Stage 2–13: PENDING。Full Integration Readiness: NO。任务开始于 2026-10-01，交付检查于 2026-10-02。

## Goal

在现有 Loader / Parent-Child 前获取经过验证的单文档业务 Metadata；非法元数据明确失败。只实施 Stage 1，不改变旧语料、OCR、切分策略、位置 ID、检索与持久化。

## Repository Baseline

- Repository: https://github.com/ykw15617426/edurag_to_manufacturingrag
- Branch: main；Stage Start HEAD: `64809b23ee507dd50067e91333dc818a5053224e`。
- 修改前工作区 clean；`git fetch origin` 后 HEAD == origin/main。
- 保留 Stage 0 `b6db2e8d70f6c701975e24cefd10a04514139d2e` 与治理发布历史；没有重做审计。
- 已读取治理、Stage 0 文档、Processor、现有 Loader/Splitter、配置、requirements 与 Smoke Tests。
- requirements 已声明 Pydantic 2.12.5 / pydantic_core 2.41.5 / PyYAML 6.0.3；无需更改依赖文件。
- 本机有效 Parent/Child size=512/128，overlap=120/30；Dense/Sparse 0.8/0.3、nprobe=10 保持不变；未入库或访问数据库。

## Schema Design

ManufacturingDocumentMetadata、KnowledgeType、MaintenanceCycle 已实现。必填 document_id/document_version/title/knowledge_type，七种知识类型受控。业务字符串 trim，必填空白失败、可选空白转 null；版本/报警码/备件号拒绝数字转换，保留大小写、符号和前导零。

周期支持有限正数 value + 六种 unit，或 trigger；残缺 pair 始终失败。alarm/fault/maintenance/parts 条件必填；型号可选。顶层和周期 extra=forbid；不能伪造系统字段。日期采用 calendar date、序列化 ISO；language 默认 zh-CN 可覆盖。完整定义见 [正式合约](../MANUFACTURING_METADATA_SCHEMA.md)。

## Metadata Source Rules

TXT/MD 支持文件头 Front Matter，剥离后仅正文交原 Loader；所有支持格式允许 `<完整文件名>.yaml`，二进制只使用 sidecar。两来源冲突、制造业模式缺来源、空 YAML、非 mapping、重复键、非法/不安全 YAML、未知/非法字段均明确失败。

安全解析使用 SafeLoader 重复键检查 + yaml.safe_load。项目异常区分来源缺失/冲突、YAML、Schema 与合并错误，包含原文件、Metadata 来源、字段、原因，不输出文档正文/输入值。不支持 YAML merge key；不自动找 stem.yaml。

## Implementation Summary

Schema 与 Resolver 不导入 LangChain/模型/数据库。load_with_metadata 是薄适配层：先校验，再调用 Processor 提供的原 Loader；Front Matter 正文写临时同名同扩展文件，原文件不改写，成功/失败清理临时目录并恢复原 source/file_path。

业务 Metadata 和 source_file/metadata_source 进入 Document.metadata，同名 Loader 字段冲突拒绝。Processor 新增 keyword-only metadata_mode，默认 legacy；manufacturing 必须显式指定，未知模式拒绝。Parent-Child 分块正文逻辑及位置 ID 未改。

## Changed Files

- `rag_qa/schemas/__init__.py`、`rag_qa/schemas/manufacturing_metadata.py`：正式合约。
- `rag_qa/ingestion/__init__.py`、`rag_qa/ingestion/metadata_loader.py`：来源、安全解析、异常、临时正文与合并。
- `rag_qa/core/document_processor.py`：显式模式和原 Loader 适配。
- `tests/test_manufacturing_metadata.py`：合成单元样例与可选真实 Parent-Child 测试。
- `docs/MANUFACTURING_METADATA_SCHEMA.md`、本报告：合约和阶段证据。
- `AGENTS.md`、`.agent/PLANS.md`：当前授权阶段和执行状态。
- `README.md`、`docs/README.md`：状态和导航。
- `docs/CURRENT_ARCHITECTURE.md`、`docs/MANUFACTURING_MIGRATION_PLAN.md`：真实增量与阶段边界。

共 14 个文件；Stage 0 报告/遗留清单、数据、配置、requirements、模型、VectorStore 和数据库均未修改。

## Compatibility

默认 Legacy 无需 YAML，保留 source/file_path/timestamp 与正文处理行为；不由文件夹名称判断 Manufacturing。现有位置参数兼容，旧 CLI 保持 Legacy。合成样例明确不是企业生产材料。

Legacy/模式分派单元测试执行真实 Processor 函数，但隔离 Loader/导入依赖使用替身，只验证函数分派和 metadata 约定，不算真实 OCR/LangChain 集成。真实 TXT Loader/Parent-Child 测试因缺依赖 SKIPPED。没有用替身声称模型、数据库或端到端通过。

## Tests

Windows，Python 3.13.9。原环境 Pydantic 2.12.4 / PyYAML 6.0.3 / pytest 8.4.2；另建 Git 忽略的 `.venv/stage1-validation`，仅装仓库指定 Pydantic 2.12.5 / pydantic_core 2.41.5 / PyYAML 6.0.3 和 pytest 8.4.2。未安装完整模型/服务运行依赖。

| Command | Result | 范围 |
| --- | --- | --- |
| `python -m pytest tests/test_manufacturing_metadata.py tests/test_stage0_smoke.py -q -rs` | 105 passed / 0 failed / 10 skipped | 原环境；核心规则真实运行 |
| `.venv/stage1-validation/Scripts/python.exe -m pytest tests/test_manufacturing_metadata.py -q -rs` | 98 passed / 0 failed / 1 skipped | 锁定 Pydantic 2.12.5；真实 Parent-Child 缺依赖 |
| `.venv/stage1-validation/Scripts/python.exe -m pytest tests/test_manufacturing_metadata.py tests/test_stage0_smoke.py -q -rs` | 105 passed / 0 failed / 10 skipped | 锁定版本；Stage 0 7 passed / 9 skipped |
| `git diff --check` | PASS | 已跟踪补丁格式；`git diff --cached --check` 同样 PASS，覆盖全部新增文件 |

覆盖七种合法类型、必填缺失/空白、严格字符串、条件必填、周期 pair/trigger/单位/值、日期与 JSON 序列化、系统字段拒绝、Front Matter/剥离/BOM/CRLF、完整文件名 sidecar、冲突/缺失/空/非法 YAML、可读错误、Loader 合并冲突、临时文件清理、非法 Metadata 不调用 Loader、Legacy 行为与显式模式。

Stage 1 的 1 skipped 是真实 Parent-Child；Stage 0 的 9 skipped 为原 Loader/Processor、模型/检索/数据库/API 依赖不足。SKIPPED 不代表运行 PASS。

## Known Risks

- 缺 LangChain、docx/pptx、PyMuPDF/OpenCV 等依赖，真实 Loader 与 Parent-Child 运行未验证；当前测试仅支持核心合约与隔离适配逻辑结论。
- 原 Markdown Loader 仍依赖 Unstructured；未验证二进制 OCR/复杂版式或老 PPT。
- 单文档单型号/知识类型，不处理多型号列表、节级覆盖与企业词典。
- 临时正文使用 UTF-8/标准换行；Front Matter 必须在文件首行；程序需有临时目录写权限。
- 位置 ID 在重复入库/目录变化时的风险保留到 Stage 2；不存在跨调用事务或增量删除。
- VectorStore 仍按旧字段持久化；新增 Metadata 不会自动完整写入 Milvus。已有 CLI/在线链路未切换制造业模式。

## Architecture Impact

新增 File → Resolver → Safe YAML → Pydantic → Existing Loader → Document.metadata → Existing Parent-Child 的显式路径；复用既有引擎。架构文档只补充真实代码能力，不宣称完整制造业在线链路。

Document SHA256: NOT IMPLEMENTED — Stage 2。
Child SHA256: NOT IMPLEMENTED — Stage 2。
Milvus Manufacturing Schema: NOT IMPLEMENTED — Stage 3。
Versioned Ingestion: NOT IMPLEMENTED — Stage 4。
Metadata Filter: NOT IMPLEMENTED — Stage 6。

## Git

主提交：`feat: add manufacturing metadata validation`。Commit / Push / Remote Verification：PASS。已执行 `git push`、`git fetch origin`、`git rev-parse HEAD`、`git rev-parse origin/main`、`git status`，验证 HEAD == origin/main 且 Working Tree clean。发布确认后的微小状态回写并入同一本次 Stage 提交，最终再次 fetch 核对；最终 SHA 在用户回复给出，不在本报告预写自身哈希。

Diff 审阅确认仅本次 14 文件；文档相对链接检查 PASS，新增 Schema/Adapter 的 Python 3.10 语法解析 PASS（不等同 Python 3.10 运行测试）。

## Stage 2 Readiness

YES（限定 Document / Child 身份与指纹设计）：已有可校验业务合约和显式模式作为输入。完整 Loader/分块运行依赖需在对应验证前补齐；Full Integration Readiness: NO。Stage 2: PENDING，本任务完成后停止，不自动实施。
