# Manufacturing Versioned Ingestion — Stage 4

2026-10-02。正式入口为 `rag_qa/ingestion/versioned_ingestion.py` 的 `VersionedIngestion`，控制面为 `manifest_store.py` 的 `SQLiteManifestStore`。复用 Stage 1 Metadata Resolver、Stage 2 原文件 Hash/身份/切分和 Stage 3 VectorStore/Schema；不自动切换在线入口。单 worker / 单 writer，调用方必须串行执行所有摄取与删除；不支持 distributed multi-worker。

## Manifest and configuration

`MANUFACTURING_MANIFEST_DB_PATH` 优先于 INI `[ingestion] manufacturing_manifest_db_path`，fallback 为项目根下 `runtime/manufacturing_manifest.sqlite3`。示例 INI 的相对路径按工作目录解析，建议从仓库根执行或配置绝对路径。`runtime/` 已 Git 忽略；不提交 DB、WAL、journal 或本地路径配置。容器需自行配置持久化目录/挂载，当前任务没有启动或验证容器。

SQLite `active_documents` 以 document_id 为唯一 PK，每个文档只有一条 active record。Manifest DB 应固定对应同一 Milvus endpoint/database/collection；不是全局跨集合版本目录。表字段如下：

| Field | Meaning |
| --- | --- |
| document_id | Stage 1 业务 namespace / PRIMARY KEY |
| active_document_version | 最后一次成功提交的 opaque string |
| document_sha256 | Stage 2 原主文件 bytes Hash |
| metadata_sha256 | 规范化业务 Metadata Hash |
| processing_signature | 显式处理合约 Hash |
| collection_name / storage_schema_version | 数据面集合与 manufacturing_v1 |
| manifest_schema_version | 独立控制面版本 manifest_v1 |
| source_file / metadata_source | 成功快照的路径与来源 |
| child_ids / child_count | 排序的唯一稳定 IDs，compact JSON / count |
| revision / updated_at | 首次 1、成功更新递增 / UTC ISO 时间 |

初始化/提交/删除使用短事务，不在 OCR、Embedding、Milvus 网络调用期间持有 SQLite 写事务。提交/删除以 expected_revision 做 CAS；CAS 仅检测控制面旧读，不是多 worker 的数据面互斥锁。陌生数据库、未知 user_version、字段/类型/PK 漂移明确失败，不自动接管或修复。

## Metadata fingerprint and processing signature

`metadata_sha256()` 只选择 Stage 1 `ManufacturingDocumentMetadata` 业务字段，再调用 `to_metadata()` 规范化。canonical JSON 使用 `sort_keys=True`、`ensure_ascii=False`、`separators=(",", ":")`、UTF-8 SHA256，禁止非有限 JSON 数值。Enum、日期、周期和默认 None 按 Stage 1 合约归一化；不含 source_file/file_path/timestamp/运行字段/原文件 Hash/Child ID。

sidecar YAML key order 改变不会改变 Metadata Hash；业务值改变会改变。Front Matter 位于原主文件中，其 key order 改变仍会改变 document_sha256，不能因此跳过同版本源文件冲突。

`ProcessingContract` 包含 processing_contract_version、fingerprint_contract_version、Parent/Child size/overlap、storage_schema_version；同样 canonical JSON → SHA256。不 Hash 源码。实际传给 Processor 的参数与 signature 使用同一个对象；默认从当前 Config 读取，切分默认值未修改。合同版本初值分别为 manufacturing_processing_v1 / manufacturing_fingerprints_v1，表示现有处理与指纹规则。未来规则改变必须显式 bump 相应合约版本；模型/OCR 文件替换不会自动检测，应纳入处理合约版本治理。

## Version policy and skip

版本不转 float、不比较大小。不同 opaque version 可成为 active，只有最后 Manifest 提交成功才生效。

同版本但 source/业务 Metadata Hash 不同：`DocumentVersionConflictError`，必须 bump document_version。同版本、内容/Metadata 相同而 processing_signature 变：REINDEX。Manifest 集合或 Schema 不兼容：`ManifestCompatibilityError`，要求显式迁移。

只有 version、两个输入 Hash、signature、集合/Schema 都一致，且 Strong 完整查询的 Milvus IDs 等于 Manifest IDs，才返回 SKIP_UNCHANGED。返回前再次确认输入未变；无 Loader/OCR、Split、Embedding、Upsert、Delete 或 revision/updated_at 更新。纯文件/Metadata 读取与 Hash、SQLite 读取和 Milvus 查询仍会发生。Source 路径和 runtime timestamp 不参与 skip 条件；仅移动未变文件不会刷新持久化 provenance。

## Mutation order and diff

