# Stage 12 — Retrieval Evaluation + Hit@K + MRR + RAGAS

日期：2026-10-05；分支 main；起始 HEAD `d4ea1fd58544e88a789d94b96f4a8f4436ddb0bf`，fetch 后 origin/main 相同且 Working Tree clean。Implementation: PASS；Metric Unit Validation: PASS；Real Retrieval Evaluation: NOT RUN；**Overall Stage 12: PARTIAL**。Last Completed Stage 保持 11 — PASS；Active Stage: NONE；Stage 13: PENDING / readiness NO；Full Integration Readiness: NO。

最新 Completion（2026-10-05，开始 HEAD `2c168dc972e75dc7de34265c5df9ba83fc8ff959`）：真实本地 BGE-M3 embedding / CrossEncoder predict 与 Milvus 连接 PASS；Direct Provision 被现有服务的 nullable 合约不兼容阻断，Overall 仍 PARTIAL。下面原实现阶段的结果/环境为历史记录，最新命令、资源现场和限制见末尾 Completion 节。

GitHub Sync: PASS。实现提交 `7d9e7a38c56e77153d7879c5e56df38323702d3d` 已正常 Push；随后 fetch、两个 rev-parse 返回相同 SHA，git status 为 clean。在该干净实现提交上复跑离线预检，机器报告记录该 Git SHA 和 source_tree_dirty=false；最终发布记录用独立文档提交同步，最终 HEAD 在回复核验提供，不预写自身哈希。Git发布不改变Stage 12 PARTIAL或真实检索NOT RUN结论。

## 范围与文件

新增 `rag_qa/evaluation/` 的 schemas/metrics/evaluator/adapters/runner/ragas_runner/provenance/benchmark，独立制造业 canonical 标签集和 [机器报告](../evaluation_results.json)。复用已有 Stage 5/6/7/8/9 实际组件；fake/recording 仅用于单测，不输出受控真实检索质量分数。教育 rag_assessment、旧 CSV/输出、业务语料、requirements/config/Stage 2–10 业务语义与历史报告保持。

新增 retrieval/settings.py；VectorStore 仅制造业 hybrid 参数改为读取实例 settings，默认行为保持。API cache/service/runtime 最小增加检索配置版本/指纹传播，已验证 k/M/weights/nprobe/BM25 改变会 miss，修复未来维护调参后旧答案仍命中的边界。四个 Stage 12 测试文件覆盖确定指标/严格标签/统计/配对/资源保护/配置/cache、实际 Stage 9 方法 scripted subquery 与一次 rerank。同步 README/治理/计划/index/当前架构/迁移计划/[评估合约](../MANUFACTURING_EVALUATION.md)/缓存合约。

## 实际数据与指标

| 项目 | 实际结果 |
| --- | --- |
| Dataset type / scope | controlled_synthetic；SYNTHETIC / NOT PRODUCTION FACTS |
| Dataset sample count | 25；3 models / 21 authored documents / 42 authored children |
| Dataset SHA256 | 93764ff2054c900a5a4991b4bc2296edc37fa21621e33d988c217443b3d2ea7b |
| Knowledge revision | NOT RUN / null（未建立真实 eval Manifest） |
| Report Git SHA / source snapshot | 实际命令执行时的 HEAD 与代码 bytes hash/dirty 标记，见机器报告；最终发布 SHA 在回复提供 |
| Collection / schema | manufacturing_rag_eval_v1 / manufacturing_v1，仅计划名称，未创建集合 |
| BGE-M3 / Milvus / CrossEncoder | 真实运行均 NOT RUN；单测 recording/fake 不是质量评估 |
| k / M / weights / nprobe | 5 / 2 / 0.8, 0.3 / 10，生产默认未调 |
| BM25 acceptance | disabled；production tuning: NOT AUTHORIZED BY DATA |
| Child Hit@5 / Recall@5 / MRR@5 | NOT RUN |
| Parent Hit@2 / Recall@2 / MRR@2 | NOT RUN |
| Document Hit@2 / Recall@2 / MRR@2 | NOT RUN |
| Hard identifier leak / FastPath quality / Strategy delta | NOT RUN；只有确定统计控制单测 |
| RAGAS faithfulness/relevancy/context precision/context recall | NOT RUN；answer-quality RAGAS not validated |
| Real retrieval/rerank/total latency | NOT RUN；测试计时不当真实性能 |
| Production tuning changed? | NO；synthetic 无生产调参授权 |

## Commands / Results

Python 为 `.venv/stage1-validation/Scripts/python.exe`（3.13.9），pytest 8.4.2。模型权重文件本地存在，但该环境缺 milvus_model/sentence_transformers/torch/langchain_core；默认 Python 虽有 torch，仍缺 milvus_model/sentence_transformers/langchain_core，不能推断模型可运行。未连接 Milvus/Redis/外部 LLM，未下载模型或安装大型运行栈。

