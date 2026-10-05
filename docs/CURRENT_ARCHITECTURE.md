# 当前真实架构（Stage 0 基线 + Stage 1–12 增量）

审计日期：2026-10-01。源代码基线：`ff95920`，`main`。下列 Implemented 表示实际代码中存在该路径，不等于本次已完成端到端运行验证。

当前检查点（2026-10-05）：Stage 0–11 PASS；Stage 12 PARTIAL（框架/指标单测完成，真实检索/RAGAS NOT RUN）；Stage 13 PENDING，Full Integration Readiness: NO。以下历史章节保留其交付时状态。

## 1. 入口与模块职责

| 入口/目录 | 当前责任与边界 |
| --- | --- |
| `manufacturing_app.py` | Stage 11 独立FastAPI JSON/SSE；lifespan制造业runtime，import不构建客户端/模型 |
| `app.py` | FastAPI、静态网页、问候短路、HTTP/WebSocket、会话 API；模块级创建 IntegratedQASystem |
| `new_main.py` | 在线编排；MySQL/Redis/BM25 优先，流式 RAG 回退，MySQL 最近五轮历史 |
| `old_main.py` | Legacy 非流式编排；使用 `rag_system.py` |
| `rag_qa/rag_main.py` | 离线文档入库和旧纯 RAG CLI；仍使用 `rag_system.py` |
| `rag_qa/core/document_processor.py` | Loader 注册、目录遍历、学科 source、Parent/Child；没有 DocumentProcessor 类 |
| `rag_qa/core/vector_store.py` | BGE-M3、Milvus Schema/Index/upsert、hybrid search、父块恢复、CrossEncoder |
| `rag_qa/core/new_rag_system.py` | 分类、策略检索、历史 Prompt、4096 字符截断、token generator |
| `query_classifier.py` / `strategy_selector.py` | BERT 教育二分类；独立同步 LLM 选择四种策略 |
| `mysql_qa/` | `jpkb` CSV 导入、问题 BM25、Redis JSON 缓存；不是 SQL Agent |
| `static/index.html` | 当前 `/` 页，同源 HTTP + WebSocket，Markdown 渲染 |
| `static/old_index.html` / `static/src/App.jsx` | 旧页面/未接入 React 原型；React 期待 8000 `/query` SSE，与当前 API 不符 |
| `demo/` | LangChain、Milvus、Redis、BM25、日志等教学脚本，不属于生产调用链；部分有顶层副作用 |
| `rag_qa/evaluation/` | Stage 12 独立制造业标签/ID指标/真实组件观察适配与可选RAGAS，当前真实评估NOT RUN |
| `rag_qa/rag_assessment/` | 教育数据的独立 RAGAS 脚本和历史输出，未接在线真实召回 |

## 2. 离线入库链路

```text
python -m rag_qa.rag_main --data-processing --data-dir ./rag_qa/data
  → main(query_mode=False) 初始化 VectorStore（先尝试创建 OpenAI 客户端）
  → 遍历 config.VALID_SOURCES，拼接 <data-dir>/<source>_data
  → process_documents(dir) → load_documents_from_directory(dir)
  → os.walk（未排序）→ 根据扩展名选择 Loader → loader.load()
  → metadata: source = basename(dir).replace('_data', '')
              file_path = 原文件路径；timestamp = 当前本地 ISO 时间
  → MarkdownTextSplitter 或 ChineseRecursiveTextSplitter 生成 Parent
  → 对每个 Parent 再 split_documents 得到 Child
  → Child 带 parent_id/parent_content/id 和继承的 metadata
  → VectorStore.add_documents：批量 BGE-M3(texts)
  → dense + sparse 数据组装 → client.upsert(Milvus)
```

### Loader 的实际实现

| 格式 | 路径/实现 | 限制 |
| --- | --- | --- |
| TXT | LangChain TextLoader，UTF-8 | 无编码探测 |
| Markdown | UnstructuredMarkdownLoader；MarkdownTextSplitter | 非 YAML Metadata parser；系统级 Unstructured 依赖未验证 |
| DOCX | OCRDOCLoader：按 XML 块遍历段落、表格；段落内图片 OCR | 表格语义被平铺，未保留页码/结构 |
| PDF | OCRPDFLoader：PyMuPDF page.get_text + 大图 OCR | OCR 只覆盖宽高均达页面 60% 的图片；无 xref 图片不处理；整文档输出一条 Document |
| PPTX | OCRPPTLoader：形状排序、文本、表格、图片 OCR、组合递归 | `.ppt` 也注册了同一 python-pptx Loader，但二进制老 PPT 不保证支持 |
| PNG/JPG | OCRIMGLoader → RapidOCR | 未注册 JPEG/TIFF 等扩展名 |
| OCR | get_ocr 优先 rapidocr_paddle，ImportError 时退到 rapidocr_onnxruntime | 非导入类的 Paddle 初始化错误不会回退 |

