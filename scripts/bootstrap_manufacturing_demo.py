"""Explicit synthetic bootstrap through real Stage 1–4 ingestion, never fixture rows."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys


def run_ingestion(directory, *, demo=False):
    from base.config import config
    if demo and not config.MILVUS_MANUFACTURING_COLLECTION_NAME.startswith(('manufacturing_rag_acceptance_', 'manufacturing_rag_demo_')):
        raise ValueError('isolated demo/acceptance collection required')
    from rag_qa.core.vector_store import VectorStore
    from rag_qa.ingestion.manifest_store import SQLiteManifestStore
    from rag_qa.ingestion.versioned_ingestion import VersionedIngestion
    vector = VectorStore(schema_mode='manufacturing')
    try:
        with SQLiteManifestStore(config.MANUFACTURING_MANIFEST_DB_PATH) as manifest:
            results = VersionedIngestion(manifest, vector).ingest_directory(directory)
            records = [manifest.get(result.document_id) for result in results]
            return dict(status='PASS', dataset_type='controlled_synthetic' if demo else 'operator_supplied',
                collection=vector.collection_name, manifest=config.MANUFACTURING_MANIFEST_DB_PATH,
                server_version=vector.client.get_server_version(), results=[asdict(result) for result in results],
                snapshot_fingerprint=manifest.snapshot_fingerprint(vector.collection_name),
                documents=[dict(document_id=r.document_id, document_version=r.active_document_version,
                    revision=r.revision, child_ids=list(r.child_ids), source_file=r.source_file) for r in records])
    finally:
        vector.client.close()


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir',default=str(Path(__file__).resolve().parents[1]/'examples/manufacturing_demo'))
    parser.add_argument('--real-data',action='store_true',help='explicit operator-supplied sources; never label bundled demo as real data')
    parser.add_argument('--output',default='runtime/bootstrap.json')
    args=parser.parse_args(argv)
    try:
        source=Path(args.source_dir).resolve(strict=True)
        demo_root=(Path(__file__).resolve().parents[1]/'examples/manufacturing_demo').resolve()
        if (args.real_data and source==demo_root) or (not args.real_data and source!=demo_root):
            raise ValueError('explicit demo/real source boundary required')
        report=run_ingestion(source,demo=not args.real_data)
        if not report['results']:
            raise ValueError('no source documents')
    except Exception as exc:
        report=dict(status='FAIL',error_code='INGESTION_FAILED',exception_type=type(exc).__name__)
    output=Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],output=str(output)),ensure_ascii=False))
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__':
    sys.exit(main())
