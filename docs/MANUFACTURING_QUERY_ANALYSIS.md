# Manufacturing Query Analysis — Stage 5

2026-10-02。正式入口 `rag_qa.query.QueryAnalyzer.analyze(query)`，输出验证过的 `QueryAnalysis`。新模块只做分析，不执行检索、Filter、策略选择、改写或答案生成；不导入教育 BERT、Legacy QueryClassifier/StrategySelector、新旧 RAG 编排、Milvus/模型/API SDK 或配置凭据。

## Contracts

| Contract | Values / fields |
| --- | --- |
| QueryIntent | alarm_fault / maintenance / parameter / parts / knowledge / general |
| ConfidenceLevel | high / medium / low；定性等级，未经概率校准 |
| QueryEntities | equipment_model / alarm_code / part_number / manufacturer / equipment_type / fault_symptom；全部 Optional |
| QueryAnalysis | intent / confidence / entities / analysis_source / warnings |
| AnalysisSource | rules / llm / hybrid / fallback |

alarm_fault 包括报警、故障现象、原因和处理；maintenance 包括保养、检修、周期和步骤；parameter 包括参数、规格和技术指标；parts 包括备件、配件、零件和物料号；knowledge 包括操作说明、手册和设备知识；general 表示无法可靠归类，**不代表绕过 RAG**。

Pydantic 对 Schema unknown fields/intent/confidence 拒绝，不把数值概率、教育标签或自由文本归入制造业意图。实体使用 StrictStr，trim 外层空白，保留内部原文；ID 必须为 ASCII 字母/数字/连字符/下划线，不改变大小写/符号/前导零。长度按 UTF-8 bytes 与 Stage 3 同名字段容量一致（测试核对），不修改 Milvus Schema。中文或其他符号的业务标识符暂不支持，不自动转写；描述字段支持中文。所有 Schema 均可 `model_dump(mode="json")`，QueryAnalysis 提供 `to_metadata()`，没有 bypass/strategy/filter/answer 字段。

## Deterministic entity extraction

优先扫描明确 label：型号/设备型号/model、报警码/故障码/alarm、备件号/配件号/零件号/物料号/part number。保留原始 token，例如 mZ_0002、ALM-007、brg_0002_a、00001234。制造商/设备类型/故障现象仅在 `label: 原文` 时做确定性提取。

没有企业词典；不对任意 ASCII 字符串猜角色。未标 label 的值只在附近存在制造业关键词且具有狭窄形状时接受：字母-数字型设备型号、E数字/ALM-数字报警码、字母-数字-后缀型备件号。例中的 MZ-2000/BRG-6205-ZZ 是 synthetic token，不是企业词典。没有上下文的独立 token 输出 None，未知前缀/格式可能漏掉，语义分类器可基于原文证据补充。

日期、量值和单位拒绝：2026-01-01、500小时、3.5MPa、3000rpm 不作为型号/物料号。显式声明的纯数字 ID 可以保留，但不能是日期/量值。Regex 防止从另一个 token 或小数中截取局部，过长值拒绝而不截断。label 与值之间分隔扫描有界（最多 16 字符），避免大量空白导致无界回溯。

单值合约不能表达多个型号/报警码/配件号：发现多个不同候选时该字段置 None，增加 ambiguous_<field>，最终 low；LLM 不能从中默默选一个。重复提到同一原文值不算歧义。实体/置信度不自动决定后续过滤行为。

## Semantic classifier boundary

注入 `SemanticIntentClassifier.classify(query) -> str`，输出必须为一个 JSON object，由 `SemanticClassification` Pydantic 验证：intent、confidence、可选 entities；不接收 analysis_source、自由说明或检索决定。严格拒绝非法 JSON、重复 key、非有限数值、unknown intent/confidence、未知字段、非法实体。原始输入单独作为查询数据传给 classifier；不修改或 lowercase query。

`JSONSemanticClassifier(completion)` 是无 SDK 的语义 Prompt/JSON 请求适配器，传入 system + 原 user query、temperature=0.0、response_format={"type":"json_object"}。system 明确六意图、定性置信度、实体原文证据、查询不能覆盖分析指令、general 不绕 RAG，并包含生成的 JSON Schema。completion 是调用方注入的同步函数，返回 API response content 字符串，负责模型、凭据、SDK、连接生命周期和有限 timeout；适配器不会自行创建真实 API 客户端或加载模型。temperature=0 不保证服务端逐字确定性。

