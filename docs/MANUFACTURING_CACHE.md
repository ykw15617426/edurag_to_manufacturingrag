# Manufacturing Answer Cache Governance（Stage 11）

`rag_qa/api/cache.py:ManufacturingAnswerCache`使用独立namespace，不复用旧RedisClient或answer:{query}。Redis只优化经过Stage 10 guard的answered GroundedAnswerResult；raw LLM JSON/token、错误、insufficient不缓存，无Negative Cache。服务也重新验证注入runtime结果的结构/claim-citation links与确切渲染后才返回，不能假装fake generator输出都是validated。

## Key 与 TTL

`manufacturing:answer:v1:<sha256>`；SHA256来自canonical JSON(sort_keys/紧凑分隔/UTF8/无NaN)，包含cache_contract_version、generation_contract_version、knowledge_revision、normalized query、QueryAnalysis.to_metadata、LLM_MODEL、RETRIEVAL_K、CANDIDATE_M。query只NFC+outer/whitespace合并，不改大小写/-/_/前导零。session不参与，不存在对话语义；key不暴露raw query。只对query规范化，analysis保持Stage 5原结果，等价query可能因分析描述不同得到不同key，保守miss。

所有SET明确EX positive integer TTL，fallback300秒仅bound lifetime，不是调优。旧版本key无需FLUSHDB/主动删除，自然过期；不提交query/缓存/密钥到Git。Redis值含最终已验证答案与来源，本阶段未新增数据加密或多租户隔离要求。

## Knowledge Revision

Stage 4 SQLiteManifestStore只加read-only snapshot_fingerprint；原commit_snapshot/delete/CAS/摄取语义不变。一次SELECT active documents按document_id ASC，验证ManifestRecord、revision/child_count，canonical序列化所有现有事实与revision（包括document_id/active version/三个hash/processing/collection/schema/child_ids/source），排除updated_at后SHA256。revision保留，timestamp-only差异不制造修订。

Online KnowledgeRevisionProvider每次off-loop使用新mode=ro SQLite连接并关闭，要求已初始化manifest_v1且collection绑定一致；不创建/采用/修复空DB，不复用跨线程的Stage 4 writer连接。最终revision=SHA256(canonical JSON(manifest fingerprint, configured collection, loaded approved snapshot bytes SHA256或None))。文档版本/hash/Metadata/processing/Child集合/新增删除改变namespace；FastPath bytes变化在runtime重建时连同corpus一起切换namespace。无配置snapshot也正常工作。

Stage 4仍单worker/单writer，Manifest提交是成功摄取检查点，不是Milvus事务锁。本阶段不解决摄取进行中Manifest与数据面暂时不一致、跨服务副本revision原子协调或正在执行查询的快照隔离，不能声称生产并发一致性完全验证。

## 校验与失败

get miss或Redis异常直接走完整Stage 5–10；只有固定状态cache=degraded，不传播host/password。命中JSON做重复key/大小保护、GroundedAnswerResult extra/字段/UTF校验，强制answered、有claims/citations、唯一且合法ID、每claim links集合等于used/citations、Parent SHA、knowledge_type、无内联citation/list markup，以及按Stage 10规则重建渲染与answer_text逐字一致。非法值尝试DELETE该key再miss，删除失败仍miss。

写入只接受typed answered，重新结构验证，SET ex=TTL。网络/timeout失败继续返回本次validated答案；不因此发原始模型内容。**缓存没有原Evidence正文，不重新证明事实grounding**；信任边界是本应用Stage 10的合法writer和受保护Redis。结构合法的恶意Redis篡改不能由这些检查证明语义可信，本阶段不宣称实现签名认证或对恶意缓存管理员防护。

可观察disconnect时不写缓存；已提交的同步Redis命令和随后断连有竞态，无法撤回。JSON与SSE使用同一Service/Cache，无协议切换导致的双生成。Manifest V1答案留在旧key，V2同query用新key并再次执行pipeline，旧值依TTL回收。

参数/启动与错误协议见[API合约](MANUFACTURING_API.md)，command/result见[Stage 11报告](STAGE_REPORTS/STAGE11_REPORT.md)。真实Redis/Milvus/API端到端NOT RUN；Stage 12–13 PENDING。
