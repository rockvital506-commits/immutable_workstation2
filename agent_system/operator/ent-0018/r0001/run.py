"""I3 runner candidate. Fail closed until the exact coordinator is registered."""
import copy
import json
import os
from pathlib import Path
import re
import runpy
import uuid

BASE=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
OWN={'session.py','session.schema.json','evidence.py','verify.py','usage.md','run.py','runner_verify.py'}
DEPENDENCIES={('ENT-0009','r0002'),('ENT-0016','r0002'),('ENT-0013','r0001'),('ENT-0015','r0001'),('ENT-0017','r0001')}
STEPS=['source_a','candidate','stage','reader','handoff','source_b','comparison']
FLAGS=['transition_allowed','release_allowed','export_allowed','activation_allowed']
NOT_CHECKED=['execution_authentication','source_authentication','plan_authentication','freshness',
             'global_event_completeness','agent_behavior','target_environment','release_permission','activation_permission']


class OperatorBlocked(Exception):
    def __init__(self,code,status='failed'):
        self.code,self.status=code,status
        super().__init__(code)


def _canonical(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False)


def _installed(path):
    if (type(path) is not str or path.startswith('/') or '\\' in path or ':' in path
            or any(x in ('','.','..') for x in path.split('/'))):raise OperatorBlocked('INSTALLED_PATH')
    with (BASE/path).open('rb') as stream:raw=stream.read(16*1024*1024+1)
    if len(raw)>16*1024*1024:raise OperatorBlocked('INSTALLED_LIMIT')
    return raw


def _load():
    s=runpy.run_path(str(HERE/'session.py'))
    try:n,parse,_,_=s['_tools']()
    except s['SessionBlocked'] as error:raise OperatorBlocked(error.code,'unsupported') from None
    stage=runpy.run_path(str(BASE/'staging/ent-0015/r0001/stage.py'))
    reader=runpy.run_path(str(BASE/'staging/ent-0016/r0002/read.py'))
    candidate=runpy.run_path(str(BASE/'candidates/ent-0013/r0001/check.py'))
    compare=runpy.run_path(str(BASE/'validation/ent-0017/r0001/compare.py'))
    replay=runpy.run_path(str(BASE/'validation/ent-0010/r0001/bundle.py'))
    evidence=runpy.run_path(str(HERE/'evidence.py'))
    nt=n['_load']()
    return dict(s=s,n=n,parse=parse,report_validator=nt[1][1],binding=nt[3],stage=stage,
                reader=reader,candidate=candidate,compare=compare,replay=replay,e=evidence)


def _bootstrap(t):
    """Protected installed namespace only. Never bootstrap approval from source."""
    parse=t['parse'];s=t['s'];ref=s['reference']
    raw=_installed('catalog/registry.json');registry=parse(raw);cid=registry['catalog_id']
    versions={(e['entity_id'],r['revision']):r for e in registry['entities'] for r in e['revisions']}
    key=('ENT-0018','r0001')
    if key not in versions:raise OperatorBlocked('COORDINATOR_NOT_REGISTERED','unsupported')
    own=versions[key]
    if (own['kind']!='protocol' or own['scopes']!=['agent_system.operator_trial']
            or own['approval']['status']!='approved' or any(x['type']!='depends_on' for x in own['relations'])
            or {(x['target']['entity_id'],x['target']['revision']) for x in own['relations']}!=DEPENDENCIES):
        raise OperatorBlocked('COORDINATOR_PROFILE_MISMATCH')
    prefix='operator/ent-0018/r0001/'
    if {a['path'] for a in own['artifacts']}!={prefix+p for p in OWN}:raise OperatorBlocked('COORDINATOR_COMPOSITION')
    expected=dict(s['PINS'])
    for a in own['artifacts']:
        if a['role']!='normative':raise OperatorBlocked('COORDINATOR_COMPOSITION')
        expected[a['path']]={k:a[k] for k in ('sha256','size_bytes')}
    payloads={p:_installed(p) for p in expected}
    for p,r in expected.items():
        try:s['_pin'](payloads[p],r)
        except s['SessionBlocked']:raise OperatorBlocked('INSTALLED_PROFILE_CHANGED') from None
    names=sorted(os.listdir(BASE/'catalog/approvals'))
    if len(names)>10000 or any(re.fullmatch('[0-9a-f-]{36}\.json',n) is None for n in names):raise OperatorBlocked('INSTALLED_LEDGER_SET')
    decisions={'catalog/approvals/'+name:_installed('catalog/approvals/'+name) for name in names}
    subject=dict(catalog_id=cid,entity_id=key[0],revision=key[1])
    bound=t['binding'](raw,decisions,payloads,[subject],operation='validate',area='agent_system.operator_trial')
    _passed(bound,'passed_known_inputs')
    closure={(x['entity_id'],x['revision']) for x in bound['selected_closure']}
    artifact_paths={a['path'] for k in closure for a in versions[k]['artifacts']}
    if artifact_paths!=set(expected):raise OperatorBlocked('INSTALLED_CLOSURE_MISMATCH')
    records={k:copy.deepcopy(versions[k]) for k in closure}
    profile=dict(catalog_id=cid,selection=[subject],artifacts=[dict(path=p,**r) for p,r in sorted(expected.items())],
                 candidate=dict(s['PINS']['candidates/ent-0013/r0001/candidate.json']))
    return profile,records


