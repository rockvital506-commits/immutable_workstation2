"""Local-owner declared-context permission semantics, NOT current action authorization."""
from dataclasses import dataclass
import hashlib
from importlib import metadata
import json
from pathlib import Path
import runpy
import uuid

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[2]
LIMIT=16*1024*1024
TOTAL=64*1024*1024
COUNT=10000
PINS={'permissions/ent-0014/r0001/check.py': {'sha256': '18d47b251a0709ebd021a9473553c7faeb12b8e977d90ed41b20899dde9df1d2', 'size_bytes': 7333}, 'permissions/ent-0014/r0001/proposal.schema.json': {'sha256': '142a2a628ed5125229ac48a9e1d6768f62cf21ff138cc12a83fa1c220369ac39', 'size_bytes': 4320}, 'permissions/ent-0014/r0001/verify.py': {'sha256': 'd94ce36432537ce5e13f4d059fc6f0a0772c0e8fc6cbfb19734aa59e1937ed1e', 'size_bytes': 8170}, 'permissions/ent-0014/r0001/usage.md': {'sha256': '3ba366a47b00d576bfb1254dee15404b6e3c245437f3097be301907326eb2fd1', 'size_bytes': 15107}, 'permissions/ent-0014/r0002/permissions.schema.json': {'sha256': 'fad42d9a79676dd2458a2412493328a55064dc66505d5696751a5643e6fa0941', 'size_bytes': 7335}}


class PermissionBlocked(Exception):
    def __init__(self,code):self.code=code;super().__init__(code)


def reference(raw):
    return dict(sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))


