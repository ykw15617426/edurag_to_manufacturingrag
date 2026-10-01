# Stage 3 — Milvus Manufacturing Schema

## Status

2026-10-02。Implementation: PASS；Validation: PASS（限定下述实测范围）；Stage 3: PASS。Stage 0–2 / Governance: PASS；Stage 4–13: PENDING；Full Integration Readiness: NO。

## Goal

把 Stage 1/2 合约、指纹和稳定身份接入明确的独立 Manufacturing Milvus 持久化路径，不切换旧在线系统、不改 Stage 2 算法、不实施版本摄取或删除。

## Repository Baseline

Repository: https://github.com/ykw15617426/edurag_to_manufacturingrag；Branch: main。
Stage Start HEAD: `53608eac4ba86f558e85a6be840fbdb45bb56400`。
初始工作区 clean；`git fetch origin` 后 HEAD == origin/main。已读取规定的治理、架构/迁移/Schema/Fingerprint 文档、Stage 1/2 报告及实际 VectorStore、Processor、Metadata/Fingerprints/Schema、配置、Compose、requirements 和测试。

仓库指定 pymilvus 2.5.4。检查真实 SDK 的 FieldSchema/CollectionSchema、describe_collection、describe_index 以及 Prepare row Upsert 编码；没有凭旧示例选择 API。Stage 1/2 报告保持历史结论，不回写成完整集成 PASS。

## Collection Isolation

新增 MILVUS_MANUFACTURING_COLLECTION_NAME，默认 manufacturing_rag_v1；INI、示例和 Compose 同步。schema_mode 默认 legacy，只有显式 manufacturing 使用新集合。配置或显式选择与 Legacy 集合重名时在加载模型/连接服务前失败。没有创建、修改或删除真实用户集合；记录客户端只验证调用顺序。

## Schema Design

Manufacturing Milvus Schema: IMPLEMENTED。
Independent Manufacturing Collection: IMPLEMENTED（配置及创建/兼容检查代码；真实创建未执行）。

32 个明确字段，auto_id=False、dynamic field=False；Dense dim 从 embedding_function.dim["dense"] 传入，Sparse 保留。Optional 使用 nullable=True / Python None。VARCHAR 长度集中定义并按 UTF-8 bytes 校验；text/parent_content 保持 65535 容量，路径 4096。Schema version=manufacturing_v1 为系统字段，不允许 YAML 输入。

字段表和规则统一见 [MANUFACTURING_MILVUS_SCHEMA.md](../MANUFACTURING_MILVUS_SCHEMA.md)。真实 SDK builder 与 native NULL 序列化已离线验证；服务端 nullable 支持仍需 Live 验证，不静默回退占位字符串或动态字段。

## Primary Key Design

Stable Child ID as PK: IMPLEMENTED。直接使用 Stage 2 metadata["id"]，要求与 child_id 一致；不再二次 MD5/SHA256。Legacy MD5(metadata["id"]) 保持原逻辑。Collection Schema Version、Document Business Version、未来 Ingestion Manifest Version 明确区分。

## Field Mapping

Manufacturing Metadata Persistence: IMPLEMENTED（Row/Upsert 路径，真实数据库写入未验证）。
Fingerprint Persistence: IMPLEMENTED（字段及映射，真实数据库写入未验证）。

重新校验 Stage 1 业务字段、required 字段、六个稳定 ID/Hash 的 lowercase 64-char hex、id/child_id 一致性。周期拆成 value/unit/trigger，日期为 ISO，业务版本保持字符串。Plain row 不带 Pydantic/Enum/Path/datetime；未知 Metadata 拒绝；已有 file_path 仅作为允许的输入 provenance，由 source_file 字段明确持久化。

整个 batch 在 Embedding 前验证 Metadata；全部 row 的向量维度、有限值、Sparse 索引及长度通过后才一次 upsert。错误包含 Child ID/字段/原因，不输出正文。原 parent_content 与业务 Metadata 不丢失，source 仍是目录来源而非设备业务标签。

## Index Design

Dense/Sparse Index Definitions: IMPLEMENTED。
Dense: IVF_FLAT / IP / nlist=128；Sparse: SPARSE_INVERTED_INDEX / IP / drop_ratio_build=0.2。
WeightedRanker(0.8,0.3)、nprobe=10、切分配置和 Stage 2 身份算法不变。没有质量评估或调参。

