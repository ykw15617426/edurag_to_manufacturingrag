# Stage 0 Final Report

审计日期：2026-10-01；仓库：ykw15617426/edurag_to_manufacturingrag。

## Status

**PARTIAL**。源代码审计、渐进迁移边界、制造业术语设计、遗留清单、低风险调整及一个 Stage 0 提交已准备。实际 Smoke：7 PASS、9 SKIPPED、0 FAIL。缺依赖阻止了核心 RAG/FastAPI 的真实 import 与初始化验证；不能声称完整 RAG 系统已稳定运行。

## 1. Repository Baseline

```text
branch: main
baseline commit: ff95920f0eab785f9482e70b4ca2f65e630ef6a7 (Add resume PDF)
initial working tree: clean; tracked 99 files
remote: https://github.com/ykw15617426/edurag_to_manufacturingrag.git
```

修改前执行了 git status、git branch、git log -5 --oneline。只有两个历史提交；没有用户未提交修改需要覆盖。简历 PDF 保持原样，不是工程测试数据。

已阅读指定核心文件（app/new_main/old_main、Config/Compose/requirements、rag_main、所有 core、MySQL/Redis/BM25/sql_main、RAGAS 脚本）及 Loader/Splitter/demo/静态前端源码。数据检查：教育 FAQ CSV 467 条，分类训练 JSONL 486 条，评估 JSON 30 条/小集 5 条；二进制数据确认路径、格式与 Loader 实现，未进行全量 OCR/解析回归。

## 2. Current Architecture

### Offline Ingestion

```text
rag_main --data-processing + 明确 data 根目录
→ 逐 VALID_SOURCES 拼 source_data → os.walk → 扩展名 Loader.load
→ metadata(source/file_path/timestamp)
→ Chinese/Markdown Parent Splitter → Child Splitter
→ 位置型 parent_id/child_id → BGE-M3 dense+sparse
→ MD5(metadata id) PK → Milvus upsert
```

不存在 SHA256、版本控制、内容去重和 stale delete。跨 source 的 process_documents 调用从 doc_0 开始，可能复用同一主键。

### Online Retrieval

```text
用户 → FastAPI → 问候短路或进入 new_main.query
→ MySQL 会话历史 → BM25Search 内先 Redis 答案缓存
→ jieba + BM25 全库 softmax → 高于 0.85 则查 MySQL 精确候选并缓存
→ 否则新版 RAG → BERT 分类
→ 通用知识直接 LLM；专业咨询进入同步 LLM StrategySelector
→ direct / HyDE / SubQuery / Backtracking
→ BGE-M3 → Milvus 两路 Hybrid → WeightedRanker(0.8,0.3)
→ set(parent_content) → CrossEncoder → 上下文/历史 Prompt
→ 4096 字符截断 → 同步 LLM stream → WebSocket token 响应 → 写历史
```

HTTP 仅 next 一次，遇 RAG 返回 WebSocket 指示，网页随后重发同一 query；不能认为 HTTP 完整执行上述链路。完整 Schema、Index、字段和端点说明见 [CURRENT_ARCHITECTURE.md](CURRENT_ARCHITECTURE.md)。

## 3. Existing Capabilities

