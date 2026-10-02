# EduRAG → 制造业设备智能运维 RAG

本仓库正在从教育问答迁移到制造业内部设备运维知识问答。Stage 0 基线与治理已完成；Stage 1 已实现制造业 Metadata 校验与显式处理模式，已完成发布验证。现有在线运行链路仍使用教育领域数据、分类和提示词；Stage 3 已实现显式制造业 Milvus Schema 与写入映射；真实服务验证尚未完成。Stage 4 已实现版本 Manifest、跨运行 Skip、增量摄取与显式/差集删除控制；真实服务验证尚未完成。Stage 5 已提供独立制造业 QueryAnalysis、规则实体与可注入 JSON 语义分类边界；真实 LLM 和在线接入未验证。Stage 6 已实现安全 Metadata Filter、保留硬标识符的软条件放宽和制造业 Child Hybrid Retrieval；真实 Milvus/模型和在线接入未验证。Stage 7 已实现按 parent_id 保留 Metadata/命中统计、父块 CrossEncoder 重排与配置 Top-M；真实重排模型未执行。Stage 8 已提供已批准制造业语料的Exact Alarm/FAQ与raw BM25证据快路径，默认BM25不短路，拒绝/错误回退Stage 7；真实服务和线上接入未验证。Stage 9 已实现严格DIRECT/REWRITE/SUBQUERY、意图限定快路径、标识符保护、多查询Child融合与原query一次Parent重排；未接入在线生成。SSE 和检索评估尚未实现。

## 审计文档

- [当前真实架构](docs/CURRENT_ARCHITECTURE.md)
- [制造业迁移阶段计划与术语基线](docs/MANUFACTURING_MIGRATION_PLAN.md)
- [Stage 0 检查、问题和测试结果](docs/STAGE_REPORTS/STAGE0_REPORT.md)
- [教育遗留逐文件、逐行清单](docs/EDURAG_LEGACY_INVENTORY.md)

## 项目治理与文档入口

- [仓库维护约定](AGENTS.md)
- [项目工作区说明](.agent/README.md)与[维护计划](.agent/PLANS.md)
- [正式文档索引](docs/README.md)与[治理设置报告](docs/STAGE_REPORTS/REPOSITORY_GOVERNANCE_SETUP_REPORT.md)

Stage 0 提交 `b6db2e8d70f6c701975e24cefd10a04514139d2e` 已推送并核对远端；历史技术验证仍为 PARTIAL。Stage 1: PASS；[Metadata 合约与调用方式](docs/MANUFACTURING_METADATA_SCHEMA.md)，[Stage 1 报告](docs/STAGE_REPORTS/STAGE1_REPORT.md)。Stage 2: PASS；[指纹与稳定身份](docs/MANUFACTURING_FINGERPRINTS.md)、[Stage 2 报告](docs/STAGE_REPORTS/STAGE2_REPORT.md)。Stage 3: PASS；[制造业存储合约](docs/MANUFACTURING_MILVUS_SCHEMA.md)、[Stage 3 报告](docs/STAGE_REPORTS/STAGE3_REPORT.md)。Stage 4: PASS；[版本摄取合约](docs/MANUFACTURING_VERSIONED_INGESTION.md)、[Stage 4 报告](docs/STAGE_REPORTS/STAGE4_REPORT.md)。Stage 5: PASS；[查询分析合约](docs/MANUFACTURING_QUERY_ANALYSIS.md)、[Stage 5 报告](docs/STAGE_REPORTS/STAGE5_REPORT.md)。Stage 6: PASS；[制造业检索合约](docs/MANUFACTURING_RETRIEVAL.md)、[Stage 6 报告](docs/STAGE_REPORTS/STAGE6_REPORT.md)。Stage 7: PASS；[Parent 检索合约](docs/MANUFACTURING_PARENT_RETRIEVAL.md)、[Stage 7 报告](docs/STAGE_REPORTS/STAGE7_REPORT.md)。Stage 8: PASS；[快路径合约](docs/MANUFACTURING_FAST_PATH.md)、[Stage 8 报告](docs/STAGE_REPORTS/STAGE8_REPORT.md)。Stage 9: PASS；[检索策略合约](docs/MANUFACTURING_RETRIEVAL_STRATEGY.md)、[Stage 9 报告](docs/STAGE_REPORTS/STAGE9_REPORT.md)。Stage 10–13 保持 PENDING，Full Integration Readiness: NO。

## 运行前提

从仓库根目录执行命令。现有 `requirements.txt` 是原项目完整依赖列表，本次未重新锁定依赖或验证全量安装。Dockerfile 使用 Python 3.10.20；Stage 0 检查环境为 Python 3.13.9，二者不能视为同一验证环境。

```powershell
python -m pip install -r requirements.txt
Copy-Item config.example.ini config.ini
```

编辑本地 `config.ini` 的数据库、服务地址、模型与密钥；也可设置同名环境变量。优先级为 **进程环境变量 > config.ini > 代码 fallback**。`base/config.py` 不会自动加载 `.env`；Docker Compose 会用 `.env` 做变量替换，和直接运行 Python 有区别。复制示例只是配置起点，不会准备依赖服务。

需要自行准备：

- MySQL 数据库和 `jpkb` 教育问答表。`MySQLClient.create_table/insert_data` 是手工初始化方法，CSV 入库不是幂等操作。
- Redis 和 Milvus；Milvus 数据库需预先存在，VectorStore 才会创建/加载集合。
- 本地 `rag_qa/models/` 下的 `bge-m3`、`bge-reranker-large`、`bert-base-chinese` 和经过训练的 `bert_query_classifier`。本机存在这些目录，但 Stage 0 未验证权重完整性/推理。
- 可用的 DashScope 配置。示例中密钥为空，须自行填写；模型名沿用原项目，未验证在线可用性。

```powershell
python app.py
```

服务入口固定为 `http://localhost:8080`，浏览器访问根路径。按 `Ctrl+C` 停止。模块导入会立即初始化模型和客户端并尝试创建会话表，不是无副作用的 import。`/health` 仅返回固定 healthy，不代表依赖就绪。

纯 RAG 入库入口（会写 Milvus，Stage 0 未实际执行）：

```powershell
python -m rag_qa.rag_main --data-processing --data-dir ./rag_qa/data
```

参数须指向包含 `ai_data/java_data/...` 的上级目录。历史默认 `./data/ai_data` 与内部拼接逻辑不匹配，暂留审计 TODO，故使用显式路径。旧命令行问答入口为 `python old_main.py`、`python -m mysql_qa.sql_main`；在线应用使用 `new_main.py`。

`docker-compose.yml` 只定义应用容器。它不会启动 MySQL、Redis、Milvus、etcd、MinIO，也没有随 Git 发布模型权重。不要把 `docker compose up --build` 理解为完整可运行的部署方案。

## Stage 0 Smoke Tests

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest tests/test_stage0_smoke.py -q -rs
```

缺失依赖会逐项显示 SKIPPED；不使用假模型/假数据库冒充集成通过。Document Processor 是函数模块，初始化检查覆盖真实 splitter、TXT loader 和分块流程。FastAPI app 的真实导入会访问外部资源，完整环境准备后才执行：

```powershell
$env:STAGE0_LIVE_SMOKE = '1'
python -m pytest tests/test_stage0_smoke.py -q -rs
Remove-Item Env:STAGE0_LIVE_SMOKE
```

即使设置该开关，缺依赖仍会 SKIPPED；已具备依赖时的运行错误会 FAIL。测试不调用付费生成 API，不跑教育分类训练，不刷新生产知识库。现有数据、demo 和 RAGAS 结果均保留为历史基线。
