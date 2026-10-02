# Manufacturing Parent Aggregation + Reranker — Stage 7

2026-10-02。高层入口 `ManufacturingRetriever.retrieve_parents(query, analysis, k=None)` 复用 [Stage 6 Filter/Child Retrieval](MANUFACTURING_RETRIEVAL.md)，再按 parent_id 聚合、调用当前 VectorStore 的 `reranker.predict`、返回 Top-M Parent Evidence。未接入 new_rag_system，没有答案/引用或 Stage 8+ 路由。

## Aggregation

`aggregate_parents(children)` 输出按确定顺序排列的 `ParentEvidence` tuple；包含 page_content、只读顶层 metadata、matched_children、best_retrieval_score、first_child_rank，并提供 parent_id、child_hit_count、matched_child_ids 属性。page_content 来自 parent_content，分组只用 parent_id。相同正文、不同 parent_id 的父块分别保留。

输入是 Stage 6 完整 Child Metadata。根据现有 Stage 3 scalar Schema 派生所有 Parent/Document 字段，保留 parent_content、document_id/version、title/knowledge_type、设备/制造商/报警/故障/维保/备件字段、维保周期的三个扁平字段、effective_date/language、schema_version、document_sha256/parent_content_sha256、source_file/metadata_source/source/timestamp。不修改 Schema 或重算稳定 ID。

同 parent_id 下上述全部字段必须一致，额外 provenance 也保留并检查。冲突抛 `ParentAggregationError`，不任选一份 Metadata；错误消息记录字段名，不输出正文。缺字段、非法 SHA256、id != child_id、非法 retrieval_score 或重复 Child ID 同样报错；重复 ID 表示输入不符合正常单次 Milvus hit 合约，不用重复命中虚增计数。来自 Child 的预填 Parent 汇总分数字段拒绝接受。

Child 专属 id/child_id/child_content_sha256/retrieval_score 不当成公共 Parent 属性；每条命中保存为 ChildMatch（child_id、child_content_sha256、retrieval_score、child_rank）。输入顺序的 rank 从 **1** 开始；matched_child_ids 按首次命中顺序排列。聚合不改输入。

```text
best_retrieval_score = max(child retrieval_score)
child_hit_count = number of distinct Child hits
first_child_rank = earliest Child rank

Pre-rerank ordering:
best_retrieval_score DESC → first_child_rank ASC → parent_id ASC
```

最大分数保留强命中，负数和大于 1 的有效分数照常使用；不平均、不归一化、不解释为概率。

## Rerank and Parent Documents

`rerank_parents(query, parents, reranker, *, top_m)` 用确定性预排序构建 `[[query, parent_content], ...]`；复用 `vector_store.reranker`，不加载第二个模型。空结果不调用模型；只有一个 Parent 也调用模型并保存 rerank_score；对全部候选评分后才取 Top-M。

结果仍为 LangChain Document tuple，page_content = parent_content，metadata 保留公共业务/来源字段，并增加：

| Field | Meaning |
| --- | --- |
| id / parent_id | Parent 稳定身份；id 是 parent_id 的 alias，不沿用任意 Child ID |
| best_retrieval_score | 最大原始 Child 检索分数 |
| rerank_score | 当前 CrossEncoder 的独立原始分数 |
| child_hit_count | 命中 Child 数 |
| matched_child_ids | Child ID list，按命中 rank |
| first_child_rank | 首个命中 rank，1-based |
| matched_children | 每个 Child 的 ID、正文指纹、原始分数、rank，保留 Child provenance |

最终排序 `rerank_score DESC → best_retrieval_score DESC → first_child_rank ASC → parent_id ASC`。不覆盖 best_retrieval_score；tie 使用上述全部字段决定，不按 Document 对象或 set 迭代顺序排序。

模型 exception、非 iterable、数量不等于 Parent 数、非 scalar、bool/string、NaN/inf 都抛 `RerankerError`。采用 **fail closed**，没有返回预排序作为隐式 fallback，没有隐藏模型故障；异常文字不泄露输入。模型只给单分数；二维/多分类输出不被自动 flatten。有效 NumPy scalar score 支持且保留原值。

## Configuration and entrypoint

`retrieve` 与 `retrieve_parents` 的 `k=None` 延迟读取 `config.RETRIEVAL_K`，显式 k 覆盖。沿用环境变量 → INI → fallback 优先级；fallback **5** 不变。`retrieve_parents` 每次从 `config.CANDIDATE_M` 读取 Top-M（fallback **2** 不变），验证其为正 integer；不新设一个固定 Top-M，也不调参。显式调用 k=10 仍合法。

返回沿用 `RetrievalResult`：documents 为 Parent Document tuple，attempts/final_plan 保留 Stage 6 Child 检索证据；attempt.hit_count 仍为 Child hit 数，不是 Parent 数。Parent 冲突/重排失败不会重试检索或移除 hard filter。调用方须传入与 QueryAnalysis 对应的原 query。

```python
from rag_qa.query import QueryAnalyzer
from rag_qa.core.vector_store import VectorStore
from rag_qa.retrieval import ManufacturingRetriever

query = "MZ-2000 报警 E102 怎么处理？"
store = VectorStore(schema_mode="manufacturing")
result = ManufacturingRetriever(store).retrieve_parents(
    query, QueryAnalyzer().analyze(query)
)
parent_documents = result.documents
filter_attempts = result.attempts
```

示例需要完整依赖、本地 BGE-M3/BGE-Reranker 和兼容制造业集合；本次未执行真实模型/服务示例。入口只适用于 manufacturing store；Legacy `hybrid_search_with_rerank` 及 `set(parent_content)` 的历史实现原样保留，制造业新 Parent 路径不使用该方法。

## Validation and scope

Synthetic Child 与 injectable scorer 验证身份/Metadata/最大分数/命中统计、稳定排序、模型输入与失败处理、配置单一来源，包含真实 VectorStore Child 方法到 Top-M 的 recording 联动。见 [Stage 7 报告](STAGE_REPORTS/STAGE7_REPORT.md)。Fake scorer 与 LangChain Document 替身不证明真实 CrossEncoder 或 LangChain 集成；真实 BGE-Reranker、Milvus/向量模型、在线集成 NOT RUN，Full Integration Readiness: NO。

未实现 Stage 8 BM25/报警快路径、Stage 9 Rewrite/HyDE/subquery/strategy、Stage 10 Generation/Citations、Stage 11 SSE 或 Stage 12 tuning。Stage 8–13 PENDING；本阶段结束后停止。
