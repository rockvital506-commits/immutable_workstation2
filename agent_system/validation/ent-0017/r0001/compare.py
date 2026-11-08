#!/usr/bin/env python3
"""Compare pinned archived/current-declared byte views without granting permission."""
import hashlib
import json
from pathlib import Path
import re
import runpy
import uuid

BASE=Path(__file__).resolve().parents[3]
PINS={'staging/ent-0016/r0001/read.py': {'sha256': '942839d7e292cd7f744346f27693cd4e7cc573961d1599f66df4c566548545cf', 'size_bytes': 9691}, 'staging/ent-0016/r0001/verify.py': {'sha256': 'f06e8a76da5f2c9005934d47b0f439b4b8751a0bc50a921bd773bbbd6305967f', 'size_bytes': 11917}, 'staging/ent-0016/r0001/usage.md': {'sha256': '3dccac0b1705a6a9723d8d72228733010c710a2e3a012ad84c1412b3e6210251', 'size_bytes': 12738}}
LIMIT=16*1024*1024


class _Stop(Exception):
    def __init__(self,code):self.code=code


def reference(raw):return dict(sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))


def encode(value):return (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()


def _keys(value,keys):
    if type(value) is not dict or set(value)!=set(keys.split()):raise _Stop('COMPARISON_SHAPE')


def _pin(raw,expected):
    return (type(raw) is bytes and len(raw)<=LIMIT and type(expected) is dict
            and set(expected)=={'sha256','size_bytes'} and type(expected['sha256']) is str
            and type(expected['size_bytes']) is int and reference(raw)==expected)


def _load():
    for path,expected in PINS.items():
        with (BASE/path).open('rb') as stream:raw=stream.read(expected['size_bytes']+1)
        if reference(raw)!=expected:raise RuntimeError('Installed trial reader changed')
    reader=runpy.run_path(str(BASE/'staging/ent-0016/r0001/read.py'))
    stage,check,parse,binding=reader['_load']()
    return reader,stage,check,parse,binding


def _json(raw,parse):
    if not raw.endswith(b'\n') or raw.endswith(b'\n\n') or b'\r' in raw:raise _Stop('JSON_SERIALIZATION')
    return parse(raw)


def compare_views(plan_bytes,expected_plan,manifest_bytes,objects,current_registry,current_decisions):
    result=dict(schema_version='1',layer='known_view_comparison',status='failed',
                overall_admission='not_evaluated',current_permissions='not_evaluated',
                transition_allowed=False,release_allowed=False,export_allowed=False,activation_allowed=False,
                performed=False,diagnostics=[],not_checked=['plan_authentication','source_authentication',
                'view_freshness','global_event_completeness','physical_trial_acquisition','execution_authentication',
                'coverage_claim_truth','agent_behavior','target_environment','release_permission','activation_permission'])
    reader=None
    try:
        if not _pin(plan_bytes,expected_plan):raise _Stop('PLAN_REFERENCE_MISMATCH')
        if type(objects) is not dict or type(current_decisions) is not dict:raise _Stop('INPUT_MAP_TYPE')
        objects,current_decisions=dict(objects),dict(current_decisions)
        if (len(objects)>10001 or len(current_decisions)>10000
                or any(type(p) is not str or type(b) is not bytes or len(b)>LIMIT for p,b in [*objects.items(),*current_decisions.items()])
                or sum(map(len,objects.values()))>80*1024*1024
                or sum(map(len,current_decisions.values()))>64*1024*1024):raise _Stop('INPUT_TYPE_OR_LIMIT')
        try:reader,stage,check,parse,binding=_load()
        except (OSError,ValueError,RuntimeError,ImportError,KeyError):
            result['status']='unsupported';result['diagnostics']=[dict(code='INSTALLED_PROFILE_UNAVAILABLE')];return result
        plan=_json(plan_bytes,parse)
        _keys(plan,'schema_version kind plan_id archive_manifest current_registry current_decisions context')
        if plan['schema_version']!='1' or plan['kind']!='known_view_comparison_plan':raise _Stop('PLAN_PROFILE')
        if type(plan['plan_id']) is not str or str(uuid.UUID(plan['plan_id']))!=plan['plan_id']:raise _Stop('PLAN_ID')
        _keys(plan['context'],'operation area')
        if any(type(v) is not str or re.fullmatch('[a-z][a-z0-9_.-]{0,255}',v) is None for v in plan['context'].values()):
            raise _Stop('QUERY_CONTEXT')
        if not _pin(manifest_bytes,plan['archive_manifest']):raise _Stop('ARCHIVE_MANIFEST_REFERENCE')
        if not _pin(current_registry,plan['current_registry']):raise _Stop('CURRENT_REGISTRY_REFERENCE')
        reader['_entries'](plan['current_decisions'])
        declared=[dict(path=p,**reference(b)) for p,b in sorted(current_decisions.items())]
        if plan['current_decisions']!=declared:raise _Stop('CURRENT_DECISION_REFERENCES')
        manifest=_json(manifest_bytes,parse)
        reader['_keys'](manifest,'schema_version profile kind run_id candidate registry payloads decisions readiness release_allowed export_allowed activation_allowed transition_allowed overall_admission')
        if (manifest['schema_version']!='1' or manifest['profile']!=stage['PROFILE'] or manifest['kind']!='incomplete_trial_snapshot'
                or type(manifest['run_id']) is not str or str(uuid.UUID(manifest['run_id']))!=manifest['run_id']):raise _Stop('ARCHIVE_PROFILE')
        if (manifest['readiness']!='incomplete_candidate' or manifest['overall_admission']!='not_evaluated'
                or any(manifest[f] is not False for f in ['release_allowed','export_allowed','activation_allowed','transition_allowed'])):
            raise _Stop('ARCHIVE_PERMISSION_CLAIM')
        reader['_ref'](manifest['candidate']);reader['_ref'](manifest['registry'])
        reader['_entries'](manifest['payloads']);reader['_entries'](manifest['decisions'])
        if (len(manifest['payloads'])+len(manifest['decisions'])+1>10000
                or sum(r['size_bytes'] for r in [manifest['registry'],*manifest['payloads'],*manifest['decisions']])>64*1024*1024):
            raise _Stop('ARCHIVE_SET_LIMIT')
        expected={}
        for row in [manifest['candidate'],manifest['registry'],*manifest['payloads'],*manifest['decisions']]:
            r={k:row[k] for k in ['sha256','size_bytes']};sha=r['sha256']
            if sha in expected and expected[sha]!=r:raise _Stop('ARCHIVE_OBJECT_CONFLICT')
            expected[sha]=r
        if set(objects)!=set(expected):raise _Stop('ARCHIVE_OBJECT_SET')
        if any(reference(objects[p])!=r for p,r in expected.items()):raise _Stop('ARCHIVE_OBJECT_BYTES')
        candidate=objects[manifest['candidate']['sha256']];archived_registry=objects[manifest['registry']['sha256']]
        payloads={r['path']:objects[r['sha256']] for r in manifest['payloads']}
        archived_decisions={r['path']:objects[r['sha256']] for r in manifest['decisions']}
        if len(current_registry)+sum(map(len,current_decisions.values()))+sum(map(len,payloads.values()))>64*1024*1024:
            raise _Stop('CURRENT_SET_LIMIT')
        archived=check(candidate,manifest['candidate'],archived_registry,archived_decisions,payloads)
        if archived['status']!='consistent_incomplete_candidate':
            result['status']=archived['status'];result['diagnostics']=archived['diagnostics'];return result
        for p,b in archived_decisions.items():
            if p not in current_decisions or current_decisions[p]!=b:raise _Stop('ARCHIVED_DECISION_NOT_RETAINED')
        old,new=parse(archived_registry),parse(current_registry)
        if old['catalog_id']!=new['catalog_id']:raise _Stop('CATALOG_ID_CHANGED')
        records={(e['entity_id'],v['revision']):v for e in new['entities'] for v in e['revisions']}
        for e in old['entities']:
            for v in e['revisions']:
                key=(e['entity_id'],v['revision'])
                if key not in records or json.dumps(v,sort_keys=True,allow_nan=False)!=json.dumps(records[key],sort_keys=True,allow_nan=False):raise _Stop('ARCHIVED_RECORD_NOT_RETAINED')
        current=check(candidate,manifest['candidate'],current_registry,current_decisions,payloads)
        if current['status']!='consistent_incomplete_candidate':
            result['status']=current['status'];result['diagnostics']=current['diagnostics'];return result
        roots=parse(candidate)['roots']
        before=binding(archived_registry,archived_decisions,payloads,roots,**plan['context'])
        after=binding(current_registry,current_decisions,payloads,roots,**plan['context'])
        if before['status'] not in ['passed_known_inputs','blocked_known_scope']:
            result['status']=before['status'];result['diagnostics']=before['diagnostics'];return result
        result.update(archive_query=before['status'],declared_query=after['status'],
                      known_view_relation='declared_extension',plan=dict(expected_plan),
                      added_decisions=len(current_decisions)-len(archived_decisions),context=dict(plan['context']))
        if after['status']!='passed_known_inputs':
            result['status']=after['status'];result['diagnostics']=([dict(code='DECLARED_KNOWN_SCOPE_BLOCK')] if after['status']=='blocked_known_scope' else after['diagnostics']);return result
        result['status']='compared_known_views_no_admission'
    except _Stop as error:result['diagnostics']=[dict(code=error.code)]
    except (OSError,ValueError,TypeError,KeyError,AttributeError,RuntimeError,RecursionError):
        result['diagnostics']=[dict(code='COMPARISON_OR_INPUT_INVALID')]
    except Exception as error:
        if reader is None or not isinstance(error,reader['_Stop']):raise
        result['diagnostics']=[dict(code=error.code)]
    return result
