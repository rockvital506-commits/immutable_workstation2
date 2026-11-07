#!/usr/bin/env python3
"""Execute one externally pinned plan; local evidence, never admission or writes."""
import copy
import hashlib
import json
from pathlib import Path
import re
import runpy
import uuid

BASE = Path(__file__).resolve().parents[3]
PROFILE = 'linux-observed-set-5r3-6r3'
LIMIT = 16 * 1024 * 1024
PINS = {'adapters/ent-0005/r0003/reader.py': {'sha256': '0ddfb68d81eaf9e3ba56ca20b909462958b8e9de938d230a02d3a14e8b76fc7f', 'size_bytes': 15565}, 'adapters/ent-0005/r0003/usage.md': {'sha256': '489b9247257472d69ec0266a031edcac09d38e00c117de627a3a38d837262f14', 'size_bytes': 12063}, 'adapters/ent-0005/r0003/verify.py': {'sha256': '3a8faf2098e99433223678f2dee92e94af3b511ccc946998024e98c943e55336', 'size_bytes': 22384}, 'catalog/contracts/agent_system/ent-0001/r0001.md': {'sha256': '684e18cc01dc6b1ffd66899615df03b01e756f40f1354f3ac82a81563a944773', 'size_bytes': 7564}, 'catalog/contracts/agent_system/ent-0002/r0003.md': {'sha256': 'bfdea24314d9f5b26cd54ddaa41fe9aea9843c0f669417c040c1c80991188a1a', 'size_bytes': 17780}, 'specification/ent-0003/r0002/catalog-base.schema.json': {'sha256': '42fab3c453930ad9128b2b422837b82d84db9ed6092872765bd7fe1ffaf9a820', 'size_bytes': 8696}, 'specification/ent-0003/r0002/usage.md': {'sha256': 'a8e6c818ec4bda9eb4d38b3b9abb8ec9e3d694a42329771109931bbc8c5c6ceb', 'size_bytes': 9053}, 'specification/ent-0007/r0001/decision-events.schema.json': {'sha256': '4cce54eaff0d12e1e59a4aeb0eb1dd9f0f0b951f43968317c70adb7c714005c1', 'size_bytes': 12322}, 'specification/ent-0007/r0001/events.py': {'sha256': '26a7dee29f5f5196fd458da90246f343035f2843bed5434f2e71340abb0eaabe', 'size_bytes': 11016}, 'specification/ent-0007/r0001/usage.md': {'sha256': 'ddaa2074aa5dfe6595f95b24f0e937871a2430be84f9a2c416f87d5d2974b4df', 'size_bytes': 10376}, 'specification/ent-0007/r0001/verify.py': {'sha256': 'fca460f867777250da0348845bbedc1cc6804a57988abfb1c50f6db32dc18378', 'size_bytes': 13994}, 'specification/ent-0008/r0001/usage.md': {'sha256': 'f775530264c1fa0a76b368a264ce4b343405b6b7b6b0e1a39002e97ea3ea0c65', 'size_bytes': 14765}, 'specification/ent-0008/r0001/validation-plan.schema.json': {'sha256': 'e53e11315ebe54566edc5a395e7c4eee57cb82bdac86f9573feed57a0602664b', 'size_bytes': 3590}, 'specification/ent-0008/r0001/validation-run-report.schema.json': {'sha256': '7dece17f75d695484b2814c89f17f4e1623f6fec033d24c92953c740540da8bc', 'size_bytes': 15972}, 'specification/ent-0008/r0001/verify.py': {'sha256': '7196efe0f6b59f74ba791f80f497ce827d517d344e2c84556991db2f7f54a026', 'size_bytes': 14770}, 'validation/ent-0004/r0002/requirements-linux-cp311.lock': {'sha256': '4f0eda8261647c9bc18d2f013ef914737290e20c6a82de15f476108b6a528e71', 'size_bytes': 746}, 'validation/ent-0004/r0002/usage.md': {'sha256': '78807c10e4ad843472a1413df661c27cdbbd92a889446a000fbc1e9566e1d369', 'size_bytes': 7567}, 'validation/ent-0004/r0002/verify.py': {'sha256': '1523ca399a9aee8f89656591b62e1d776504385fe025131c818c694ebb32aedf', 'size_bytes': 10872}, 'validation/ent-0006/r0003/check.py': {'sha256': 'd94e2c85c2bd40ff31b5d7edd2f0c9755cf5eb3ce6ab42488aeaff4feb8c275c', 'size_bytes': 12042}, 'validation/ent-0006/r0003/usage.md': {'sha256': '89b80b152f5651bdf6ba1880b24f7175a0e7e2c9fa9915e2b306993204d9bff3', 'size_bytes': 13351}, 'validation/ent-0006/r0003/verify.py': {'sha256': '9a76cb7cb7d6bb5c5aefdba003cf9c57979ae2f3f9d626dd6e2aeb54ee674e51', 'size_bytes': 18332}}  # Fixed installed closure, not source-selected.