1. Preflight 原文件与 Stage 1 Metadata，读取 Manifest，检查兼容和版本策略。
2. 处理单一 authoritative source 的完整 Child 快照；复用 `process_document_file()` 和原共享切分实现。
3. 再 Hash/解析 source + business Metadata，变更或失效报 SourceChangedDuringIngestionError。
4. 验证每个 Child 的业务快照/版本/原文件 Hash/provenance 与 preflight 一致，拒绝重复 PK。空 Processor 结果失败，删除必须走显式入口，避免空 Loader 输出触发意外清库。
5. 完整查询 actual_ids；added=desired-actual，retained=desired∩actual，removed=actual-desired。
6. Upsert 全部 desired，包括 retained，确保新版本/标题/设备标签等 scalar 更新。
7. Strong 查询确认 desired 全部存在，失败禁止 stale delete。
8. 按 stable PK 删除 removed。
9. Strong 完整查询验证 final IDs == desired。
10. 最后提交 Manifest，成功才递增 revision。

状态为 INGEST（无 Manifest）、UPDATE（版本不同）、REINDEX（仅处理合约改变）、RECONCILE（同输入但实际快照漂移）、SKIP_UNCHANGED；结果还包含排序的 added/retained/removed IDs。

管理方法仅允许 manufacturing 模式。`list_document_child_ids()` 采用 pymilvus 2.5.4 `query_iterator(limit=-1, batch_size=1000, consistency_level="Strong")` 读至空页、finally close，不使用固定 query limit。document_id 使用 JSON string literal 编码；校验返回 document_id 与 id/child_id 一致、PK 格式和唯一性。`delete_child_ids()` 先校验全 batch，再按 1000 PK 分批删除；Legacy 拒绝管理/删除入口。这是离线摄取 administration，不是 Stage 6 在线 Metadata Filter。

## Failure recovery and explicit delete

Upsert 失败/部分失败：不删 stale，不推进 Manifest。Delete 失败/部分失败：保留旧 Manifest。最终查询不符或 SQLite 提交失败：同样不推进。下一次以旧 Manifest、当前 authoritative input 与实际 Milvus 重新处理，Upsert desired、删除实际 stale、最终验证、再提交。没有自动回滚已写 Milvus 数据，也没有跨系统 ACID 或历史版本存档/自动 rollback。

`delete_document(document_id)`：查询 actual → 按 PK delete → verify empty → delete Manifest。Manifest 删除失败时实际数据可已空，重试仍能删除旧控制记录。重复调用返回 NOOP；其他 document_id 不受影响。

目录入口先读取所有支持的主文件 Metadata/ID，忽略 YAML sidecar，首个 mutation 前拒绝同 batch duplicate document_id。不同文件不能共用一个 namespace；目录缺文件不自动 prune。目录 batch 不具备原子性，后续文档失败时此前成功文档保留；应串行重试。

## Usage

以下示例会写制造业集合，需已准备原 Loader/BGE/Reranker 依赖、模型、Milvus database 和兼容服务；本阶段没有对真实服务运行：

现有 VectorStore 构造仍会初始化本地 BGE/Reranker；Skip 保证无 Loader/切分/Embedding 推理与数据面 mutation，不代表构造无需模型资源。

```python
from rag_qa.core.vector_store import VectorStore
from rag_qa.ingestion.manifest_store import SQLiteManifestStore
from rag_qa.ingestion.versioned_ingestion import VersionedIngestion

vectors = VectorStore(schema_mode="manufacturing")
try:
    with SQLiteManifestStore() as manifest:
        ingestion = VersionedIngestion(manifest, vectors)
        result = ingestion.ingest_file("approved/manual.pdf")
        # ingestion.ingest_directory("approved")  # duplicates preflight, no pruning
        # ingestion.delete_document("MANUAL-001")  # explicit destructive operation
finally:
    vectors.client.close()
```

## Validation limits and next boundary

测试使用真实临时 SQLite、Stage 1 解析/Stage 2 身份/Stage 3 Row Mapper 与有状态合成网关。接线测试执行真实 Processor/VectorStore 方法，但 Loader、Splitter、模型和网络为替身。验证最终 Row 集合 A/B/D 且 C absent、跨运行 Skip、scalar 刷新、失败收敛及其他文档隔离；不只检查 delete 被调用。

未执行真实 Milvus/OCR/BGE；Full Integration Readiness: NO。Strong 查询的实际服务兼容性、负载/大 batch 写入、容器持久化仍需验证。网络错误直接失败，可串行重试；没有无限重试或错误吞掉继续提交。

Source 应在摄取期间静止：两次 Hash/Metadata 校验和输出一致检查不是文件系统锁，不能保证发现 ABA 变化或校验后外部写入。在线查询可能短暂看到混合快照，因为 Milvus 与 SQLite 不具备分布式事务；ID 集合验证不审计历史 Row scalar/向量正确性。

Stage 5–13 PENDING；Intent/Entity、Metadata Retrieval Filter、Parent/Reranker/BM25/SSE/Evaluation 均未实施。实测和 Git 证据见 [Stage 4 报告](STAGE_REPORTS/STAGE4_REPORT.md)。
