"""Read-only inspection inside the explicitly isolated acceptance container."""
from contextlib import closing
import importlib.metadata
import json
from pathlib import Path
import sqlite3


def inspect_snapshot():
    from base.config import config
    from pymilvus import MilvusClient
    from rag_qa.api.runtime import KnowledgeRevisionProvider
    from rag_qa.ingestion.manifest_store import manifest_snapshot_fingerprint
    name = config.MILVUS_MANUFACTURING_COLLECTION_NAME
    if not name.startswith('manufacturing_rag_acceptance_'):
        raise ValueError('acceptance collection required')
    path = Path(config.MANUFACTURING_MANIFEST_DB_PATH).resolve(strict=True)
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
        db.row_factory = sqlite3.Row
        records = [dict(row) for row in db.execute('SELECT document_id,active_document_version,revision,child_ids,source_file FROM active_documents ORDER BY document_id')]
        fingerprint = manifest_snapshot_fingerprint(db,name)
    client = MilvusClient(uri=f'http://{config.MILVUS_HOST}:{config.MILVUS_PORT}',db_name=config.MILVUS_DATABASE_NAME,timeout=20)
    try:
        rows = sorted(client.query(name,filter='',output_fields=['id','child_id','parent_id','document_id','document_version','source_file','equipment_model'],limit=16384,consistency_level='Strong'),key=lambda row:row['id'])
        expected = {cid for record in records for cid in json.loads(record['child_ids'])}
        if expected != {row['id'] for row in rows}:
            raise ValueError('actual child snapshot mismatch')
        return dict(status='PASS',collection=name,server_version=client.get_server_version(),
            client_version=importlib.metadata.version('pymilvus'),manifest=str(path),
            manifest_fingerprint=fingerprint,knowledge_revision=KnowledgeRevisionProvider(path,name)(),
            documents=records,child_count=len(rows),children=rows,
            model_weights_mounted={name:(Path(config.MODELS_DIR)/name/'pytorch_model.bin').is_file()
                                  for name in ('bge-m3','bge-reranker-large')})
    finally:
        client.close()


def inspect_cache():
    from base.config import config
    import redis
    client=redis.Redis(host=config.REDIS_HOST,port=config.REDIS_PORT,password=config.REDIS_PASSWORD,
        db=config.REDIS_DB,decode_responses=True,socket_timeout=5,socket_connect_timeout=5)
    try:
        keys=list(client.scan_iter(match='manufacturing:answer:v1:*'))
        return dict(status='PASS',redis_version=client.info('server')['redis_version'],
            keys=[dict(key=key,ttl=client.ttl(key)) for key in sorted(keys)])
    finally:
        client.close()


if __name__=='__main__':
    import sys
    try:
        report=inspect_cache() if '--cache' in sys.argv else inspect_snapshot()
    except Exception as exc:
        report=dict(status='FAIL',error_code='ACCEPTANCE_INSPECTION_FAILED',exception_type=type(exc).__name__)
    print(json.dumps(report,ensure_ascii=False))
    sys.exit(0 if report['status']=='PASS' else 1)
