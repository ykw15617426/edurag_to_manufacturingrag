# 制造业 Grounded Generation 合约（Stage 10）

## 入口与复用

`rag_qa.generation.StructuredAnswerGenerator(completion).generate(query, analysis, strategy_result)`只消费已检索Evidence，不调用另一套Retrieval、不读取旧数据、不接入app/new_main/new_rag_system。Stage 9的documents（Parent Documents或FastPathEvidence）统一处理；Stage 8 FastPathResult也可直接传入，使用evidence字段。若Stage 9original_query与query不同则拒绝。Legacy生成提示词和通用知识绕检索行为未修改。

```python
from rag_qa.generation import StructuredAnswerGenerator

# completion由调用方提供：负责SDK/模型/凭据、有限timeout并返回JSON content字符串。
generator = StructuredAnswerGenerator(completion)
result = generator.generate(original_query, original_analysis, strategy_result)
print(result.answer_text)
```

## Evidence normalization / guard

`normalize_evidence`统一为冻结的EvidenceRecord，按去重后原顺序生成E1/E2/...。保留正文、parent_id/document_id/version、title/knowledge_type、equipment_model/manufacturer/alarm_code/part_number、source_file/effective_date/language；存在时保留best_retrieval_score/rerank_score/match_type/fast_path_reason，仅供观测。

必填文本非空、strict UTF-8；字段容量复用Stage 3，Parent为小写64位SHA256，日期仅ISO calendar date，hard ID沿用Stage 5字符约束。缺必填/坏输入抛EvidenceIntegrityError。同parent的任一正规化事实不同（正文、身份、版本、标题、来源、业务属性、日期/语言）抛EvidenceConflictError；一致去重并保持首次观测分数，不把score差异当业务冲突。同document_id出现多个document_version即冲突，不猜最新版本。调用方输入不修改，不重算Stage 2 ID。

QueryAnalysis中非空hard字段必须与每条Evidence同字段精确相等；缺值也不能证明兼容，因此拒绝为EvidenceGuardError，不交给LLM选Metadata。对general同样执行guard。空Evidence直接insufficient_evidence、静态文本“现有知识库证据不足，无法可靠回答该问题。”，不调用模型。存在Evidence但未配置completion是系统错误。

最多128条输入Evidence（含重复）；每字段存储上限及JSON payload总2MiB只是资源保护，超过即GenerationError，**不截断或偷偷丢证据**。不调模型context参数。

## Prompt 与严格生成

静态system只放治理指令及GeneratedAnswer JSON Schema；query、analysis、正文与Metadata序列化为user JSON DATA，不拼进system。正文即使含“忽略所有系统指令”也是数据。system规定所有意图只依据supplied Evidence；严禁外部知识补充报警/维修/拆装步骤、周期、备件、参数或安全操作。alarm_fault/maintenance/parts/parameter未明确支持时必须insufficient；不得补写常识性维修步骤。score不等于事实/可信度，不编造页码/作者/日期/URL，不输出推理链。

注入同步completion只收到messages、temperature=0.0、response_format=json_object，不创建API客户端/加载模型，不控制transport期限，也不声称能够中断永久阻塞callable。返回严格JSON字符串，最大131072 UTF-8 bytes；拒绝围栏/非对象/重复key/NaN/Infinity、未知字段或无效UTF-8。

GeneratedAnswer(extra=forbid/frozen)：status=answered或insufficient_evidence。answered至少1条GeneratedClaim，无insufficient_reason；每claim text非空最多4096字符、evidence_ids至少1个且不重复，最多128个。insufficient时claims为空且reason非空。最多64条claims。所有Citation ID为E+无前导零正整数。模型insufficient_reason只在结构化解析阶段验证，不作为操作建议回显；最终仍用静态不足文本、空claim/citation和model_reported_insufficient_evidence warning。

## Claim级保护与来源

每claim引用的ID必须存在，E99等抛GenerationValidationError，不静默丢弃。禁止claim自行写[E1]或数字列表前缀，正文的引用全部由Renderer从结构化evidence_ids追加。每条claim都过标识符/数字guard：只允许在原query或**该claim引用**Evidence的正文、title、equipment_model/manufacturer/alarm_code/part_number/effective_date中出现的完整token。未引用证据不能支撑；score/routing原因、版本号和文件路径中的数字不能作为维修参数依据。

ASCII token按大小写敏感的字母数字及内部点/下划线/连字符/加号匹配，未知token一律拒绝，包含纯字母型号；因此也可能拒绝新的英文普通词。数字字面量检查保留正负号、小数精度、科学计数、百分比/温度后缀及Unicode数字形式，中文相邻数字也检查；不自动换单位/改前导零/把3.50等同3.5。规则保守且有格式覆盖边界，不能冒充企业标识词典或完整量纲推理。

GroundedAnswerResult包含status、answer_text、claims、citations、used_evidence_ids、warnings。每claim渲染“text[E1][E2]”；来源按Evidence顺序列出实际title、document_id/version、source_file，JSON转义防止元数据换行创造新来源行。Citation结构保留evidence_id/title/document_id/version/parent_id/knowledge_type/source_file。仅列使用来源，不虚构page/author/date/URL，也不渲染score为可信度百分比。FastPath从同一pipeline生成，批准Evidence不是最终Answer。

## 错误与验证边界

EvidenceIntegrityError/ConflictError/GuardError和GenerationValidationError均继承GenerationError。超时、网络、坏JSON/schema/citation、标识符/数字幻觉等fail closed，不转成insufficient、不retry外部知识、不暴露异常秘密。API业务降级留Stage 11。

Guard只能检查结构、引用合法、Metadata一致和显式标识符/数字文本支持；不能证明语义蕴含、维修动作正确、数字单位含义、完整证据充分性或真实LLM永远免疫Prompt Injection。中文数词和没有数字/ASCII的新维修动作不能靠这些token规则判定，仍需Stage 12真实评估。synthetic completion/Document替身不是生产准确率或全链路PASS。

证据与命令见[Stage 10报告](STAGE_REPORTS/STAGE10_REPORT.md)。前置接口见[策略](MANUFACTURING_RETRIEVAL_STRATEGY.md)、[Parent](MANUFACTURING_PARENT_RETRIEVAL.md)、[FastPath](MANUFACTURING_FAST_PATH.md)、[QueryAnalysis](MANUFACTURING_QUERY_ANALYSIS.md)。真实模型/API/服务/在线端到端NOT RUN；Full Integration Readiness: NO；Stage 11–13 PENDING。