| Command | Result | Status |
| --- | --- | --- |
| git status --short / branch / log / fetch / 两 rev-parse | 指定基线、main、初始 clean、远端一致 | PASS |
| importlib.find_spec + 模型目录/文件检查（两 Python 环境） | 真实模型栈缺依赖；weights 存在不代表推理通过 | PASS（预检事实） |
| `python -m pip download ragas==0.2.6 --no-deps --dest .venv/stage12-api-inspection` + zipfile API 源码读取 | 157KB wheel，未安装/升级；0.2.6 参数/字段/类已核对 | PASS |
| cache/runtime/retrieval 首轮 targeted pytest | 91 passed / 0 failed | PASS |
| 四个 Stage 12 文件初轮 pytest | 83 passed / 1 skipped；Live 未启用 | PASS（unit） |
| 加入 scripted/provenance/rejection 验证后的 Stage 12 pytest | 89 passed / 1 skipped | PASS（unit） |
| `python -m pytest tests -q -rs --tb=short` | 999 passed / 0 failed / 13 skipped，Stage 12 核心 92 项 | PASS（实际运行范围） |
| `python -m rag_qa.evaluation.runner --prepare` | 25 canonical synthetic 样本及稳定 dataset SHA | PASS |
| `python -m rag_qa.evaluation.runner --output docs/evaluation_results.json` | preflight ready=false；全部真实 metrics null / NOT RUN | PASS（预检），质量 NOT RUN |
| real BGE→Milvus Dense/Sparse→filter→aggregation→CrossEncoder / RAGAS judge | 缺依赖及显式 judge，未启用 Live | NOT RUN |
| AST / 相对链接 / git diff --check / 受保护范围 | 18个Python文件、184个相对链接；Legacy方法及Stage 2–10/教育评估/config/requirements保持；机器报告代码指纹一致 | PASS |
| Commit / Push / fetch/equal / clean | 实现7d9e7a3正常发布，Local HEAD == origin/main且clean；完成发布记录独立文档提交，最终SHA在回复核验 | PASS |

13 skipped = 历史12项缺完整依赖或 Stage 3 Live 未启用，加 Stage 12 Live 未启用1项；不把 skip 当 PASS。增加helper拒绝生产资源测试后最终999 passed / 13 skipped；此前完整轮998 passed / 13 skipped。未发生测试失败轮。审阅时修正 scripted planner 返回类型及 rejection reason-code 统计，并加对应实际 Stage 9 控制验证；没有修改生产 Stage 9。

## 限制与停止边界

本次没有 approved representative Manufacturing Evaluation Set，也没有实际真实检索。case C 只能 Implementation/Metric Unit PASS、Overall Stage PARTIAL；不能将 synthetic 或手工 fake 排名的满分写成 Manufacturing Quality。V2 标签场景不冒充真实多版本 live mutation 测试，完整 Loader/摄取/服务启动未验证。

Live Runner 明确 opt-in，只能新建/读取隔离 eval Collection 和独立 Manifest，不 drop/clear/delete 正式资源；普通单测不加载模型/数据库/API。DIRECT baseline bypass fast/planner；scripted 只作 controlled strategy test，LLM 仅显式选择才调用。Stage 9 的 M 仍由 config 所有，M 候选实验只在 --mode direct 中运行；不修改全局 config，文档声明该限制。

阶段实测报告不能证明生产质量、性能、Planner 准确率或答案正确率。停止在 Stage 12 PARTIAL，不开始 Stage 13。

## Stage 12 Completion：真实环境尝试（2026-10-05）

从用户指定 main `2c168dc972e75dc7de34265c5df9ba83fc8ff959` 开始，git fetch origin 后两个 HEAD 相同且初始 clean。未改任何 repository Python 源码、固定 Dataset、Ground Truth、配置、requirements、Compose 或生产数据。最新机器证据：[Completion Preflight](../stage12_completion_preflight.json)、[Direct失败结果](../evaluation_results_direct.json)。原 [evaluation_results.json](../evaluation_results.json) 保留最初 NOT RUN 预检来源；新的 Paired 尚未执行，不能替换成假 paired 分数。

使用现有 `D:\Soft\ANACONDA\Anaconda\envs\EduRAG\python.exe`，Python 3.10.18。分发 Metadata 的 torch2.10.0 / pymilvus2.5.4 / milvus-model0.2.5 / sentence-transformers3.0.1 / langchain-core1.2.16 / FlagEmbedding1.3.5 均匹配 requirements；torch runtime 为2.10.0+cpu。未安装/升级依赖或下载模型。HF_HUB_OFFLINE / TRANSFORMERS_OFFLINE / HF_DATASETS_OFFLINE 均为1，模型路径仍原本地 bge-m3 / bge-reranker-large。单独预检文件位于 ignored .venv，结果位于 ignored runtime；日志、缓存、模型和 venv 不发布。