def installed_profile():
    """Trusted profile description, not a discovered source plan or a permission."""
    t=_load();return copy.deepcopy(_bootstrap(t)[0])


def _flags(value):
    if (value.get('overall_admission')!='not_evaluated' or value.get('transition_allowed') is not False
            or any(value.get(flag) is not False for flag in [*FLAGS,'compatible_release_allowed'] if flag in value)):
        raise OperatorBlocked('CHILD_PERMISSION_CLAIM')


def _passed(value,status):
    _flags(value)
    if value['status']!=status:
        state=value['status'] if value['status'] in ['blocked_known_scope','failed_partial','unsupported'] else 'failed'
        raise OperatorBlocked('CHILD_'+state.upper(),state)


def _source_packet(t,packet,rawplan,plan,records):
    s=t['s'];ref=s['reference'];parse=t['parse']
    if type(packet) is not dict or set(packet)!={'report_bytes','documents','capture'}:raise OperatorBlocked('SOURCE_PACKET_SHAPE')
    report=parse(packet['report_bytes'])
    if not t['report_validator'].is_valid(report):raise OperatorBlocked('SOURCE_REPORT_SCHEMA')
    if report['plan']!=ref(rawplan) or report['plan_id']!=plan['plan_id']:raise OperatorBlocked('SOURCE_PLAN_BINDING')
    refs=[report['plan']]+[v['evidence'] for v in report['stages'].values() if 'evidence' in v]
    docs=packet['documents']
    if type(docs) is not dict or set(docs)!={r['sha256'] for r in refs}:raise OperatorBlocked('SOURCE_DOCUMENT_SET')
    for r in refs:s['_pin'](docs[r['sha256']],r)
    if docs[ref(rawplan)['sha256']]!=rawplan:raise OperatorBlocked('SOURCE_PLAN_BINDING')
    cap=packet['capture']
    if report['status']!='passed_known_inputs':
        if cap is not None:raise OperatorBlocked('PARTIAL_CAPTURE_EXPOSED')
        return report,None,None
    if type(cap) is not dict or set(cap)!={'registry','artifacts','decisions'}:raise OperatorBlocked('SOURCE_CAPTURE_SHAPE')
    for key in ['artifacts','decisions']:
        if type(cap[key]) is not dict:raise OperatorBlocked('SOURCE_CAPTURE_SHAPE')
    if set(cap['artifacts'])!={r['path'] for r in plan['artifacts']} or set(cap['decisions'])!={r['path'] for r in plan['decisions']}:raise OperatorBlocked('SOURCE_CAPTURE_SET')
    payloads=dict(cap['artifacts']);payloads['catalog/registry.json']=cap['registry']
    all_inputs=dict(payloads,**cap['decisions'])
    entries=[plan['registry'],*plan['artifacts'],*plan['decisions']]
    if len(all_inputs)!=len(entries) or set(all_inputs)!={x['path'] for x in entries}:raise OperatorBlocked('SOURCE_CAPTURE_SET')
    for r in entries:s['_pin'](all_inputs[r['path']],{k:r[k] for k in ('sha256','size_bytes')})
    replay=t['replay']['verify_bundle'](packet['report_bytes'],ref(packet['report_bytes']),ref(rawplan),docs,all_inputs)
    _passed(replay,'consistent_recorded_bundle')
    registry=parse(cap['registry'])
    actual={(e['entity_id'],r['revision']):r for e in registry['entities'] for r in e['revisions']}
    if any(k not in actual or _canonical(actual[k])!=_canonical(r) for k,r in records.items()):raise OperatorBlocked('SOURCE_PROFILE_RECORD_MISMATCH')
    return report,dict(registry=cap['registry'],artifacts=dict(cap['artifacts']),decisions=dict(cap['decisions'])),all_inputs


