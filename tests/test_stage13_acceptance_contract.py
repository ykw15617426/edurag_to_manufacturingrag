"""Offline rejection tests only; no Docker, HTTP, model loading or LLM requests."""
from copy import deepcopy
import json

import pytest

from scripts.stage13_acceptance import AcceptanceFailure, parse_sse, validate_answer, validate_stream, run


@pytest.fixture
def snapshot():
    return {'children':[dict(document_id='SYN-DEMO-PARAMETER-001',document_version='1.0',
        parent_id='a'*64,source_file='/app/examples/manufacturing_demo/parameter.txt'),
        dict(document_id='SYN-DEMO-MAINTENANCE-001',document_version='1.0',
        parent_id='b'*64,source_file='/app/examples/manufacturing_demo/maintenance.txt')]}


def answer(snapshot):
    citation=dict(snapshot['children'][0],evidence_id='E1')
    return dict(status='answered',answer_text='模拟转速为1200 rpm。[E1]',
        claims=[dict(text='模拟转速为1200 rpm。',evidence_ids=['E1'])],
        citations=[citation],used_evidence_ids=['E1'])


@pytest.mark.parametrize('field,value',[
    ('document_id','SYN-DEMO-MAINTENANCE-001'),('document_version','2.0'),
    ('parent_id','c'*64),('source_file','/app/wrong.txt')])
def test_forged_or_stale_citation_rejected(snapshot,field,value):
    result=answer(snapshot)
    result['citations'][0][field]=value
    with pytest.raises(AcceptanceFailure):
        validate_answer(result,snapshot,'SYN-DEMO-PARAMETER-001','1200')


def test_number_in_renderer_only_does_not_pass(snapshot):
    result=answer(snapshot)
    result['claims'][0]['text']='参数可参考文档。'
    with pytest.raises(AcceptanceFailure,match='NUMERIC'):
        validate_answer(result,snapshot,'SYN-DEMO-PARAMETER-001','1200')


def maintenance_events(snapshot):
    return [('start',{}),('analysis',{}),('retrieval',{}),('generation',{'status':'validated'}),
        ('answer',{'text':'模拟维护周期为250小时。'}),
        ('citations',[dict(snapshot['children'][1],evidence_id='E1')]),
        ('done',{'status':'answered','cache_hit':False,'used_evidence_ids':['E1']})]


@pytest.mark.parametrize('change',['double_done','error','raw','cache_hit','wrong_source','empty'])
def test_sse_unsafe_terminal_or_evidence_rejected(snapshot,change):
    events=maintenance_events(snapshot)
    if change=='double_done': events.append(events[-1])
    elif change=='error': events.insert(3,('error',{'code':'GENERATION_ERROR'}))
    elif change=='raw': events[3]=('generation',{'status':'raw'})
    elif change=='cache_hit': events[-1][1]['cache_hit']=True
    elif change=='wrong_source': events[-2][1][0]=dict(snapshot['children'][0],evidence_id='E1')
    elif change=='empty': events=[]
    with pytest.raises(AcceptanceFailure):
        validate_stream(events,snapshot)


def test_sse_wire_parse_uses_all_actual_frames(snapshot):
    events=maintenance_events(snapshot)
    wire=''.join('event: '+name+'\r\ndata: '+json.dumps(data,ensure_ascii=False)+'\r\n\r\n' for name,data in events)
    parsed=parse_sse(wire)
    assert validate_stream(parsed,snapshot)['done_count']==1


def test_normal_invocation_cannot_start_live_acceptance(monkeypatch):
    monkeypatch.delenv('STAGE13_LIVE',raising=False)
    with pytest.raises(AcceptanceFailure,match='STAGE13_LIVE_REQUIRED'):
        run(None)


def test_demo_bootstrap_forbids_production_collection(monkeypatch):
    from base.config import config
    from scripts.bootstrap_manufacturing_demo import run_ingestion
    monkeypatch.setattr(config,'MILVUS_MANUFACTURING_COLLECTION_NAME','manufacturing_rag_v1')
    with pytest.raises(ValueError,match='isolated'):
        run_ingestion('unused',demo=True)