class PlanBlocked(Exception):
    def __init__(self, code, unsupported=False):
        self.code, self.unsupported = code, unsupported
        super().__init__(code)


def reference(data):
    return dict(sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))


def _encode(value):
    data = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    if len(data) > LIMIT:
        raise PlanBlocked('DOCUMENT_LIMIT')
    return data


def _load():
    try:
        for path, expected in PINS.items():
            with (BASE / path).open('rb') as stream:
                data = stream.read(expected['size_bytes'] + 1)
            if reference(data) != expected:
                raise PlanBlocked('INSTALLED_PROFILE_CHANGED', True)
        contract = runpy.run_path(str(BASE / 'specification/ent-0008/r0001/verify.py'))
        parse, validators, _ = contract['load']()
        reader = runpy.run_path(str(BASE / 'adapters/ent-0005/r0003/reader.py'))
        binding = runpy.run_path(str(BASE / 'validation/ent-0006/r0003/check.py'))
        return parse, validators, reader, binding['check_catalog'], contract['NOT_CHECKED']
    except PlanBlocked:
        raise
    except (ImportError, OSError, ValueError, KeyError, RuntimeError):
        raise PlanBlocked('INSTALLED_PROFILE_UNAVAILABLE', True) from None


def _plan(data, expected, parse, validator):
    if type(data) is not bytes or len(data) > LIMIT:
        raise PlanBlocked('INVALID_PLAN_BYTES_OR_LIMIT')
    if (type(expected) is not dict or set(expected) != {'sha256', 'size_bytes'}
            or type(expected['size_bytes']) is not int
            or not isinstance(expected['sha256'], str)
            or re.fullmatch('[0-9a-f]{64}', expected['sha256']) is None):
        raise PlanBlocked('INVALID_PLAN_REFERENCE')
    if reference(data) != expected:
        raise PlanBlocked('PLAN_REFERENCE_MISMATCH')
    try:
        if not data.endswith(b'\n') or data.endswith(b'\n\n') or b'\r' in data:
            raise PlanBlocked('PLAN_SERIALIZATION')
        value = parse(data)
        if not validator.is_valid(value):
            raise PlanBlocked('PLAN_SCHEMA')
        entries = [value['registry'], *value['artifacts'], *value['decisions']]
        if len(entries) > 10000:
            raise PlanBlocked('PLAN_SET_LIMIT')
        if len({a['path'] for a in entries}) != len(entries):
            raise PlanBlocked('PLAN_DUPLICATE_PATH')
        if any(type(a['size_bytes']) is not int for a in entries):
            raise PlanBlocked('PLAN_SIZE_TYPE')
        if sum(a['size_bytes'] for a in entries) > 64 * 1024 * 1024:
            raise PlanBlocked('PLAN_SET_LIMIT')
        if any(s['catalog_id'] != value['catalog_id'] for s in value['selection']):
            raise PlanBlocked('PLAN_CATALOG_MISMATCH')
        return value
    except PlanBlocked:
        raise
    except (ValueError, TypeError, KeyError, RecursionError):
        raise PlanBlocked('PLAN_PARSE_OR_SCHEMA') from None


def _records(entries):
    if type(entries) is not list or any(type(a) is not dict for a in entries):
        raise PlanBlocked('CHILD_INPUT_MISMATCH')
    mapped = {a['path']: a for a in entries}
    if len(mapped) != len(entries):
        raise PlanBlocked('CHILD_INPUT_MISMATCH')
    return mapped


def _acquired(captured, plan):
    groups = [(captured['artifacts'], [plan['registry'], *plan['artifacts']]),
              (captured['decisions'], plan['decisions'])]
    for blobs, entries in groups:
        if type(blobs) is not dict or set(blobs) != {a['path'] for a in entries}:
            raise PlanBlocked('CHILD_INPUT_MISMATCH')
        for a in entries:
            data = blobs[a['path']]
            if type(data) is not bytes or reference(data) != {k: a[k] for k in ('sha256', 'size_bytes')}:
                raise PlanBlocked('CHILD_INPUT_MISMATCH')
    evidence = captured['evidence']
    expected = [plan['registry'], *plan['artifacts'], *plan['decisions']]
    if (evidence['layer'] != 'planned_source_acquisition'
            or evidence['source_consistency'] != 'mutable_tree_observations'
            or _records(evidence['inputs']) != _records(expected)
            or evidence['same_root_capability'] is not True
            or evidence['directory_before'] != evidence['directory_after']
            or evidence['directory_before']['entries'] != sorted(a['path'].split('/')[-1] for a in plan['decisions'])
            or evidence['overall_admission'] != 'not_evaluated' or evidence['transition_allowed'] is not False):
        raise PlanBlocked('CHILD_INPUT_MISMATCH')


