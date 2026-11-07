#!/usr/bin/env python3
"""Bind permission proposals; incomplete candidates can never acquire permission."""
import hashlib
import json
from pathlib import Path
import runpy

BASE=Path(__file__).resolve().parents[3]
PINS={'candidates/ent-0013/r0001/candidate.json': {'sha256': '3a9231b668cc63b1d4a60d032dfe49fb61223a3b2c81b3fd79a42a1ee1b7f428', 'size_bytes': 69062}, 'candidates/ent-0013/r0001/check.py': {'sha256': 'f185875d034bc61697d926c45eedbb4764d281ccb96a8dca8cc7488dea42a660', 'size_bytes': 12871}, 'candidates/ent-0013/r0001/verify.py': {'sha256': '0292c5c700714d7db0cbf27b2e76a56d9d0f1e69e3f19d3488527313dda8a86e', 'size_bytes': 8484}, 'candidates/ent-0013/r0001/usage.md': {'sha256': '080abfa5143db3920ed9eec80380e21e31ac43f99fb8236dc678fd4c009cafca', 'size_bytes': 15101}, 'permissions/ent-0014/r0001/proposal.schema.json': {'sha256': '142a2a628ed5125229ac48a9e1d6768f62cf21ff138cc12a83fa1c220369ac39', 'size_bytes': 4320}}
LIMIT=16*1024*1024


def reference(raw):
    return dict(sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))


