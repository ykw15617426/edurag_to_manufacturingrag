# Manufacturing Alarm / FAQ / BM25 Fast Path — Stage 8

2026-10-02。入口 `ManufacturingFastPath(corpus, parent_retriever, acceptance_policy=None).retrieve_with_fast_path(query, analysis, k=None)`。它是现有 Stage 7 检索的证据优化层，不创建另一套 RAG engine、不接入 new_main/new_rag_system，不返回最终 answer。

## Approved corpus and strict entries

调用方必须提供已批准的制造业 FAQ/alarm evidence；此模块不连接教育 jpkb、MySQL/Redis，不读取旧语料。批准与语料生命周期由调用方负责，本模块不能判断文本是否真实/正确或授权有效。测试全部 synthetic。

`FastPathEntry` 继承现有制造业业务 Metadata 合约，新增 entry_id、question、evidence_text、parent_id、source_file；保留 document_id/version、title、knowledge_type、equipment_model/alarm_code/part_number/manufacturer、设备/故障/维保/date/language。业务条件必填沿用 Stage 1；标识符格式/容量沿用 Stage 5，Parent ID 必须为小写64位SHA256，公共字段容量核对 Stage 3，不重算身份。entry_id 最多128 UTF-8 bytes，question/evidence_text各65535、source_file4096；非空且 strict string。没有 answer 字段，unknown fields 拒绝。

`FastPathCorpus(approved_entries)` 将 typed entries 或 dict 统一验证、复制为 FastPathEntry，按 entry_id 排序后建真实 `rank_bm25.BM25Okapi` 索引；duplicate ID、坏 Metadata/ID、旧 tuple question 形态或无可索引 token 问题初始化即 `CorpusValidationError`，不静默吞掉坏语料。Entry 和嵌套 maintenance_cycle 冻结。

`corpus.to_json()` / `FastPathCorpus.from_json(snapshot)` 是内存语料快照接口，schema_version=manufacturing_fast_path_v1；拒绝 unknown/duplicate JSON key 和错误版本/形态。重建重新使用 canonical entries 和同一 tokenizer，冷热问题/Metadata/tokens/raw ranking 完全一致。本阶段没有实现 Redis TTL、缓存读写或数据库 Schema。

## Matching order and trust

从 [Stage 5 QueryAnalysis](MANUFACTURING_QUERY_ANALYSIS.md) 复用 [Stage 6 hard 条件](MANUFACTURING_RETRIEVAL.md)：所有有效 equipment_model/alarm_code/part_number 都要求 entry 同字段精确相等；None 不作 wildcard。high/medium/low 均不能为了快路径召回丢掉 hard。Soft 属性本阶段不作为强制缩小范围条件。

1. Hard ambiguity warning 直接回退，不从 warning 任选候选。
2. 原 query 出现语料已知 alarm token，而 Stage 5 没有安全确认为对应 alarm_code，回退 `unresolved_alarm_identifier`。这是拒绝短路保护，不补实体、不替 Stage 5 推断角色。
3. Exact Alarm：全部 hard 兼容条目中，code只对应一个条目且其 knowledge_type=alarm，接受 EXACT_ALARM。带明确型号 reason=unique_alarm_with_hard_identifiers；不带型号、批准语料只有该唯一含义 reason=unique_alarm_meaning_in_approved_corpus。
4. 相同 code 对应多个兼容条目（包括其他知识类型、版本或型号）直接回退 ambiguous_alarm_evidence，不继续 exact FAQ/BM25 去绕过歧义；不能跨型号任选一个。
5. Exact FAQ：在 hard 兼容范围按 normalized question 精确匹配；唯一条目才接受，多个匹配回退 ambiguous_exact_faq。
6. BM25：先选择 hard 兼容条目，再调用同一全语料索引的 get_batch_scores；没有兼容条目则回退。无 acceptance policy 仅输出排名候选并回退 Stage 7；只有显式 policy 接受时才返回 BM25_FAQ。

“E102 怎么处理？”的无标签 token 在 Stage 5 当前规则中未必被确认；Stage 8 不改变分析器。若已验证 alarm_code 且存在多型号含义，则 ambiguous_alarm_evidence；若未确认但为语料已知 code，则 unresolved_alarm_identifier。两种情况均保留原 query/analysis 回退，而不会跨设备短路。

## Normalization, tokenizer and scores

Exact FAQ 只用 Unicode NFC、outer strip、普通 whitespace 合并；不改大小写/连字符/下划线/前导零、不删除标点、不做语义等价改写。证据正文仅 strip 外层，不重写处理步骤。

