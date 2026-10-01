# Manufacturing Metadata Schema — Stage 1

2026-10-01。正式合约为 `rag_qa/schemas/manufacturing_metadata.py`；安全解析和薄适配为 `rag_qa/ingestion/metadata_loader.py`。这是单文档级 Metadata，不支持型号列表或节级覆盖；不把多型号手册自动压成单型号标签。

## 字段

| 字段 | 类型 | 规则 |
| --- | --- | --- |
| document_id | 必填 string | trim、非空；保留大小写，不生成 ID/Hash |
| document_version | 必填 string | trim、非空；YAML 必须引用数字形版本，例如 `"1.10"`，数字不转字符串 |
| title | 必填 string | trim、非空 |
| knowledge_type | 必填 enum string | manual / alarm / fault / maintenance / parameter / parts / case；只 trim，不改大小写 |
| equipment_type / equipment_model / manufacturer | optional string | 只 trim；空白转 null；不强制型号，不做品牌词典/别名转换 |
| alarm_code | optional string | 保留大小写、符号和前导零；数字拒绝 |
| fault_type / fault_symptom | optional string | trim；空白转 null；没有封闭故障词典 |
| maintenance_type | optional string | trim；空白转 null |
| maintenance_cycle | optional object | 见下述子模型 |
| part_number | optional string | trim，保留符号和前导零；数字拒绝 |
| effective_date | optional date | YAML date 或 ISO 日期字符串；输出 ISO 日期；空白转 null，非法日期/时间戳拒绝 |
| language | string，默认 zh-CN | 显式非空字符串可覆盖；不自动检测 |

所有字符串均不做数字到字符串的隐式转换。`to_metadata()` 使用 Pydantic JSON 序列化：枚举为字符串、日期为 ISO、周期为普通 dict、可选空值为 null。

## 条件校验

- alarm 必须有 alarm_code。
- fault 至少有 fault_type 或 fault_symptom。
- maintenance 至少有 maintenance_type 或 maintenance_cycle。
- parts 必须有 part_number。
- manual / parameter / case 没有额外强制字段。

MaintenanceCycle 支持正的有限数值 value + unit，或非空字符串 trigger，也可以同时有完整周期和 trigger。unit 为 hour / day / week / month / year / cycle。value/unit 必须成对，即使有 trigger 也不能提供残缺的数值周期。拒绝零/负数、布尔值、数字字符串、无穷值、未知单位和未知字段；trigger 不建立额外企业规则词典。

顶层及 MaintenanceCycle 均 `extra=forbid`。拼写错误和系统字段均失败，包括 document_sha256、parent_content_sha256、child_content_sha256、parent_id、child_id、ingestion_version、vector_id、created_at，以及 source/file_path/timestamp/source_file/metadata_source。后续身份与版本字段不能由 YAML 伪造。

## 来源与安全解析

TXT / Markdown 允许首行 `---` 的 Front Matter，下一行独立 `---` 结束；接受 UTF-8 BOM 和 CRLF。缺结束标记报错。文件头后才出现的 `---` 属于正文，不自动识别为 Metadata。

所有现有支持格式可以使用 `<完整原文件名>.yaml`，例如 `manual.pdf.yaml`、`manual.docx.yaml`、`manual.txt.yaml`，不查找 `manual.yaml`。PDF / DOCX / PPT(X) / PNG / JPG 使用 sidecar，不读取二进制内部 YAML。已有 `.ppt` 仍映射原 PPTX 加载器，不能据此声称真实老 PPT 受支持。

一个文件只能有一种权威来源：Front Matter 和 sidecar 同时存在，即使 sidecar 为空也报 MetadataSourceConflictError。制造业模式缺来源报 MissingMetadataError，并指明原文件。

先用 SafeLoader 子类拒绝重复键，再使用 `yaml.safe_load`。空/null/空 mapping、列表、标量、非法语法和可执行 Python 标签均失败。不支持 YAML merge key；使用明确字段的单一 mapping。Pydantic 失败转为 InvalidManufacturingMetadataError，包含 file、metadata source、field、reason；不附带输入值或文档正文。读取失败与非法 YAML 用 InvalidYamlMetadataError；合并冲突用 MetadataMergeConflictError。异常向上抛出，不吞掉错误；处理器失败时不会返回供后续入库使用的完整文档列表，但不提供跨调用事务。