`AliTextSplitter` 调用 ModelScope 文档分段模型，但当前 processor 未使用它。中文 splitter 没有末尾空字符串兜底分隔符，长无标点文本可能超过目标 chunk_size；这里只记录。

### ID 与幂等性

- Parent：`doc_{i}_parent_{j}`；Child：`doc_{i}_parent_{j}_child_{k}`。`i` 是 Loader 结果列表位置，不是全局文件 ID。
- 每次 process_documents 从 i=0 重置；每个 source 目录分别调用，因此不同学科也可能生成相同 Child ID。
- Milvus PK：`hashlib.md5(doc.metadata['id'].encode('utf-8')).hexdigest()`，无 source、文件、版本、内容参与。
- 同一位置重复 upsert 会覆盖，但不是文档/内容去重。目录顺序变化、插入/删除文本会改变 ID 与内容的对应。
- 没有文件字节 SHA256、规范化 Child SHA256、版本 Manifest、版本状态、差集删除、文档级事务。
- parent_content 重复存储在每条 Child 中；没有独立 Parent 表。file_path 在 Processor 中有，但 add_documents 未写入 Milvus。

### Milvus Schema / Index

`VectorStore._create_or_load_collection`：`auto_id=False`、动态字段启用。已有集合直接 load，没有 schema/index 兼容性检查。

| 字段 | 类型/边界 |
| --- | --- |
| id | VARCHAR(100)，Primary Key，MD5 位置 ID |
| text | VARCHAR(65535)，Child 文本 |
| dense_vector | FLOAT_VECTOR，dim=embedding_function.dim['dense']（代码注释 1024，实际值运行时取模型） |
| sparse_vector | SPARSE_FLOAT_VECTOR |
| child_id / parent_id | VARCHAR(100) |
| parent_content | VARCHAR(65535) |
| source / timestamp | VARCHAR(50) |

Dense：`IVF_FLAT / IP / nlist=128`。Sparse：`SPARSE_INVERTED_INDEX / IP / drop_ratio_build=0.2`。

Dense request 的真实字面值是 `param={'metric_type': 'IP', 'nprobe': 10}`；不是示例里嵌套的 `params.nprobe`。实际服务器是否应用该参数还未验证，不能声称有效 nprobe 已测为 10。Sparse request：`param={'metric_type': 'IP'}`。

BGE-M3 在 VectorStore 中固定 CPU，参数写作 `use_f16=False`；demo 写作 `use_fp16=True`。版本接口兼容性待验证，不在 Stage 0 静默改参数。CrossEncoder 本地 bge-reranker-large，固定 CPU。

## 3. 在线 Query 链路

```text
用户 → static/index.html → POST /api/query
  → check_greeting：匹配问候则直接返回，无数据库/RAG
  → new_main.IntegratedQASystem.query generator 的第一次消费
  → MySQL 最近 5 轮会话（有 session_id 时）
  → BM25Search.search(query, threshold=0.85)
      → Redis answer:<原始 query> 命中：返回缓存答案
      → 否则 jieba.lcut(query.lower())
      → BM25Okapi.get_scores（全问题库）→ softmax → argmax
      → best_score > 0.85 时 MySQL 按候选问题精确查答案
      → 查到则缓存 Redis，记录历史，yield(answer, True)
      → 不可靠/异常：返回 need_rag=True
  → new_rag_system.generate_answer
      → BERT predict_category（通用知识 / 专业咨询）
      → 通用知识：不检索，直接准备 Prompt
      → 专业咨询：StrategySelector 同步请求独立 OpenAI 客户端
          → 直接检索 / HyDE / SubQuery / Backtracking
          → 增强策略先完整消费 LLM 改写结果，再检索
          → VectorStore.hybrid_search_with_rerank
      → 拼接 Parent 上下文、历史、问题、客服手机号
      → 整体 Prompt 取前 4096 字符
      → 同步 DashScope stream → yield(token, False)
      → generator 全消费结束后写历史 → yield('', True)
```

BM25 是教育 FAQ 分支的优先匹配，不参与 Milvus Dense/Sparse 融合，也没有在 BM25 分支应用 source_filter。BM25 question corpus 启动时加载：Redis 两个全局 key 优先，否则 MySQL `SELECT question FROM jpkb`，jieba 分词后写 Redis；没有刷新和版本命名空间。