def _scope(t,cap,selection,operation,area):
    checked=t['binding'](cap['registry'],cap['decisions'],cap['artifacts'],selection,operation=operation,area=area)
    _passed(checked,'passed_known_inputs')


def _handoff(t,receipt,packet,candidate,source,payloads):
    s=t['s'];ref=s['reference'];parse=t['parse']
    _passed(receipt,'staged_trial_only')
    if receipt['staged'] is not True or receipt['stage_created'] is not True:raise OperatorBlocked('STAGE_RECEIPT')
    if type(receipt['local_ref']) is not str or not receipt['local_ref'].startswith('local/trials/'):raise OperatorBlocked('STAGE_RECEIPT')
    run_id=receipt['local_ref'][len('local/trials/'):]
    if str(uuid.UUID(run_id))!=run_id:raise OperatorBlocked('STAGE_RECEIPT')
    if type(packet) is not dict or set(packet)!={'result','capture'}:raise OperatorBlocked('READER_PACKET')
    result=packet['result'];_passed(result,'consistent_archived_trial')
    if (any(v.get(flag) is not False for v in [receipt,result] for flag in FLAGS)
            or receipt.get('profile')!=t['stage']['PROFILE'] or result.get('current_permissions')!='not_evaluated'):
        raise OperatorBlocked('CHILD_PERMISSION_CLAIM')
    if result['profile']!='ent-0016-r0002-private-trial-capture' or result['manifest']!=receipt['manifest']:raise OperatorBlocked('READER_RECEIPT_BINDING')
    cap=packet['capture']
    if type(cap) is not dict or set(cap)!={'manifest_bytes','objects'}:raise OperatorBlocked('READER_CAPTURE')
    s['_pin'](cap['manifest_bytes'],receipt['manifest'])
    manifest=parse(cap['manifest_bytes'])
    expected=dict(schema_version='1',profile=t['stage']['PROFILE'],kind='incomplete_trial_snapshot',run_id=run_id,
                  candidate=ref(candidate),registry=ref(source['registry']),
                  payloads=[dict(path=p,**ref(b)) for p,b in sorted(payloads.items())],
                  decisions=[dict(path=p,**ref(b)) for p,b in sorted(source['decisions'].items())],
                  readiness='incomplete_candidate',release_allowed=False,export_allowed=False,activation_allowed=False,
                  transition_allowed=False,overall_admission='not_evaluated')
    objects={ref(raw)['sha256']:raw for raw in [candidate,source['registry'],*payloads.values(),*source['decisions'].values()]}
    if _canonical(manifest)!=_canonical(expected) or cap['objects']!=objects:raise OperatorBlocked('TRIAL_HANDOFF_MISMATCH')
    if (result['payload_count']!=len(payloads) or result['decision_count']!=len(source['decisions'])
            or result['objects_count']!=len(objects) or receipt['objects_count']!=len(objects)
            or result['captured_bytes']!=sum(map(len,objects.values()))):raise OperatorBlocked('READER_COUNTS')
    return dict(manifest_bytes=cap['manifest_bytes'],objects=dict(cap['objects']))


