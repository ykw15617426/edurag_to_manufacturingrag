# Stage 12 — Retrieval Evaluation + Hit@K + MRR + RAGAS

最新结论（2026-10-05 Completion V2）：**Stage 12: PASS**，真实受控Retrieval Evaluation PASS；Last Completed Stage: Stage 12 — PASS；Active Stage: NONE；Stage 13 PENDING/readiness YES；Full Integration Readiness NO。RAGAS/真实LLM Planner NOT RUN，Production tuning NO。具体版本、指标与边界见末尾Completion V2。

## 原实现及前次Completion记录（历史）

日期：2026-10-05；分支 main；起始 HEAD `d4ea1fd58544e88a789d94b96f4a8f4436ddb0bf`，fetch 后 origin/main 相同且 Working Tree clean。Implementation: PASS；Metric Unit Validation: PASS；Real Retrieval Evaluation: NOT RUN；**Overall Stage 12: PARTIAL**。Last Completed Stage 保持 11 — PASS；Active Stage: NONE；Stage 13: PENDING / readiness NO；Full Integration Readiness: NO。

前次 Completion（历史，2026-10-05，开始 HEAD `2c168dc972e75dc7de34265c5df9ba83fc8ff959`）：真实本地 BGE-M3 embedding / CrossEncoder predict 与 Milvus 连接 PASS；Direct Provision 被现有服务的 nullable 合约不兼容阻断，Overall 仍 PARTIAL。下面原实现阶段的结果/环境为历史记录，最新命令、资源现场和限制见末尾 Completion 节。

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

从用户指定 main `2c168dc972e75dc7de34265c5df9ba83fc8ff959` 开始，git fetch origin 后两个 HEAD 相同且初始 clean。未改任何 repository Python 源码、固定 Dataset、Ground Truth、配置、requirements、Compose 或生产数据。当时机器证据：[Completion Preflight](../stage12_completion_preflight.json)、[归档Direct失败结果](../stage12_completion_v1_direct_failure.json)。当时Paired未执行、最初NOT RUN报告保留在Git历史；本次Completion V2真实成功后evaluation_results.json已更新为Paired，evaluation_results_direct.json已更新为真实v4 Direct。

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


## Completion V2 — Compatible Milvus Live Evaluation（2026-10-05）

起始main `ac57fca5763c3b38405ad0b9d4057038f60c7cd3`，fetch后远端一致、Working Tree clean。**Stage 12 Retrieval PASS**；独立correctness fix `91d980ac33138ac51b44c36fc560afe577ef54bb`。评估源提交即该修复提交，报告source_tree_dirty=true来自计划/结果文档变化；没有未提交业务实现。

### 实际环境、资源与修复

继续现有EduRAG Python3.10.18及固定模型依赖，没有修改requirements、下载替代模型或改config.ini。真实BGE-M3 / Milvus / CrossEncoder为REAL；仅当前进程环境覆盖localhost:19531 / stage12_eval_v2，HF_HUB_OFFLINE / TRANSFORMERS_OFFLINE / HF_DATASETS_OFFLINE为1。