## Existing Collection Compatibility

已有 Manufacturing collection 在显式 load 前检查完整字段集合、PK/auto_id、向量 dim、类型、nullable/default、容量及预期索引配置。不匹配报 ManufacturingSchemaMismatchError（collection / expected / actual），不 load/use/drop/重建。新建集合也检查 introspection 结果，能力不支持时失败。

SDK 2.5.4 带 index_params 的 create_collection 会自行创建索引并 load **新建**集合，随后适配器再核对返回的 Schema/Index；没有对已有不兼容集合走该路径。没有自动迁移或删除代码。SDK/RPC 错误向上抛出，不吞掉错误以继续操作。

## Legacy Compatibility

默认集合、Schema（dynamic=True）、MD5 PK、文本/Parent 字段、索引与检索参数保持。旧 app/new_main/rag_main 默认调用未修改。原位置 ID 与 YAML 校验/Stage 2 指纹测试继续通过。

制造业分支提取指定二维 CSR Sparse 行，避免使用 Legacy 的 fallback 第 0 行；Legacy Sparse 分支未改。原 VectorStore 仍初始化 BGE/Reranker，未复制平行引擎或下载模型。

## Implementation Summary

新增纯 specs/Schema/Row/兼容辅助模块 milvus_schema.py；SDK 导入延迟到 builder。现有 VectorStore 增加 schema_mode 和独立集合选择、制造业 Schema ensure 与 batch preflight/strict rows；Embedding/Search/Reranker 仍复用。配置和治理只同步新增参数及当前阶段。

## Changed Files

- `rag_qa/core/milvus_schema.py`：32 字段、Index specs、Row mapper、兼容检查与创建/加载编排。
- `rag_qa/core/vector_store.py`：显式模式、隔离选择、严格 upsert 和制造业 Sparse 行提取。
- `base/config.py`、`config.example.ini`、`docker-compose.yml`：新增独立集合配置。
- `tests/test_manufacturing_milvus_schema.py`：核心合约、Row、Legacy/隔离控制、SDK 离线及 optional Live。
- `tests/test_manufacturing_metadata.py`：schema_version 不可由 YAML 输入。
- `docs/MANUFACTURING_MILVUS_SCHEMA.md`、本报告：正式合约与验收证据。
- `docs/CURRENT_ARCHITECTURE.md`、`docs/MANUFACTURING_MIGRATION_PLAN.md`、`docs/MANUFACTURING_METADATA_SCHEMA.md`、`docs/MANUFACTURING_FINGERPRINTS.md`：增量事实及历史/后续边界。
- `AGENTS.md`、`.agent/PLANS.md`、`README.md`、`docs/README.md`：治理状态、任务计划和导航。

共 17 文件。Processor、Fingerprint 算法、业务 Schema、requirements、旧数据、模型、本地 config.ini 和 Stage 0–2 报告未修改。

## Tests

Windows / Python 3.13.9。沿用 Git 忽略的 .venv/stage1-validation：Pydantic 2.12.5 / pydantic_core 2.41.5 / PyYAML 6.0.3 / pytest 8.4.2；安装 pymilvus 2.5.4 验证真实 SDK API。首次按依赖范围安装最新 setuptools 时 pkg_resources 缺失导致 SDK 导入失败；按仓库 pin setuptools 75.1.0 修正，同时对齐 protobuf 6.33.5、numpy 2.2.6、pandas 2.3.1、ujson 5.11.0；grpcio 1.67.1 与仓库一致。没有更改仓库依赖或安装/下载模型。

| Command | Result | 范围 |
| --- | --- | --- |
| `.venv/stage1-validation/Scripts/python.exe -m pytest tests/test_manufacturing_milvus_schema.py tests/test_manufacturing_fingerprints.py tests/test_manufacturing_metadata.py tests/test_stage0_smoke.py -q -rs` | 244 passed / 0 failed / 12 skipped | Stage 3 103/1；Stage 2 34/1；Stage 1 100/1；Smoke 7/9 |
| `python -m pytest tests/test_manufacturing_milvus_schema.py -q -rs` | 101 passed / 0 failed / 3 skipped | 原环境缺 SDK，核心合约/映射/记录客户端仍实际运行；2 SDK + 1 Live 跳过 |

