# Manufacturing Retrieval Evaluation（Stage 12）

2026-10-05：Implementation / Metric Unit Validation: PASS；Real Retrieval Evaluation / RAGAS: NOT RUN；Stage 12: PARTIAL。Full Integration Readiness 与 Stage 13 readiness: NO。当前环境可运行评估单测，不能从 fake adapter 得出真实检索质量。

## 数据与来源

独立模块 `rag_qa/evaluation/`，旧 `rag_qa/rag_assessment/` 教育数据、CSV 和脚本保持不变。严格 `EvaluationDataset` 接受 controlled_synthetic / approved_manufacturing / production_replay，以及明确 provenance_note。后两者的标识是调用方对来源的声明，需要外部审批依据，不由字符串自动证明生产代表性。

`RetrievalEvaluationSample` 要求唯一 sample_id、非空有界 UTF-8 query，以及三层非空 Relevant ID 集；Parent/Child 必须小写 SHA256，Document ID 是 Stage 1/2 的业务命名空间字符串，不能强制成 SHA。QueryEntities 复用 identifier 合法格式；禁止重复 IDs/tags，期望集合排序规范化，Ranking 则按首次出现去重后 Top-K。没有 Relevant IDs 的负样本不混入这些指标，须另设计负样本评估。

JSONL 第一行是无 samples 字段的 dataset header，后续每行一个 sample；JSON 是完整对象。拒绝重复 JSON key、NaN、空 dataset 和教育旧结构。Canonical JSON 排序 sample_id 与集合标签、紧凑序列化后计算 dataset_sha256；它是规范化内容 hash，不是含空白的文件 bytes hash。

固定文件：[controlled_synthetic_v1.json](../rag_qa/evaluation/benchmarks/controlled_synthetic_v1.json)。25 样本、3 个合成设备型号、21 篇合成文档、42 个 authored Child，覆盖 alarm/fault/maintenance/parameter/parts/manual/case、相同 E102、相似症状/PN、active V2 与多相关 Parent。ID 由真实 Stage 2 build_parent_id/build_child_id 公式生成；这证明身份构造，不证明真实 Loader/业务语料。V2 场景只是固定 active 标签及正文中的 V1 历史提示，未执行 V1→V2 真实 Milvus 更新测试。

**SYNTHETIC / NOT PRODUCTION FACTS**。数据集 SHA256：`93764ff2054c900a5a4991b4bc2296edc37fa21621e33d988c217443b3d2ea7b`。禁止用此数据开启生产 BM25 或调生产权重。

## 指标与观测

Hit@K = Top-K 存在 Relevant ID；Recall@K = Relevant ∩ Top-K 的数量 / Relevant 总数；MRR@K = 第一个 Relevant rank 的倒数，未命中为 0。对样本取 macro mean，JSON 保留原浮点，不取整成夸张百分比。空切片返回 sample_count=0 和 null；空 Dataset 明确拒绝。

Child 用 k=5；Parent 和 Document 分别用 M=2，三层独立统计。Document 按最终 Parent 顺序稳定去重；不能把 Child Hit@5 当 Parent Hit@2。FastPath 接受时未执行 Child 检索，Child 指标标 not_applicable_fast_path 并排除该层 denominator。真正运行错误则保留在指标 denominator 中按空排名计 0，同时记录 error_count，不把错误样本静默丢掉。

逐样本保留 query/expected 与 returned IDs、first relevant rank/hit/recall/mrr、原 QueryAnalysis、planner source/fallback、filter expression/attempts、FastPath status/reason/raw BM25 score/scope/token count 与可选 timings。按 labeled intent、tag、hard/no-hard、alarm/non-alarm切片；期望 identifier 与分析输出 mismatch 单独记录。

Leak 检查所有返回 Child 和 Parent 的 Metadata 对期望 equipment_model/alarm_code/part_number，缺字段也算不兼容。sample leak count/rate 以成功且有 hard 标签的样本为 denominator，失败计数另列；leaked item count 包含 Child 和 Parent 两种输出项，不代表去重后的文档数量。值实测，不硬编码 0。

Exact Alarm、Exact FAQ、BM25 分开：eligible 由明确 fast_path_labels 给出；接受统计包括无 eligibility 标签的接受并另列此计数，coverage 只用 eligible accepted / eligible。precision 要求 Parent 与 Document label 命中且无 hard leak。BM25 阈值 sweep 用有限 raw score + matched tokens，输出 accepted/precision/coverage/relevant recall/false accepts；只做诊断，不启用生产。当前没有真实 sweep 或 precision/coverage 分数。

## 实际组件与实验

`ComponentEvaluationAdapter` 复用 Stage 5 分析、Stage 6 Hybrid/Filter、Stage 7 聚合/CrossEncoder、Stage 8 probe、Stage 9 策略/融合；观察 wrapper 记录同一轮实际 Child 结果，不为评估再次检索/重排。DIRECT 明确不使用 Planner/FastPath；Strategy 允许 none/scripted/显式 LLM。Scripted 只表示 controlled strategy test。真实 LLM Planner 调用才可讨论真实策略效果；本阶段没有 Planner 准确率。