Tokenizer 先保持 ASCII 字母数字及内部 -/_ 的完整 token，例如 MZ-2000、mZ_0002、ALM-007、E102、BRG-6205-ZZ、P_0003_A、00001234；普通英文也保持大小写。余下基本中文/扩展A跨度用单字+相邻双字 token，确定且不依赖 jieba 字典。它不是完整语言分词器，其他语言/复杂量值/设备别名覆盖有限，质量评估留 Stage 12。

索引复用已锁定 rank-bm25==0.2.2 的 BM25Okapi 默认算法参数，不调参。保留 raw_score、1-based rank、corpus_size（全部批准条目）、candidate_scope_size（hard兼容条目数）与matched_token_count；相同分数按 entry_id ASC 排名。不做 softmax、不把分数解释为概率。IDF与平均长度来自全批准语料，所以增加无关 FAQ 仍可改变 raw score；候选边界先限定，不自动扩大。

`BM25AcceptancePolicy(minimum_raw_score=...)` 要求显式有限数字，测试阈值不作为生产建议；还要求至少一个 token 重合。可注入其他 `accepts(candidate)->bool` 策略，策略负责是否足够可信；未配置不自动短路。阈值校准/真实接受质量属于 Stage 12。

## Evidence and fallback

`FastPathResult` 保留 status（ACCEPTED/FALLBACK）、match_type（exact_alarm/exact_faq/bm25_faq/fallback）、evidence tuple、matched_entry、bm25_score/rank/corpus_size、reason、candidates、warnings、parent_result。Exact匹配不是概率，不编造数值分数：bm25_score/rank=None。

接受时 evidence 为 `FastPathEvidence(page_content=evidence_text, metadata=...)`，提供与 Document 相同的正文/Metadata访问接口；包含完整 Entry业务/来源字段、parent_id，id=parent_id alias、match_type/reason。maintenance_cycle沿用 typed业务合约的对象结构，不伪造 Child命中数、Milvus或Reranker分数。matched_entry保留完整canonical条目。该内容仍须经过后续 Stage 10 Evidence Guard。

拒绝或运行异常时调用原 `ManufacturingRetriever.retrieve_parents(query, analysis, k=k)`；k=None交由现有 config.RETRIEVAL_K 决定，query/analysis对象原样传递。不改 Stage 6 Filter或Stage 7聚合/重排。evidence此时为Stage 7 Parent Documents，parent_result保留其 attempts。空 Parent结果也如实返回。

优化层 search/policy异常记录 reason/warning=fast_path_error，不输出异常私有内容，然后回退；非法初始化不会被 runtime fallback 吞掉。Stage 7自身异常在 catch之外继续向上抛。

```python
from rag_qa.query import QueryAnalyzer
from rag_qa.retrieval import FastPathCorpus, ManufacturingFastPath

# approved_entries 由调用方准备，必须包含完整制造业业务/来源字段。
corpus = FastPathCorpus(approved_entries)
fast_path = ManufacturingFastPath(corpus, manufacturing_parent_retriever)
query = "MZ-2000 报警 E102 怎么处理？"
result = fast_path.retrieve_with_fast_path(query, QueryAnalyzer().analyze(query))
evidence = result.evidence  # 证据；没有生成或发出最终 answer
```

## Evidence and limits

见 [Stage 8 报告](STAGE_REPORTS/STAGE8_REPORT.md)。真实 BM25离线排名、canonical快照、合成决策与Stage 7控制联动已验证；不是企业数据/语义质量或生产安全阈值证据。真实MySQL/Redis、BGE/Milvus/CrossEncoder、在线端到端 NOT RUN，Full Integration Readiness: NO。

Stage 8交付边界：不实施 Stage 9改写/HyDE/subquery/backtracking/strategy、Stage 10生成/引用、Stage 11缓存治理/TTL/SSE、Stage 12阈值调优。Stage 9–13 PENDING；本阶段发布后停止。


## Stage 9 增量：公开探测与意图 eligibility（2026-10-02）

新增`FastPathEligibility`三个严格bool（allow_exact_alarm/allow_exact_faq/allow_bm25）及公开`probe`，拒绝/错误仅返回结构化FALLBACK、空Evidence、parent_result=None，不立即检索Parent。Stage 9仅alarm_fault开启Exact Alarm，其他意图可安全继续FAQ/BM25。原`retrieve_with_fast_path`默认全开并继续在miss调用Stage 7，向后兼容；原阈值和歧义/硬条件规则保留。完整编排见 [检索策略合约](MANUFACTURING_RETRIEVAL_STRATEGY.md)，历史Stage 8报告不重写。