### Retrieval → Parent → Rerank

```text
Query/改写内容 → BGE-M3([query])
  → Dense AnnSearchRequest(limit=k) + Sparse AnnSearchRequest(limit=k)
  → 两路同用 source == '<source_filter>'（字符串插值）
  → Milvus hybrid_search(reqs=[dense, sparse], WeightedRanker(0.8, 0.3), limit=k)
  → _doc_from_hit(entity)：变成 Child Document（未保留 distance/score/child_id）
  → _get_unique_parent_docs：set(parent_content) → 仅带正文的 Parent Document
  → Parent 少于 2：直接截取 candidate_m
  → 否则 CrossEncoder.predict([[query, parent_content], ...]) → 排序 → Top M
```

默认 K=5、M=2；新版 SubQuery 内容字典去重后仍取前 M，没有跨子查询统一评分。旧 RAG 的 SubQuery 路径保留所有去重候选，区别记录后保持。

### HTTP / WebSocket 协议

- HTTP `/api/query` 只调用一次 `next(query_result, None)`；FAQ 完整答案可返回。RAG 第一个 token 后，HTTP 返回 `is_streaming=True` 与“请使用WebSocket”提示，**不把第一 token 返回给用户，也不完成历史写入**。
- 当前网页随后再次发送同一 query 到 WebSocket `/api/stream`，重跑历史/BM25/分类/检索/LLM。问题是生成器未完整消费及重复计算，不宜简单描述成“HTTP 返回第一个 token”。Stage 11 修复。
- WebSocket 正常消费同步 generator，发送 start/token/end/error；中途 await sleep 并不能使之前的同步调用变成异步。
- 无 SSE 服务端接口。React 原型检测 text/event-stream 不代表后端实现 SSE。
- async handlers 内同步 MySQL、Embedding、Milvus、BERT、CrossEncoder、LLM stream 会阻塞 event loop。全局共享 connection/cursor 也需要后续并发治理。

## 4. 已有能力矩阵

