# 制造业检索策略合约（Stage 9）

## 实现入口与边界

`rag_qa/query/rewrite.py` 定义严格 `RetrievalStrategy` / `StrategyDecision` 和变体保护；`rag_qa/retrieval/strategy.py` 提供 `ManufacturingStrategyRetriever(retriever, planner=None, fast_path=None).retrieve(query, analysis, k=None)`。传入已有 Stage 6 `ManufacturingRetriever`，不创建第二套 Milvus/模型实现。未接入 app/new_main/new_rag_system，不生成答案或引用。

```python
from rag_qa.retrieval.strategy import ManufacturingStrategyRetriever
# child_retriever 是已配置 manufacturing VectorStore 的 ManufacturingRetriever。
engine = ManufacturingStrategyRetriever(child_retriever, planner=planner, fast_path=approved_fast_path)
result = engine.retrieve(original_query, original_analysis)
```

## 决策与变体

可注入 `StructuredStrategyPlanner.plan(query, analysis)` 返回严格 JSON object 字符串或 `StrategyDecision`；typed 对象也重新校验。transport/API、超时期限由调用方适配器管理，核心不启动网络请求、线程或模型。抛出 TimeoutError 会降级；此接口不会强行中断阻塞适配器。

Schema extra=forbid/frozen：strategy 只允许 direct/rewrite/subquery；reason_code 为 1–64 位小写字母/数字/下划线机器码，首字符字母。DIRECT 无有效变体字段；REWRITE 恰好一个 rewritten_query，无 subqueries；SUBQUERY 原始输出 1–4 项，无 rewritten_query。JSON 不接受围栏、重复键、常量 NaN/Infinity、非对象或超过32768 UTF-8 bytes。无 planner 默认 DIRECT；JSON/schema/unsupported/timeout/error 都整体回退原 query DIRECT，保留结构化原因，异常秘密不进入结果。

变体非空、最长16384字符、严格 UTF-8。原 query 始终第一条且原样保留；REWRITE 加一条，SUBQUERY 加最多四条。所有变体先验证后才发起检索，任何非法项令整个决策降级，不能只执行合法的一半。重复以空白折叠后的文本键去重，保留第一次原文本与顺序；与 original 重复的项移除；若无新增变体则 DIRECT fallback。重复去重不能绕过原始输出最多四项的上限。

每条变体完整保留原 QueryAnalysis 中已确认 equipment_model/alarm_code/part_number，大小写、连字符、下划线、前导零和完整 token 边界不变。不得新增原 query 未出现的 ASCII token（字母/数字/点/连字符/下划线组成）；这是没有企业标识词典时的保守保护，包括纯字母型号和纯数字备件号，也会拒绝新增英文普通词或数字量词。可扩展召回范围有限，不能声称覆盖所有企业命名格式或改写质量提升。中文同义改写仍需保留每个硬标识符。**变体不重新分析，不产生新 Metadata Filter**；每次传同一原 QueryAnalysis 对象给 Stage 6。

## Fast Path eligibility / probe

公开 `ManufacturingFastPath.probe(query, analysis, k=None, eligibility=FastPathEligibility(...))` 只返回 ACCEPTED evidence 或 FALLBACK reason，miss 的 evidence为空、parent_result=None，不调用 Parent 检索。三个严格bool控制 exact_alarm/exact_faq/bm25。Stage 9 仅 alarm_fault 允许 Exact Alarm；parts/maintenance/parameter/knowledge/general 仍可安全地走 Exact FAQ/BM25，否则进入策略检索。Stage 8 `retrieve_with_fast_path` 默认三个开关全开，miss原样调用Stage 7，保持历史公开行为。已有hard兼容、报警歧义、未知code和显式BM25 policy继续生效，不改阈值。

fast path 接受时跳过 planner/Milvus/reranker，strategy=direct、decision_source=fast_path、query_variants=(original,) 表示原文探测，retrieval_attempts为空表示未执行Child检索；documents是批准的FastPathEvidence，不伪称经过Parent重排。

## Child fusion → Parent aggregation → rerank

每个变体调用已有 Stage 6 Child retrieve，k省略时沿用config.RETRIEVAL_K，hard/soft与一次零召回放宽不变。按child_id融合，取最高finite raw retrieval_score；相同Child正文或除score外任一Metadata冲突抛ChildFusionError。排序为score DESC → winning query variant序号 ASC →该变体Child rank ASC →child_id ASC；并列同Child保留最早位置。序号/rank为1-based。输入不改写。

`fusion_signals`独立记录winning位置和所有命中变体序号，不注入Child Metadata，避免改变Stage 7公共Parent属性一致性。随后复用 `aggregate_parents`，再用**原始query**和现有 vector_store.reranker 对全部Parent一次predict。最后沿用config.CANDIDATE_M截断；空Parent不调模型。不按变体分别重排或混合rerank/retrieval score；Stage 7冲突/模型错误继续传播。

`StrategyRetrievalResult`记录strategy、original_query、query_variants、decision_source(default/planner/fallback/fast_path)、fallback_reason、reason_code、fast_path_attempt、每变体retrieval_attempts（完整Stage 6尝试/hit_count）、documents与fusion_signals；不记录自由推理链。

Manufacturing HyDE/Backtracking: NOT IMPLEMENTED。生成假设文档可能增加不存在的设备/故障事实，回溯可能削弱硬标识符约束；缺少真实评估收益依据。本阶段保持 Legacy StrategySelector/HyDE/Backtracking 原样。

验证及限制见 [Stage 9 报告](STAGE_REPORTS/STAGE9_REPORT.md)。相关前置合约：[查询分析](MANUFACTURING_QUERY_ANALYSIS.md)、[Child检索](MANUFACTURING_RETRIEVAL.md)、[Parent聚合与重排](MANUFACTURING_PARENT_RETRIEVAL.md)、[批准证据快路径](MANUFACTURING_FAST_PATH.md)。Full Integration Readiness: NO；Stage 10–13 PENDING。
