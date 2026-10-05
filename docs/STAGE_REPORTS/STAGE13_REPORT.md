# Stage 13 — Docker + Integration Tests + README + Final Acceptance

日期：2026-10-06（Asia/Shanghai）。起始 main：`461a452610664b79cbfcfc012cb1ca8ba94a2d59`，fetch 后本地/远端一致，工作区 clean。用户授权本阶段的实际 Docker、隔离合成文件入库与在线 LLM 验收，及最终文档交付；不创建 Stage 14。

## 最终状态与范围

```text
Implementation: PASS
Infrastructure: PASS
Real Source-File Ingestion: PASS
Real Online LLM Integration: PASS
Stage 13 Acceptance: PASS
Stage 0–13: PASS
Last Completed Stage: Stage 13 — PASS
Active Stage: NONE
Full Integration Readiness: YES (controlled local Integration only)
Migration: COMPLETE
Production Quality Certification: NO
Production Scale Validation: NO
RAGAS: NOT RUN
```

GitHub 同步证据见末节，最终文档 HEAD 与 clean 在交付回复核验。以上集成仅覆盖本机隔离 synthetic 文件/问题，不是生产质量、安全或容量认证。Stage 12 的固定 25-query benchmark、历史结果与旧服务没有改动。

## 文件与实现范围

| 范围 | 改动及真实调用关系 |
| --- | --- |
| `Dockerfile` / `.dockerignore` | Python 3.10.20 slim，固定运行依赖，CPU torch wheel，UID 10001；默认 uvicorn manufacturing_app:app；排除配置/秘密、模型/训练 checkpoint、runtime/SQLite/Git 与本地输出 |
| `docker-compose.yml` / `.env.example` | 五服务、版本固定、健康依赖、持久卷、必填秘密环境；模型只读/Manifest 外置；正式切分 512/120 与 128/30，移除旧教育/MySQL 部署配置 |
| `docker-compose.acceptance.yml` | one-shot bootstrap 完成后启动 API；独立 acceptance collection/Manifest；正式 Compose 不自动灌 Demo |
| `examples/manufacturing_demo/` | NOTICE、两份 TXT 及 Stage 1 合法 YAML Sidecar；1200 rpm/250 小时明确 SYNTHETIC / NOT PRODUCTION FACTS |
| `scripts/bootstrap_manufacturing_demo.py` | 真实 VectorStore + SQLiteManifestStore + VersionedIngestion.ingest_directory，默认 Demo 仅隔离命名空间；显式 operator-supplied source 入口，不直接 upsert fixture |
| `scripts/stage13_acceptance.py` | STAGE13_LIVE=1 显式 HTTP/SSE、bootstrap/来源/缓存/健康、Redis 降级与 API/整栈重启验收；普通 pytest 不启动服务/LLM |
| `scripts/stage13_snapshot.py` / `check_image.py` | 只读实际 Manifest/Milvus/缓存核验、实际无挂载镜像扫描 |
| `tests/test_stage13_acceptance_contract.py` | 14 项离线控制/拒绝测试：伪造或过期来源、错误数字/SSE、Live gate、禁止 Demo 写正式集合 |
| README / 治理 / 当前事实文档 | 最终项目介绍、可重复启动/停止/摄取/API/测试、现状与证据索引；保留历史阶段及 Legacy 清单 |
| 本报告与两份 Stage 13 JSON | 公开安全验收记录；不包含 key/password/prompt/raw model response |

没有修改业务源码、requirements.txt、真实 config.ini/.env、Legacy 入口、模型、Stage 12 Dataset/评估结果或默认 Python 检索配置。真实 Key 仅用于本地 ignored acceptance.env，Redis/MinIO 使用本地随机密码；未提交环境、卷、DB 或日志。

## 环境、构建与实际镜像核验