完整 `Capability | Status | File | Notes` 矩阵见 [架构文档第 4 节](CURRENT_ARCHITECTURE.md#4-已有能力矩阵)，包含全部要求项和 Missing 能力。状态为代码事实：Implemented 不代表本次集成验证 PASS；Partial 为路径存在但有实际缺口；Legacy 为旧入口/教学路径；Missing 为当前主系统无实现。

可复用：多格式解析/OCR、两级切分、BGE-M3 Dense/Sparse、Milvus Hybrid、两类索引、WeightedRanker、CrossEncoder、BM25/Redis/MySQL、策略增强、FastAPI/WebSocket。教育二分类、Parent Aggregation、增量入库、RAGAS/Compose 均有缺口。SSE、制造业 YAML/Pydantic Metadata、SHA256、Version Manifest、差集删除、Hit@K/MRR 尚未实现。

## 4. Confirmed Problems

以下文件路径均相对仓库根目录。行号引用基线或本阶段少量修正后的附近位置，函数名是定位主依据。除明确标注修复的项目，均只审计和建立后续 TODO。

| Problem | File | Function/Class | Current Behavior | Risk | Target Stage |
| --- | --- | --- | --- | --- | --- |
| 5.1 位置 ID 不稳定且跨目录冲突 | rag_qa/core/document_processor.py:77,103,113；vector_store.py:123 | process_documents / add_documents | doc_i_parent_j_child_k；每个调用 i 重置；PK 只 MD5(metadata id) | 遍历/切分改变会错绑身份；多个 source 覆盖互相的数据；MD5 不能补足身份语义 | Stage 2 身份合约；Stage 4 增量管理 |
| 5.2 无 Document SHA256 | document_processor.py；vector_store.py | load_documents_from_directory / add_documents | 未对 file bytes 做 SHA256 | 无法确认原文修改、重复文档和版本来源 | Stage 2 TODO |
| 5.3 无 Child Content SHA256 | document_processor.py；vector_store.py | process_documents / add_documents | 无 normalized child 内容 hash；只位置主键覆盖 | 无内容幂等；相同正文不同位置不是去重 | Stage 2 TODO |
| 5.4 Upsert 无 stale delete | vector_store.py:113；rag_main.py:74 | add_documents / main | 仅 upsert 当前 rows；无文档范围旧 ID 对比/delete | 删除文件、减少 chunk、位置变化留下旧 rows；无版本边界 | Stage 4 |
| 5.5 Parent 去重丢失信息 | vector_store.py:223,236 | _doc_from_hit / _get_unique_parent_docs | 先丢 distance/child_id，再 set(parent_content) 返回空 metadata Document | parent_id、metadata、score、child hit count、召回顺序丢失；同正文不同设备错误合并 | Stage 7 |
| 5.6 权重基线 | vector_store.py:193,196 | hybrid_search_with_rerank | reqs=[dense,sparse]；WeightedRanker(0.8,0.3) | 无制造业评估依据；只是记录值，不能擅改/按另一 demo 推测 | Stage 12 决定权重 |
| 5.7 nprobe 字面值与有效值边界 | vector_store.py:181 | hybrid_search_with_rerank | param={'metric_type':'IP','nprobe':10} | 当前未确认 SDK/服务器实际应用；示例使用嵌套 params 是不同代码 | 后续兼容验证；Stage 12 调优 |
| 5.8 BM25 阈值依赖语料 | mysql_qa/retrieval/bm25_search.py:54,80,88；new_main.py:177 | _softmax / search | 全库 exp(score-max)/sum 与 0.85 比较，非 raw 分数 | 增加文档扩大分母；分布变平/变尖改变置信度；单条语料会得到 1，不能当校准概率 | Stage 8 |
| 5.9 Redis 无 TTL | mysql_qa/cache/redis_client.py:29,33；bm25_search.py:31,95 | set_data / _load_data / search | SET(key,json)，无 EX/PX；答案 key 仅 query，corpus 全局 key | 长期残留旧知识；设备/版本/source 无隔离 | Stage 11 |
| 5.10 HTTP 非流式 BUG | app.py:140,162,181；new_main.py:194-205；static/index.html:649 | query / IntegratedQASystem.query / sendMessage | next 一次；RAG token 未返回，响应指示 WebSocket；网页重发查询 | 不返回完整答案，不完成首次历史写入，重复检索/生成成本与时延 | Stage 11 |
| 5.11 当前协议不是 SSE | app.py:190；static/src/App.jsx:49 | websocket_endpoint / React 原型 handleSubmit | 服务端 WebSocket；React 草稿期待 /query SSE，未接主入口 | 文档误报 SSE、前后端草稿不兼容 | Stage 11（新增 SSE） |
| 5.12 Async 内同步阻塞 | app.py:95,141,191；new_main.py；vector_store.py | async handlers / query / reranker.predict | 同步 MySQL/Embedding/Milvus/BERT/CrossEncoder/LLM generator 直接执行 | 阻塞 Event Loop；并发请求共享全局 cursor | Stage 11 |
| 5.13 Compose 依赖不完整 | docker-compose.yml:1 | services.edurag-app | 只有 app，环境变量引用 mysql/redis/milvus；无 etcd/minio | 无法通过当前 Compose 启动完整栈；容器名解析需外部网络 | 部署阶段（Stage 13 候选） |
| 5.14 配置漂移 | config.example.ini:35；docker-compose.yml:39；base/config.py | Config / environment | 示例 Parent512/120 Child128/30；Compose/fallback Parent1000/150 Child200/30；Compose 两 overlap 读同一 CHUNK_OVERLAP | 运行方式改变切分；单值同时覆盖两个 overlap 可能无效；数据库/LLM 默认也不同 | Stage 1 前确认配置；Stage 12 业务参数选择 |
| Redis 密码错误类型（已修） | base/config.py:50 | Config.__init__ | 原 getint 对空/非数字密码报 ValueError，且 os.getenv fallback 先求值 | 复制无密钥示例也不能启动 | Stage 0：get 字符串读取，真实测试 PASS |
| VALID_SOURCES 可执行表达式（已修） | base/config.py:101 | Config.__init__ | 原 eval 执行配置表达式 | 读取配置有非必要代码执行副作用 | Stage 0：literal_eval；合法列表保持，表达式拒绝 |
| CLI import 路径错误（已修源码） | rag_qa/rag_main.py:4；mysql_qa/sql_main.py:2 | 模块顶层 imports | 原裸 core/db/cache/retrieval 无法从根目录按包运行 | 根目录 -m 入口找不到内部模块 | Stage 0 改包限定路径；真实 import 因依赖缺失 SKIPPED |
| BM25 冷/热启动候选类型不同 | bm25_search.py:39,46,90；mysql_client.py:89 | _load_data / search / fetch_answer | 冷启动保留 fetch_questions 的 tuple 列表；缓存写字符串；取候选没解包 | 冷启动高分候选将 tuple 传到 MySQL 单问题参数，可能无法查对答案，异常回退 RAG | Stage 8 |
| Sparse fallback 错取第一行 | vector_store.py:155-158 | get_sparse_dict | except 分支总是 embeddings['sparse'].getrow(0) | 批量 i>0 时 fallback 可能写入第一条稀疏向量；兼容性必须实测 | Stage 3 前基础兼容验证 |
| Parent 同分排序脆弱 | vector_store.py:218 | hybrid_search_with_rerank | sorted(zip(scores,parent_docs),reverse=True) | 分数相等时继续比较 Document，可能 TypeError；排序无稳定二级 key | Stage 7 |
| source filter 未校验/FAQ 忽略 | vector_store.py:176；bm25_search.py:62；app.py:62 | hybrid_search_with_rerank / search / QueryRequest | raw source_filter 拼表达式；FAQ/答案缓存不看 source | 表达式错误/意外匹配，跨设备知识不能保证隔离 | Stage 6；Stage 8/11 FAQ/cache |
| 分类与 Prompt 的工业适用性 | query_classifier.py:59-74；new_rag_system.py:202 | load_model / generate_answer | 缺训练目录就创建新分类头；教育标签；Prompt 取前4096字符 | 分类可靠性无依据；末尾问题可被截掉；工业问题可能绕过检索 | Stage 5；生成阶段候选 |
| 配置与启动生命周期 | base/config.py；app.py:38；app.py:283 | Config / 模块顶层 / health_check | 无 dotenv 自动加载；全局模型/DB 初始化；health 固定 healthy | 单纯 import 需服务；配置注释误导；健康接口不能证明依赖就绪 | Stage 11；Stage 0 修正注释 |
| Docker 上下文与忽略范围 | Dockerfile:35；.gitignore | COPY . . / 忽略规则 | 无 .dockerignore；/**/models 还命中 demo/langchain/models 教学源码 | 本地 .env/config/模型/简历可进入镜像；误认为模型 demo 已发布 | 部署治理；当前不扩大发布范围 |
| 评估证据不足 | rag_assessment/*.py,*.csv*；classify_data/model_generic_5000.json | 模块顶层 RAGAS / train_model | 预填教育上下文；历史 CSV 包含 NaN；训练文件名5000但486条 | 无在线回放/标签ID，不能得出制造业 Hit@K/MRR；注释90%+未验证 | Stage 12；Stage 5 数据治理 |

### stale C 的准确结论

不能机械声称“A/B/C 变 A/B/D 就一定残留 C”。现有主键按位置生成：如果这三块位置完全相同，D 可覆盖 C 对应 PK，C 不一定残留。然而 **没有任何 stale delete**：比如 A/B/C 改为 A/B（第三个 PK 无新 upsert），或原文档移除/改切分后部分旧 PK 不再出现，就会保留旧 C。当前代码既可能错误覆盖，也可能残留，正式修复须同时解决稳定身份与文档版本差集。

### 未确认的版本兼容项

VectorStore 使用 `BGEM3EmbeddingFunction(use_f16=False)`，demo 写 `use_fp16=True`。由于当前没有 milvus_model 包，Stage 0 无法检查安装版本的实际函数签名，不能把“字面不同”直接宣称为已复现报错。nprobe 参数形状同理。两项已列为集成前必须核实的事项，代码未被盲改。

本地被 Git 忽略的 demo 模型示例还有硬编码 API 密钥；不输出值、不把这些源码强制加入本提交。原本地 .env/config.ini 保持，不提交。生产使用前应由持有人更换实际使用的密钥；本次没有调用或验证密钥。

## 5. EduRAG Legacy

完整清单：[EDURAG_LEGACY_INVENTORY.md](EDURAG_LEGACY_INVENTORY.md)，31 个文件、1,152 个命中行、69 个历史资产。范围和二进制正文未 OCR 的限制在清单开头明确。

| Category | 清理/迁移对象 | 本次动作 |
| --- | --- | --- |
| A 必须删除（后续发布前） | app.py 旧软件激活示例；未接入且协议错误的 React 草稿从发布物排除 | 标记，未删除 |
| B 制造业替换 | 教育品牌、学生问候、学科过滤、AI/JAVA 培训策略示例、通用知识/专业咨询语义、客服 phone、subjects_kg/jpkb/edurag 业务绑定 | 建立 TODO |
| C 保留可重命名 | edu_* Loader/Splitter、EduRAG logger 等通用技术实现 | 保持现调用路径 |
| D 暂时不动 | ai/java/ops_data、samples、分类训练集、FAQ CSV、所有 demo、旧入口/网页、RAGAS JSON/CSV/img | 原位历史基线标记；零删除/移动 |

## 6. Changes Made

| File | 为什么修改 | 是否影响现有行为 |
| --- | --- | --- |
| base/config.py | Redis 密码按字符串读；eval→literal_eval；纠正 .env 注释 | 修复空/非数字密码；合法列表同义，主动拒绝执行表达式；未更改业务参数 |
| rag_qa/rag_main.py | 包限定 imports | 根目录 -m 的预期入口可正确解析内部路径；真实导入未验证 |
| mysql_qa/sql_main.py | 包限定 imports | 同上，不改 SQL/BM25 流程 |
| rag_qa/edu_text_spliter/edu_chinese_recursive_text_splitter.py | 3 个 regex 改 raw 字符串 | regex 文本不变，移除 Python SyntaxWarning |
| rag_qa/edu_text_spliter/edu_model_text_spliter.py | 同义 raw regex | 行为不变，不启用语义 splitter |
| README.md | 项目状态、真实运行前提、根目录命令、停止方式、测试方法 | 文档，无运行行为改变 |
| docs/CURRENT_ARCHITECTURE.md | 真实流程、Schema/Index、能力矩阵、配置/评估基线 | 文档 |
| docs/MANUFACTURING_MIGRATION_PLAN.md | 阶段计划、复用边界、制造业字段/knowledge_type 候选、ready 边界 | 设计，无 Metadata Pipeline |
| docs/EDURAG_LEGACY_INVENTORY.md | 完整文本定位与资产保留分类 | 文档；不移动旧数据 |
| docs/STAGE0_REPORT.md | 当前报告、问题证据、测试结果、已知限制 | 文档 |
| requirements-dev.txt | 测试 runner 独立依赖 | 不改现有 runtime requirements |
| tests/test_stage0_smoke.py | 配置回归、真实导入/初始化检查、源码编译 | 缺环境跳过；不替换为 mocks；app live import 显式开关 |

.gitignore 已在仓库基线排除 .env/config.ini、权重、缓存、日志、向量库；此次无必要重复修改。没有新建平行引擎、改权重/nprobe、统一切分业务值、重写父块聚合/BM25、实现 YAML/SHA256/Manifest/Filter/SSE，或伪造评估指标。

## 7. Tests

环境：Windows，`D:\Soft\ANACONDA\Anaconda\python.exe`，Python 3.13.9。执行目录：仓库根目录。

| Command | Result | Status |
| --- | --- | --- |
| python -m pytest tests/test_stage0_smoke.py -q -rs（首次） | 7 passed, 9 skipped, 4 SyntaxWarning；已据此修复同义 regex 字符串 | PARTIAL |
| python -m pytest tests/test_stage0_smoke.py -q -rs（修复后） | 7 passed, 9 skipped；无 warnings，0 FAIL | PARTIAL |
| git diff --check | 无格式错误，exit 0；Git 提示现有 CRLF 转换策略，非补丁错误 | PASS |

逐项结果（同一 pytest 命令，不另造执行记录）：

| Test | Result |
| --- | --- |
| Config 示例读取与原切分参数 | PASS |
| Redis 空密码 | PASS |
| Redis 非数字密码 | PASS |
| 进程环境变量覆盖 | PASS |
| VALID_SOURCES 拒绝可执行表达式 | PASS |
| 无本地配置时原 fallback | PASS |
| 核心 Python 源码编译（不是 import） | PASS |
| document_processor import | SKIPPED：缺 langchain_core/community/text_splitters、docx/pptx/fitz/cv2 |
| VectorStore 类 import | SKIPPED：缺 milvus_model/pymilvus/sentence_transformers/langchain_core |
| 新版 RAGSystem import | SKIPPED：缺 langchain_core/transformers |
| 旧版 RAGSystem import | SKIPPED：缺 langchain_core/transformers |
| rag_main import | SKIPPED：缺上述解析/向量/分类依赖 |
| sql_main import | SKIPPED：缺 pymysql/redis/rank_bm25 |
| new_main import | SKIPPED：缺数据库/检索/分类依赖 |
| Document Processor 初始化（真实 splitter/TXT loader/process_documents） | SKIPPED：同解析依赖不足；本模块没有类构造器 |
| FastAPI app 真实 import | SKIPPED：缺 fastapi 及上述运行依赖；未用 mock 绕过全局初始化 |

完整线上服务、真实权重推理、Milvus 写入/检索、MySQL/Redis 连通性、WebSocket 客户端回归、Docker build、RAGAS 运行、分类训练、API 模型可用性均 **NOT RUN**。本地模型目录存在，不能据目录名声称模型完整或已运行；没有断言服务未启动。现有 demo 脚本不是正式测试，不批量执行其中具有外部副作用的脚本。

## 8. Known Risks

- 高优先级后续修复：位置 ID 跨目录覆盖、无 stale delete、父块元数据丢失、HTTP generator 消费不完整、缓存长期过期知识、async 阻塞。
- 当前还缺部署与依赖安装的运行证明；真实模块 import/初始化没有 PASS。基础 smoke 通过只限定配置与语法。
- 教育分类与 Prompt 仍主导现有系统，不可宣称已经用于制造业可靠检索。配置漂移原样保留，进入实际入库前须确认单一有效配置。
- 旧数据保留，二进制语料没有全量 OCR；完整文档解析质量与型号/报警隔离均未评估。

## 9. Stage 1 Readiness

**YES（限定范围）**：可进入 YAML/Pydantic Metadata 合约与离线实现；已有可复用入口和后续修复顺序。制造业字段和七个 knowledge_type 已在迁移计划中建立候选基线。

**完整集成 readiness：NO。** Blocker：当前 Python 缺依赖，模型完整性与 MySQL/Redis/Milvus/API 未验证；版本兼容项尚待运行确认。Stage 1 单元开发不必等待全栈运行，实际入库/在线验证必须先解除这些阻碍。

## 10. Git

提交策略：只创建一个 `refactor: establish manufacturing RAG migration baseline` 提交。提交前执行 git diff、git status、git diff --check，并检查暂存文件；不纳入 .env、config.ini、API 密钥、实际密码、权重或新增大型语料。原有简历/数据无改动。

```text
commit hash: 此报告随 Stage 0 提交保存；git log -1 --format=%H -- docs/STAGE0_REPORT.md 可获取该提交
push status: not pushed
```

本请求要求完成一个 Stage 0 commit，未要求发布此次改造；本次不 push。最终 commit hash、工作区状态与暂存检查的实际结果在交付回复中给出。此处不回写同一提交的哈希，避免文档自引用导致哈希变化。
