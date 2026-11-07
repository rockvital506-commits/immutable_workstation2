#!/usr/bin/env python3
"""Check consistency of one incomplete candidate profile, never grant readiness."""
import ast
import hashlib
import json
from pathlib import Path
import re
import runpy

BASE = Path(__file__).resolve().parents[3]
ENTRY_PINS = {'validation/ent-0009/r0001/execute.py': {'sha256': '1a4340e4dfe4b01841702ffcb88a65caa0f8ccc05d6adce03c1e4b3d2e6ebdf9', 'size_bytes': 12955}, 'validation/ent-0009/r0001/verify.py': {'sha256': 'a082eeb938a62f4005d83f3664d027c403055c1f7851ff73a3a6517a09f41268', 'size_bytes': 11721}, 'validation/ent-0009/r0001/usage.md': {'sha256': '6c9ed888e4d5538a53521fa4406ce6df50e287718d2c5cc4545882432173425f', 'size_bytes': 11256}}
CORE_SHA = '684e18cc01dc6b1ffd66899615df03b01e756f40f1354f3ac82a81563a944773'
LIMIT = 16 * 1024 * 1024


class _Stop(Exception):
    def __init__(self, code, unsupported=False):
        self.code, self.unsupported = code, unsupported


def _ref(raw):
    return dict(sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))


def _load():
    for path, expected in ENTRY_PINS.items():
        with (BASE/path).open('rb') as stream:
            raw=stream.read(expected['size_bytes']+1)
        if _ref(raw)!=expected:
            raise _Stop('INSTALLED_ENTRY_CHANGED',True)
    entry=runpy.run_path(str(BASE/'validation/ent-0009/r0001/execute.py'))
    try:
        return entry['_load']()
    except entry['PlanBlocked'] as error:
        raise _Stop(error.code,error.unsupported) from None


def _keys(value,keys):
    if type(value) is not dict or set(value)!=set(keys.split()):
        raise _Stop('CANDIDATE_SHAPE')


def _equal(a,b):
    return json.dumps(a,sort_keys=True,ensure_ascii=False,allow_nan=False)==json.dumps(b,sort_keys=True,ensure_ascii=False,allow_nan=False)


def _subject(s):
    return (s['catalog_id'],s['entity_id'],s['revision'])


def _rows(rows,ids):
    if type(rows) is not list or len(rows)!=len(ids) or {r['id'] for r in rows}!=set(ids):
        raise _Stop('COVERAGE_ROW_SET')
    for row in rows:
        _keys(row,'id core_item label status clauses checks gaps')
        expected_item=int(row['id'][1:]) if row['id'].startswith('C') else 1
        if type(row['core_item']) is not int or row['core_item']!=expected_item:
            raise _Stop('CORE_ITEM_MISMATCH')
        allowed=['model_only'] if row['id'].startswith('W') else ['partial','specified_only']
        if row['status'] not in allowed:
            raise _Stop('UNSUPPORTED_COMPLETENESS_CLAIM')
        if type(row['label']) is not str or not row['label'].strip():
            raise _Stop('CANDIDATE_SHAPE')
        for field in ['clauses','checks','gaps']:
            if type(row[field]) is not list or not 1<=len(row[field])<=100:
                raise _Stop('COVERAGE_DETAIL_MISSING')
        for gap in row['gaps']:
            _keys(gap,'code detail')
            if (type(gap['code']) is not str or re.fullmatch('[A-Z][A-Z0-9_]{0,95}',gap['code']) is None
                    or type(gap['detail']) is not str or not gap['detail'].strip()):
                raise _Stop('COVERAGE_GAP_SHAPE')


