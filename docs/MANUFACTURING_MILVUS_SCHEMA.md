# Manufacturing Milvus Schema — Stage 3

2026-10-02。正式代码合约为 `rag_qa/core/milvus_schema.py`，通过现有 VectorStore 的显式 `schema_mode="manufacturing"` 接入。Schema/Row Mapper/隔离控制已实现并测试；真实 Milvus 服务尚未验证，不能将 SDK 离线测试视为成功创建生产集合。

2026-10-05 Completion V2补充：上述为Stage 3交付时的历史验证边界。隔离Milvus server pkg/v2.5.4 / client2.5.4已通过nullable=None写读探针、完整Schema/Index核验与42 Child实际upsert；仅受控synthetic评估，不代表生产集合已部署，详见[Stage 12报告](STAGE_REPORTS/STAGE12_REPORT.md)。

## Collection and versions

Legacy 默认 `MILVUS_COLLECTION_NAME=edurag`，原 Schema、动态字段及 MD5 PK 保留。Manufacturing 默认独立 `MILVUS_MANUFACTURING_COLLECTION_NAME=manufacturing_rag_v1`；INI 键为 `[milvus] manufacturing_collection_name`。优先级仍为进程环境变量 → config.ini → fallback；示例与 Compose 已同步，未更改本地 config.ini。

配置同名直接失败；Manufacturing 不能选择配置中的 Legacy 名称或 edurag，Legacy 不能选择配置中的 Manufacturing 名称。检查在加载模型、连接服务之前执行。显式自定义集合名应保留版本后缀语义，旧在线/CLI 调用默认仍 Legacy，不自动切换。

`manufacturing_rag_v1` 的 v1 是 **Storage Schema Version**，row 的系统字段 `schema_version="manufacturing_v1"` 自动添加；与 document_version（业务文档版本）及未来 Ingestion Manifest Version 区分。YAML 不能输入 schema_version，Stage 1 extra=forbid 保持有效。

## PK and fields

`auto_id=False`、`enable_dynamic_field=False`。唯一主键为 VARCHAR(64) id，直接使用 Stage 2 稳定 Child ID：`Milvus PK == metadata["id"] == metadata["child_id"]`，不做第二次 Hash。

VARCHAR 的 max_length 和 Row 长度校验按 UTF-8 bytes，统一在合约模块定义；超长报错，不截断。Required 表示非 nullable；Optional 在 row 中统一用 None，对应 nullable=True，不用空字符串/N/A/"null" 占位。

| Field | Milvus Type | Required / Optional | Source | Purpose |
| --- | --- | --- | --- | --- |
| id | VARCHAR(64), PK | Required | Stage 2 | 稳定 Child Identity |
| text | VARCHAR(65535) | Required | Loader/Splitter | 原 Child 正文 |
| dense_vector | FLOAT_VECTOR(runtime dim) | Required | BGE-M3 | Dense 向量 |
| sparse_vector | SPARSE_FLOAT_VECTOR | Required | BGE-M3 | Sparse 向量 |
| schema_version | VARCHAR(64) | Required | Stage 3 system | manufacturing_v1 |
| child_id | VARCHAR(64) | Required | Stage 2 | 与 PK id 一致 |
| parent_id | VARCHAR(64) | Required | Stage 2 | 稳定 Parent Identity |
| parent_content | VARCHAR(65535) | Required | Splitter | 原 Parent 正文 |
| document_id | VARCHAR(256) | Required | Stage 1 | 业务 namespace |
| document_version | VARCHAR(64) | Required | Stage 1 | 严格字符串业务版本 |
| document_sha256 | VARCHAR(64) | Required | Stage 2 | 原主文件 bytes 指纹 |
| parent_content_sha256 | VARCHAR(64) | Required | Stage 2 | 规范化 Parent 指纹 |
| child_content_sha256 | VARCHAR(64) | Required | Stage 2 | 规范化 Child 指纹 |
| title | VARCHAR(1024) | Required | Stage 1 | 文档标题 |
| knowledge_type | VARCHAR(32) | Required | Stage 1 | 七种受控类型的字符串 |
| equipment_type | VARCHAR(128) | Optional | Stage 1 | 设备类型 |
| equipment_model | VARCHAR(256) | Optional | Stage 1 | 保留业务型号字符 |
| manufacturer | VARCHAR(256) | Optional | Stage 1 | 制造商 |
| alarm_code | VARCHAR(128) | Optional / alarm 条件必填 | Stage 1 | 报警码字符串 |
| fault_type | VARCHAR(256) | Optional | Stage 1 | 故障类型 |
| fault_symptom | VARCHAR(8192) | Optional | Stage 1 | 故障现象 |
| maintenance_type | VARCHAR(256) | Optional | Stage 1 | 维保类型 |
| maintenance_cycle_value | DOUBLE | Optional | Stage 1 flattened | 正数周期值 |
| maintenance_cycle_unit | VARCHAR(16) | Optional | Stage 1 flattened | hour/day/week/month/year/cycle |
| maintenance_cycle_trigger | VARCHAR(256) | Optional | Stage 1 flattened | 状态触发字符串 |
| part_number | VARCHAR(256) | Optional / parts 条件必填 | Stage 1 | 备件号字符串 |
| effective_date | VARCHAR(10) | Optional | Stage 1 | ISO YYYY-MM-DD |
| language | VARCHAR(32) | Required | Stage 1 | 默认 zh-CN，可覆盖 |
| source_file | VARCHAR(4096) | Required | Stage 1 system | 原主文件 provenance |
| metadata_source | VARCHAR(32) | Required | Stage 1 system | front_matter / sidecar |
| source | VARCHAR(256) | Optional | Existing Processor | 目录来源，不替代型号/制造商 |
| timestamp | VARCHAR(64) | Optional | Existing Processor | 加载时间字符串 |