## 接入与兼容

```python
from rag_qa.core.document_processor import process_documents

# 显式制造业模式；需现有 Loader/Splitter 运行依赖，不访问 Milvus。
children = process_documents("path/to/manufacturing_files", metadata_mode="manufacturing")

# 原有位置参数保持兼容；默认 legacy 不读取或校验 YAML。
legacy_children = process_documents("rag_qa/data/ai_data")
```

`load_documents_from_directory(..., metadata_mode="manufacturing")` 也支持显式模式；未知模式直接拒绝。目录名不决定模式。现有 CLI 没有自动改为制造业入口；目前通过 Python 函数明确调用。

Front Matter 经验证后，只有正文写入生命周期受控的临时同名/同扩展名文件，交给原 TXT/Markdown Loader。原文件不改写；成功或 Loader 异常均清理临时目录；Loader 的 source/file_path 若等于临时路径则恢复原路径。二进制和 sidecar 文档直接走原 Loader，不改 OCR。

业务 Metadata + source_file（绝对路径）+ metadata_source（front_matter/sidecar）加入 Document.metadata；若 Loader 已持有同名字段，明确拒绝。现有处理器继续设置 source（目录名去 `_data`）、file_path（原输入路径）、timestamp（加载时间），与业务字段分离。source 仍是 Legacy 分类来源，不冒充设备业务标签。

现有 Splitter 负责 Metadata 继承。Legacy Parent/Child 保持 `doc_i_parent_j` / `doc_i_parent_j_child_k`；Stage 2 Manufacturing 已增加原文件与内容 SHA256 和稳定身份，规则见 [MANUFACTURING_FINGERPRINTS.md](MANUFACTURING_FINGERPRINTS.md)。当前 VectorStore 不完整持久化业务字段/指纹，不应将此接口直接当作完成的制造业 Milvus 摄取链路。

## Synthetic examples

以下仅为合成单元测试示例，不是真实企业生产材料。TXT/MD 可以将任一 YAML 放在首尾 `---` 之间，结束标记后的正文才进入 page_content；二进制使用完整文件名 sidecar。

```yaml
document_id: MZ2000-ALARM-001
document_version: "1.10"
title: Synthetic MZ-2000 E102 Alarm
knowledge_type: alarm
equipment_model: MZ-2000
alarm_code: E102
```

```yaml
document_id: MZ2000-MAINT-001
document_version: "1.0"
title: Synthetic Lubrication Maintenance
knowledge_type: maintenance
maintenance_cycle:
  value: 500
  unit: hour
```

```yaml
document_id: MZ2000-FAULT-001
document_version: "1.0"
title: Synthetic Vibration Fault
knowledge_type: fault
fault_symptom: Synthetic spindle vibration
```

```yaml
document_id: MZ2000-PART-001
document_version: "1.0"
title: Synthetic Spindle Bearing
knowledge_type: parts
part_number: BRG-6205-ZZ
```

测试命令：`python -m pytest tests/test_manufacturing_metadata.py -q -rs`。核心测试只需要仓库已声明的 Pydantic、PyYAML 和 requirements-dev 的 pytest；真实 Parent-Child 测试缺 Loader/LangChain 依赖时明确 SKIPPED。详细实测见 [Stage 1 报告](STAGE_REPORTS/STAGE1_REPORT.md)。

## System-generated Stage 2 fields

Stage 1 业务合约不增加 YAML 可写字段；document_sha256、parent_content_sha256、child_content_sha256、parent_id、child_id/id 均由系统生成，YAML 仍禁止提供。Loaded Document 增加原主文件 byte fingerprint；Child 继承业务字段、原文件 Hash、Parent 内容 Hash，并增加 Child 内容 Hash、稳定 parent_id 与相等的 child_id/id。

sidecar bytes 不参与 document_sha256；同一主文件更改 sidecar，原文件 Hash 可以不变。该字段不是业务版本或 Metadata 指纹，Stage 4 不可仅靠它做跨运行判断。
