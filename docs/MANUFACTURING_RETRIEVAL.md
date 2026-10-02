# Manufacturing Metadata Filter + Hybrid Retrieval — Stage 6

2026-10-02。入口为 `rag_qa.retrieval.ManufacturingRetriever.retrieve(query, analysis, k=None)`；复用现有显式 manufacturing `VectorStore`、BGE-M3 和 Milvus。输出 `RetrievalResult.documents`（按 SDK 顺序的 Child Document tuple）、`attempts`（每次 plan/hit_count）及 `final_plan`。Child 入口不接入在线答案编排，不做 Parent 去重或 CrossEncoder 重排。Stage 7 消除默认 k=10 的漂移：k=None 延迟读取 config.RETRIEVAL_K（fallback5 保持），显式 k 仍覆盖；Parent 高层入口见 [Parent 检索合约](MANUFACTURING_PARENT_RETRIEVAL.md)。

## Filter contract

输入必须是 [Stage 5 QueryAnalysis](MANUFACTURING_QUERY_ANALYSIS.md)。调用方须传入分析所对应的原 query；QueryAnalysis 不保存 query，本阶段不修改该合约。字符串标识符保持大小写、连字符、下划线和前导零。

| 条件 | 信任与用途 |
| --- | --- |
| equipment_model / alarm_code / part_number | Hard；有效非歧义值在所有 confidence 下保留，零召回不可删除 |
| manufacturer / equipment_type | Soft；仅 high 且无严重歧义/冲突时使用；不自动做品牌别名转换 |
| intent-derived knowledge_type | Soft；同上，使用多个知识类型而非单一类型 |
| fault_symptom | 不做 equality；保留原 query 参与向量检索 |

| Intent | Soft knowledge_type |
| --- | --- |
| alarm_fault | alarm / fault / case / manual |
| maintenance | maintenance / case / manual |
| parameter | parameter / manual |
| parts | parts / manual |
| knowledge / general | 无强制类型条件 |

`MetadataFilterPlan` 是 frozen dataclass，字段为 mode、只读 hard_filters/soft_filters、派生 expression、warnings、relaxation_reason、removed_fields。表达式不接受外部赋值；条件复制后冻结。字段严格分组白名单，值再次使用 Stage 5 实体约束验证；knowledge_type 使用受控枚举列表。

`build_expression(hard_filters, soft_filters)` 对每个 literal 使用 `json.dumps(..., ensure_ascii=False)`，使用固定 `==`、`in` 与 `and`。空条件为 `""`；禁止任意字段、任意 raw expression、fault_symptom equality、source_filter 或错误值类型。引号、反斜杠、`==`、`[]` 在字符串内部安全编码。它不声称替代真实 Milvus parser 验证。

## Policy and relaxation

- high 且无严重 warning：有条件则 STRICT，使用 hard + soft；完全无条件则 NONE。
- medium/low 或严重 warning：有 hard 则 RELAXED（hard only），否则 NONE。
- 严重 warning 包括 `ambiguous_*`、含 `conflict`、multiple_intent_cues、semantic_classifier_failed、invalid_query、semantic_entity_rejected_*。未知 warning 保留供观察，不自动移除确定标识符。
- `ambiguous_<field>` 不生成该 hard 条件；不从 warning 解析候选。语义实体冲突时 Stage 5 已保留的确定规则值仍可作为 hard。
- STRICT 有 soft 且零召回：移除全部 soft，保留 hard 转 RELAXED；无 hard 转 NONE。记录 `zero_hits_drop_soft_filters` 与所有 removed_fields。
- 没有 soft 的 plan 不重试；RELAXED + hard 零召回直接返回空；NONE 零召回也不重复查询。最多两次调用。
- 异常向调用方传播，不作为零召回、不触发去过滤重试。general 始终检索，有 exact ID 使用 hard，无可信条件使用 NONE。

规则模式的 Stage 5 通常只给 medium，例 “MZ-2000 报警 E102 怎么处理？”仍生成型号 + 报警码 conjunction，默认不额外限制类型。只有可信 high 分析才加入 alarm/fault/case/manual。润滑问题同理，可信 high 时加入 maintenance/case/manual；ACME/数控机床字段仅由 Stage 5 已确认值提供，Stage 6 不猜品牌。

## Adapter and results

`VectorStore.hybrid_search_children(query, *, filter_plan=None, k=config.RETRIEVAL_K)` 强制 `schema_mode="manufacturing"`；None 表示无过滤，其他输入必须是 MetadataFilterPlan。以派生表达式替代公共 raw expression 参数，避免绕过白名单。query 非空且最多 16384 字符，k 为 1–16384 的 integer（不接受 bool）；输入错误在 embedding/client 前失败。

两个 AnnSearchRequest 使用同一 expression：Dense `IP / nprobe=10`，Sparse `IP`，`WeightedRanker(0.8, 0.3)`，两路及最终 limit 都是 k。不调参，relaxation 重用原 query 和 k。

请求 [Stage 3 Schema](MANUFACTURING_MILVUS_SCHEMA.md) 全部 30 个非向量字段；text 成为 page_content，其余 29 字段保留在 metadata，包括稳定 PK/Child/Parent、Parent 正文、文档版本/三个指纹、业务标签、维保周期三个扁平字段和来源。nullable 字段保留 None。SDK 顶层 id 可补齐 entity.id；id 与 child_id 必须一致且为 SHA256，冲突或缺少请求字段会报错，不静默丢失 Metadata。

SDK hit 的 distance（优先）或 score 原样保存为 `retrieval_score`，要求有限数值；保持顺序，不做归一化、不解释为概率。相同 parent_id 的多个 Child 全部保留供 Stage 7 使用。

```python
from rag_qa.query import QueryAnalyzer
from rag_qa.core.vector_store import VectorStore
from rag_qa.retrieval import ManufacturingRetriever

query = "MZ-2000 报警 E102 怎么处理？"
analysis = QueryAnalyzer().analyze(query)
store = VectorStore(schema_mode="manufacturing")
result = ManufacturingRetriever(store).retrieve(query, analysis, k=10)
children = result.documents
attempts = result.attempts
```

该示例需要本地真实模型、完整依赖和兼容集合；构造函数仍沿用已有 CrossEncoder 初始化，但新 child 方法不调用它。本次未执行示例，不把模型 fake 当作集成成功。

## Evidence and limits

见 [Stage 6 报告](STAGE_REPORTS/STAGE6_REPORT.md)。离线测试验证 policy、表达式编码、真实 VectorStore 方法的 recording client 参数/Metadata，以及 PyMilvus 2.5.4 请求对象。Live Milvus、真实 BGE 检索质量、线上答案链路均 NOT RUN；未设置 STAGE6_LIVE_MILVUS=1，未创建或访问任何真实集合。

未来可显式授权 live synthetic 验证，仅限 `stage6_test_<uuid>_v1`；禁止用 `edurag` 或 `manufacturing_rag_v1` 做测试。保守 soft 策略可能扩大召回；hard 错误会得到空结果，业务纠错属于后续设计，不能自动全库回退。Full Integration Readiness: NO；Stage 6 交付时 Stage 7–13 PENDING，当前阶段以上方治理状态与最新报告为准。
