# Stage 11 — FastAPI + SSE + Redis Cache Governance

日期：2026-10-02。main；起始HEAD `11affd15b57c6d9f2ee7236b4bce0d657305b363`，fetch后Local HEAD == origin/main；初始工作区clean。Stage 11: PASS；Implementation/Validation/GitHub Sync: PASS；实现提交已正常push/fetch/equal/clean核验，完成状态以独立文档提交发布；最终SHA在回复核验提供，不预写自身提交SHA。

## 文件与复用范围

新增manufacturing_app.py和rag_qa/api/{__init__,schemas,service,cache,runtime,sse,app}.py，复用真实Stage 5分析→Stage 9策略→Stage 10生成，统一JSON/SSE与validated cache。Runtime一个OpenAI-compatible client、finite timeout、startup批准快照、默认BM25不接受；无import-time重初始化。新API不使用Legacy IntegratedQASystem/MySQL/教育FAQ。

Manifest仅新增read-only fingerprint方法/helper，原写入/删除/CAS不变；base/config.py和config.example.ini新增manufacturing运行保护参数/显式CORS，不改检索值/权重。新增四个Stage 11测试文件、[API合约](../MANUFACTURING_API.md)、[Cache合约](../MANUFACTURING_CACHE.md)及本报告；同步治理/计划、README/index、当前架构与迁移计划，保留历史报告。

## Commands / Results

python为ignored `.venv/stage1-validation/Scripts/python.exe`（Python3.13.9 / pytest8.4.2）。按已有requirements安装fastapi0.115.12/starlette0.46.2/httpx0.27.2/anyio4.12.1/redis5.3.1/openai2.24.0/uvicorn0.41.0及轻量传递依赖；不改requirements、不安装模型栈/新SSE server依赖、不连接真实服务。先核对本地OpenAI.__init__的timeout/max_retries签名，并按[OpenAI官方JSON说明](https://developers.openai.com/api/docs/guides/structured-outputs)保留本地Schema验证；兼容模型服务支持未实测。

| Command | Result | Status |
| --- | --- | --- |
| git status/branch/log/fetch及两rev-parse | 指定基线、main、clean且远端一致 | PASS |
| `python -m pytest tests/test_manufacturing_api.py tests/test_manufacturing_sse.py tests/test_manufacturing_cache.py tests/test_manufacturing_runtime.py -q -rs --tb=short` | 修正及扩展后独立88 passed；最终回归含CORS增加后94项通过 | PASS |
| 完整Stage 0–11回归（下方命令） | 907 passed / 0 failed / 12 skipped | PASS |
| AST / 文档相对链接 / git diff --check / 保护范围及Diff审阅 | 14文件AST、139相对链接目标、保护范围及补丁检查通过 | PASS |
| FastAPI TestClient/lifespan/StreamingResponse、fake runtime/recording SDK | 实际框架执行，控制与协议通过 | PASS（限定） |
| 独立进程阻断SDK/模型导入后import manufacturing_app | 无runtime建立/连接/加载 | PASS |
| Real production runtime startup / Redis / Milvus / BGE / CrossEncoder / LLM API / Real Online Integration | 未开启STAGE11_LIVE，不执行真实服务请求 | NOT RUN |
| Commit / Push / Fetch / equal / clean | 实现提交正常Push；fetch后Local HEAD == origin/main，Working Tree clean | PASS |

```powershell
.venv/stage1-validation/Scripts/python.exe -m pytest tests/test_manufacturing_api.py tests/test_manufacturing_sse.py tests/test_manufacturing_cache.py tests/test_manufacturing_runtime.py tests/test_manufacturing_evidence.py tests/test_manufacturing_generation.py tests/test_manufacturing_query_rewrite.py tests/test_manufacturing_strategy.py tests/test_manufacturing_bm25.py tests/test_manufacturing_fast_path.py tests/test_parent_aggregation.py tests/test_manufacturing_parent_retrieval.py tests/test_manufacturing_metadata_filters.py tests/test_manufacturing_retrieval.py tests/test_manufacturing_query_analysis.py tests/test_manifest_store.py tests/test_versioned_ingestion.py tests/test_manufacturing_milvus_schema.py tests/test_manufacturing_fingerprints.py tests/test_manufacturing_metadata.py tests/test_stage0_smoke.py -q -rs --tb=short
```

12 SKIPPED为已有缺模型/应用依赖及未启用Stage 3 Live测试；新增轻量依赖不满足完整模型栈。非最终轮曾35pass/1fail（测试Child列表和原值相同）、60pass/1fail（测试误禁公开used_evidence_ids）、85pass/1fail（测试classifier属性名错误）；修正fixture/断言后通过，不把失败轮记PASS。Redis构造失败core仍可建、cache=degraded已补控制状态。

## 验证范围与限制

验证JSON一次generation/完整响应/422/insufficient200/安全错误；SSEcontent-type/start first/只发完整guard后的chunk/citation/done或error一次且互斥/缓存hit不伪造阶段；断连阻止后续retrieval/generation/cache，fake blocking component与并发async task证明off-loop；缓存TTL/hash标识符保持/answered only/坏值delete-miss/Redis降级；临时真实SQLite稳定指纹、updated_at排除、版本/hash/Metadata/processing/Child/新增删除、FastPath bytes结合；Manifest V1缓存到V2新namespace不返回旧命中；真实Stage 5→9→10对象经工厂/recording接口完成HTTP并缓存；shared client/finite timeout/no retry/Prompt/explicit snapshot错误/关闭资源/配置优先级/CORS。

query/retrieval/generation核心、Stage 2 IDs/Stage 3 Schema/Stage 4 mutation/Stage 5合约/Stage 6 filter/Stage 7聚合重排/Stage 8 BM25/Stage 9 fusion/Stage 10 guards和Legacy app/new_main/RedisClient保持。未调配置检索数值、未提交实际配置/凭据/模型/缓存、未写真实数据库或重跑入库。

session仅correlation无对话memory；FastPath在startup绑定loaded bytes，更新需重建runtime，不能hash新文件而继续旧corpus。已进入同步线程的BGE/Milvus/OpenAI调用不能强杀，Redis已发命令不能撤回，靠有限底层timeout结束；断连检查有竞态。Manifest检查点不提供Milvus跨操作事务/生产并发快照隔离。缓存结构验证不能证明恶意Redis修改后的语义事实，完整grounding在Stage 10合法writer。

真实依赖startup/模型/API与线上性能/语义指标未验证，不把fake TestClient当Real Online Integration。Full Integration Readiness: NO；Stage 12–13 PENDING，完成后停止，不执行评估/tuning/Docker最终验收。

## 发布证据

实现Commit：`c6fe27c6e3665445d202d4a3cd16e614455d4972`（`feat: add manufacturing online api`）。已执行`git push`、`git fetch origin`、两`git rev-parse`、`git status --short`，两SHA一致且status为空：PASS。完成状态正常独立文档提交，不amend/force push；最终HEAD及clean在回复核验。Last Completed Stage: Stage 11 — PASS；Active Stage: NONE；Stage 12–13 PENDING。
