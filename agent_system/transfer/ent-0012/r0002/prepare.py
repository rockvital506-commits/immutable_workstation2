"""Exact inactive composition preparation. Metadata only; no permission/actuator."""
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import runpy
import stat
import uuid

BASE=Path(__file__).resolve().parents[3]
HERE='transfer/ent-0012/r0002/'
OWN=['prepare.py','preparation.schema.json','procedure.md','prompt.md','usage.md','verify.py']
DEPENDENCIES=[('ENT-0012','r0001'),('ENT-0011','r0002'),('ENT-0014','r0003'),('ENT-0018','r0001')]
PROCEDURE=HERE+'procedure.md';PROMPT=HERE+'prompt.md';SCHEMA=HERE+'preparation.schema.json'
SEED='candidates/ent-0013/r0001/candidate.json'
PREFIXES=('catalog/contracts/agent_system/','adapters/','specification/','validation/','protocols/','transfer/','permissions/','staging/','operator/','candidates/')
LIMIT=16*1024*1024
# PINS inserted from exact protected installed dependencies, not source data.
PINS={'validation/ent-0009/r0002/execute.py': {'sha256': 'e28329880072ce4a13b4306bfa5c423860ad8e959147b9653f9ed13650be20ba', 'size_bytes': 14202}, 'validation/ent-0009/r0002/verify.py': {'sha256': '54a77f771b518a8af9a0d430b03c49e4f32182a180ee71981970ca550dd74296', 'size_bytes': 19812}, 'validation/ent-0009/r0002/usage.md': {'sha256': '9e8c100d8126c1cda232ddd169a90a95844e62f896bac9b415102c0deb0522c0', 'size_bytes': 7482}, 'candidates/ent-0013/r0001/candidate.json': {'sha256': '3a9231b668cc63b1d4a60d032dfe49fb61223a3b2c81b3fd79a42a1ee1b7f428', 'size_bytes': 69062}, 'candidates/ent-0013/r0001/check.py': {'sha256': 'f185875d034bc61697d926c45eedbb4764d281ccb96a8dca8cc7488dea42a660', 'size_bytes': 12871}, 'candidates/ent-0013/r0001/verify.py': {'sha256': '0292c5c700714d7db0cbf27b2e76a56d9d0f1e69e3f19d3488527313dda8a86e', 'size_bytes': 8484}, 'candidates/ent-0013/r0001/usage.md': {'sha256': '080abfa5143db3920ed9eec80380e21e31ac43f99fb8236dc678fd4c009cafca', 'size_bytes': 15101}, 'operator/ent-0018/r0001/acceptance_verify.py': {'sha256': '479dcc4a54d3ca5d2f7cf5a8a844d987ce6b90050955a66abfcea4b66c94aae9', 'size_bytes': 11722}, 'operator/ent-0018/r0001/evidence.py': {'sha256': '255bffc084d40ce598248ddda687249dcf548992ab4bc386a12cdaeb997f972f', 'size_bytes': 9453}, 'operator/ent-0018/r0001/lab.py': {'sha256': 'b14bebf61d26e2e2f6291db9c4d7d2a982b907488682c06a4acb7675cb98cc0f', 'size_bytes': 4182}, 'operator/ent-0018/r0001/procedure.md': {'sha256': '54f41439a8399f89e6d11dd7fd8ac95569e0bfce96667df5c3bb7bb4e2d0ccbd', 'size_bytes': 7077}, 'operator/ent-0018/r0001/prompt.md': {'sha256': '87f5ca9e72f58442981602d7910178c13b49f80ab931333d373f4f20c58be378', 'size_bytes': 2307}, 'operator/ent-0018/r0001/replay.py': {'sha256': '95ce2ad08944b1a8fe6d74b27a30f97f087b12b6ff159397b8b1876144fe5e37', 'size_bytes': 12615}, 'operator/ent-0018/r0001/replay_verify.py': {'sha256': 'b2ecd0a50dfb99452ffc910f89954f17a0e4700f61c198895a3dffcb5051a864', 'size_bytes': 8421}, 'operator/ent-0018/r0001/run.py': {'sha256': '68d3251e7b212b673b6705b32855f554829d76147467a18262e208635b4b1c00', 'size_bytes': 23614}, 'operator/ent-0018/r0001/runner_verify.py': {'sha256': 'd7451bdf77d030f11811472f83ccc3d43e1fb05004832b181a6029a05fa2df6e', 'size_bytes': 17076}, 'operator/ent-0018/r0001/session.py': {'sha256': '789a60c5b09744f804bfb3e9685eb63796fbfdeb561376aace5fc2bca8e82aad', 'size_bytes': 12464}, 'operator/ent-0018/r0001/session.schema.json': {'sha256': '76a3030a1f107a92e24cc80af978b0b1c9a0c5c0f16718829b8907a51a66e76f', 'size_bytes': 2856}, 'operator/ent-0018/r0001/usage.md': {'sha256': '13eeeab847fa30e15e6cce444a1b2cdd9982cf5147035aed8dfa25aadac12679', 'size_bytes': 12012}, 'operator/ent-0018/r0001/verify.py': {'sha256': '444b7ea06dd237a1720573ff0cb9e88d12a3b97cd30e7987372c7d931a71ee3a', 'size_bytes': 13735}, 'transfer/ent-0012/r0002/preparation.schema.json': {'sha256': '4bb5139908226a3ae7894df60dc5092a7f35c5dad3bb0c6623ea1bd90017ea4f', 'size_bytes': 1289}, 'transfer/ent-0012/r0002/procedure.md': {'sha256': '566c5ba67ce471e881d131d5273718c49c9a1e35ba9c8bf122c565b4b3ed0f7b', 'size_bytes': 3879}, 'transfer/ent-0012/r0002/prompt.md': {'sha256': '1c5e7a9300e964812c755ecbd187984db0faa818371b19cd93ea67777dfc4917', 'size_bytes': 2706}}