def _bound(child, plan):
    if child['status'] not in ('passed_known_inputs', 'blocked_known_scope', 'failed', 'unsupported'):
        raise PlanBlocked('CHILD_RESULT_MISMATCH')
    if child['overall_admission'] != 'not_evaluated' or child['transition_allowed'] is not False:
        raise PlanBlocked('CHILD_RESULT_MISMATCH')
    if child['status'] in ('passed_known_inputs', 'blocked_known_scope'):
        expected = [{k: a[k] for k in ('path', 'sha256', 'size_bytes')}
                    for a in [plan['registry'], *plan['artifacts'], *plan['decisions']]]
        event = child['restriction_evaluation']
        context = event['context']
        decision_inputs = [{k: a[k] for k in ('path', 'sha256', 'size_bytes')} for a in plan['decisions']]
        if (child['layer'] != 'catalog_binding_and_graph'
                or child['source_consistency'] != 'mutable_tree_observations'
                or event['layer'] != 'known_entity_decisions'
                or _records(event['inputs']) != _records(decision_inputs)
                or bool(event['active_blocks']) != (child['status'] == 'blocked_known_scope')
                or _records(child['inputs']) != _records(expected)
                or context['operation'] != plan['context']['operation']
                or context['area'] != plan['context']['area']
                or context['subjects'] != child['selected_closure']
                or any(s not in child['selected_closure'] for s in plan['selection'])
                or event['transition_allowed'] is not False
                or event['overall_admission'] != 'not_evaluated'
                or event['status'] != ('no_known_block_in_scope' if child['status'] == 'passed_known_inputs'
                                       else 'blocked_known_scope')):
            raise PlanBlocked('CHILD_RESULT_MISMATCH')


def execute_plan(root, plan_bytes, expected_plan):
    """Preflight raises PlanBlocked; a validated run returns bytes/content-addressed docs.

    Trusted installed namespace must not be writable by the untrusted source.
    No arbitrary child reports/callbacks are accepted, no filesystem writes.
    """
    parse, (plan_validator, report_validator), reader, checker, not_checked = _load()
    plan = _plan(plan_bytes, copy.deepcopy(expected_plan), parse, plan_validator)
    documents = {reference(plan_bytes)['sha256']: plan_bytes}
    report = dict(schema_version='1', kind='validation_run_report', run_id=str(uuid.uuid4()),
                  plan_id=plan['plan_id'], plan=reference(plan_bytes), execution_profile=PROFILE,
                  source_consistency='mutable_tree_observations', status='incomplete',
                  overall_admission='not_evaluated', transition_allowed=False,
                  stages={name: dict(status='not_run', diagnostics=[]) for name in ['acquisition', 'binding']},
                  not_checked=list(not_checked))
    stage = 'acquisition'
    try:
        captured = reader['read_set'](root, [plan['registry'], *plan['artifacts']], plan['decisions'])
        _acquired(captured, plan)
        raw = _encode(captured['evidence'])
        documents[reference(raw)['sha256']] = raw
        report['stages'][stage] = dict(status='passed_known_inputs', evidence=reference(raw), diagnostics=[])
        stage = 'binding'
        payloads = dict(captured['artifacts'])
        registry = payloads.pop('catalog/registry.json')
        if parse(registry)['catalog_id'] != plan['catalog_id']:
            raise PlanBlocked('SOURCE_CATALOG_MISMATCH')
        child = checker(registry, captured['decisions'], payloads, copy.deepcopy(plan['selection']),
                        **plan['context'])
        _bound(child, plan)
        raw = _encode(child)
        documents[reference(raw)['sha256']] = raw
        status = child['status']
        diagnostics = ([dict(code='KNOWN_SCOPE_BLOCK')] if status == 'blocked_known_scope'
                       else child['diagnostics'])
        report['stages'][stage] = dict(status=status, evidence=reference(raw), diagnostics=diagnostics)
        report['status'] = status
    except reader['ReadBlocked'] as error:
        report['status'] = 'unsupported' if error.code == 'UNSUPPORTED_PLATFORM' else 'failed'
        report['stages'][stage] = dict(status=report['status'], diagnostics=[dict(code=error.code)])
    except PlanBlocked as error:
        report['status'] = 'unsupported' if error.unsupported else 'failed'
        report['stages'][stage] = dict(status=report['status'], diagnostics=[dict(code=error.code)])
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, RecursionError):
        report['status'] = 'failed'
        report['stages'][stage] = dict(status='failed', diagnostics=[dict(code='STAGE_UNAVAILABLE')])
    if not report_validator.is_valid(report):
        raise PlanBlocked('RUN_ENVELOPE_INVALID')
    return dict(report_bytes=_encode(report), documents=documents)
