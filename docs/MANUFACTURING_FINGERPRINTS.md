# Manufacturing Fingerprints — Stage 2

2026-10-02。算法在 `rag_qa/ingestion/fingerprints.py`，仅使用 Python 标准库。接入现有 Metadata Adapter 和 Processor；没有新的 RAG Engine、数据库操作或持久化状态。

## Document SHA256

`document_sha256 = SHA256(original source file bytes)`，流式、有限大小 block 读取，输出 lowercase 64-char hex。block size 不是业务语义。

制造业路径先完成 Stage 1 Metadata 校验，再对原主文件计算 Hash，之后调用原 Loader。TXT/Markdown 包含原始 Front Matter、BOM 和换行字节；不 Hash 临时 sanitized body。PDF 等只 Hash 主文件，**不包含 `<完整文件名>.yaml`**。

这是 **Source File Byte Fingerprint**，不是 Document Version Fingerprint、Metadata Fingerprint 或 Ingestion Version。sidecar 改变而主文件不变，document_sha256 不变是预期行为；Front Matter 在主文件内，修改它会改变原文件 Hash。

将来的 Stage 4 不能仅凭 document_sha256 决定版本或跨运行 Skip，还需 document_id、document_version、validated metadata / manifest state。本阶段没有 Manifest、跨运行 Skip、增量编排或删除。

## Content normalization

`normalize_content_for_hash(text)` 顺序为：Unicode NFC → CRLF/CR 转 LF → 每行 rstrip 去尾随空白 → 整体 strip 去首尾空白。最后 UTF-8 编码做 SHA256。只为 Hash 计算规范化，原 page_content / parent_content 保持原输出。

内部正常空格、行首缩进（整体首尾除外）、内部空行、大小写和标点不改；不做 NFKC、全半角转换、语义清洗。`A B` 与 `AB`、`E102` 与 `e102`、中文不同标点的 Hash 不同。NFC 等价形式、LF/CRLF/CR 和尾随空格可以相同。

## Stable identity formula

组件编码使用 canonical JSON array：`ensure_ascii=False`、`separators=(",", ":")`，UTF-8 SHA256，输出 lowercase 64-char hex。

```text
parent_id = SHA256(JSON(["parent", document_id, parent_content_sha256, occurrence]))
child_id  = SHA256(JSON(["child", document_id, parent_id, child_content_sha256, occurrence]))
```

document_id 来自 Stage 1 的已验证业务字段，保留业务大小写。编码明确区分组件边界，业务 ID 含 `:` 等字符也不会因字符串拼接产生歧义；不用 Python hash()。

document_version、document_sha256、绝对路径、timestamp、os.walk 排序、全局 i/j/k 均不参与制造业 ID。因此同一业务文档跨独立运行换版本、移动文件、改变其他文档遍历顺序时，只要 Parent/Child 规范化内容和同内容 occurrence 未变，ID 不变。不同 document_id 即使正文相同，内容 Hash 可以一样、ID 必须不同。

## Duplicate occurrence

Parent occurrence 以 document_id + parent_content_sha256 分组，从 0 递增；同一业务文档的多个 Loader 输出共享计数。Child occurrence 只在当前 Parent 的相同 child_content_sha256 内从 0 递增。不同内容的插入不增加其他 Hash 的计数；完全重复的块仍全部保留，不做去重删除。

每次调用重新计数；不持久化。输入应是一个业务 document_id 的单一文档版本快照，业务命名空间应唯一。混入多个主文件/版本却复用同一个 document_id 时，无法用正文识别重复块的历史来源，不能承诺跨文件排序/版本混合稳定性。

完全相同块之间缺乏额外语义锚点，若在已有重复内容前插入/删除同内容块，occurrence 会重新分配。Parent 内容或切分边界变化时，Parent ID 变化，其所有 Child 的 Parent namespace 随之改变；不承诺编辑 Parent 后所有 Child ID 保持不变。测试“不同 Child 插入不位移”限定 Parent identity 保持不变，以验证局部 occurrence 而非全局 k。

## Metadata and compatibility

Loaded Document 增加 document_sha256。Parent Metadata 增加 parent_content_sha256，id 是稳定 Parent ID，parent_content 为原 Parent 正文。Child 继承业务字段和 document_sha256/parent_content_sha256，并有 parent_id、parent_content、child_content_sha256、id 和兼容 child_id；`id == child_id`。

这些系统字段不能从 YAML 输入，Stage 1 extra=forbid 继续生效。Adapter 拒绝 Loader 提供同名 document_sha256；不允许覆盖系统计算结果。

只有显式 `metadata_mode="manufacturing"` 使用稳定 ID。默认 Legacy 仍是 `doc_i_parent_j` / `doc_i_parent_j_child_k`，不增加指纹或 child_id；旧 CLI 仍 Legacy。

## Persistence boundary

Stage 2 交付时 Fingerprints exist in Document metadata, but Manufacturing Milvus persistence was **NOT IMPLEMENTED**。Stage 3 后续已实现独立制造业集合、指纹字段与稳定 Child ID 直接 PK，详见 [存储合约](MANUFACTURING_MILVUS_SCHEMA.md)；Legacy PK 仍 MD5(metadata["id"])。本文件身份算法不变；真实服务写入/增量删除仍未验证或未实现。

文件 Hash、Metadata 读取、Loader 并非文件系统原子快照，调用时源文件应静止；没有锁、Manifest 或跨运行状态。切分参数/算法变化仍可能改变内容边界和身份。

## Validation

`python -m pytest tests/test_manufacturing_fingerprints.py tests/test_manufacturing_metadata.py tests/test_stage0_smoke.py -q -rs`。

Hash/规范化/ID 核心测试真实执行；Processor 的控制边界测试使用合成 Loader/Splitter 替身隔离 identity bookkeeping，不算 LangChain/OCR 集成。真实 Loader/Parent-Child 环境不足时明确 SKIPPED；结果见 [Stage 2 报告](STAGE_REPORTS/STAGE2_REPORT.md)。
