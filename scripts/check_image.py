"""Run inside the built image WITHOUT model/runtime/secret mounts."""
import json
import os
from pathlib import Path


def main():
    root=Path('/app')
    assert os.getuid()!=0
    assert not (root/'.git').exists()
    assert not (root/'config.ini').exists()
    assert not list(root.rglob('.env*'))
    assert not list(root.rglob('*.sqlite*'))
    for pattern in ('*.safetensors','*.pt','*.pth','pytorch_model.bin'):
        assert not list(root.rglob(pattern))
    for name in ('bge-m3','bge-reranker-large'):
        assert not (root/'rag_qa/models'/name).exists()
    for path in (root/'runtime',root/'logs'):
        assert os.access(path,os.W_OK)
    assert (root/'examples/manufacturing_demo/parameter.txt.yaml').is_file()
    assert (root/'manufacturing_app.py').is_file()
    print(json.dumps(dict(status='PASS',uid=os.getuid(),non_root=True,
        model_weights_baked=False,secret_files_baked=False,git_baked=False,
        runtime_sqlite_baked=False,runtime_logs_writable=True)))


if __name__=='__main__':
    main()