共 32 字段。fault 和 maintenance 的条件必填仍由 Stage 1 合约重新校验。结构化 MaintenanceCycle 不作为 JSON/Pydantic 对象写入：value/unit/trigger 扁平化，未提供的成员均为 None。

## Row validation

整个 batch 在 Embedding 前做 Metadata preflight，防止缺身份/非法元数据进入模型调用；所有 row 验证完成后才一次 upsert，不写部分非法 batch。id/child_id/parent_id 与三种 Hash 全部验证 lowercase 64-char hex，id 与 child_id 不一致报 ManufacturingRowValidationError，包含 child id、字段和原因，不输出正文。

重新校验 Stage 1 业务 Schema；版本不转数字。业务 Enum/date/周期转换为普通字符串、ISO 日期和扁平 number/None；source_file 的 Path 与 timestamp 的 datetime 可显式转字符串。未知 Metadata 拒绝，不静默丢字段；允许已有 file_path 作为输入 provenance，但 row 使用 source_file，不重复存储 file_path。原单文档 Loader 可保留现有字段；若未来 Loader 添加字段，须显式设计映射。

Dense 维度由 `embedding_function.dim["dense"]` 传入，不写死 1024；row 检查长度和有限数值。Sparse 转普通整数索引/float 值的非空 dict，检查 uint32 索引及有限数值。制造业 Sparse 选取指定的二维 CSR 行；Legacy 提取逻辑保持。输出只有明确 Schema 字段与 Milvus 支持的普通结构，不含 Enum、Pydantic、Path 或 datetime 对象。

## Indexes and existing collections

- Dense：dense_index，IVF_FLAT / IP / nlist=128。
- Sparse：sparse_index，SPARSE_INVERTED_INDEX / IP / drop_ratio_build=0.2。
- WeightedRanker(0.8, 0.3)、nprobe=10 和切分参数不变；不做质量调参。

已存在 Manufacturing collection 必须 describe 后核对完整字段集合、类型、唯一 PK/auto_id、动态字段、nullable/default、VARCHAR 容量和 Dense dim，以及预期 Dense/Sparse 索引的字段、类型、metric 和参数。额外字段或长度漂移也不符合本 v1 合约；额外非基线索引不会被删除。SDK 描述省略的 false 属性按该 SDK 的默认 false 比较，集合 auto_id/dynamic 标志必须明确存在。

Completion V2修正SDK索引描述格式读取：nlist/drop_ratio_build可位于顶层或params映射，两处同时出现则必须都符合原规格。缺失、错误、非有限或冲突值仍拒绝，不改变字段/索引合约或跳过任何校验。

不匹配报 ManufacturingSchemaMismatchError，包含 collection、expected、actual；不继续 load/upsert，不 drop/rebuild/修复旧集合。若不存在，创建明确的新 Schema 和 indexes，再检查返回的 Schema/Index 后使用。SDK 2.5.4 的 create_collection 在带索引时可能自行 load 新建集合，现有集合的检查始终先于应用显式 load。服务端能力不足或 RPC 错误向上抛出，不回退动态字段或占位字符串。

Schema builder、nullable 序列化、原生 None Upsert 的 valid_data 编码已使用真实 pymilvus 2.5.4 离线验证。**未验证真实服务的 nullable/索引兼容性或成功写入**；服务器须支持当前显式合约。

## Explicit offline usage

下列是会写独立集合的调用示例，本阶段未对真实服务执行：

```python
from rag_qa.core.document_processor import process_documents
from rag_qa.core.vector_store import VectorStore

children = process_documents("approved/manufacturing_files", metadata_mode="manufacturing")
store = VectorStore(schema_mode="manufacturing")
store.add_documents(children)
```

需要既有 Loader/BGE-M3/Reranker 运行依赖、本地模型、已有 Milvus database 和兼容服务；不为获取维度下载模型。原 VectorStore 仍初始化 Reranker；本阶段不改生命周期或构造平行引擎。

## Verification and Stage 4 boundary

核心测试不要求 SDK/server；真实 SDK 离线测试可选。Live 仅显式 `STAGE3_LIVE_MILVUS=1`，连接 STAGE3_MILVUS_URI / STAGE3_MILVUS_DATABASE，在随机 `stage3_test_<uuid>_v1` 中 upsert 合成 rows、按 PK 读取字段、清理本测试成功创建的集合；不操作 edurag 或配置中的真实制造业集合。没有启用开关时 SKIPPED。

Stable PK enables Stage 4; it does not replace Stage 4。相同 Child ID upsert 同 PK 的写入路径已实现；真实服务替换语义需 Live 验证。V1 A/B/C → V2 A/B/D 时旧 C 仍可能保留。Manifest、跨运行 Skip、Incremental Diff、Delta/Stale Delete、版本激活/回滚尚未实现。制造业过滤路由/Parent 聚合、在线切换与检索质量也未实现。

实测与发布证据见 [Stage 3 报告](STAGE_REPORTS/STAGE3_REPORT.md)。