| 项目 | 实际值 |
| --- | --- |
| Docker Client / Server | 29.8.0 / 29.8.0 |
| Compose | v5.5.1 |
| 容器 Python | 3.10.20 |
| torch | 2.10.0+cpu，CUDA available=false；满足原 2.10.0 锁定要求 |
| milvus-model / sentence-transformers | 0.2.5 / 3.0.1 |
| pymilvus / Milvus server | 2.5.4 / pkg/v2.5.4 |
| Redis / Etcd | 7.2.7 / v3.5.16 |
| MinIO | RELEASE.2023-03-20T20-16-18Z |
| 模型 | 本地 BGE-M3 与 bge-reranker-large CrossEncoder；真实 CPU 推理 |
| 镜像 | manufacturing-rag:stage13 |
| 验收镜像 ID | sha256:ad4993c95d4dc0b190d1c56df110b01a14b642e48fad2037dff0dc93a45bf3ca |
| 实测 image size | 2,948,264,154 bytes，约 2.75 GiB；事实记录，无 size SLA |
| Project / HTTP | stage13-acceptance / http://127.0.0.1:18080 |

已实际执行 build，不将文本/编译检查当作镜像成功。第一轮发现历史 BERT checkpoint 进入 build context，停止本任务 build，补齐忽略规则，原文件保留；CPU 安装尝试遇到 CPU wheel index 缺依赖构建包，改为先 `torch==2.10.0+cpu --no-deps`，再由常规索引安装未变的完整 requirements，最终 build exit 0。没有下载替代模型。最后缓存构建显示 23.21 kB 增量 context transfer，不能称作完整项目 context 大小。

实际无 volume/env 挂载的 `stage13-image-check` 容器运行 `python -m scripts.check_image`：UID 10001、非 root、runtime/logs 可写；没有 .env/config.ini、SQLite、Git、BGE 模型目录及权重。另通过 `docker cp stage13-image-check:/app/. runtime/stage13/image-audit-app` 扫描实际镜像的 129 个文件和实际 image Config，匹配本地 API key/Redis password/MinIO password bytes：0 个文件命中，Config 无秘密。仅输出统计，未输出秘密。实际 API Mount 检查模型 read_only=true、runtime/logs 为外置 bind。

