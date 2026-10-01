# Stage 2 — Parent-Child + Document / Child SHA256 Fingerprints

## Status

2026-10-02。Implementation: PASS；Validation: PASS（限实测范围）；Stage 2: PASS（已完成 Git 发布核对）。Stage 0 / Governance / Stage 1: PASS；Stage 3–13: PENDING；Full Integration Readiness: NO。

## Goal

仅生成源主文件、Parent/Child 内容指纹与制造业稳定身份，复用现有 Loader/Splitter。默认 Legacy 保持位置 ID。不实施 Stage 3 或 Stage 4 的持久化/摄取决策。

## Repository Baseline

Repository: https://github.com/ykw15617426/edurag_to_manufacturingrag；Branch: main。
Stage Start HEAD: `86bdc9cb4e4bea3a0aa7f9b9601d1acee57c91cb`。
初始工作区 clean；执行 `git fetch origin` 后 HEAD 与 origin/main 相同。Stage 0 / 1 报告保留为历史证据，未重做审计。

已读取 AGENTS/.agent、文档索引、架构/迁移/Schema、Stage 0/1 报告及真实 Processor、Metadata Adapter、Schema、VectorStore 与现有测试。VectorStore 显式写旧字段，PK 为 MD5(metadata["id"])；本次未修改它。

## Fingerprint Definitions

- Document SHA256: IMPLEMENTED — 原主文件 bytes 的流式 SHA256；Front Matter 包含在原文件中，临时正文不参与；sidecar bytes 排除。
- Parent Content SHA256: IMPLEMENTED — Parent 原 page_content 经规范化后 UTF-8 SHA256。
- Child Content SHA256: IMPLEMENTED — Child 原 page_content 经规范化后 UTF-8 SHA256。
- Stable Manufacturing Parent ID: IMPLEMENTED。
- Stable Manufacturing Child ID: IMPLEMENTED；Child `id == child_id`。

所有 Hash/ID 为 lowercase 64-char hex。`document_sha256` 是 **Source File Byte Fingerprint**，不是业务版本、Metadata 指纹或 Ingestion Version。sidecar YAML 改变且主文件不变，document_sha256 不变是预期行为；Stage 4 版本判断需 document_id/document_version/validated metadata/manifest state，不能仅凭主文件 Hash。

## Content Normalization

NFC → CRLF/CR 转 LF → 每行去尾随空白 → 整体去首尾空白。内部正常空格、内部空行、大小写、标点保留；不做 NFKC 或语义清洗。规范化只用于 Hash，不改原 page_content / parent_content。

## Stable Identity Design

确定性 JSON list 使用 ensure_ascii=False、紧凑 separators，UTF-8 SHA256：

```text
Parent: ["parent", document_id, parent_content_sha256, occurrence]
Child:  ["child", document_id, parent_id, child_content_sha256, occurrence]
```

不包含 document_version、document_sha256、路径、timestamp、os.walk 顺序和全局 i/j/k。不同文档/Parent 的同内容 Child 不碰撞；同内容 occurrence 区分完全重复块并保留全部块。Parent 计数在一个调用中按业务 document_id/content hash 分组，跨同文档多个 Loader 输出共享；Child 计数限当前 Parent。完整规则与限制见 [指纹文档](../MANUFACTURING_FINGERPRINTS.md)。

## Legacy Compatibility

默认 metadata_mode="legacy" 保留 `doc_i_parent_j` / `doc_i_parent_j_child_k`；不新增指纹/child_id，不要求 YAML。显式 manufacturing 才生成稳定身份。原切分参数、source/file_path/timestamp、parent_content、Stage 1 业务 Metadata 与错误校验保留。YAML 仍禁止输入新增 parent_content_sha256 及全部系统字段。

Legacy 位置 ID 已通过隔离 Processor 控制流程测试；不将 Loader/Splitter 替身视为真实 LangChain/OCR 集成。

## Implementation Summary

新增纯标准库 fingerprints.py：流式文件 Hash、内容规范化/Hash、Parent/Child ID。Metadata Adapter 在验证后、原 Loader 前对原主文件生成 document_sha256，加入现有冲突检查。Processor 在原分块循环中按模式加入 Hash/ID 和重复计数，业务 Metadata 继承不重建、不丢失。

Stage 1 可选真实制造业测试的 ID 断言同步为稳定身份；增加 parent_content_sha256 拒绝测试。不改 Schema 可写字段、OCR、Splitter 实现、VectorStore 或数据库。

## Changed Files

- `rag_qa/ingestion/fingerprints.py`：纯 Hash/Identity 函数。
- `rag_qa/ingestion/metadata_loader.py`：原主文件 Hash 接入与合并冲突。
- `rag_qa/core/document_processor.py`：制造业 Parent/Child 稳定身份和重复计数。
- `tests/test_manufacturing_fingerprints.py`：标准已知 SHA256、Hash/Identity/隔离流程及可选真实集成。
- `tests/test_manufacturing_metadata.py`：新增系统字段拒绝，更新制造业 ID 断言。
- `docs/MANUFACTURING_FINGERPRINTS.md`、本报告：指纹规则与证据。
- `docs/MANUFACTURING_METADATA_SCHEMA.md`、`docs/CURRENT_ARCHITECTURE.md`：系统字段与真实链路。
- `AGENTS.md`、`.agent/PLANS.md`、`docs/MANUFACTURING_MIGRATION_PLAN.md`：最小阶段/治理同步。
- `README.md`、`docs/README.md`：状态与导航。