| Capability | Status | File | Notes |
| --- | --- | --- | --- |
| 多格式 Loader | Partial | document_processor.py；edu_document_loaders/* | TXT/MD/DOCX/PDF/PPTX/PNG/JPG 有实现；老 .ppt 支持未成立 |
| OCR | Implemented | edu_ocr.py；edu_*loader.py | 图像抽字路径存在，准确率与复杂版式未实测 |
| Parent-Child | Implemented | document_processor.py:77 | 两级切分；位置 ID、文本冗余 |
| BGE-M3 | Implemented | vector_store.py:43,117,170 | 同时消费 dense/sparse；模型调用兼容未跑 |
| Dense Retrieval | Implemented | vector_store.py:178 | Hybrid 内的一路；无独立公开 Dense API |
| Sparse Retrieval | Implemented | vector_store.py:186 | BGE-M3 sparse，不是 Milvus BM25 内置函数 |
| Hybrid Retrieval | Implemented | vector_store.py:193 | 两路 AnnSearchRequest |
| Milvus | Implemented | vector_store.py:52 | 需外部服务/已有数据库 |
| IVF_FLAT | Implemented | vector_store.py:84 | IP，nlist=128 |
| SPARSE_INVERTED_INDEX | Implemented | vector_store.py:92 | IP，drop_ratio_build=0.2 |
| WeightedRanker | Implemented | vector_store.py:196 | Dense=0.8，Sparse=0.3，保持 |
| BGE Reranker | Implemented | vector_store.py:39,217 | Parent CrossEncoder；分数未输出 |
| Upsert | Partial | vector_store.py:113 | 按位置 PK upsert；无版本增量和 stale delete |
| Metadata Filter | Partial | vector_store.py:176 | 只有 source 字符串表达式，无制造业字段过滤 |
| Legacy Parent Aggregation | Partial | vector_store.py:236 | set 正文去重，身份/metadata/score 丢失 |
| Legacy BM25 | Partial | mysql_qa/retrieval/bm25_search.py | FAQ 全库 softmax，冷启动候选 tuple 类型问题 |
| Redis | Implemented | mysql_qa/cache/redis_client.py | corpus/答案 JSON 缓存；无 TTL/版本 |
| MySQL | Implemented | mysql_qa/db/mysql_client.py；new_main.py | jpkb + conversations；CSV 导入非幂等 |
| Query Classification | Partial | query_classifier.py | 教育二分类；缺训练模型时新建分类头，不能视为可靠分类 |
| Manufacturing FAQ Fast Path | Implemented | retrieval/fast_path.py；manufacturing_bm25.py | Stage 8 approved Corpus、exact/歧义guard、raw BM25、Evidence/fallback；生产质量未评估 |
| Manufacturing Parent Retrieval | Implemented | retrieval/parent_aggregation.py；parent_reranker.py；manufacturing_retriever.py | Stage 7 身份/Metadata/命中统计与父块重排；真实模型/在线未验证 |
| Manufacturing Query Analysis | Implemented | query/analyzer.py；entities.py；classifier.py；schemas.py | Stage 5 规则/结构化语义边界；真实 LLM/在线未验证 |
| Strategy Selector | Implemented | strategy_selector.py | 同步 LLM 字符串选择器，不是制造业 Intent Router |
| HyDE | Implemented | new_rag_system.py:28 | 假设答案作为检索 query |
| SubQuery | Partial | new_rag_system.py:48 | 子查询检索存在；无全局融合排序 |
| Backtracking | Implemented | new_rag_system.py:90 | LLM 简化 query 后检索 |
| FastAPI | Implemented | app.py | 启动/HTTP 完整性/并发风险未修 |
| WebSocket | Implemented | app.py:190；static/index.html | 同步 token generator 驱动 |
| SSE | Missing | app.py | React 草稿不构成后端 SSE |
| RAGAS | Partial | rag_assessment/*.py | 对预填教育 QA/context 评估；历史结果含 NaN，不是在线回放 |
| Hit@K / MRR | Missing | rag_assessment/ | 无标签 ID 和 retrieval evaluator |
| Dockerfile | Implemented | Dockerfile | 镜像定义存在；构建未验证 |
| 完整 Compose stack | Partial | docker-compose.yml | 仅 edurag-app，无数据库依赖服务 |
| 旧非流式 RAG / CLI | Legacy | old_main.py；rag_system.py；sql_main.py | 保留回归参照 |
| 语义 splitter / demo Agent | Legacy | edu_model_text_spliter.py；demo/ | 主链路没有调用 |
| YAML / Pydantic Metadata | Implemented | schemas/manufacturing_metadata.py；ingestion/metadata_loader.py；document_processor.py | Stage 1 显式 manufacturing 模式；核心单元测试通过，真实 Loader/分块集成缺依赖未验证 |
| Document/Parent/Child SHA256 | Implemented | ingestion/fingerprints.py；metadata_loader.py；document_processor.py | Stage 2 指纹；Stage 3 制造业写入映射已实现，真实 Milvus 未验证 |
| Version Manifest / stale delete | Implemented | ingestion/manifest_store.py；versioned_ingestion.py；vector_store.py admin | Stage 4 单 worker 控制已测试；Live 未验证 |

## 5. 配置、部署与评估基线

| 项目 | config.example.ini | Compose / 代码 fallback |
| --- | --- | --- |
| Parent size / overlap | 512 / 120 | 1000 / 150 |
| Child size / overlap | 128 / 30 | 200 / 30 |
| Overlap 环境键 | PARENT_CHUNK_OVERLAP / CHILD_CHUNK_OVERLAP（代码） | 两者都读取 CHUNK_OVERLAP（Compose） |
| MySQL port | 3307 | Compose 3307；代码 fallback 3306 |
| Milvus database | itcast07 | itcast |
| LLM model | qwen3.8-max | qwen3.7-max-preview |
| 客服电话 | 教育客服占位 | 多处不同默认值 |

Stage 0 不统一这些业务值，避免默默改变已入库切分边界；Stage 1 前确认有效配置，后续用评估确定参数。Config 的 os.getenv 第二个参数会先求值，配置文件里的无效整数仍可能挡住合法环境覆盖。本次只把 Redis 密码改为字符串读取，VALID_SOURCES 改为 literal_eval；不自动加载 .env。

Dockerfile `COPY . .`，没有 `.dockerignore`：本地密钥/权重/简历可能进入构建上下文或镜像，即便被 .gitignore 排除。Stage 0 没有构建镜像、启动容器、改库、执行训练或入库。

评估文件：rag_evaluate_data.json 为 30 条，small 为 5 条，字段 question/context/answer/ground_truth。脚本对预填数据调用 RAGAS 四项指标，并直接 `DataFrame([result])` 输出对象信息。两个 CSV 是历史输出，不能作为本次通过证据。分类训练文件虽叫 model_generic_5000.json，实际是 **486 条 JSONL**；注释“90%+”没有本次实验支撑。

## 6. Stage 1 增量（2026-10-01）

真实新增链路：Manufacturing File → Metadata Resolver → Safe YAML → Pydantic Validation → Existing Loader → Document.metadata → Existing Parent-Child。入口为 Processor 的 `metadata_mode="manufacturing"`，默认 legacy；不按目录名检测业务域。Front Matter 在原 Loader 前剥离，二进制使用完整文件名 sidecar；不替换 OCR 或 Splitter。非法 Metadata/来源冲突明确抛异常，业务字段与 Loader 字段冲突拒绝。

字段与边界见 [正式合约](MANUFACTURING_METADATA_SCHEMA.md)，实测见 [Stage 1 报告](STAGE_REPORTS/STAGE1_REPORT.md)。当前有效 Parent/Child size 为 512/128、overlap 为 120/30，未改变配置或入库参数。位置 ID 仍为 doc_i_parent_j_child_k；旧数据/模型/集合不动。

Stage 1 当时 SHA256 / Milvus Manufacturing Schema / Versioning 未实现；SHA256 的后续实现见下述 Stage 2 增量。VectorStore 仍按旧字段写入，不持久化新增制造业 Metadata，现有 CLI/在线入口仍为 Legacy；不能据此声称制造业端到端检索可用。真实 Parent-Child 集成测试因依赖缺失 SKIPPED，Full Integration Readiness: NO。

## 7. Stage 2 增量（2026-10-02）

Manufacturing File → Stage 1 Metadata Resolver → Raw Document SHA256 → Existing Loader → Parent Split → Parent Content SHA256 + Stable Parent ID → Child Split → Child Content SHA256 + Stable Child ID。只有 manufacturing 模式生效；默认 Legacy 位置 ID 保留。原文件 Hash 流式计算，Front Matter 临时正文和 sidecar 不作为 Hash 输入。

稳定 ID 以 document_id 为业务 namespace，规范化内容 Hash 和同内容 occurrence 构成确定性 JSON 编码；不包含版本、路径、时间或全局位置。完全重复块保留并区分；业务 Metadata 与 parent_content 保留。详细算法及稳定性限制见 [指纹合约](MANUFACTURING_FINGERPRINTS.md)，验证见 [Stage 2 报告](STAGE_REPORTS/STAGE2_REPORT.md)。

Stage 2 当时 Milvus Manufacturing Schema: Missing；Version Manifest: Missing；Delta Delete: Missing。该阶段 VectorStore 未修改：PK 仍 MD5(metadata["id"])，业务字段/指纹没有完整持久化。无跨运行 Skip 或摄取编排。真实 Loader/Parent-Child 集成仍缺依赖，Full Integration Readiness: NO。

## 8. Stage 3 增量（2026-10-02）

制造业离线调用新增显式 `VectorStore(schema_mode="manufacturing")`：File → Metadata → Fingerprints → Parent/Child → Metadata preflight → Dense+Sparse → Strict Row Mapping → 独立 Manufacturing Collection。复用原 VectorStore/BGE-M3，不自动替换 app/new_main/rag_main 的 Legacy 默认。

默认集合 manufacturing_rag_v1、系统 schema_version=manufacturing_v1，32 个明确字段、auto_id=False、dynamic fields=False、稳定 Child ID 直接 PK；业务字段、三种指纹和 provenance 有持久化代码路径，周期 value/unit/trigger 扁平化，optional 使用原生 NULL。已有集合在使用前检查字段/PK/dim/nullable/容量/index；不匹配失败、不自动 drop。Legacy 集合、Schema 和 MD5 PK 保持原行为。详见 [存储合约](MANUFACTURING_MILVUS_SCHEMA.md) 与 [Stage 3 报告](STAGE_REPORTS/STAGE3_REPORT.md)。

真实 pymilvus 2.5.4 Schema/Index 构建及 NULL Upsert 编码已离线验证；真实 Milvus 服务/BGE 端到端写入未验证。Stage 3 交付时版本 Manifest、Cross-run document skip、Delta/Stale Delete、制造业 Intent/Metadata Filter 和 Parent Aggregation Refactor 尚未实现。稳定 PK 不等于增量摄取完成，旧版本消失的块仍可能残留。Full Integration Readiness: NO。

## 9. Stage 4 增量（2026-10-02）

显式离线 VersionedIngestion：Source/Metadata preflight → SQLite Manifest 与版本冲突检查 → 完全未变时 Strong 实际 IDs 验证并 Skip；其余调用现有单文件 Loader/共享 Parent-Child → 输入再次校验 → 实际 IDs Diff → Upsert 完整 desired → 确认 desired 存在 → stable PK 删除 stale → 验证最终快照 → 最后 SQLite Manifest 提交。

控制面 SQLiteManifestStore（manifest_v1）独立于数据面 manufacturing_v1，唯一 document_id active record、排序 Child JSON、revision CAS 与 UTC 更新时间。metadata_sha256 只 Hash Stage 1 规范业务字段；processing_signature 使用显式合约版本与实际切分参数。不改 Stage 2 Hash/ID、Stage 3 Schema/Row、Legacy、权重或 nprobe。

新增 manufacturing 专用 query_iterator 管理方法完整读取文档，安全编码 document_id，Strong 查询、关闭 iterator、批量按 PK delete；Legacy 拒绝这些路径。目录先预检重复 ID，sidecar 不作主文件，无自动 prune。显式删除验证 empty 后才移除 Manifest。SQLite 事务不跨 Loader/模型/网络；仅支持串行单 worker，不是 distributed ACID，在线读取可能短暂混合快照。

真实 SQLite、状态网关最终快照和失败恢复已验证；Processor/VectorStore 接线测试的 Loader/Splitter/模型/网络是替身，真实 Milvus/OCR/BGE 未运行。详见 [版本摄取合约](MANUFACTURING_VERSIONED_INGESTION.md) 和 [Stage 4 报告](STAGE_REPORTS/STAGE4_REPORT.md)。Stage 4 交付时 Intent/Entity、在线 Metadata Filter、Parent/Reranker/BM25/SSE/Evaluation 未实施，Full Integration Readiness: NO。

## 10. Stage 5 增量（2026-10-02）

新增独立轻量 QueryAnalyzer：原 Query → 规则标识符/显式描述实体 → 可注入 semantic classifier JSON → Pydantic Schema 校验 → 原文证据与规则优先 merge → QueryAnalysis。六意图与 high/medium/low 定性置信度、rules/llm/hybrid/fallback 来源和 warning codes；无 classifier 为 rules，服务/JSON/Schema 异常保留规则结果降级。未导入教育 BERT、策略、配置凭据或 SDK，general 无绕检索决定。

型号/报警/备件 ID 保留大小写/符号/前导零，日期/量值和无上下文 token 不猜；语义补值须原 query 完整文本证据，不能覆盖规则或改变确定性 token 角色。多值单字段拒绝任选，None + warning/low。不增加 Milvus Schema 字段、不生成 Filter、检索策略或答案；new_rag_system 和旧查询/策略文件原样保留。

synthetic core、独立进程阻断 Legacy/模型/API import 和 Stage 0–4 回归通过；真实 LLM 分类质量、API 超时/JSON 支持和在线集成未验证。合约见 [查询分析文档](MANUFACTURING_QUERY_ANALYSIS.md)，证据见 [Stage 5 报告](STAGE_REPORTS/STAGE5_REPORT.md)。Stage 5 交付时过滤策略未实施；Stage 6 增量见下节。Full Integration Readiness: NO。

## 11. Stage 6 增量（2026-10-02）

`rag_qa/retrieval/filters.py` 从 QueryAnalysis 构建固定字段的 hard/soft plan 与 JSON 编码安全表达式；high 且无严重 warning 才加 soft，其他情况 hard-only/NONE。`ManufacturingRetriever` 调用现有 `VectorStore.hybrid_search_children`；零结果只移除 soft，hard 标识符始终保留；异常不回退。general 仍检索。

新方法仅 manufacturing，Dense IP/nprobe10、Sparse IP、WeightedRanker(0.8,0.3) 不变；请求全部非向量字段，保留 Child/Parent/版本/三个指纹/业务/来源 Metadata 和原始 SDK score。返回 Child，不调用父去重或 CrossEncoder。旧 hybrid_search_with_rerank/分类/策略/在线编排未改，构造函数仍沿用既有模型初始化。

65 项 Stage 6 离线 policy/recording adapter/SDK 请求与 Stage 0–5 回归通过；Live Milvus、真实模型和在线制造业链路 NOT RUN。合约见 [制造业检索](MANUFACTURING_RETRIEVAL.md)，证据见 [Stage 6 报告](STAGE_REPORTS/STAGE6_REPORT.md)。Stage 6 交付时 Stage 7–13 PENDING；Stage 7 增量见下节。Full Integration Readiness: NO。


## 12. Stage 7 增量（2026-10-02）

`retrieve_parents` 复用 Stage 6 Child 检索及 filter attempts，按 parent_id 聚合全部公共 Metadata，冲突明确 ParentAggregationError。最大 Child score、命中 IDs/数量、首 rank 与每 Child 指纹/score/rank 保留；同正文不同 Parent 身份不合并。预排序为 best_retrieval_score DESC、first_child_rank ASC、parent_id ASC。

现有 vector_store.reranker 对 [原 query, parent_content] 评分，rerank_score 与 best_retrieval_score 分别保留；稳定 tie 后按 config.CANDIDATE_M 截断为完整 Parent Documents。空不调模型、单 Parent 仍评分；异常/数量错误/NaN/inf/non-scalar fail closed。默认 k 已由独立10改为延迟读取 config.RETRIEVAL_K；fallback5/Top-M fallback2和 ANN 参数不变。

Stage 7 79 项 synthetic/scorer/recording 测试与历史回归通过，总计544 passed / 0 failed / 12 skipped；真实 CrossEncoder/BGE/Milvus和在线未执行。VectorStore/filters/Legacy/在线代码、存储/摄取/查询合约及配置不改。合约见 [Parent 检索](MANUFACTURING_PARENT_RETRIEVAL.md)，证据见 [Stage 7 报告](STAGE_REPORTS/STAGE7_REPORT.md)。Stage 7交付时Stage 8–13 PENDING；Stage 8增量见下节。Full Integration Readiness: NO。


## 13. Stage 8 增量（2026-10-02）

`FastPathCorpus`由调用方批准的制造业Entry构建，严格Metadata/身份验证和canonical snapshot重建一致；不连接教育jpkb或Redis。`ManufacturingFastPath`优先hard-compatible唯一报警、normalized exact FAQ，再raw BM25排名；跨型号/重复含义与未安全确认code拒绝短路。所有hard ID保持，不猜实体；只有显式policy才允许BM25接受。

Tokenizer保持标识符大小写/-/_/前导零，中文用char/bigram；BM25复用requirements锁定的BM25Okapi，保留raw score/rank/total与scope size，不softmax。接受结果只提供Evidence和provenance；拒绝或search异常记录原因后原query/analysis/k回退Stage 7，Stage 7错误继续抛出。Legacy、在线和Stage 6/7实现未变。

62项Stage 8核心与Stage 0–7回归：606 passed / 0 failed / 12 skipped；真实BM25离线算法已运行，真实服务/模型/端到端NOT RUN。合约见 [制造业快路径](MANUFACTURING_FAST_PATH.md)，证据见 [Stage 8 报告](STAGE_REPORTS/STAGE8_REPORT.md)。Stage 8交付时Stage 9–13 PENDING，Full Integration Readiness: NO。


## 14. Stage 9 增量（2026-10-02）

`query/rewrite.py` 严格验证DIRECT/REWRITE/SUBQUERY与reason_code，planner可注入，无planner默认DIRECT。非法JSON/schema/超时/变体整体DIRECT回退。原query始终保留，最多4个子查询；确认硬标识符完整保留，新增ASCII token保守拒绝，重复稳定去重。不得重新分析变体或改变原QueryAnalysis生成的Filter。

`ManufacturingFastPath.probe`公开只探测、不触发Stage 7 fallback。Stage 9仅alarm_fault允许Exact Alarm，其他五意图仍可符合现有安全规则的FAQ/BM25；原Stage 8公开入口默认行为保留。`ManufacturingStrategyRetriever`复用Stage 6每变体Child检索，按child_id取最高raw score并检查Metadata/正文冲突；稳定排序后才复用Stage 7聚合及一次原query Parent rerank。融合provenance独立记录，不改变Parent Metadata一致性或config Top-M/k。

83项Stage 9核心验证通过；Stage 0–9回归689 passed / 0 failed / 12 skipped；真实LLM/Milvus/BGE/CrossEncoder及在线端到端NOT RUN。Legacy StrategySelector/HyDE/Backtracking/new_rag_system未修改；Manufacturing HyDE/Backtracking未实施。合约见 [制造业检索策略](MANUFACTURING_RETRIEVAL_STRATEGY.md)，证据见 [Stage 9 报告](STAGE_REPORTS/STAGE9_REPORT.md)。Stage 10–13 PENDING，Full Integration Readiness: NO。


## 15. Stage 10 增量（2026-10-02）

`rag_qa/generation`消费Stage 9 Parent/FastPath Documents及Stage 8 evidence，按最终顺序稳定E1/E2标识。规范化验证来源/业务属性/Parent身份与正文，同parent事实冲突或同doc多版本fail closed；每条Evidence必须兼容原QueryAnalysis全部hard字段，缺值不作wildcard。空Evidence直接静态insufficient且不调模型，general亦如此。

`StructuredAnswerGenerator(completion).generate(query, analysis, strategy_result)`以静态system约束supplied Evidence，正文/query仅JSON DATA；严格生成status/claims/evidence_ids，逐claim检查有效citation、原query或所引证据中的标识符与数字token。Renderer从结构化claims添加引用，列实际来源Metadata、不伪造页码或score可信度。FastPath同样进入生成，不直接原文当答案；timeout/网络/非法JSON/schema/幻觉均GenerationError，不假装证据不足。

124项Stage 10核心及历史回归813 passed / 0 failed / 12 skipped；token guard不证明语义蕴含、维修操作正确或真实模型免疫Prompt Injection，ASCII新普通词也可能保守拒绝。transport timeout由completion控制；不调模型Context参数、不截断证据/整段Prompt。Stage 2–9实现与Legacy prompts/new_rag_system/在线/config保持，真实LLM/服务/线上端到端NOT RUN。合约见 [制造业生成](MANUFACTURING_GENERATION.md)，证据见 [Stage 10报告](STAGE_REPORTS/STAGE10_REPORT.md)。Stage 11–13 PENDING；Full Integration Readiness: NO。


## 16. Stage 11 增量（2026-10-02）

`rag_qa/api`统一Service分析→KnowledgeRevision→cache→Stage 9检索→Stage 10生成，heavy同步工作均to_thread。Runtime在lifespan创建，一个OpenAI-compatible client共享分类/策略/生成，finite timeout、max_retries=0；显式approved FastPath snapshot启动加载与hash绑定，非法即not_ready，未配置None/默认BM25接受policy None。Legacy app/new_main/WebSocket/MySQL/教育FAQ/生成不变。

JSON POST `/api/manufacturing/query`完整执行一次、严格请求、session仅correlation；SSE POST `/api/manufacturing/stream`只把guard后的answer_text分块，start/阶段/answer/citations/done或error一次，缓存hit不假装retrieval/generation。断连检查阻止后续阶段/缓存/发送；不能强杀已入同步线程的模型/服务调用或撤回已提交Redis命令，底层timeout提供边界。

Manifest只读fingerprint派生active事实/revision，排除updated_at；在线mode=ro新连接不创建DB。Cache key hash包含revision+loaded snapshot bytes hash、query/analysis/model/k/Top-M及合约版本；answered-only且TTL、坏值delete+miss、Redis失败降级，不复用answer:{query}。base/config.py/example仅新增runtime/CORS参数，旧业务配置值不变。health live/ready分离、关闭持有clients，显式CORS无wildcard/credentials。

94项Stage 11核心及Stage 0–10回归：907 passed / 0 failed / 12 skipped。实际FastAPI/StreamingResponse、临时SQLite与fake SDK验证控制，不是真实模型/服务端到端PASS。真实runtime启动/Redis/Milvus/BGE/CrossEncoder/API未执行，Full Integration Readiness: NO。合约：[API](MANUFACTURING_API.md)、[Cache](MANUFACTURING_CACHE.md)；证据：[Stage 11报告](STAGE_REPORTS/STAGE11_REPORT.md)。Stage 12–13 PENDING。


## 17. Stage 12 增量（2026-10-05）

独立 rag_qa/evaluation 严格标签/Canonical SHA、三层 Hit/Recall/MRR、逐样本观察与intent/tag/hard/alarm切片；真实组件 adapter 复用 Stage 5–9，同轮捕获Child/FastPath/filter/planner与一次重排。固定25条 synthetic 数据用Stage 2 ID公式，不能视为生产语料或实际真实检索；JSON预检真实质量指标null。RAGAS按锁定0.2.6源码实现显式judge边界，缺依赖/模型API则NOT RUN，不运行旧教育评估。

retrieval/settings.py 集中制造业权重0.8/0.3、nprobe10与retrieval contract；VectorStore实例可带EvaluationProfile派生settings，生产默认不变。API cache/runtime/service增量传递真实settings fingerprint，覆盖k/M/weights/nprobe/BM25 mode及threshold，所有语义变化导致新key；不调整TTL/生产BM25 policy/Stage 2–10算法和Legacy。

999 passed / 0 failed / 13 skipped；Stage 12核心92项单测，真实BGE/Milvus/CrossEncoder/LLM Planner/RAGAS judge/真实性能均NOT RUN。当前验证venv缺milvus_model/sentence_transformers/torch/langchain_core，weights目录和文件存在不代表实际推理通过。Stage 12整体PARTIAL，Last Completed Stage仍11 PASS；Active NONE，Stage 13 PENDING/readiness NO，Full Integration Readiness NO。证据：[评估合约](MANUFACTURING_EVALUATION.md)、[机器预检](evaluation_results.json)、[Stage 12报告](STAGE_REPORTS/STAGE12_REPORT.md)。