def _reference(reference,components,payloads,subject_validator,cache,parse):
    _keys(reference,'subject path reference_type locator')
    if not subject_validator.is_valid(reference['subject']):
        raise _Stop('INVALID_REFERENCE_SUBJECT')
    key=_subject(reference['subject'])
    if key not in components or type(reference['path']) is not str:
        raise _Stop('REFERENCE_OUTSIDE_COMPONENTS')
    path=reference['path']
    if path not in {a['path'] for a in components[key]['artifacts']}:
        raise _Stop('REFERENCE_OUTSIDE_COMPOSITION')
    locator=reference['locator']
    if type(locator) is not str or not locator or len(locator)>1024:
        raise _Stop('INVALID_LOCATOR')
    kind=reference['reference_type']
    if kind=='section':
        found=locator in payloads[path].decode('utf-8').splitlines() and locator.startswith('## ')
    elif kind=='test':
        if path not in cache:
            cache[path]={n.name for n in ast.walk(ast.parse(payloads[path].decode('utf-8'))) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        found=locator in cache[path] and locator.startswith('test_')
    elif kind=='scenario':
        cases=parse(payloads[path])
        if cases.get('verification_level')!='model_review' or cases.get('agent_behavior_verified') is not False:
            raise _Stop('SCENARIO_LEVEL_MISMATCH')
        found=locator in {case['case_id'] for case in cases['cases']}
    else:
        raise _Stop('REFERENCE_TYPE_UNSUPPORTED')
    if not found:
        raise _Stop('LOCATOR_NOT_FOUND')


def check_candidate(candidate_bytes,expected_candidate,registry_blob,decisions,payloads):
    result=dict(schema_version='1',layer='incomplete_candidate_coverage',status='failed',
                overall_admission='not_evaluated',transition_allowed=False,compatible_release_allowed=False,
                export_allowed=False,activation_allowed=False,core_coverage='not_evaluated',
                checks=[],blockers=[],diagnostics=[],not_checked=['coverage_claim_truth','agent_behavior',
                'target_environment','source_acquisition_boundary','source_authentication',
                'global_event_completeness','release_permission','export_permission','activation_permission'])
    try:
        if type(candidate_bytes) is not bytes or len(candidate_bytes)>LIMIT:
            raise _Stop('CANDIDATE_BYTES_OR_LIMIT')
        if (type(expected_candidate) is not dict or set(expected_candidate)!={'sha256','size_bytes'}
                or type(expected_candidate['size_bytes']) is not int or _ref(candidate_bytes)!=expected_candidate):
            raise _Stop('CANDIDATE_REFERENCE_MISMATCH')
        if (type(registry_blob) is not bytes or len(registry_blob)>LIMIT or type(decisions) is not dict or type(payloads) is not dict
                or len(decisions)+len(payloads)+1>10000):
            raise _Stop('INPUT_TYPE_OR_LIMIT')
        decisions,payloads=dict(decisions),dict(payloads)
        if (any(type(b) is not bytes or len(b)>LIMIT for b in [*decisions.values(),*payloads.values()])
                or len(registry_blob)+sum(map(len,decisions.values()))+sum(map(len,payloads.values()))>64*1024*1024):
            raise _Stop('INPUT_TYPE_OR_LIMIT')
        parse,(plan_validator,_),_,checker,_=_load()
        if not candidate_bytes.endswith(b'\n') or candidate_bytes.endswith(b'\n\n') or b'\r' in candidate_bytes:
            raise _Stop('CANDIDATE_SERIALIZATION')
        candidate=parse(candidate_bytes)
        _keys(candidate,'schema_version kind profile candidate_id descriptor_subject descriptor_in_payload core_subject context roots components coverage conditions readiness blocked_transitions overall_admission transition_allowed compatible_release_allowed export_allowed activation_allowed')
        if (candidate['schema_version']!='1' or candidate['kind']!='incomplete_candidate_specification'
                or candidate['profile']!='core-candidate-13r1'):
            raise _Stop('CANDIDATE_PROFILE_UNSUPPORTED',True)
        for flag in ['descriptor_in_payload','transition_allowed','compatible_release_allowed','export_allowed','activation_allowed']:
            if candidate[flag] is not False:raise _Stop('CANDIDATE_PERMISSION_CLAIM')
        if (candidate['overall_admission']!='not_evaluated' or candidate['readiness']!='incomplete_candidate'
                or candidate['blocked_transitions']!=['compatible_release','export','activation']
                or candidate['context']!=dict(operation='validate',area='agent_system.candidate')):
            raise _Stop('CANDIDATE_GATE_MISMATCH')
        subject_validator=plan_validator.evolve(schema={'$ref':'urn:agent-system:schema:catalog-base:1#/$defs/subject'})
        uuid_validator=plan_validator.evolve(schema={'$ref':'urn:agent-system:schema:catalog-base:1#/$defs/uuid'})
        if not uuid_validator.is_valid(candidate['candidate_id']):raise _Stop('CANDIDATE_ID')
        for s in [candidate['descriptor_subject'],candidate['core_subject']]:
            if not subject_validator.is_valid(s):raise _Stop('CANDIDATE_SUBJECT')
        cid=candidate['core_subject']['catalog_id']
        if (candidate['core_subject']!=dict(catalog_id=cid,entity_id='ENT-0001',revision='r0001')
                or candidate['descriptor_subject']!=dict(catalog_id=cid,entity_id='ENT-0013',revision='r0001')):
            raise _Stop('CANDIDATE_SUBJECT')
        if type(candidate['components']) is not list or not 1<=len(candidate['components'])<=10000:
            raise _Stop('COMPONENT_SET')
        components={}
        revision_validator=plan_validator.evolve(schema={'$ref':'urn:agent-system:schema:catalog-base:1#/$defs/revision'})
        for component in candidate['components']:
            _keys(component,'subject record');s=component['subject'];record=component['record']
            if (not subject_validator.is_valid(s) or s['catalog_id']!=cid or not revision_validator.is_valid(record)
                    or record['revision']!=s['revision'] or _subject(s) in components):raise _Stop('COMPONENT_SET')
            components[_subject(s)]=record
        if _subject(candidate['descriptor_subject']) in components:raise _Stop('DESCRIPTOR_SELF_INCLUSION')
        registry=parse(registry_blob)
        if registry['catalog_id']!=cid:raise _Stop('REGISTRY_CATALOG_MISMATCH')
        actual={(cid,e['entity_id'],v['revision']):v for e in registry['entities'] for v in e['revisions']}
        for key,record in components.items():
            if key not in actual or not _equal(record,actual[key]):raise _Stop('FROZEN_COMPONENT_MISMATCH')
        artifact_paths=[a['path'] for v in components.values() for a in v['artifacts']]
        if len(set(artifact_paths))!=len(artifact_paths) or set(payloads)!=set(artifact_paths):raise _Stop('PAYLOAD_SET_MISMATCH')
        roots=candidate['roots']
        if (type(roots) is not list or not 1<=len(roots)<=10000
                or any(not subject_validator.is_valid(s) or _subject(s) not in components for s in roots)
                or len({_subject(s) for s in roots})!=len(roots)):
            raise _Stop('ROOT_SET')
        parent=checker(registry_blob,decisions,payloads,roots,**candidate['context'])
        if parent['status']!='passed_known_inputs':
            result['status']=parent['status'];result['diagnostics']=([dict(code='KNOWN_SCOPE_BLOCK')] if parent['status']=='blocked_known_scope' else parent['diagnostics']);return result
        if {_subject(s) for s in parent['selected_closure']}!=set(components):raise _Stop('CLOSURE_MISMATCH')
        core_path='catalog/contracts/agent_system/ent-0001/r0001.md'
        if hashlib.sha256(payloads[core_path]).hexdigest()!=CORE_SHA:raise _Stop('CORE_CHANGED')
        result['checks'].extend(['frozen_component_records','known_input_binding_and_scope','exact_payload_and_closure'])
        _rows(candidate['coverage'],[f'G{i:02d}' for i in range(1,8)]+[f'W{i:02d}' for i in range(1,10)])
        _rows(candidate['conditions'],[f'C{i:02d}' for i in range(2,11)])
        cache={}
        for row in [*candidate['coverage'],*candidate['conditions']]:
            for reference in row['clauses']:
                if reference.get('reference_type')!='section':raise _Stop('CLAUSE_REFERENCE_TYPE')
                _reference(reference,components,payloads,subject_validator,cache,parse)
            for check in row['checks']:
                _keys(check,'reference level result')
                if check['result']!='defined_only' or check['level'] not in ['document_structure','model_review','bounded_fixture_execution']:
                    raise _Stop('UNATTESTED_CHECK_RESULT')
                reference=check['reference']
                if reference.get('reference_type') not in ['scenario','test']:
                    raise _Stop('CHECK_REFERENCE_TYPE')
                if (reference['reference_type']=='scenario') != (check['level']=='model_review'):
                    raise _Stop('CHECK_LEVEL_MISMATCH')
                _reference(reference,components,payloads,subject_validator,cache,parse)
            result['blockers'].append(dict(id=row['id'],gap_count=len(row['gaps'])))
        result['checks'].extend(['coverage_and_contract_row_sets','reference_locations_only','incomplete_gates'])
        result['core_coverage']='incomplete';result['status']='consistent_incomplete_candidate'
    except _Stop as error:
        result['status']='unsupported' if error.unsupported else 'failed';result['diagnostics']=[dict(code=error.code)]
    except ImportError:
        result['status']='unsupported';result['diagnostics']=[dict(code='ENGINE_UNAVAILABLE')]
    except (OSError,ValueError,TypeError,KeyError,RuntimeError,RecursionError,SyntaxError,AttributeError):
        result['diagnostics']=[dict(code='CANDIDATE_OR_INPUT_INVALID')]
    return result
