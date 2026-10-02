# 制造业 FastAPI / SSE 合约（Stage 11）

## 入口与运行前提

轻量入口 `manufacturing_app.py` → `rag_qa/api/app.py:create_manufacturing_app(runtime_factory=None)`。import只构造FastAPI/路由并解析本地配置，**不会连接服务、加载模型、构造OpenAI/Redis/Milvus客户端**；真实runtime在lifespan线程中构建，可注入fake runtime测试。Legacy app.py/new_main/WebSocket/教育生成完全保留，制造业不使用IntegratedQASystem或MySQL对话表。

从仓库根目录、具备完整既有运行依赖及本地模型/服务的环境启动：

```powershell
python -m uvicorn manufacturing_app:app --host 127.0.0.1 --port 8080
```

Ctrl+C停止。端口与Legacy相同示例，两个入口同时运行需用户自行选不同端口。需准备既有requirements、BGE-M3/CrossEncoder、本地制造业集合与完成Stage 4摄取的Manifest；MANUFACTURING_MANIFEST_DB_PATH须指向已初始化的manifest_v1、同一制造业集合。在线Revision只读打开，不创建空Manifest掩盖错误。VectorStore构造沿用现有制造业Schema检查/创建与模型初始化，未修改其实现。

真实生产runtime启动、模型/Milvus/OpenAI请求本次 **NOT RUN**。FastAPI TestClient/lifespan/StreamingResponse测试使用fake runtime/recording adapter：控制验证PASS，不代表Real Online Integration PASS或真实服务已可用。可在明确准备环境后手动设置STAGE11_LIVE=1开展验证；本次未开启，不提供会隐式访问真实服务的测试。

## Runtime 与配置

一个OpenAI-compatible client，model=config.LLM_MODEL，api_key/base_url沿用既有DASHSCOPE配置。同一completion adapter供JSONSemanticClassifier、OpenAIManufacturingStrategyPlanner、StructuredAnswerGenerator；SDK仅在runtime懒加载，不回灌Stage 5/9/10。request明确stream=False；只抽取finish_reason=stop且非空message.content，截断/拒绝/空内容失败。策略Prompt要求严格JSON Schema、全部hard ID原样保留、无新identifier/ASCII词、最多4子查询；Stage 9验证与fallback不绕过。