def run_operator_trial(source_a_root,session_bytes,expected_session,documents,*,source_b_root=None):
    """One local run; no caller child reports/callbacks, never release or activation.

    Protected installation must already contain the exact approved coordinator.
    Preflight errors raise OperatorBlocked before claims/source IO. All completed
    runs return safe codes/counts/refs only; raw data remains private evidence.
    """
    try:
        t=_load();s=t['s'];ref=s['reference'];encode=s['encode']
        profile,records=_bootstrap(t)
        for root in [source_a_root]+([source_b_root] if source_b_root is not None else []):
            if type(root) not in (str,type(Path('.'))):raise OperatorBlocked('SOURCE_ROOT_TYPE')
        prepared=s['validate_session'](session_bytes,expected_session,documents,profile,has_source_b=source_b_root is not None)
    except OperatorBlocked:raise
    except (OSError,ValueError,TypeError,KeyError,RuntimeError,ImportError,RecursionError):raise OperatorBlocked('PREFLIGHT_INVALID') from None
    except Exception as error:
        if 't' not in locals() or not isinstance(error,t['s']['SessionBlocked']):raise
        raise OperatorBlocked(error.code) from None
    session=prepared['session'];store=t['e']['EvidenceStore']()
    result=dict(profile='operator-trial-linux-r0001',status='failed',task_id=session['task_id'],
                purpose='local_core_trial',overall_admission='not_evaluated',current_permissions='not_evaluated',
                **{flag:False for flag in FLAGS},steps={step:dict(status='not_run') for step in STEPS},
                query='not_requested' if source_b_root is None else 'not_run',
                capture_invocations=0,completed_source_reports=0,validated_captures=0,source_acquisition_calls=0,
                evidence_sealed=False,not_checked=list(NOT_CHECKED),diagnostics=[])
    active=None
    def put(value):return store.put(encode(value))
    def record(step,value,status='passed'):
        allowed={'passed','passed_known_inputs','failed','failed_partial','unsupported','blocked_known_scope',
                 'consistent_incomplete_candidate','staged_trial_only','consistent_archived_trial','compared_known_views_no_admission'}
        result['steps'][step]=dict(status=status if status in allowed else 'failed',document=put(value))
    def source(step,index,root):
        raw=prepared['documents'][session['plan_a' if index==0 else 'plan_b']['sha256']]
        plan=prepared['plans'][index]
        result['capture_invocations']+=1
        try:packet=t['n']['capture_plan'](root,raw,ref(raw))
        except BaseException:
            result['source_acquisition_calls']=None
            raise
        try:report,cap,inputs=_source_packet(t,packet,raw,plan,records)
        except BaseException:
            result['source_acquisition_calls']=None
            raise
        result['completed_source_reports']+=1
        if result['source_acquisition_calls'] is not None:result['source_acquisition_calls']+=1
        for b in packet['documents'].values():store.put(b)
        report_ref=store.put(packet['report_bytes'])
        bundle=dict(kind='operator_source_bundle',plan=ref(raw),report=report_ref,
                    documents=[ref(b) for _,b in sorted(packet['documents'].items())],inputs=None)
        if inputs is not None:
            bundle['inputs']=[dict(path=p,**store.put(b)) for p,b in sorted(inputs.items())]
        record(step,bundle,report['status'])
        result['steps'][step]['child_run_id']=report['run_id']
        _passed(report,'passed_known_inputs')
        result['validated_captures']+=1
        return cap
    try:
        with store:
            session_ref=store.put(session_bytes)
            for raw in prepared['documents'].values():store.put(raw)
            try:
                active='source_a';a=source(active,0,source_a_root)
                active='candidate';candidate=a['artifacts']['candidates/ent-0013/r0001/candidate.json']
                s['_pin'](candidate,session['candidate']);descriptor=t['parse'](candidate)
                payloads={x['path']:a['artifacts'][x['path']] for c in descriptor['components'] for x in c['record']['artifacts']}
                checked=t['candidate']['check_candidate'](candidate,session['candidate'],a['registry'],a['decisions'],payloads)
                record(active,checked,checked['status']);_passed(checked,'consistent_incomplete_candidate')
                active='stage';_scope(t,a,profile['selection'],'stage_trial','agent_system.trial')
                receipt=t['stage']['stage_trial'](candidate,session['candidate'],a['registry'],a['decisions'],payloads)
                record(active,receipt,receipt['status']);_passed(receipt,'staged_trial_only')
                active='reader';_scope(t,a,profile['selection'],'read_trial','agent_system.trial')
                run_id=receipt['local_ref'].removeprefix('local/trials/')
                packet=t['reader']['capture_trial'](run_id,receipt['manifest'])
                record(active,packet['result'],packet['result']['status']);_passed(packet['result'],'consistent_archived_trial')
                active='handoff';archive=_handoff(t,receipt,packet,candidate,a,payloads)
                for raw in archive['objects'].values():store.put(raw)
                manifest_ref=store.put(archive['manifest_bytes'])
                record(active,dict(manifest=manifest_ref,objects=[ref(b) for _,b in sorted(archive['objects'].items())]))
                result['status']='trial_checked_no_query'
                if source_b_root is not None:
                    active='source_b';b=source(active,1,source_b_root)
                    active='comparison';_scope(t,b,profile['selection'],**session['query'])
                    plan=dict(schema_version='1',kind='known_view_comparison_plan',plan_id=str(uuid.uuid4()),
                              archive_manifest=manifest_ref,current_registry=ref(b['registry']),
                              current_decisions=[dict(path=p,**ref(v)) for p,v in sorted(b['decisions'].items())],context=session['query'])
                    raw=encode(plan);store.put(raw)
                    query=t['compare']['compare_views'](raw,ref(raw),archive['manifest_bytes'],archive['objects'],b['registry'],b['decisions'])
                    record(active,dict(plan=ref(raw),result=query),query['status'])
                    result['query']=query['status'] if query['status'] in ['compared_known_views_no_admission','blocked_known_scope','failed','unsupported'] else 'failed'
                    _passed(query,'compared_known_views_no_admission')
                    result['status']='trial_checked_with_known_query_no_admission'
            except OperatorBlocked as error:
                result.update(status=error.status,diagnostics=[dict(code=error.code)])
                if active and result['steps'][active]['status']=='not_run':result['steps'][active]=dict(status=error.status,code=error.code)
            except (OSError,ValueError,TypeError,KeyError,RuntimeError,RecursionError):
                result.update(status='failed',diagnostics=[dict(code='STEP_INVALID')])
                if active:result['steps'][active]=dict(status='failed',code='STEP_INVALID')
            except Exception as error:
                if isinstance(error,t['e']['EvidenceBlocked']):raise
                if not isinstance(error,(s['SessionBlocked'],t['n']['PlanBlocked'])):raise
                state='unsupported' if isinstance(error,t['n']['PlanBlocked']) and error.unsupported else 'failed'
                result.update(status=state,diagnostics=[dict(code='CHILD_INPUT_INVALID')])
                if active:result['steps'][active]=dict(status=state,code='CHILD_INPUT_INVALID')
            journal=dict(kind='operator_run_journal',session=session_ref,run_id=store.run_id,
                         terminal_claim=copy.deepcopy(result),seal_confirmation='external_receipt_required')
            journal_ref=put(journal)
            receipt=store.seal(dict(kind='operator_run_index',journal=journal_ref))
            result.update(evidence=receipt,evidence_sealed=True)
    except Exception as error:
        if not isinstance(error,t['e']['EvidenceBlocked']):raise
        result.update(status='evidence_write_failed',evidence_sealed=False,diagnostics=[dict(code=error.code)],
                      partial_evidence_ref='local/operator-runs/'+store.run_id)
    return result