临时Compose位于ignored `runtime/stage12-milvus-v2/docker-compose.yml`，依据[Milvus v2.5.4官方部署配置](https://github.com/milvus-io/milvus/blob/v2.5.4/deployments/docker/standalone/docker-compose.yml)调整隔离名称并显式指定目标镜像。实际get_server_version返回**pkg/v2.5.4**，PyMilvus **2.5.4**；不从image tag推断版本。独立stage12-v2-milvus/etcd/minio、stage12-v2-eval-network及三套stage12-v2-eval-*-data卷；仅Milvus绑定127.0.0.1:19531与管理端口19091，etcd/MinIO不对宿主发布。正式docker-compose.yml/旧milvus_standalone/etcd/minio未修改、升级、停止或删除；旧19530没有端口冲突。

Nullable probe：新Collection manufacturing_rag_eval_nullable_probe_v3，equipment_type nullable=True实际describe通过；插入id=1/equipment_type=None，Strong读回同样为null，row_count=1。临时检查脚本先纠正实际版本字符串pkg/v前缀；随后因SDK insert返回ids为RepeatedScalarContainer导致证据JSON序列化失败，仅修正ignored脚本并只读核验已有探针，无重复创建/插入或删除；不是nullable功能失败。

第一轮v3 Direct仍FAIL：ManufacturingSchemaMismatchError / dense_index.nlist expected128 / actualNone，服务器实际顶层nlist="128"、drop_ratio_build="0.2"；字段nullable校验已通过。实际SDK [2.5.4 describe_index源码](https://github.com/milvus-io/pymilvus/blob/v2.5.4/pymilvus/client/grpc_handler.py)可返回顶层参数，仓库校验只读params误判。修复仅读取两种真实表示，有两种时同时验证；继续拒绝缺失/错误/非有限/冲突值，字段/索引规格、None、IDs及检索设置保持。13项新增离线测试证明兼容读取与拒绝行为；Schema专项116 passed / 1 skipped。v3空集合及无Manifest现场保留，修复后只读Schema/Index PASS；不用它再次--provision，换新v4。

成功Collection **manufacturing_rag_eval_v4**；Manifest **runtime/evaluation/manufacturing_rag_eval_v4.sqlite3**；实际42 Child、21 active Document快照。Schema/Index、实际Child ID集合、Ground Truth Parent/Document/Child标签核验PASS。

Knowledge revision：`bb0502be277fc6ccb09ce49c4101020e67ae130fcdf19c604553df4678b176c7`；Provision Direct、Paired Direct、Strategy及结束只读核验相同。Dataset仍25 samples / controlled_synthetic / SHA256 `93764ff2054c900a5a4991b4bc2296edc37fa21621e33d988c217443b3d2ea7b`，固定标签和业务数据未改。

### Command / Result

| Command / action | Result | Status |
| --- | --- | --- |
| `docker compose -f runtime/stage12-milvus-v2/docker-compose.yml up -d --wait --wait-timeout 180` | 独立三容器/网络/卷，全部healthy | PASS |
| `nullable_probe.py` 与只读 `--verify-existing` | actual pkg/v2.5.4 / client2.5.4；nullable=True、None写读 | PASS（临时脚本序列化修正后） |
| v3 Direct --live --provision | 顶层Index参数被误判；无Child/Manifest | FAIL（修复前历史） |
| v4 Direct命令（下文） | Schema→42 Child真实BGE→upsert→Manifest→snapshot→25 retrieval→CrossEncoder→metrics；exit0 | PASS |
| v4 Paired命令（下文，不含--provision） | 25/25 Direct+25/25 scripted Strategy，revision稳定；exit0 | PASS |
| `runtime/stage12-milvus-v2/verify_evaluation.py` | 真实资源只读复核及所有安全阈值/来源/分母核验 | PASS |
| `.venv/stage1-validation/Scripts/python.exe -m pytest tests -q -rs --tb=short`（Live后） | 1012 passed / 0 failed / 13 skipped | PASS |
| `runtime/stage12-milvus-v2/final_checks.py` / `git diff --check` | 211相对链接、2 Python AST、15文件合法任务范围、固定Dataset/Schema合约/参数及失败归档内容保持 | PASS |

13 skipped是原轻量validation环境缺完整应用依赖及未启用Stage3/12 Live测试；真实模型/检索已另用3.10环境CLI执行，不将skip当集成通过。此前全回归和专项也通过；未安装新pytest到真实模型环境。

```powershell
$env:MILVUS_HOST = "localhost"
$env:MILVUS_PORT = "19531"
$env:MILVUS_DATABASE_NAME = "stage12_eval_v2"
$env:STAGE12_LIVE = "1"
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
$env:HF_DATASETS_OFFLINE = "1"
$env:PYTHONPATH = "D:\AiProject\edu_rag"
$stage12Python = "D:\Soft\ANACONDA\Anaconda\envs\EduRAG\python.exe"
# 首次实际Provision；现有v4禁止重复此命令
& $stage12Python -m rag_qa.evaluation.runner --live --provision --mode direct --collection manufacturing_rag_eval_v4 --manifest runtime/evaluation/manufacturing_rag_eval_v4.sqlite3 --output docs/evaluation_results_direct.json
# 同资源复跑只用此Paired命令，无--provision
& $stage12Python -m rag_qa.evaluation.runner --live --mode paired --planner scripted --collection manufacturing_rag_eval_v4 --manifest runtime/evaluation/manufacturing_rag_eval_v4.sqlite3 --output docs/evaluation_results.json
```

### 三层ID指标（Paired同快照）

| Metric | Direct | Strategy | Strategy − Direct |
| --- | ---: | ---: | ---: |
| Child Hit@5 | 1.000000 | 1.000000 | +0.000000 |
| Child Recall@5 | 0.870000 | 0.875000 | +0.005000 |
| Child MRR@5 | 0.933333 | 1.000000 | +0.066667 |
| Parent Hit@2 | 1.000000 | 1.000000 | +0.000000 |
| Parent Recall@2 | 1.000000 | 1.000000 | +0.000000 |
| Parent MRR@2 | 1.000000 | 1.000000 | +0.000000 |
| Document Hit@2 | 1.000000 | 1.000000 | +0.000000 |
| Document Recall@2 | 1.000000 | 1.000000 | +0.000000 |
| Document MRR@2 | 1.000000 | 1.000000 | +0.000000 |

Direct三层分母25；Strategy Parent/Document分母25，Child分母仅4：21次FastPath接受没有Child检索。Child层差值只是不同分母的诊断，不构成检索质量提升结论。独立Provision Direct的三层质量数值与Paired Direct相同，时延不同。所有原始未取整指标和逐样本记录保存于JSON。

### Safety / Strategy

Direct/Strategy的error_count=0、hard_identifier_leak_count=0、identifier_analysis_mismatch_count=0、zero_result_count=0；各25/25执行。规则intent mismatch各3，完整保留，没有通过改标签隐藏。Paired是controlled scripted strategy test：24 direct / 1 subquery / 0 rewrite，fallback0；不代表真实LLM Planner准确率，也没有验证本轮未触发的rewrite效果。

| FastPath | Eligible | Accepted | Incorrect accepted | Precision | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| exact_alarm | 3 | 3 | 0 | 1.0 | 1.0 |
| exact_faq | 18 | 18 | 0 | 1.0 | 1.0 |
| bm25_faq | 3 | 0 | 0 | null / N/A | 0.0 |

BM25仍disabled，0接受的precision为null；incorrect accepted=0不证明开启BM25安全。Exact Alarm/FAQ接受均属于固定synthetic样本，不代表生产准确率。

### Latency（local CPU controlled synthetic benchmark）

| Run | Stage | Samples | mean_ms | p95_ms |
| --- | --- | ---: | ---: | ---: |
| Provision Direct | child_retrieval | 25 | 149.642 | 158.547 |
| Provision Direct | rerank | 25 | 536.945 | 614.604 |
| Provision Direct | total_retrieval | 25 | 687.315 | 772.233 |
| Paired Direct | child_retrieval | 25 | 153.224 | 172.075 |
| Paired Direct | rerank | 25 | 452.325 | 610.940 |
| Paired Direct | total_retrieval | 25 | 606.205 | 757.007 |
| Strategy | child_retrieval | 25 | 35.894 | 157.283 |
| Strategy | rerank | 25 | 89.136 | 508.237 |
| Strategy | total_retrieval | 25 | 125.811 | 658.478 |

时延只覆盖检索调用，不含模型加载、摄取或API/网络生成，未受控分析主机负载/冷启动。Strategy mean包含21次无Child/CE推理的FastPath，不能把这个均值当单次BGE或CrossEncoder耗时，不是生产SLA。

### 文件、保护范围与停止边界

源码修改仅rag_qa/core/milvus_schema.py参数描述规范化，测试仅tests/test_manufacturing_milvus_schema.py。文档/机器结果：AGENTS.md、.agent/PLANS.md、README.md、docs/README.md、CURRENT_ARCHITECTURE、MANUFACTURING_MIGRATION_PLAN、MANUFACTURING_EVALUATION、MANUFACTURING_MILVUS_SCHEMA的相关说明、本报告、evaluation_results.json、evaluation_results_direct.json、新stage12_completion_v2_verification.json及原样stage12_completion_v1_direct_failure.json归档。旧stage12_completion_preflight.json原样保留；v1/v2/2.4.10失败历史未抹去。

生产配置仍k5/M2/dense0.8/sparse0.3/nprobe10/BM25 disabled，production_quality_claim=false、Production tuning NO。requirements/真实config.ini/正式Compose/固定Dataset/Legacy/模型/生成/线上入口未改；临时Compose、volumes、Manifest、probe脚本和logs均ignored不提交。

运行现场：旧三服务及新stage12-v2三服务均保留运行；没有drop/clear/delete或删除容器/卷。需停止新评估服务时，在仓库根目录执行以下命令；不会删除持久数据，重启后仅复用资源，无--provision：

```powershell
docker compose -f runtime/stage12-milvus-v2/docker-compose.yml stop
docker compose -f runtime/stage12-milvus-v2/docker-compose.yml up -d --wait
```

交付：[Paired](../evaluation_results.json)、[Direct](../evaluation_results_direct.json)、[V2机器核验](../stage12_completion_v2_verification.json)、[前次失败归档](../stage12_completion_v1_direct_failure.json)。Stage 0–12 PASS；Last Completed Stage12 PASS；Active NONE；Stage13 PENDING/readiness YES；Full Integration Readiness NO。RAGAS及真实LLM Planner NOT RUN。本任务结束后不开始Stage13。

Completion V2 Git发布记录待最终验证后补充；最终HEAD在回复核验，不预写自身哈希。