| Command / action | Result | Status |
| --- | --- | --- |
| Python环境 metadata 检查与实际 import torch/sentence_transformers/milvus_model/pymilvus/langchain_core | 现有3.10环境及固定核心依赖均可导入 | PASS |
| `.venv/stage12-model-preflight.py`：BGEM3EmbeddingFunction本地实例化与一次encode | Dense shape (1,1024)，Sparse nnz16，向量有限 | PASS（真实模型预检） |
| 同脚本：CrossEncoder本地实例化与一次predict | finite score 0.02599869854748249；不是质量指标 | PASS（真实模型预检） |
| 初次 localhost:19530 TCP / docker ps | ConnectionRefusedError；Docker Desktop未启动 | FAIL（初次环境状态） |
| `docker desktop start --detach`；`docker start milvus-etcd milvus-minio`；`docker start milvus_standalone` | 启动本机已存在的运行环境；没有创建/升级容器或改Compose | PASS |
| MilvusClient get_server_version / list_databases / has_collection(eval_v1) | localhost:19530；server v2.4.10；itcast07已存在；初始eval_v1不存在 | PASS（真实连接） |
| Direct Provision CLI（下文） | exit1，ManufacturingSchemaMismatchError；nullable被返回为false | FAIL（真实Schema兼容） |
| 同CLI用新v2集合/Manifest重试，输出runtime/evaluation/evaluation_results_direct_v2.json | 相同Schema mismatch，exit1，保留现场 | FAIL（确认非名称碰撞） |
| describe_collection / get_collection_stats（仅eval_v1/v2） | 两集合存在，row_count均0；两个Manifest均不存在 | PASS（现场核验） |
| `.venv/stage1-validation/Scripts/python.exe -m pytest tests -q -rs --tb=short` | 999 passed / 0 failed / 13 skipped；使用原3.13.9验证环境，非真实质量指标 | PASS（控制回归） |
| 42 Children实际upsert / Manifest commit / 25-query完整检索 / Paired /真实检索latency | 在Schema兼容验证前被阻断 | NOT RUN |
| RAGAS Judge / Real Planner LLM | 本任务不要求，未接外部Judge/Planner | NOT RUN |

运行命令（PowerShell，以该 Conda Python 执行；仅进程环境设 STAGE12_LIVE=1）：

```powershell
python -m rag_qa.evaluation.runner --live --provision --mode direct --collection manufacturing_rag_eval_v1 --manifest runtime/evaluation/manufacturing_rag_eval_v1.sqlite3 --output docs/evaluation_results_direct.json
```

精确阻塞：`ManufacturingSchemaMismatchError`；`field=equipment_type.nullable; expected=True; actual=False`。实际describe同样返回equipment_model/alarm_code/part_number nullable=false。既有server v2.4.10不能保持当前manufacturing_v1的nullable合约；本次未改SDK、Schema或None语义绕过。v1是本次初次Provision留下的空集合，按恢复规则用新的v2重试，得到同一差异；未drop/clear/delete任何集合，未读取或修改正式manufacturing_rag_v1/edurag内容。

Milvus [2.5 nullable官方文档](https://milvus.io/docs/v2.5.x/nullable-and-default.md)说明nullable应在建集合时设定且不能事后更改；本次以真实describe与现有严格validator为直接证据，不把更换集合名当兼容修复。不升级/重建本机服务，不进入Stage 13基础设施任务。后续需提供能保留Stage 3 nullable字段的兼容Milvus环境，再用新的隔离资源运行；这是尚未满足的环境条件，不是已完成事项。

本地preflight曾因检查代码假定Dense为numpy而产生AttributeError（真实SDK实际返回list），已仅修正ignored检查脚本，再次真实encode/predict通过；repository源码未变。Live CLI失败的原因是独立的nullable mismatch。requests传递依赖有版本warning，但实际模型与SDK导入/推理成功，未擅改固定依赖。EduRAG环境未安装pytest，回归明确使用既有validation venv，不混淆两个运行环境。

Dataset仍CONTROLLED SYNTHETIC / 25 / SHA256 `93764ff2054c900a5a4991b4bc2296edc37fa21621e33d988c217443b3d2ea7b`。Knowledge revision=null；所有Child/Parent/Document Hit/Recall/MRR、FastPath质量、Strategy效果与真实检索延迟仍NOT RUN。生产参数保持k5/M2/weights0.8,0.3/nprobe10/BM25 disabled；production_quality_claim=false，production tuning NO。Stage 12 PARTIAL，Stage 13 readiness NO，Full Integration Readiness NO。

运行现场保留：Docker Desktop及原milvus_standalone/etcd/minio处于运行状态；若需停止本次启动的服务，可执行 `docker stop milvus_standalone milvus-etcd milvus-minio`，只停止服务，不删除数据。再次运行不得对v1/v2使用--provision或清空它们，须先核验，兼容环境上使用新的隔离名称。

Completion GitHub Sync: PASS。证据提交 `8e936846589746cb32a6d6dd6a7281510243a81a` 已正常Push；`git fetch origin`、`git rev-parse HEAD`、`git rev-parse origin/main`返回同一SHA，`git status`为clean。最终检查197个相对链接、Dataset SHA及保护范围均PASS，`git diff --check` PASS；只有本任务文档/证据变化。发布记录用独立文档提交同步，最终HEAD在回复核验提供，不预写自身哈希。Git发布成功不改变Stage 12 PARTIAL结论；当前任务停止，不开始Stage 13。
