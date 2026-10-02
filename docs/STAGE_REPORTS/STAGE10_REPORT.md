# Stage 10 — Answer Generation + Citations + Evidence Guard

日期：2026-10-02。branch：main；起始HEAD：`90bff8baffceefa83f270d52f075efd4ad3ae778`，fetch后Local HEAD == origin/main，初始Working Tree clean。Implementation/核心Validation已完成；GitHub Sync PENDING，发布后更新。最终SHA在回复核验提供，不预写本提交自身SHA。

## 实现与文件范围

新增`rag_qa/generation/{__init__,schemas,evidence,prompts,generator}.py`，统一消费Stage 9 Parent/FastPath documents及Stage 8 evidence，建立EvidenceRecord完整性/版本/hard guard、JSON DATA Prompt、可注入completion、严格结构化答案、逐claim citation/identifier/numeric guard与来源Renderer。不创建第二套Retrieval，未修改Legacy prompts/new_rag_system/在线入口。

新增`tests/test_manufacturing_evidence.py`、`tests/test_manufacturing_generation.py`。新增[生成合约](../MANUFACTURING_GENERATION.md)和本报告；最小同步AGENTS/PLANS、README/docs索引、当前架构与迁移计划。历史Stage报告保留。

实际链路：Evidence normalization →冲突/版本/hard guards →空Evidence直接insufficient不调LLM →static instruction+JSON data →completion →strict JSON/Pydantic →逐Claim合法ID与文本token支持 →渲染Claim引用及实际来源。FastPath批准证据也调用completion，不直接原文当答案。错误继承GenerationError并继续抛出，不伪装证据不足。

## Commands / Results

python指仓库ignored `.venv/stage1-validation/Scripts/python.exe`（Python3.13.9 / pytest8.4.2）。未安装新依赖、下载模型或连接数据库。

| Command | Result | Status |
| --- | --- | --- |
| `git status --short`; `git branch --show-current`; `git log -5 --oneline`; `git fetch origin`; 两个`git rev-parse` | 初始clean/main，HEAD与origin/main符合指定基线 | PASS |
| `python -m pytest tests/test_manufacturing_evidence.py tests/test_manufacturing_generation.py -q -rs --tb=short`（初次修正后及扩展后；最终亦包含在完整回归中） | 扩展后独立123 passed；最终完整回归中核心124项通过 | PASS |
| Stage 0–10完整回归（下方命令） | 813 passed / 0 failed / 12 skipped | PASS |
| Python AST / 相对文档链接 / `git diff --check` / Diff及保护范围审阅 | 7文件AST、124相对链接目标、补丁及受保护源码范围通过 | PASS |
| Real LLM/API、CrossEncoder/BGE、Live Milvus、online端到端 | 未执行；不是完整集成PASS | NOT RUN |
| Commit / Push / Fetch / equal / clean | 待发布 | PENDING |

```powershell
.venv/stage1-validation/Scripts/python.exe -m pytest tests/test_manufacturing_evidence.py tests/test_manufacturing_generation.py tests/test_manufacturing_query_rewrite.py tests/test_manufacturing_strategy.py tests/test_manufacturing_bm25.py tests/test_manufacturing_fast_path.py tests/test_parent_aggregation.py tests/test_manufacturing_parent_retrieval.py tests/test_manufacturing_metadata_filters.py tests/test_manufacturing_retrieval.py tests/test_manufacturing_query_analysis.py tests/test_manifest_store.py tests/test_versioned_ingestion.py tests/test_manufacturing_milvus_schema.py tests/test_manufacturing_fingerprints.py tests/test_manufacturing_metadata.py tests/test_stage0_smoke.py -q -rs --tb=short
```

首轮107 passed / 1 failed：中文相邻全角数字未被旧numeric lookbehind捕获；修正为排除ASCII标识字符/数字边界后108项通过，再增补格式/资源/导入边界123项通过。非最终完整回归曾812 passed / 12 skipped，新增Metadata日期支持后最终813 passed / 0 failed / 12 skipped，以上表为准，不把失败运行记PASS。12个SKIPPED为既有缺依赖与未启用Live测试，不等于集成PASS。

测试覆盖实际Stage 7 Document/Stage 8 FastPath正常化；E1/E2稳定顺序/一致去重/输入保留；同parent事实冲突、同doc多版本、bad UTF8/缺字段/SHA/日期/score/容量、hard mismatch和None；六意图空Evidence零模型调用；valid answered/insufficient、空Claim/无引用/未知Citation/坏JSON/重复键/Schema；未引用Evidence不能支持Claim，型号/报警/备件号和前导零变形/新数字/符号精度/Unicode数字；FastPath进入同一生成链；实际Metadata来源、不伪造page或confidence；transport fail closed和秘密不暴露；Prompt Injection只放JSON DATA，资源上限不截断，独立进程阻断SDK/model导入。

## 保护与真实限制

Stage 2 IDs/Stage 3 Schema/Stage 4 Manifest/Stage 5 QueryAnalysis/Stage 6 Filter/Stage 7 Aggregation/Reranker/Stage 8 BM25 policy/Stage 9 Strategy/Fusion均未修改；Legacy generation、app/new_main、模型Context/权重/切分/配置/依赖/旧数据未改。未提交.env/config.ini/凭据/模型/日志。

Completion由调用方实现API/finite timeout，核心不强耦合SDK也不终止永久阻塞callable。ASCII检查保守，可能拒绝新的英文普通词；数字格式不推理单位等价。系统仅检查引用/结构/显式token证据，不证明维修语义/完整蕴含/实际LLM安全性；无数字/ASCII的新中文步骤、中文数词与事实正确性需Stage 12评估。未声称模型免疫Prompt Injection。

Stage 11–13 PENDING；Full Integration Readiness: NO。Stage 10发布完成后停止，不实现FastAPI/SSE/Redis TTL/session/tuning/Docker最终集成。