def _encode(value):
    return (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()


def _pinned(raw,expected):
    return (type(raw) is bytes and len(raw)<=LIMIT and type(expected) is dict
            and set(expected)=={'sha256','size_bytes'} and type(expected['size_bytes']) is int
            and type(expected['sha256']) is str and reference(raw)==expected)


def _load():
    for path,expected in PINS.items():
        with (BASE/path).open('rb') as stream:
            raw=stream.read(expected['size_bytes']+1)
        if reference(raw)!=expected:raise RuntimeError('Installed profile changed')
    candidate=runpy.run_path(str(BASE/'candidates/ent-0013/r0001/check.py'))
    try:
        parse,(validator,_),_,binding,_=candidate['_load']()
    except candidate['_Stop']:
        raise RuntimeError('Installed profile unavailable') from None
    schema=parse((BASE/'permissions/ent-0014/r0001/proposal.schema.json').read_bytes())
    type(validator).check_schema(schema)
    return candidate['check_candidate'],parse,validator.evolve(schema=schema),binding


class _Stop(Exception):
    def __init__(self,code):self.code=code


def _proposal(raw,expected,parse,validator):
    if not _pinned(raw,expected):raise _Stop('PROPOSAL_REFERENCE_MISMATCH')
    if not raw.endswith(b'\n') or raw.endswith(b'\n\n') or b'\r' in raw:raise _Stop('PROPOSAL_SERIALIZATION')
    value=parse(raw)
    if not validator.is_valid(value):raise _Stop('PROPOSAL_SCHEMA')
    refs=[value['candidate'],value['registry'],*value['decisions']]
    if value['release_request'] is not None:refs.append(value['release_request'])
    if any(type(r['size_bytes']) is not int for r in refs):raise _Stop('REFERENCE_SIZE_TYPE')
    if [d['path'] for d in value['decisions']]!=sorted({d['path'] for d in value['decisions']}):
        raise _Stop('DECISION_REFERENCE_SET')
    return value


def check_proposal(proposal_bytes,expected_proposal,candidate_bytes,expected_candidate,
                   registry_blob,decisions,payloads,release_request_bytes=None):
    result=dict(schema_version='1',layer='permission_proposal',status='failed',
                authority='proposal_only',overall_admission='not_evaluated',
                transition_allowed=False,release_allowed=False,export_allowed=False,
                activation_allowed=False,performed=False,checks=[],diagnostics=[],
                not_checked=['owner_authentication','coverage_claim_truth','agent_behavior',
                             'target_environment','global_event_completeness','source_acquisition_boundary',
                             'release_decision_semantics','publication','activation'])
    try:
        if not _pinned(proposal_bytes,expected_proposal):raise _Stop('PROPOSAL_REFERENCE_MISMATCH')
        try:
            candidate_check,parse,validator,binding=_load()
        except (OSError,ImportError,RuntimeError,ValueError,KeyError):
            result['status']='unsupported';result['diagnostics']=[dict(code='INSTALLED_PROFILE_UNAVAILABLE')];return result
        request=_proposal(proposal_bytes,expected_proposal,parse,validator)
        if (not _pinned(candidate_bytes,expected_candidate) or request['candidate']!=expected_candidate):
            raise _Stop('CANDIDATE_REFERENCE_MISMATCH')
        if type(registry_blob) is not bytes or len(registry_blob)>LIMIT or request['registry']!=reference(registry_blob):
            raise _Stop('REGISTRY_REFERENCE_MISMATCH')
        if type(decisions) is not dict or type(payloads) is not dict:raise _Stop('INPUT_TYPE')
        decisions,payloads=dict(decisions),dict(payloads)
        if (len(decisions)+len(payloads)+1>10000
                or any(type(p) is not str or type(b) is not bytes or len(b)>LIMIT for p,b in [*decisions.items(),*payloads.items()])
                or len(registry_blob)+sum(map(len,decisions.values()))+sum(map(len,payloads.values()))>64*1024*1024):
            raise _Stop('INPUT_TYPE_OR_LIMIT')
        refs=[dict(path=p,**reference(b)) for p,b in sorted(decisions.items())]
        if request['decisions']!=refs:raise _Stop('DECISION_REFERENCE_MISMATCH')
        if request['action']=='release':
            if release_request_bytes is not None:raise _Stop('UNEXPECTED_PARENT')
        else:
            parent=_proposal(release_request_bytes,request['release_request'],parse,validator)
            if parent['action']!='release' or parent['request_id']==request['request_id']:raise _Stop('INVALID_RELEASE_PARENT')
            for field in ['candidate','registry','decisions']:
                if parent[field]!=request[field]:raise _Stop('PARENT_SNAPSHOT_MISMATCH')
            if request['export_paths']!=sorted(payloads):raise _Stop('EXPORT_PATH_SET_MISMATCH')
        result['checks'].append('proposal_snapshot_and_parent_binding')
        candidate_result=candidate_check(candidate_bytes,expected_candidate,registry_blob,decisions,payloads)
        if candidate_result['status']!='consistent_incomplete_candidate':
            result['status']=candidate_result['status'];result['diagnostics']=candidate_result['diagnostics'];return result
        result['checks'].append('candidate_consistency_not_readiness')
        candidate=parse(candidate_bytes)
        actions=[('release','agent_system.release'),('export','agent_system.transfer')] if request['action']=='export' else [('release','agent_system.release')]
        for operation,area in actions:
            scoped=binding(registry_blob,decisions,payloads,candidate['roots'],operation=operation,area=area)
            if scoped['status']!='passed_known_inputs':
                result['status']=scoped['status'];result['diagnostics']=([dict(code='KNOWN_SCOPE_BLOCK')] if scoped['status']=='blocked_known_scope' else scoped['diagnostics']);return result
        result['checks'].append('known_requested_scopes_only')
        result['status']='blocked_incomplete_candidate'
        result['diagnostics']=[dict(code='INCOMPLETE_CORE_COVERAGE'),dict(code='POSITIVE_PERMISSION_PATH_UNIMPLEMENTED')]
    except _Stop as error:
        result['diagnostics']=[dict(code=error.code)]
    except (ValueError,TypeError,KeyError,AttributeError,RuntimeError,RecursionError):
        result['diagnostics']=[dict(code='PROPOSAL_OR_INPUT_INVALID')]
    return result