class PreparationBlocked(Exception):
    def __init__(self,code):self.code=code;super().__init__(code)


def _stop(code):raise PreparationBlocked(code)
def reference(raw):return dict(sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))
def encode(value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    if len(raw)>LIMIT:_stop('DOCUMENT_LIMIT')
    return raw


def _pin(raw,expected):
    if (type(raw) is not bytes or len(raw)>LIMIT or type(expected) is not dict
            or set(expected)!={'sha256','size_bytes'} or type(expected['size_bytes']) is not int
            or reference(raw)!=expected):_stop('REFERENCE_MISMATCH')


def _installed(path):
    with (BASE/path).open('rb') as f:raw=f.read(PINS[path]['size_bytes']+1)
    _pin(raw,PINS[path]);return raw


def _tools():
    if platform.system()!='Linux' or platform.machine()!='x86_64':_stop('UNSUPPORTED_PLATFORM')
    for p in PINS:_installed(p)
    entry=runpy.run_path(str(BASE/'validation/ent-0009/r0002/execute.py'))
    try:parse,validators,reader,checker,_=entry['_load']()
    except entry['PlanBlocked'] as error:_stop(error.code)
    candidate=runpy.run_path(str(BASE/'candidates/ent-0013/r0001/check.py'))
    evidence=runpy.run_path(str(BASE/'operator/ent-0018/r0001/evidence.py'))
    schema=parse(_installed(SCHEMA));type(validators[0]).check_schema(schema)
    from referencing import Registry
    def deny(_):raise ValueError('External schema retrieval forbidden')
    validator=type(validators[0])(schema,format_checker=validators[0].format_checker,registry=Registry(retrieve=deny))
    return entry,parse,validators[0],validator,reader,checker,candidate,evidence


def _versions(registry):return {(e['entity_id'],v['revision']):v for e in registry['entities'] for v in e['revisions']}
def _key(subject):return (subject['entity_id'],subject['revision'])
def _subject(cid,key):return dict(catalog_id=cid,entity_id=key[0],revision=key[1])
def _flags():return dict(overall_admission='not_evaluated',performed=False,transition_allowed=False,compatible_release_allowed=False,release_allowed=False,export_allowed=False,activation_allowed=False,export_performed=False,activation_performed=False,current_binding_changed=False)
def _allowed(path):return type(path) is str and path.startswith(PREFIXES) and not any(p in ('','..','.') for p in path.split('/')) and '\\' not in path and ':' not in path


def _prepare(root,request_bytes,expected_request,plan_bytes,expected_plan,acknowledge_inactive_only):
    if acknowledge_inactive_only is not True:_stop('EXPLICIT_INACTIVE_ACK_REQUIRED')
    _pin(request_bytes,expected_request);_pin(plan_bytes,expected_plan)
    entry,parse,pv,rv,reader,checker,candidate,evidence=_tools()
    request=parse(request_bytes)
    if (not request_bytes.endswith(b'\n') or request_bytes.endswith(b'\n\n') or b'\r' in request_bytes
            or not rv.is_valid(request) or not request['purpose'].strip()):_stop('REQUEST_SCHEMA_OR_SERIALIZATION')
    if str(uuid.UUID(request['request_id']))!=request['request_id']:_stop('REQUEST_ID')
    for field,path in [('procedure',PROCEDURE),('prompt',PROMPT),('seed_candidate',SEED)]:
        if type(request[field]['size_bytes']) is not int or request[field]!=PINS[path]:_stop('REQUEST_COMPONENT_REFERENCE')
    if request['plan']!=expected_plan:_stop('REQUEST_PLAN_REFERENCE')
    _pin(plan_bytes,request['plan'])
    try:plan=entry['_plan'](plan_bytes,expected_plan,parse,pv)
    except entry['PlanBlocked'] as error:_stop(error.code)
    roots=[_key(s) for s in plan['selection']]
    if (plan['context']!=dict(operation='export',area='agent_system.transfer')
            or ('ENT-0012','r0002') not in roots or len(set(roots))!=len(roots)):_stop('PREPARATION_SELECTION_OR_CONTEXT')
    paths={a['path'] for a in plan['artifacts']}
    if not {HERE+n for n in OWN}.issubset(paths):_stop('COMPONENT_MISSING')
    if any(not _allowed(p) for p in paths):_stop('PRIVATE_OR_UNSUPPORTED_PATH')
    try:observed=entry['capture_plan'](root,plan_bytes,expected_plan)
    except entry['PlanBlocked'] as error:_stop(error.code)
    execution=parse(observed['report_bytes']);docs=dict(observed['documents'])
    docs[reference(observed['report_bytes'])['sha256']]=observed['report_bytes']
    docs[reference(request_bytes)['sha256']]=request_bytes
    if execution['status']!='passed_known_inputs':
        return dict(status=execution['status'],manifest_bytes=None,execution_report_bytes=observed['report_bytes'],documents=docs)
    capture=observed['capture'];registry=parse(capture['registry']);versions=_versions(registry)
    own=versions[('ENT-0012','r0002')]
    expected_relations=[dict(type='depends_on',target=_subject(registry['catalog_id'],key)) for key in DEPENDENCIES]+[dict(type='supersedes',target=_subject(registry['catalog_id'],('ENT-0012','r0001')))]
    if (own['kind']!='protocol' or own['scopes']!=['agent_system.governance','agent_system.transfer','agent_system.connection']
            or own['relations']!=expected_relations or {a['path'] for a in own['artifacts']}!={HERE+n for n in OWN}):_stop('PREPARATION_PROFILE_RECORD')
    binding=parse(docs[execution['stages']['binding']['evidence']['sha256']])
    closure=binding['selected_closure'];components=[dict(subject=s,record=copy.deepcopy(versions[_key(s)])) for s in closure]
    expected_paths={a['path'] for c in components for a in c['record']['artifacts']}
    if expected_paths!=set(capture['artifacts']) or expected_paths!=paths:_stop('EXACT_CLOSURE_ARTIFACT_SET')
    for c in components:
        if any(not s.startswith('agent_system.') for s in c['record']['scopes']):_stop('PRIVATE_COMPONENT_SCOPE')
        if any(a['role']!='normative' for a in c['record']['artifacts']):_stop('NON_NORMATIVE_COMPONENT')
    for n in OWN:
        path=HERE+n
        with (BASE/path).open('rb') as f:installed=f.read(LIMIT+1)
        if capture['artifacts'][path]!=installed:_stop('PREPARATION_COMPONENT_CHANGED')
    seed=capture['artifacts'].get(SEED)
    if seed is None:_stop('SEED_MISSING')
    _pin(seed,PINS[SEED]);seed_value=parse(seed)
    seed_paths={a['path'] for c in seed_value['components'] for a in c['record']['artifacts']}
    seed_report=candidate['check_candidate'](seed,PINS[SEED],capture['registry'],capture['decisions'],{p:capture['artifacts'][p] for p in seed_paths})
    if seed_report['status']!='consistent_incomplete_candidate':_stop('SEED_VALIDATION_FAILED')
    seed_report_raw=encode(seed_report);docs[reference(seed_report_raw)['sha256']]=seed_report_raw
    rows=copy.deepcopy(seed_value['coverage']+seed_value['conditions'])
    manifest=dict(schema_version='1',kind='inactive_transfer_composition',status='prepared_inactive',run_id=str(uuid.uuid4()),
                  request=reference(request_bytes),plan=reference(plan_bytes),execution=reference(observed['report_bytes']),
                  purpose=request['purpose'],profile=entry['PROFILE'],procedure=dict(path=PROCEDURE,**PINS[PROCEDURE]),
                  prompt=dict(path=PROMPT,**PINS[PROMPT]),registry=reference(capture['registry']),roots=copy.deepcopy(plan['selection']),
                  context=copy.deepcopy(plan['context']),components=components,
                  observed_artifacts=[dict(path=p,**reference(b)) for p,b in sorted(capture['artifacts'].items())],
                  known_decisions=[dict(path=p,**reference(b)) for p,b in sorted(capture['decisions'].items())],
                  seed_candidate=dict(path=SEED,**PINS[SEED]),seed_validation=reference(seed_report_raw),
                  gap_basis='historical_seed_not_current_coverage',historical_rows=rows,
                  gap_to_check=[dict(id=row['id'],status='open_not_discharged',gaps=copy.deepcopy(row['gaps']),
                                     existing_checks=copy.deepcopy(row['checks']),next_step='qualify_exact_subject_and_missing_evidence_levels') for row in rows],
                  composition_coverage='not_evaluated',runtime_obligations=['durable_action_claim','positive_readiness_verifier','export_actuator',
                  'environment_adaptation','explicit_activation','exact_owner_action_grants','independent_high_water','behavior_qualification'],
                  not_checked=['source_authentication','plan_authentication','global_event_completeness','atomic_snapshot','coverage_truth',
                               'environment_compatibility','release_permission','export_permission','activation_permission','semantic_evidence_replay'],**_flags())
    raw=encode(manifest);docs[reference(raw)['sha256']]=raw
    return dict(status='prepared_inactive',manifest_bytes=raw,execution_report_bytes=observed['report_bytes'],documents=docs)


def prepare_inactive(root,request_bytes,expected_request,plan_bytes,expected_plan,*,acknowledge_inactive_only=False):
    """Read source through native capture; returns metadata only, never payloads."""
    try:return _prepare(root,request_bytes,expected_request,plan_bytes,expected_plan,acknowledge_inactive_only)
    except PreparationBlocked:raise
    except (OSError,ValueError,TypeError,KeyError,RuntimeError,ImportError,RecursionError):_stop('INPUT_OR_INSTALLED_PROFILE_UNAVAILABLE')


def make_packet(registry_bytes,decisions):
    """Build a DECLARATION from known bytes, not authority/validation or file IO."""
    entry,parse,*_= _tools();registry=parse(registry_bytes);versions=_versions(registry);cid=registry['catalog_id']
    root=('ENT-0012','r0002');closure=set();todo=[root]
    while todo:
        key=todo.pop()
        if key in closure:continue
        if len(closure)>=10000:_stop('GRAPH_LIMIT')
        closure.add(key);todo.extend(_key(r['target']) for r in versions[key]['relations'] if r['type']=='depends_on')
    artifacts=sorted([dict(path=a['path'],sha256=a['sha256'],size_bytes=a['size_bytes']) for k in closure for a in versions[k]['artifacts']],key=lambda a:a['path'])
    plan=dict(schema_version='1',kind='validation_plan',plan_id=str(uuid.uuid4()),catalog_id=cid,execution_profile=entry['PROFILE'],
              expectation_authority='caller_supplied_not_authenticated',context=dict(operation='export',area='agent_system.transfer'),
              selection=[_subject(cid,root)],registry=dict(path='catalog/registry.json',**reference(registry_bytes)),
              artifacts=artifacts,decisions=[dict(path=p,**reference(b)) for p,b in sorted(decisions.items())])
    plan_raw=encode(plan)
    request=dict(schema_version='1',kind='inactive_transfer_request',request_id=str(uuid.uuid4()),purpose='Inactive transfer composition and historical R6 gap basis; no export.',
                 plan=reference(plan_raw),procedure=PINS[PROCEDURE],prompt=PINS[PROMPT],seed_candidate=PINS[SEED])
    return encode(request),plan_raw


def installed_packet(*,trust_installed_namespace=False):
    """Observe fixed protected installation; same-source pins are NOT authority."""
    if trust_installed_namespace is not True:_stop('EXPLICIT_INSTALLED_NAMESPACE_REQUIRED')
    entry,parse,pv,rv,reader,*_=_tools()
    fd=os.open(BASE,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        def read(path):
            node=reader['_open_node'](fd,reader['_logical_parts'](path))
            try:
                before=reader['_fingerprint'](node)
                if not stat.S_ISREG(os.fstat(node).st_mode):_stop('INSTALLED_NON_REGULAR')
                raw=reader['_read_data'](node,LIMIT)
                if reader['_fingerprint'](node)!=before:_stop('INSTALLED_OBSERVATION_CHANGED')
                return raw
            finally:os.close(node)
        registry=read('catalog/registry.json');names=reader['observe_directory'](fd)['entries']
        if any(re.fullmatch('[0-9a-f-]{36}\\.json',n) is None for n in names):_stop('INSTALLED_LEDGER_NAME')
        decisions={};total=len(registry)
        for name in names:
            raw=read('catalog/approvals/'+name);total+=len(raw)
            if total>64*1024*1024:_stop('INPUT_LIMIT')
            decisions['catalog/approvals/'+name]=raw
        return make_packet(registry,decisions)
    except reader['ReadBlocked'] as error:_stop(error.code)
    except (OSError,ValueError,TypeError,KeyError,RuntimeError):_stop('INSTALLED_OBSERVATION_UNAVAILABLE')
    finally:os.close(fd)


def persist_preparation(result,*,trust_private_namespace=False):
    """Metadata CAS consistency only; not origin/semantic execution authentication."""
    if trust_private_namespace is not True:_stop('EXPLICIT_PRIVATE_NAMESPACE_REQUIRED')
    try:
        *_,evidence=_tools()
        if result['status']!='prepared_inactive' or type(result['manifest_bytes']) is not bytes:_stop('NO_SUCCESSFUL_PREPARATION')
        if set(result)!={'status','manifest_bytes','execution_report_bytes','documents'}:_stop('RESULT_SHAPE')
        manifest=json.loads(result['manifest_bytes']);docs=dict(result['documents'])
        if (manifest['kind']!='inactive_transfer_composition' or manifest['status']!='prepared_inactive'
                or manifest['composition_coverage']!='not_evaluated'):_stop('MANIFEST_PROFILE')
        _pin(result['execution_report_bytes'],manifest['execution'])
        execution=json.loads(result['execution_report_bytes'])
        if execution['status']!='passed_known_inputs':_stop('EXECUTION_NOT_PASSED')
        references=[reference(result['manifest_bytes']),manifest['request'],manifest['plan'],manifest['execution'],manifest['seed_validation']]
        references.extend(execution['stages'][s]['evidence'] for s in ['acquisition','binding'])
        if set(docs)!={r['sha256'] for r in references}:_stop('METADATA_DOCUMENT_SET')
        for r in references:_pin(docs[r['sha256']],r)
        for raw in docs.values():
            if type(json.loads(raw)) is not dict:_stop('METADATA_DOCUMENT_TYPE')
        for k,v in _flags().items():
            if type(manifest[k]) is not type(v) or manifest[k]!=v:_stop('MANIFEST_ACTION_CLAIM')
        if docs.get(reference(result['manifest_bytes'])['sha256'])!=result['manifest_bytes']:_stop('MANIFEST_OBJECT_MISSING')
        for sha,raw in docs.items():
            if reference(raw)['sha256']!=sha:_stop('DOCUMENT_REFERENCE_MISMATCH')
        try:
            with evidence['EvidenceStore']() as store:
                for raw in docs.values():store.put(raw)
                receipt=store.seal(dict(kind='inactive_transfer_preparation',manifest=reference(result['manifest_bytes']),**_flags()))
            evidence['verify_evidence'](receipt['run_id'],receipt['index'])
        except evidence['EvidenceBlocked'] as error:_stop(error.code)
        return dict(status='consistent_private_preparation_evidence',evidence=receipt,manifest=reference(result['manifest_bytes']),**_flags())
    except PreparationBlocked:raise
    except (OSError,ValueError,TypeError,KeyError,RuntimeError,ImportError):_stop('EVIDENCE_UNAVAILABLE_OR_PARTIAL')


if __name__=='__main__':
    import argparse
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--trust-installed-namespace',action='store_true')
    args=cli.parse_args()
    try:
        request,plan=installed_packet(trust_installed_namespace=args.trust_installed_namespace)
        result=prepare_inactive(BASE,request,reference(request),plan,reference(plan),acknowledge_inactive_only=True)
        if result['status']!='prepared_inactive':_stop('PREPARATION_NOT_SUCCESSFUL')
        print(json.dumps(persist_preparation(result,trust_private_namespace=True)))
    except PreparationBlocked as error:print(error.code);raise SystemExit(2)