本阶段验证该结构化语义边界/Prompt 和合成响应，不训练制造业模型、不验证真实模型分类质量。不配置 classifier 时仅 rules，不假装调用过 LLM。

## Entity trust and confidence

规则实体是权威结果，任何 LLM 不同值都不能覆盖；冲突记录 semantic_entity_conflict_<field>。规则缺值时，LLM exact identifier 必须在原 query 中以**区分大小写的完整 token**存在，并通过非日期/量值检查；E102 不是 XE1029 的证据，ALM-07 不是 ALM-007。无证据值置 None，记录 semantic_entity_rejected_<field>。描述字段也要求原 query 中的文字证据，不自动归一化品牌、设备名或症状。

若规则已明确一个 token 的角色，LLM 不能将它补到另一标识符字段（例如把报警码 E102 同时猜成设备型号）；记录 semantic_entity_role_conflict_<field>。规则明确同时声明的同值角色仍保留。

合法语义输出使用其 intent；不会用 keyword contains 再把自由回答分类。存在规则实体/规则警告时 analysis_source=hybrid，否则 llm。冲突/拒绝等 warning 把 high 降至 medium；歧义或 general 强制 low。confidence 只是可信度提示，不是经过测量的准确率或概率。

## Failure and fallback

timeout/network/任意 classifier Exception、非法 JSON 或 Schema 输出都会保留规则实体，返回 fallback，warning=semantic_classifier_failed；不输出 API exception 文字或查询正文。没有无限重试。

Fallback 和未配置 classifier 的 rules 路径使用明显关键词的有限匹配：唯一意图 cue → medium；多个 cue → 固定顺序 alarm_fault / maintenance / parameter / parts / knowledge 选首个，low + multiple_intent_cues；无可靠 cue → general/low。关键词不能处理完整语义、否定或所有非制造业同义词，不能把 synthetic 用例当成真实业务准确率。

空白、非 string、无法 UTF-8 编码或超过 16384 chars 的输入返回 general/low + invalid_query，classifier 零调用；classifier 响应上限 32768 chars。普通合法输入中的异步取消/进程终止不被 Exception fallback 吞掉。transport 超时须由 completion 实现；本模块不声称能中断永久阻塞的第三方 callable。

## Usage

无需模型/API 的显式分析：

```python
from rag_qa.query import QueryAnalyzer

analysis = QueryAnalyzer().analyze("MZ-2000 报警 E102 怎么处理？")
print(analysis.to_metadata())  # rules，alarm_fault / medium；不执行检索或回答
```

语义边界使用调用方提供的 completion：

```python
from rag_qa.query import QueryAnalyzer, JSONSemanticClassifier

def completion(*, messages, temperature, response_format):
    # 接入已配置的 JSON 分类服务，设置有限 timeout，并返回 content 字符串。
    # 此处为 synthetic 示例，未调用真实服务，不是生产分类器。
    return '{"intent":"alarm_fault","confidence":"high","entities":{"alarm_code":"E102"}}'

analysis = QueryAnalyzer(JSONSemanticClassifier(completion)).analyze(
    "MZ-2000 报警 E102 怎么处理？"
)
```

## Stage 6 boundary and verification

当前在线 new_rag_system/教育 BERT/Direct/HyDE/Subquery/Backtracking 完全保留。Stage 6 可以依据 confidence 和 warnings 决定严格过滤、放宽或无 Metadata Filter；本 Stage 不构造表达式、不操作 Milvus、不改变 Hybrid Retrieval，也不因 low 自动去掉 Filter。QueryIntent 不与文档 KnowledgeType 一对一自动映射。

测试素材均 synthetic。验证六意图结构、规则例子/字段保持、日期/量值拒绝、完整文本证据、冲突/幻觉/歧义 guard、JSON Schema/temperature、异常 fallback 和全新进程阻断 SDK/Legacy 导入。真实 API/LLM 语义质量、线上 RAG/Filter 和完整集成 NOT RUN；Full Integration Readiness: NO。

详细命令/结果与 Git 证据见 [Stage 5 报告](STAGE_REPORTS/STAGE5_REPORT.md)。Stage 6–13 PENDING，不自动推进。