Paired comparison 要求 dataset SHA、knowledge revision、检索配置 fingerprint、sample_ids 一致，计算 Parent hit/recall/mrr 和 zero-result-rate delta 及逐样本 delta。Manifest/FastPath revision 在前后复核，变更则报告失败，不冒充同一快照；这不是 Milvus 事务一致性保证。

冻结生产基线：`k=5 / M=2 / Dense=0.8 / Sparse=0.3 / nprobe=10 / BM25 disabled`。`EvaluationProfile` 支持独立 k/M/weights/nprobe/BM25 raw threshold，名称不参与语义指纹；实例 scoped settings 注入制造业 VectorStore，不写 config.ini。`--mode direct` 支持 M 实验；原 Stage 9 Top-M 仍归 config 所有，paired/strategy 的 M 必须等于当前 config，禁止临时改全局值伪装实验生效。小量候选由用户提供 profile，不做大网格暴搜。

Report 记录 Git SHA、实际代码 bytes hash 与 dirty 标记、collection/schema、模型/设备/依赖环境、knowledge revision 和配置快照。`perf_counter` 单独记录 Child 检索和 CrossEncoder predict 时间，总时延包含分析/策略/聚合等；均无生产性能承诺，unit_test timing 不能当真实性能。

## 命令与资源安全

仓库根目录，默认离线预检，不自动加载模型或连接 Milvus/LLM：

```powershell
python -m rag_qa.evaluation.runner --output .venv/stage12-evaluation/evaluation_results.json
python -m rag_qa.evaluation.runner --prepare --dataset .venv/stage12-evaluation/controlled_synthetic.json
python -m pytest tests/test_manufacturing_evaluation_metrics.py tests/test_manufacturing_evaluation_dataset.py tests/test_manufacturing_evaluation_runner.py tests/test_manufacturing_retrieval_contract.py -q -rs
```

真实依赖/服务准备后才能执行以下示例，本阶段 **NOT RUN**：

```powershell
$env:STAGE12_LIVE = '1'
python -m rag_qa.evaluation.runner --live --provision --collection manufacturing_rag_eval_stage12_run001 --manifest .venv/stage12-evaluation/run001.sqlite --planner scripted --output .venv/stage12-evaluation/run001.json
Remove-Item Env:STAGE12_LIVE
```

Collection 必须 manufacturing_rag_eval_ 前缀且不能等于配置中的两个正式集合；Manifest 必须显式路径，禁止正式 Manifest。provision 只允许不存在的 collection/DB，使用新 evaluation collection 的原 Stage 3 add_documents 和 snapshot verification，再提交独立 Manifest。仅适用于固定 synthetic 基准；不是完整 Loader/Stage 4 ingestion replay。不能并发 provision 同名资源。程序不 drop/clear/delete 集合，不自动清理任何资源；失败保留现场并返回 PARTIAL。已有 eval 资源须与实际 active Manifest/Child/Parent labels 匹配才可评估；未配置真实服务时不要直接执行上述示例。

已有资源复跑去掉 --provision；`--profile <json> --mode direct` 用于 M 候选实验，`--planner llm` 才显式调用配置 LLM。普通单测 Live 默认 skipped；可选测试还需要 STAGE12_EVAL_COLLECTION / STAGE12_EVAL_MANIFEST 指向准备好的评估资源。

## RAGAS 与缓存联动

RAGAS 辅助评估只接受 query、retrieved_contexts、generated_answer、reference_answer 四项齐全的 `AnswerEvaluationSample`，必须显式提供 judge LLM/embedding/model、dataset SHA/Git SHA 以及 enabled=True。独立 `run_ragas()` 不调用生成器，调用方从经过 Stage 10 guard 的结果收集答案与实际 contexts，不复用教育数据。

按锁定 ragas==0.2.6 的下载 wheel 检查 EvaluationDataset.from_list、Faithfulness、ResponseRelevancy、LLMContextPrecisionWithReference、LLMContextRecall；评估入口参数核对 [0.2.6 官方源码](https://github.com/explodinggradients/ragas/blob/v0.2.6/src/ragas/evaluation.py)。未安装/升级 RAGAS；只在 ignored .venv 下载 157KB wheel 查看源码。Judge 默认禁用，要求 finite timeout/有限并发，缺 API/embedding/版本不符/异常/非有限分数一律 NOT RUN，不生成假分数；记录实际 eligible 输入 SHA 和样本数。Recording API 测试不是实际 RAGAS 运行，LLM judge 也不是绝对 Ground Truth。

`retrieval/settings.py` 集中制造业默认权重/nprobe 与 manufacturing_retrieval_v1。在线工厂把 VectorStore 的 effective settings 传给 Service；Cache Key 增加 contract version + retrieval_config_fingerprint，覆盖 k/M/weights/nprobe/BM25 mode/threshold。值相同指纹相同，各字段变化导致旧缓存 miss；旧 key 依原 TTL 过期，无 FLUSHDB。Legacy hybrid 的权重/字面量与算法不改，Stage 2–10 业务语义/生成 guard 保持。

本阶段实际结果：[evaluation_results.json](evaluation_results.json)；命令证据与限制：[Stage 12 报告](STAGE_REPORTS/STAGE12_REPORT.md)。Real Retrieval、FastPath quality、Strategy quality、真实时延和 answer-quality RAGAS 均 NOT RUN；production tuning: NOT AUTHORIZED BY DATA。