基础镜像依赖包含完整历史运行库，size 较大，不为减小 size 删除固定依赖。Docker 构建隔离依据 [Docker build context](https://docs.docker.com/build/concepts/context/)；依赖启动采用 [Compose healthy/completed 条件](https://docs.docker.com/compose/how-tos/startup-order/)，本机渲染与执行均通过。

## 真正的文件摄取与幂等

实际主链：TXT → 既有 TextLoader → Stage 1 Sidecar → 原 Chinese Splitter → Stage 2 SHA256 Parent/Child → Stage 4 → 真实 BGE-M3 Dense/Sparse → Milvus → Manifest。没有 Stage 12 fixture rows 的直接 Provision，也没有 bypass Metadata Loader。

集合 `manufacturing_rag_acceptance_v1`；容器 Manifest `/app/runtime/acceptance_manifest.sqlite3`，主机 `runtime/stage13/acceptance/acceptance_manifest.sqlite3`，与正式 Manifest 隔离。

| Document | 第一次 | 第二次 | Revision | Child 数 |
| --- | --- | --- | ---: | ---: |
| SYN-DEMO-PARAMETER-001 / 1.0 | INGEST | SKIP_UNCHANGED | 1 → 1 | 1 |
| SYN-DEMO-MAINTENANCE-001 / 1.0 | INGEST | SKIP_UNCHANGED | 1 → 1 | 1 |

实际 Milvus 2 Child 与 Manifest 完全一致；两次文件快照、Child IDs 和 fingerprint 保持。参数 Child `aa58ae86768b5d1ca0ab197309626d44dead263a60f551d800a27d4f8c81adb6`；维护 Child `482a63f88bdcefa4b35ad726c39bef37095c785d73ca29ba950e3b5bcf44d1e3`。

Manifest fingerprint `85b2964b451b2f8a47dad53c5c3a3ba9a00dd98e9337e168d7ed38de56f6063c`；online knowledge revision `372de4b69ecb35655f268bc29ee12228451d721d6f3974c4de0d56e445602ed4`。第一次结果单独保存 bootstrap_first.json，避免二次 SKIP 或重启覆盖原证据。完整安全副本见 [在线记录](../stage13_acceptance_results.json)。

## 真实 LLM、JSON、SSE 与缓存

原本地配置模型 qwen3.8-max 的真实 JSON 预检返回 403 PermissionDeniedError。依用户允许的环境选择范围，仅在 ignored acceptance 环境选择 **qwen-plus / DashScope OpenAI-compatible**，严格 JSON 预检 PASS。原 config.ini/.env 保留；没有放松 Stage 10 Pydantic、Citation、Identifier 或 Numeric Guard。此模型支持 JSON mode 的外部说明见 [官方文档](https://help.aliyun.com/zh/model-studio/qwen-structured-output)，实际通过依据本次运行结果。

实际在线运行原 Stage 5/9/10 runtime/shared completion，非 fake runtime/TestClient。参数问题 `设备型号 SYN-DEMO-100 的主轴额定转速是多少？` HTTP 200/status=answered，claim 为 `设备型号 SYN-DEMO-100 的主轴额定转速为 1200 rpm。`，used ID E1，来源 SYN-DEMO-PARAMETER-001/1.0，真实 source `/app/examples/manufacturing_demo/parameter.txt` 和 Parent `fbfe0f8fc556b1a503dd617e6d23cfda482745b627e71d4d5c108363078994f0`。本地 Stage 10 numeric/identifier/citation 校验通过，才进入 renderer 与 cache。

同一 JSON 请求 cache_hit false → true，answer_text、claims、citations、used_evidence_ids 完全一致。真实 Redis key 是 namespace + 64 位 SHA256，不含 raw query，核验时 TTL=299 秒，有限且不超过 300。

另一个未缓存维护问题实际 SSE 序列 `start, analysis, retrieval, generation, answer, citations, done`；generation status=validated，250 小时的答案引用 SYN-DEMO-MAINTENANCE-001/1.0，source `/app/examples/manufacturing_demo/maintenance.txt`，Parent `b8b555364bde6bfbd9c590c8e9a6102bbf7c0d219b6577f5496a0af3c984025b`。done=1/error=0/cache_hit=false，未将参数文档误作维护引用，没有发送 raw LLM token。公开 JSON 只保存 validated 结果，不保存 Prompt/raw completion。

Redis 受控 stop 后另一个未缓存参数问题 HTTP 200/answered，cache_hit=false，ready.cache=degraded；finally 恢复 Redis，不删除卷。随后 API restart 和整栈 stop/start，ready=200，Manifest/Child IDs/知识修订保持，再查参数 HTTP 200/answered。实际 restart 结果及安全来源均在在线 JSON。

## 故障响应与真实限制

无效请求返回 HTTP 422 `{"code":"INVALID_REQUEST"}`，不回显输入。另将验收 API 环境暂时改为 LLM timeout=0.001 秒，真实 SDK 超时后的响应为 HTTP 500，仅 `code=GENERATION_ERROR` 和 request_id，未暴露 host/password/stack/Prompt/raw output；核验后恢复 timeout=30 秒并重新 ready。该抽测满足真实失败路径安全码验证，没有修改业务代码。

还尝试了 Milvus 停机抽测：未缓存请求在 HTTP 150 秒 deadline 前未拿到预期固定错误，客户端 TimeoutError，故该**附加 outage probe 为 FAIL**，不能标作 RETRIEVAL_ERROR PASS。finally 已恢复 Milvus/健康状态，保留卷与 Manifest。本次正常集成和 LLM 失败安全路径全部通过，但不宣称 Milvus 停机具有 bounded end-to-end response；底层工作可能超过客户端等待，生产依赖故障 deadline/资源回收仍未验证。readiness 主要是初始化状态，不实时证明全部依赖健康。

## 实际命令与结果

以下 `$stage13Compose` 是本次实际使用的安全参数数组，不渲染秘密：

```powershell
$stage13Compose = @('compose', '--env-file', 'runtime/stage13/acceptance.env', '-p', 'stage13-acceptance', '-f', 'docker-compose.yml', '-f', 'docker-compose.acceptance.yml')
docker compose --env-file runtime/stage13/acceptance.env config --quiet
& docker @stage13Compose config --quiet
& docker @stage13Compose build manufacturing-api
& docker @stage13Compose up -d --wait --wait-timeout 180 etcd minio milvus redis
& docker @stage13Compose up --no-deps manufacturing-bootstrap
Copy-Item runtime/stage13/acceptance/bootstrap.json runtime/stage13/acceptance/bootstrap_first.json
& docker @stage13Compose run --no-deps --name stage13-acceptance-bootstrap-second manufacturing-bootstrap python -m scripts.bootstrap_manufacturing_demo --output /app/runtime/bootstrap_second.json
& docker @stage13Compose up -d --no-deps --wait --wait-timeout 240 manufacturing-api
docker run --name stage13-image-check --entrypoint python manufacturing-rag:stage13 -m scripts.check_image
$env:STAGE13_LIVE = '1'
& .venv/stage1-validation/Scripts/python.exe -m scripts.stage13_acceptance --lifecycle
```

| Command / check | 实际 result | Status |
| --- | --- | --- |
| 正式/overlay config --quiet | 渲染合法，未打印解析后密钥 | PASS |
| build manufacturing-api | 完整运行依赖安装、制造业镜像构建 exit 0 | PASS |
| infra up --wait / compose ps -a | Redis/Etcd/MinIO/Milvus 全部 healthy | PASS |
| first / second bootstrap（上文） | 2 INGEST → 2 SKIP；各 revision 1；相同 Child IDs | PASS |
| 无挂载 image check / 实际文件秘密 bytes scan | UID 10001 / 129 files / 0 secret matches | PASS |
| STAGE13_LIVE=1 acceptance --lifecycle | 13 checks：真实 health/快照/摄取/JSON/cache/SSE/safe error/Redis降级/API与整栈restart/query；exit 0 | PASS |
| LLM 短 timeout 环境 / HTTP query / 恢复 30 秒 | 实际 GENERATION_ERROR 500、安全字段限定、恢复 ready | PASS |
| Milvus stop / HTTP query / finally start --wait | 客户端 150 秒 TimeoutError；服务恢复，未删卷 | FAIL（附加 outage deadline 检查） |
| `.venv/stage1-validation/Scripts/python.exe -m pytest tests/test_stage13_acceptance_contract.py -q -rs --tb=short` | 14 passed | PASS（offline control） |
| `.venv/stage1-validation/Scripts/python.exe -m pytest tests -q -rs --tb=short` | 1026 passed / 0 failed / 13 skipped，5.24 秒 | PASS（offline regression） |
| 最终文档链接/保护范围/秘密检查；git diff --check | 231 个相对链接、6 Python AST、29 个合法任务文件、秘密 bytes 扫描、保护范围、恢复后 ready/query 均通过 | PASS |

13 skips 分别为轻量环境缺完整依赖的 11 项 Smoke/Legacy 检查及未启用 Stage 3/12 Live 的 2 项；没有将这些 skips 标为集成成功。真实 Stage 13 在 Python 3.10.20 容器、完整运行依赖与已有权重上单独执行。RAGAS judge/生产规模/生产安全认证均 NOT RUN；真实企业知识库效果需 approved dataset。

## 保留边界与停止方式

无 distributed ingestion transaction、多 worker ingestion 或 online read/write 原子快照保证；session_id 不是 conversation memory。数字/标识符 Guard 不证明语义蕴含/操作安全；缓存信任合法 writer 和受保护 Redis，没有恶意管理员防护认证。Stage 12 是 controlled synthetic/scripted workload，无生产准确率/时延结论。本次没有重跑 RAGAS/Stage 12，也没有生产调参。

旧 2.4.10、Stage 12 V2 服务/集合/输出及历史报告全部保留。新验收基础设施保留运行于 127.0.0.1:18080；需要停止/重启使用上方同一参数数组：

```powershell
& docker @stage13Compose stop
& docker @stage13Compose start
```

不要 down -v，不删除模型、Manifest 或任何用户数据。最终 README 提供初次验收、正式 approved-data 摄取和 API 例子，不隐式启动 Legacy。所有后续工作需要用户另行定义范围。

## Git 交付

部署/摄取/验收提交 `a3e8d764ac9e9407c9d416436601ace9e643a43e`：`feat: finalize manufacturing docker deployment`。实际 Push 到 origin/main 成功，fetch 后 Local HEAD == origin/main == 此 SHA；当时尚有本任务待发布文档，不声称中途 tree clean。

最终文档以独立 `docs: finalize manufacturing rag project` 提交发布。所有文件须按 AGENTS.md 限定暂存、Push、fetch/HEAD 核对与 clean；最终 SHA 在交付回复中提供，不预写当前提交自身哈希。GitHub Sync PASS 以最终远端核对为准。当前停止，不创建 Stage 14。

证据：[在线验收结果](../stage13_acceptance_results.json)、[环境/镜像/安全核验](../stage13_integration_verification.json)、[当前架构](../CURRENT_ARCHITECTURE.md)、[README](../../README.md)。