JSON mode并不代替本地Schema/citation guard；依据[OpenAI官方Structured Outputs说明](https://developers.openai.com/api/docs/guides/structured-outputs)保留核心严格验证，第三方兼容模型是否支持该请求未在本阶段实测。SDK接口按本地锁定openai==2.24.0核验，max_retries=0，不改模型Context参数。

环境变量 > config.ini `[manufacturing]` > fallback：

| 配置 | INI key | fallback / 含义 |
| --- | --- | --- |
| MANUFACTURING_LLM_TIMEOUT_SECONDS | llm_timeout_seconds | 30，finite positive transport timeout |
| MANUFACTURING_REDIS_TIMEOUT_SECONDS | redis_timeout_seconds | 2，connect/socket timeout |
| MANUFACTURING_CACHE_TTL_SECONDS | cache_ttl_seconds | 300，positive integer、bounded lifetime |
| MANUFACTURING_FAST_PATH_SNAPSHOT_PATH | fast_path_snapshot_path | 空，不启用FastPath |
| MANUFACTURING_CORS_ORIGINS | cors_origins | JSON `[]`，无跨域授权 |

这些是运行保护默认值，不是Stage 12性能/阈值调优结论。CORS仅显式http/https origin列表，不允许`*`、路径/凭据/非法端口；allow_credentials=False。factory显式传origin同样验证。有限transport timeout不是对底层同步线程的强制总体截止。

FastPath只加载明确配置的approved manufacturing canonical snapshot，非法/缺失即runtime not_ready；未配置为None。绝不读取教育jpkb/MySQL FAQ。BM25 acceptance_policy默认None，Exact Alarm/FAQ仍遵循Stage 8/9安全规则。**快照在startup加载并绑定其原始bytes hash；文件更新需重建runtime/重启，使语料和hash一起切换**，不把新文件hash配旧内存语料写缓存。

## 统一Service / JSON API

ManufacturingOnlineService编排Stage 5 QueryAnalyzer →只读KnowledgeRevision→hashed cache lookup→Stage 9 ManufacturingStrategyRetriever→Stage 10 GroundedAnswerGenerator→validated answered cache→response。同步分析、revision、Redis、检索及生成全部asyncio.to_thread；route不重复实现检索/生成，不因JSON/SSE协议切换再次消费模型。

`POST /api/manufacturing/query`请求：`{"query":"MZ-2000 报警 E102 怎么处理？","session_id":"optional-correlation"}`。query非空、最长16384字符、合法UTF-8，unknown字段/source_filter拒绝422；session_id可空缺，若给则非空最长128。session仅correlation/request grouping，**没有semantic conversation memory**，不传历史到Prompt、不接旧MySQL会话，不参与答案缓存键。

响应：request_id/session_id、status、answer_text、claims、citations、used_evidence_ids、warnings、cache_hit。每HTTP请求完整pipeline一次；insufficient_evidence仍200且不缓存。错误只code/request_id：INVALID_REQUEST(422)、SERVICE_NOT_READY(503)、RETRIEVAL_ERROR/GENERATION_ERROR/INTERNAL_ERROR(500)；断连可观察时JSON请求返回499 CLIENT_DISCONNECTED。不发送str(exception)、prompt、原模型输出或凭据。

## SSE / 断连

`POST /api/manufacturing/stream`，StreamingResponse=text/event-stream，Cache-Control=no-cache。没有新SSE server依赖。miss事件：start → analysis(intent) → retrieval(strategy) → generation(validated) → answer → citations → done。hit事件：start → answer → citations → done；不假装执行检索或生成。analysis仍实际用于cache key，但hit不发送分析阶段事件。

完整JSON经Stage 10验证后才发answer；按256字符拆已验证answer_text，**不是raw LLM token streaming**。sources/citations来自验证结果，done带status/cache_hit/used_ids。成功只有一次done，失败只有一次error，两者互斥。SSE请求校验失败为422/start/error；runtime不可用返回start/error。不发送Chain-of-Thought/prompt/模型输出/内部异常。若客户端已经断开，无terminal发送要求，直接停止。

分析前、检索前、生成前、缓存写入前/最终发送前及每chunk检查request.is_disconnected。可观察断连不启动后续阶段、不写缓存、不继续发送；Starlette取消也停止async后续逻辑。**已在线程中的BGE/Milvus/OpenAI/Redis调用不能强杀**，依赖SDK/socket有限timeout结束；已经提交的Redis命令不能撤回，disconnect check与写入之间存在不可消除的竞态。测试只证明阶段边界取消，不夸大正在执行调用的中止能力。

## Health / 生命周期

GET /health/live仅status=alive。GET /health/ready：core=true/status=ready才200；工厂、Manifest、model/Milvus初始化或配置snapshot失败503/not_ready，reason只有RUNTIME_INITIALIZATION_FAILED等固定码。Redis为可选优化，可core ready/cache degraded；factory注入不带cache时disabled。readiness表示startup依赖构建/检查结果，不承诺后续网络健康或API密钥真实可用。

shutdown反序close Redis、Milvus client、OpenAI client；失败startup关闭已持有资源，shutdown异常不输出秘密。同步资源close同样off-loop。VectorStore构造内尚未成功返回的资源沿用旧构造函数限制，不重构Stage 3/模型实现。

缓存详见[Cache合约](MANUFACTURING_CACHE.md)，实测/限制见[Stage 11报告](STAGE_REPORTS/STAGE11_REPORT.md)。Stage 12–13 PENDING；Full Integration Readiness: NO。