共 14 文件；旧语料、配置、依赖、模型、Stage 0/1 报告、Legacy Inventory 和 VectorStore 保持原样。

## Tests

Windows / Python 3.13.9；沿用 Git 忽略的 `.venv/stage1-validation`，Pydantic 2.12.5 / pydantic_core 2.41.5 / PyYAML 6.0.3 / pytest 8.4.2。没有安装新运行依赖、启动服务或入库。

Command:

```text
.venv/stage1-validation/Scripts/python.exe -m pytest tests/test_manufacturing_fingerprints.py tests/test_manufacturing_metadata.py tests/test_stage0_smoke.py -q -rs
```

Result: **140 passed / 0 failed / 11 skipped**。Stage 2: 34 passed / 1 skipped；Stage 1: 99 passed / 1 skipped；Smoke: 7 passed / 9 skipped。两阶段各 1 skipped 为真实 Loader/Parent-Child 集成，Smoke 因 LangChain、OCR/文档格式、模型/数据库/API 依赖不足跳过；SKIPPED 不代表 PASS。

覆盖文件重复/一字节变化/binary/流式大文件/已知 abc digest、NFC/换行/尾随空白与正常字符差异、JSON 组件边界、跨进程确定性、跨文档/Parent 隔离、重复 occurrence、版本独立、路径移动/遍历顺序、无关块插入、Front Matter 原文件 Hash 与 sidecar 排除、非法 Metadata 不计算 Hash、Loader 同名 Hash 冲突、Metadata 保留、多个 Loader 输出和 Legacy ID。

真实 SHA256/Schema/Parser 函数均执行。隔离 Processor 测试使用合成 Loader/Splitter 的受控分块边界，只验证本次身份控制逻辑；真实端到端未运行。首次测试的遍历替身误改全局 os.walk，影响 tempfile cleanup；已限定到 Processor 模块引用，复测通过，未改变业务代码以绕过失败。

Diff 审阅与 `git diff --check`: PASS；文档相对链接检查: PASS；变更 Python 文件的 Python 3.10 语法解析: PASS（不等同 Python 3.10 运行验证）。`git diff --cached --check`: PASS，覆盖全部新增文件补丁格式。

## Known Risks

- 真实 Loader/LangChain 分块集成仍缺依赖；未运行 Milvus/BGE/数据库/在线问答，不宣称完整集成 PASS。
- 原文件 Hash 与 Metadata/Loader 读取没有原子快照，调用期间源文件应静止；不提供持久化事务。
- 完全重复块前插入/删除相同内容时 occurrence 会重分配，不能识别历史语义实例。
- Parent 内容或切分边界改变会改变 Parent ID，进而改变该 Parent 下 Child ID；不同 Child 插入稳定性测试限定 Parent identity 不变。
- 一个 document_id 应代表单一文档版本快照；混入同 ID 的多主文件/版本不能承诺排序独立性。
- 改变切分参数或 Loader/Splitter 输出会影响内容/身份；没有切分版本 Manifest。
- Fingerprints exist in Document metadata, but Manufacturing Milvus persistence is **NOT IMPLEMENTED**。

## Deferred Features

Manufacturing Milvus Schema: NOT IMPLEMENTED — Stage 3。
Cross-run duplicate skip: NOT IMPLEMENTED — Stage 4。
Version Manifest / Persistent Ingestion State: NOT IMPLEMENTED — Stage 4。
Incremental Upsert Orchestration / Delta Delete / Stale Delete: NOT IMPLEMENTED — Stage 4。
Metadata Filter、意图/实体、Parent 聚合、BM25、SSE、Hit@K/MRR/RAGAS 不在本任务范围。

## Architecture Impact

Manufacturing File → Stage 1 Metadata Validation → Raw File SHA256 → Existing Loader → Parent Split → Parent SHA256 + Stable Parent ID → Child Split → Child SHA256 + Stable Child ID。Legacy 分支保持原逻辑；没有平行引擎、全局去重、跨运行 Skip、Manifest 或入库编排。现有 PK 仍 MD5(metadata["id"])，不是本次设计的新 Milvus 主键。

## Git

Commit / Push / Remote Verification: PASS。主提交消息：`feat: add stable document and chunk fingerprints`。已执行 Diff 审阅、`git diff --check`、`git diff --cached --check`、`git push`、`git fetch origin`、`git rev-parse HEAD`、`git rev-parse origin/main` 和 `git status`，验证 HEAD == origin/main、Working Tree clean。发布确认后的微小状态回写并入同一本次 Stage 提交，最终再 fetch 核对；最终 SHA 在用户回复提供，不预写本报告自身哈希。

## Stage 3 Readiness

YES（限定制造业持久化设计）：Metadata 合约与系统指纹/稳定身份已存在；Stage 3 需设计 Schema/PK/集合隔离及保存字段的验收，真实运行依赖与服务须另行准备。Full Integration Readiness: NO；Stage 3: PENDING，本任务完成后停止。