def encode(value):
    return (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()


def _stop(code):raise PermissionBlocked(code)


def _pin(raw,expected):
    if (type(raw) is not bytes or len(raw)>LIMIT or type(expected) is not dict
            or set(expected)!={'sha256','size_bytes'} or type(expected['size_bytes']) is not int
            or type(expected['sha256']) is not str or reference(raw)!=expected):_stop('REFERENCE_MISMATCH')


def _pairs(items):
    out={}
    for k,v in items:
        if k in out:_stop('DUPLICATE_KEY')
        out[k]=v
    return out


def _json(raw):
    if (type(raw) is not bytes or len(raw)>LIMIT or not raw.endswith(b'\n')
            or raw.endswith(b'\n\n') or b'\r' in raw or raw.startswith(b'\xef\xbb\xbf')):_stop('SERIALIZATION')
    return json.loads(raw.decode('utf-8'),object_pairs_hook=_pairs,parse_constant=lambda _: _stop('JSON_CONSTANT'))


def _installed(path):
    expected=PINS[path]
    with (BASE/path).open('rb') as stream:raw=stream.read(expected['size_bytes']+1)
    _pin(raw,expected)
    return raw


def _schema():
    from jsonschema import Draft202012Validator,FormatChecker
    from referencing import Registry
    if metadata.version('jsonschema')!='4.26.0':_stop('INSTALLED_ENGINE_UNAVAILABLE')
    for p in PINS:_installed(p)
    value=_json(_installed('permissions/ent-0014/r0002/permissions.schema.json'))
    Draft202012Validator.check_schema(value)
    def deny(_):raise ValueError('Schema retrieval forbidden')
    return Draft202012Validator(value,format_checker=FormatChecker(),registry=Registry(retrieve=deny))


def _native(value):
    if type(value) is dict:
        for k,v in value.items():
            if k in ['size_bytes','generation'] and type(v) is not int:_stop('NATIVE_INTEGER_REQUIRED')
            if k in ['event_id','request_id','context_id','export_id']:
                if type(v) is not str or str(uuid.UUID(v))!=v:_stop('UUID')
            _native(v)
    elif type(value) is list:
        for v in value:_native(v)


def _doc(raw,kind,validator):
    value=_json(raw);_native(value)
    schema={'$defs':validator.schema['$defs'],'$ref':'#/$defs/'+kind}
    if not validator.evolve(schema=schema).is_valid(value):_stop('DOCUMENT_SCHEMA')
    return value


def _path(p):
    if (type(p) is not str or len(p.encode('utf-8'))>4096 or '\\' in p or ':' in p
            or any(ord(c)<32 or ord(c)==127 for c in p)
            or any(c in ('','.','..') for c in p.split('/'))):_stop('PATH')


def _named(items):
    for row in items:_path(row['path'])
    names=[v['path'] for v in items]
    if names!=sorted(set(names)):_stop('REFERENCE_SET')


def _event_ref(raw,event):return dict(event_id=event['event_id'],**reference(raw))


@dataclass(frozen=True,repr=False)
class _Authority:
    raw: bytes


def establish_local_authority(context_bytes,expected_context,*,trust_owner_controlled_context=False):
    """Protected caller only. Ack+pin are NOT a proof of external provenance."""
    if trust_owner_controlled_context is not True:_stop('EXPLICIT_OWNER_CONTROLLED_CONTEXT_REQUIRED')
    _pin(context_bytes,expected_context)
    try:
        context=_doc(context_bytes,'context',_schema());_context(context)
    except PermissionBlocked:raise
    except (ImportError,OSError):_stop('INSTALLED_PROFILE_UNAVAILABLE')
    except (ValueError,TypeError,KeyError,UnicodeError,RecursionError):_stop('CONTEXT_INVALID')
    return _Authority(context_bytes)


def _context(context):
    _named(context['known_events'])
    known={}
    for row in context['known_events']:
        p=row['path'];parts=p.split('/')
        if len(parts)!=2 or parts[0]!='permission-events' or not parts[1].endswith('.json'):_stop('EVENT_PATH')
        uid=parts[1][:-5]
        if str(uuid.UUID(uid))!=uid:_stop('EVENT_PATH')
        known[uid]={k:row[k] for k in ['sha256','size_bytes']}
    ids=[v['event_id'] for v in context['approved_events']]
    if ids!=sorted(set(ids)):_stop('APPROVED_EVENT_SET')
    for row in context['approved_events']:
        if known.get(row['event_id'])!={k:row[k] for k in ['sha256','size_bytes']}:_stop('APPROVED_EVENT_BINDING')


def _export(value,subject):
    if value is None:_stop('EXPORT_REQUIRED')
    if value['paths']!=[a['path'] for a in subject['artifacts']]:_stop('EXPORT_ALLOWLIST')
    if value['procedure']!=subject['procedure'] or value['prompt']!=subject['prompt']:_stop('EXPORT_PROCEDURE')


def _result():
    return dict(status='failed',context=None,request=None,subject=None,grant=None,authority_valid=False,release_permission_recognized=False,
                export_permission_recognized=False,readiness='not_checked',performed=False,
                overall_admission='not_evaluated',transition_allowed=False,release_allowed=False,
                export_allowed=False,activation_allowed=False,checks=[],diagnostics=[],
                not_checked=['owner_identity_authentication','authority_context_provenance','global_event_completeness',
                             'freshness','rollback_resistance','single_use_claim','subject_composition',
                             'coverage_truth','agent_behavior','actuation','target_environment'])


def _evaluate(request_bytes,expected_request,subject_bytes,expected_subject,event_blobs,
              authority,expected_current_context,result):
    if type(authority) is not _Authority:_stop('OWNER_AUTHORITY_NOT_ESTABLISHED')
    _pin(authority.raw,expected_current_context);_pin(request_bytes,expected_request);_pin(subject_bytes,expected_subject)
    if type(event_blobs) is not dict or len(event_blobs)>COUNT:_stop('EVENT_SET_LIMIT')
    events_raw=dict(event_blobs)
    if any(type(p) is not str or type(b) is not bytes or len(b)>LIMIT for p,b in events_raw.items()):_stop('EVENT_INPUT')
    if sum(map(len,events_raw.values()))+len(authority.raw)+len(request_bytes)+len(subject_bytes)>TOTAL:_stop('TOTAL_LIMIT')
    validator=_schema();context=_doc(authority.raw,'context',validator);_context(context)
    request=_doc(request_bytes,'request',validator);subject=_doc(subject_bytes,'subject',validator)
    _named(subject['artifacts']);_named(subject['entity_decisions'])
    if request['context']!=reference(authority.raw) or request['generation']!=context['generation']:_stop('CONTEXT_BINDING')
    if request['subject']!=expected_subject:_stop('SUBJECT_BINDING')
    actual=[dict(path=p,**reference(b)) for p,b in sorted(events_raw.items())]
    if actual!=context['known_events']:_stop('KNOWN_STREAM_BINDING')
    events={};refs={};approved={v['event_id']:v for v in context['approved_events']}
    for p,raw in events_raw.items():
        event=_doc(raw,'event',validator);uid=event['event_id'];er=_event_ref(raw,event)
        if uid in events:_stop('EVENT_ID_COLLISION')
        if p!='permission-events/'+uid+'.json':_stop('EVENT_PATH_BINDING')
        if approved.get(uid)!=er:_stop('EVENT_NOT_OWNER_APPROVED')
        events[uid]=event;refs[uid]=er
    for uid,event in events.items():
        kind=event['decision'];action=event['action']
        if kind=='authorize_export':
            parent=event['parent']
            if parent is None or refs.get(parent['event_id'])!=parent:_stop('RELEASE_PARENT_REFERENCE')
            target=events[parent['event_id']]
            if target['decision']!='authorize_release' or target['subject']!=event['subject']:_stop('RELEASE_PARENT_SUBJECT')
            if action!='export' or event['target'] is not None or event['export'] is None:_stop('EVENT_SHAPE')
        elif event['parent'] is not None or event['export'] is not None:_stop('EVENT_SHAPE')
        if kind=='authorize_release' and (action!='release' or event['target'] is not None):_stop('EVENT_SHAPE')
        if kind=='deny_permission' and event['target'] is not None:_stop('EVENT_SHAPE')
        if kind=='revoke_permission':
            target_ref=event['target']
            if target_ref is None or refs.get(target_ref['event_id'])!=target_ref:_stop('REVOKE_TARGET_REFERENCE')
            target=events[target_ref['event_id']]
            if (target['decision'] not in ['authorize_release','authorize_export'] or target['action']!=action
                    or target['subject']!=event['subject']):_stop('REVOKE_TARGET_SCOPE')
        if event['subject']==expected_subject and kind=='authorize_export':_export(event['export'],subject)
    grant_ref=request['grant']
    if refs.get(grant_ref['event_id'])!=grant_ref:_stop('GRANT_REFERENCE')
    grant=events[grant_ref['event_id']]
    if grant['subject']!=expected_subject or grant['decision']!='authorize_'+request['action']:_stop('GRANT_SCOPE')
    if request['action']=='release':
        if request['export'] is not None:_stop('UNEXPECTED_EXPORT')
        release_id=grant['event_id']
    else:
        _export(request['export'],subject)
        if request['export']!=grant['export']:_stop('EXPORT_REQUEST_BINDING')
        release_id=grant['parent']['event_id']
    result.update(context=reference(authority.raw),request=reference(request_bytes),subject=dict(expected_subject),grant=dict(grant_ref))
    result['authority_valid']=True
    result['checks']=['closed_documents_and_external_pins','owner_controlled_known_stream','exact_grant_subject_and_parent']
    def blocked(action,target_id):
        return any(e['subject']==expected_subject and e['action']==action and
                   (e['decision']=='deny_permission' or
                    (e['decision']=='revoke_permission' and e['target']['event_id']==target_id)) for e in events.values())
    release_blocked=blocked('release',release_id)
    export_blocked=request['action']=='export' and blocked('export',grant['event_id'])
    result['release_permission_recognized']=not release_blocked
    result['export_permission_recognized']=request['action']=='export' and not release_blocked and not export_blocked
    if release_blocked or export_blocked:
        result['status']='blocked_known_permission';result['diagnostics']=['KNOWN_PERMISSION_BLOCK']
    else:result['status']='permission_granted_in_declared_context'
    return request,subject


def evaluate_permission(request_bytes,expected_request,subject_bytes,expected_subject,event_blobs,
                        *,authority=None,expected_current_context=None):
    """Read-only recognition. All action flags false; caller controls trust boundary."""
    result=_result()
    try:_evaluate(request_bytes,expected_request,subject_bytes,expected_subject,event_blobs,authority,expected_current_context,result)
    except PermissionBlocked as error:result=_result();result['diagnostics']=[error.code]
    except (ImportError,OSError):result=_result();result['status']='unsupported';result['diagnostics']=['INSTALLED_PROFILE_UNAVAILABLE']
    except (ValueError,TypeError,KeyError,AttributeError,UnicodeError,RecursionError):result=_result();result['diagnostics']=['DOCUMENT_OR_INPUT_INVALID']
    return result


def check_current_candidate(request_bytes,expected_request,subject_bytes,expected_subject,event_blobs,*,
                            authority=None,expected_current_context=None,proposal_bytes,expected_proposal,
                            candidate_bytes,expected_candidate,registry_blob,entity_decisions,payloads,
                            release_request_bytes=None):
    """Native old ENT14r1 guard. This profile NEVER enables an actual transition."""
    result=evaluate_permission(request_bytes,expected_request,subject_bytes,expected_subject,event_blobs,
                               authority=authority,expected_current_context=expected_current_context)
    if result['status']!='permission_granted_in_declared_context':return result
    try:
        if type(payloads) is not dict or type(entity_decisions) is not dict:_stop('CURRENT_INPUT_TYPE')
        payloads,entity_decisions=dict(payloads),dict(entity_decisions)
        docs=[proposal_bytes,candidate_bytes,registry_blob,*payloads.values(),*entity_decisions.values()]
        if release_request_bytes is not None:docs.append(release_request_bytes)
        if (len(docs)>COUNT or any(type(raw) is not bytes or len(raw)>LIMIT for raw in docs)
                or sum(map(len,docs))+len(request_bytes)+len(subject_bytes)+len(authority.raw)
                +sum(map(len,event_blobs.values()))>TOTAL):_stop('CURRENT_INPUT_LIMIT')
        subject=_json(subject_bytes);request=_json(request_bytes);proposal=_json(proposal_bytes)
        if (subject['candidate']!=expected_candidate or subject['coverage_description']!=expected_candidate
                or subject['registry']!=reference(registry_blob) or proposal['action']!=request['action']):_stop('CURRENT_SUBJECT_BINDING')
        if type(payloads) is not dict or type(entity_decisions) is not dict:_stop('CURRENT_INPUT_TYPE')
        if subject['artifacts']!=[dict(path=p,**reference(b)) for p,b in sorted(payloads.items())]:_stop('CURRENT_ARTIFACT_BINDING')
        if subject['entity_decisions']!=[dict(path=p,**reference(b)) for p,b in sorted(entity_decisions.items())]:_stop('CURRENT_ENTITY_STREAM_BINDING')
        for field,p in [('procedure','protocols/ent-0012/r0001/governance.md'),('prompt','transfer/ent-0012/r0001/prompt.md')]:
            if subject[field]!=reference(payloads[p]):_stop('CURRENT_PROCEDURE_BINDING')
        for p in PINS:_installed(p)
        legacy=runpy.run_path(str(BASE/'permissions/ent-0014/r0001/check.py'))
        value=legacy['check_proposal'](proposal_bytes,expected_proposal,candidate_bytes,expected_candidate,
                                      registry_blob,entity_decisions,payloads,release_request_bytes)
        result['status']=value['status'];result['diagnostics']=[v['code'] for v in value['diagnostics']]
        result['checks'].append('native_legacy_candidate_and_scope_guard')
        if value['status']=='blocked_incomplete_candidate':result['readiness']='incomplete_candidate'
    except PermissionBlocked as error:result['status']='failed';result['diagnostics']=[error.code]
    except (OSError,ImportError):result['status']='unsupported';result['diagnostics']=['INSTALLED_PROFILE_UNAVAILABLE']
    except (ValueError,TypeError,KeyError,AttributeError,UnicodeError,RecursionError):result['status']='failed';result['diagnostics']=['CURRENT_INPUT_INVALID']
    return result
