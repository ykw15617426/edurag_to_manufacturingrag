"""Explicit real Docker/HTTP/SSE acceptance. Never used by default pytest."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

PARAMETER_QUERY='设备型号 SYN-DEMO-100 的主轴额定转速是多少？'
MAINTENANCE_QUERY='设备型号 SYN-DEMO-100 的模拟维护周期是多少？'


class AcceptanceFailure(RuntimeError):
    pass


def require(condition,code):
    if not condition:
        raise AcceptanceFailure(code)


def parse_sse(text):
    events=[]
    for block in text.replace('\r\n','\n').split('\n\n'):
        if not block.strip():
            continue
        name=None
        data=[]
        for line in block.splitlines():
            if line.startswith('event:'):
                name=line[6:].strip()
            elif line.startswith('data:'):
                data.append(line[5:].lstrip())
        require(name is not None and bool(data),'INVALID_SSE_FRAME')
        events.append((name,json.loads('\n'.join(data))))
    return events


def validate_citations(citations,used_ids,snapshot,document_id):
    require(bool(citations) and bool(used_ids),'MISSING_CITATIONS')
    require(set(used_ids)=={c['evidence_id'] for c in citations},'CITATION_IDS_MISMATCH')
    rows=snapshot['children']
    for citation in citations:
        require(citation['document_id']==document_id,'WRONG_DOCUMENT_CITATION')
        require(any(all(row[field]==citation[field] for field in
            ('document_id','document_version','parent_id','source_file')) for row in rows),'CITATION_NOT_IN_ACTUAL_SNAPSHOT')


def validate_answer(answer,snapshot,document_id,number):
    require(answer.get('status')=='answered','ANSWER_NOT_ANSWERED')
    require(bool(answer.get('answer_text')) and bool(answer.get('claims')),'EMPTY_ANSWER')
    require(number in ' '.join(c['text'] for c in answer['claims']),'EXPECTED_NUMERIC_FACT_MISSING')
    validate_citations(answer['citations'],answer['used_evidence_ids'],snapshot,document_id)
    require({eid for claim in answer['claims'] for eid in claim['evidence_ids']}==set(answer['used_evidence_ids']),'CLAIM_CITATIONS_MISMATCH')


def validate_stream(events,snapshot):
    names=[name for name,_ in events]
    require(names and names[0]=='start' and names[-1]=='done','INVALID_SSE_ORDER')
    require(names.count('done')==1 and names.count('error')==0,'INVALID_SSE_TERMINAL')
    require([name for name in names if name!='answer']==['start','analysis','retrieval','generation','citations','done'],'INVALID_SSE_SEQUENCE')
    require(next(data for name,data in events if name=='generation')=={'status':'validated'},'UNVALIDATED_SSE_ANSWER')
    answer=''.join(data['text'] for name,data in events if name=='answer')
    done=events[-1][1]
    require(done['status']=='answered' and done['cache_hit'] is False,'SSE_NOT_REAL_CACHE_MISS')
    require('250' in answer,'MAINTENANCE_FACT_MISSING')
    citations=next(data for name,data in events if name=='citations')
    validate_citations(citations,done['used_evidence_ids'],snapshot,'SYN-DEMO-MAINTENANCE-001')
    return dict(events=names,status=done['status'],cache_hit=False,citations=citations,
                used_evidence_ids=done['used_evidence_ids'],done_count=1,error_count=0)


def http(base,path,payload=None):
    request=Request(base+path,data=json.dumps(payload,ensure_ascii=False).encode('utf-8') if payload is not None else None,
        headers={'Content-Type':'application/json'})
    try:
        with urlopen(request,timeout=150) as response:
            return response.status,response.read().decode('utf-8')
    except HTTPError as exc:
        return exc.code,exc.read().decode('utf-8')


def wait_ready(base,timeout=240):
    until=time.monotonic()+timeout
    while time.monotonic()<until:
        try:
            status,body=http(base,'/health/ready')
            if status==200:
                return json.loads(body)
        except (URLError,TimeoutError,OSError):
            pass
        time.sleep(2)
    raise AcceptanceFailure('READY_TIMEOUT')


def run(args):
    require(os.getenv('STAGE13_LIVE')=='1','STAGE13_LIVE_REQUIRED')
    require(urlsplit(args.base_url).hostname in ('localhost','127.0.0.1'),'LOCAL_ACCEPTANCE_HTTP_REQUIRED')
    require(args.project.startswith('stage13-acceptance'),'ISOLATED_COMPOSE_PROJECT_REQUIRED')
    compose=['docker','compose','--env-file',args.env_file,'-p',args.project,
             '-f','docker-compose.yml','-f','docker-compose.acceptance.yml']
    def docker(*command,timeout=300):
        result=subprocess.run(compose+list(command),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
        require(result.returncode==0,'DOCKER_COMMAND_FAILED')
        return result.stdout.strip()
    def inspect(option=None):
        output=docker('exec','-T','manufacturing-api','python','-m','scripts.stage13_snapshot',*([option] if option else []))
        report=json.loads(output.splitlines()[-1])
        require(report['status']=='PASS','SNAPSHOT_INSPECTION_FAILED')
        return report
    evidence=dict(status='PARTIAL',scope='controlled local synthetic full integration',steps={})
    def record(name,value):
        evidence['steps'][name]=value
        Path(args.output).parent.mkdir(parents=True,exist_ok=True)
        Path(args.output).write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(dict(step=name,status='PASS')),flush=True)
    try:
        record('health_ready',wait_ready(args.base_url))
        status,body=http(args.base_url,'/health/live')
        require(status==200 and json.loads(body)['status']=='alive','LIVE_HEALTH_FAILED')
        record('health_live',dict(http_status=status))
        snapshot=inspect()
        require(snapshot['server_version'].split('/')[-1].lstrip('v')=='2.5.4','WRONG_MILVUS_VERSION')
        require(snapshot['client_version']=='2.5.4' and all(snapshot['model_weights_mounted'].values()),'REAL_COMPONENTS_MISSING')
        record('snapshot',snapshot)
        first_bootstrap=json.loads(Path(args.bootstrap_first).read_text(encoding='utf-8'))
        second_bootstrap=json.loads(Path(args.bootstrap_second).read_text(encoding='utf-8'))
        require(first_bootstrap['status']==second_bootstrap['status']=='PASS','BOOTSTRAP_FAILED')
        require(len(first_bootstrap['results'])==len(second_bootstrap['results'])==2,'DEMO_DOCUMENTS_MISSING')
        require(all(r['status']=='INGEST' for r in first_bootstrap['results']),'FIRST_BOOTSTRAP_NOT_INGEST')
        require(all(r['status']=='SKIP_UNCHANGED' for r in second_bootstrap['results']),'SECOND_BOOTSTRAP_NOT_SKIP')
        require(first_bootstrap['documents']==second_bootstrap['documents'] and
                first_bootstrap['snapshot_fingerprint']==second_bootstrap['snapshot_fingerprint'],'BOOTSTRAP_SNAPSHOT_CHANGED')
        require(all(r['revision']==1 for r in second_bootstrap['documents']),'REVISION_INCREASED_ON_SKIP')
        record('versioned_ingestion',dict(first=first_bootstrap,second=second_bootstrap,ids_stable=True,revision_stable=True))
        status,body=http(args.base_url,'/api/manufacturing/query',{'query':PARAMETER_QUERY})
        require(status==200,'JSON_HTTP_FAILED')
        first=json.loads(body)
        validate_answer(first,snapshot,'SYN-DEMO-PARAMETER-001','1200')
        require(first['cache_hit'] is False,'FIRST_REQUEST_NOT_CACHE_MISS')
        record('json_first',first)
        status,body=http(args.base_url,'/api/manufacturing/query',{'query':PARAMETER_QUERY})
        second=json.loads(body)
        require(status==200 and second['cache_hit'] is True,'CACHE_HIT_FAILED')
        for field in ('answer_text','claims','citations','used_evidence_ids'):
            require(first[field]==second[field],'CACHE_RESULT_CHANGED')
        record('json_cached',dict(cache_hit=True,answer_identical=True,citations_identical=True))
        cache=inspect('--cache')
        require(bool(cache['keys']),'CACHE_KEYS_MISSING')
        require(all(re.fullmatch(r'manufacturing:answer:v1:[0-9a-f]{64}',row['key']) and 0<row['ttl']<=300 for row in cache['keys']),'UNSAFE_CACHE_KEY_OR_TTL')
        record('redis_cache',cache)
        status,body=http(args.base_url,'/api/manufacturing/stream',{'query':MAINTENANCE_QUERY})
        require(status==200,'SSE_HTTP_FAILED')
        record('sse',validate_stream(parse_sse(body),snapshot))
        status,body=http(args.base_url,'/api/manufacturing/query',{'query':' ','unexpected':'must not echo'})
        require(status==422 and json.loads(body)=={'code':'INVALID_REQUEST'},'UNSAFE_PUBLIC_ERROR')
        record('safe_error',dict(http_status=status,response=json.loads(body)))
        if args.lifecycle:
            try:
                docker('stop','redis')
                query='请查阅合成参数文档：设备型号 SYN-DEMO-100 的主轴额定转速是多少？'
                status,body=http(args.base_url,'/api/manufacturing/query',{'query':query})
                require(status==200,'REDIS_DEGRADED_QUERY_FAILED')
                degraded=json.loads(body)
                validate_answer(degraded,snapshot,'SYN-DEMO-PARAMETER-001','1200')
                require(degraded['cache_hit'] is False,'DEGRADED_REQUEST_CACHED')
                ready=wait_ready(args.base_url)
                require(ready['cache']=='degraded','CACHE_NOT_DEGRADED')
                record('redis_degradation',dict(status='answered',cache_hit=False,cache_state=ready['cache']))
            finally:
                docker('start','redis')
            docker('restart','manufacturing-api')
            record('api_restart',wait_ready(args.base_url))
            require(inspect()['knowledge_revision']==snapshot['knowledge_revision'],'REVISION_CHANGED_AFTER_API_RESTART')
            docker('stop')
            docker('start')
            record('stack_restart',wait_ready(args.base_url))
            after=inspect()
            require(after['knowledge_revision']==snapshot['knowledge_revision'] and after['children']==snapshot['children'],'PERSISTENT_SNAPSHOT_CHANGED')
            status,body=http(args.base_url,'/api/manufacturing/query',{'query':PARAMETER_QUERY})
            require(status==200,'RESTART_QUERY_FAILED')
            validate_answer(json.loads(body),after,'SYN-DEMO-PARAMETER-001','1200')
            record('restart_query',dict(http_status=status,status='answered',knowledge_revision_stable=True))
        evidence['status']='PASS'
    except Exception as exc:
        evidence['failure']=dict(exception_type=type(exc).__name__,code=str(exc) if isinstance(exc,AcceptanceFailure) else 'ACCEPTANCE_EXECUTION_FAILED')
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=evidence['status'],output=args.output)),flush=True)
    return 0 if evidence['status']=='PASS' else 1


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:18080')
    parser.add_argument('--project',default='stage13-acceptance')
    parser.add_argument('--env-file',default='runtime/stage13/acceptance.env')
    parser.add_argument('--output',default='runtime/stage13/acceptance_results.json')
    parser.add_argument('--lifecycle',action='store_true',help='explicitly test Redis stop/start and API/stack restart')
    parser.add_argument('--bootstrap-first',default='runtime/stage13/acceptance/bootstrap_first.json')
    parser.add_argument('--bootstrap-second',default='runtime/stage13/acceptance/bootstrap_second.json')
    args=parser.parse_args(argv)
    return run(args)


if __name__=='__main__':
    raise SystemExit(main())