Schema Unit/Row Mapping/Legacy Regression/Compatibility Control: PASS。真实 pymilvus 2.5.4 无服务器 builder、verify、IndexParams 及 NULL Upsert Protobuf 编码: PASS。模型实际维度、Embedding 推理、真实 Milvus 创建/upsert/PK 查询: NOT RUN / Live SKIPPED。

覆盖独立名称/碰撞拒绝、严格字段/nullable/运行维度/版本/周期、原样 PK、版本与日期/对象序列化、required/hash/ID 不一致/超长/未知字段/无效向量失败、匹配 Schema、缺字段/类型/PK/dim/default 漂移、索引不符拒绝 load、Legacy Schema/PK 保留、非法 batch 不触发 Embedding/upsert。记录客户端只证明控制逻辑，不证明真实服务、模型或替换语义。

Live 测试默认未开启；只有 STAGE3_LIVE_MILVUS=1 才操作唯一随机 stage3_test_<uuid>_v1 测试集合，不访问 edurag/配置制造业集合，清理本测试成功创建的集合。没有启用开关、没有生产集合改动。

`git diff --check`: PASS；文档相对链接检查: PASS；变更 Python 文件的 Python 3.10 语法解析: PASS（不等同 Python 3.10 运行测试）。源码 Diff 审阅确认 Stage 1/2 算法、历史报告与 requirements 保留；`git diff --cached --check`: PASS（含全部新增文件）。

## Known Risks

- 真实 Milvus server 版本/nullable/index/写入未验证；真实 Loader/BGE/Reranker 链路仍缺依赖。Full Integration Readiness: NO。
- 实际 Embedding dim 来自运行模型；4/7 仅 synthetic specs，不能当作 BGE 维度验证。
- 严格未知 Metadata/UTF-8 byte 容量可能暴露额外 Loader 字段或超长材料，须显式映射/治理，不静默截断。
- 不检查既有集合历史 rows 的业务状态；Schema 合法不等于全库数据已迁移或版本一致。
- 失败新建可能留下未完成索引/加载的独立集合；不自动删除生产集合。Live 创建未成功返回时不会冒险删除未知所有权对象。
- Stable PK 只提供同身份 upsert 路径；V1 A/B/C → V2 A/B/D 的 C 仍可能残留。Stable PK enables Stage 4; it does not replace Stage 4。
- 原在线 Parent 聚合仍不保留全部制造业 Metadata，制造业过滤/引用/在线切换属于后续阶段。

## Deferred Features

Version Manifest / Persistent Document State: NOT IMPLEMENTED — Stage 4。
Cross-run Duplicate Skip / Unchanged Detection: NOT IMPLEMENTED — Stage 4。
Incremental Diff / Delta Delete / Stale Delete: NOT IMPLEMENTED — Stage 4。
Version Activation / Rollback: NOT IMPLEMENTED — Stage 4。
Metadata Retrieval Filter: NOT IMPLEMENTED — Stage 6。
Intent/Entity、Parent/Reranker/BM25 重构、SSE、Hit@K/MRR/RAGAS 不在本阶段范围。

## Architecture Impact

新增制造业显式离线持久化代码链路：Metadata/Fingerprints/Parent-Child → Metadata preflight → Dense+Sparse → Strict Row Mapping → 独立 Strict Manufacturing Collection。Legacy 默认不变；没有完整 Manufacturing RAG 或版本摄取完成的声明。

## Git

Commit / Push / Remote Verification: PASS。主提交消息：`feat: add manufacturing milvus schema`。本任务 17 文件已限定暂存、提交、推送并 fetch，核对 HEAD == origin/main 与 Working Tree clean；状态回写并入同一本阶段提交，最终 SHA 与再次验证结果在用户回复给出，不预写本报告自身哈希。AGENTS/PLANS 已更新 Last Completed Stage: Stage 3 — PASS、Active Stage: NONE；Stage 4–13: PENDING。

## Stage 4 Readiness

YES（限定版本/增量设计）：已有稳定 PK、业务版本/指纹字段及严格存储合约；真实服务/模型环境需按后续验收补齐。下一阶段须考虑 sidecar Metadata 变化，不能只凭 document_sha256。Stage 4–13: PENDING；本阶段完成后停止。
