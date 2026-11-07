#!/usr/bin/env python3
"""Offline consistency of recorded claims and supplied payload bytes, not execution proof."""
import hashlib
import json
from pathlib import Path
import re
import runpy
import stat

BASE = Path(__file__).resolve().parents[3]
LIMIT = 16 * 1024 * 1024
ENTRY_PINS = {'validation/ent-0009/r0001/execute.py': {'sha256': '1a4340e4dfe4b01841702ffcb88a65caa0f8ccc05d6adce03c1e4b3d2e6ebdf9', 'size_bytes': 12955}, 'validation/ent-0009/r0001/verify.py': {'sha256': 'a082eeb938a62f4005d83f3664d027c403055c1f7851ff73a3a6517a09f41268', 'size_bytes': 11721}, 'validation/ent-0009/r0001/usage.md': {'sha256': '6c9ed888e4d5538a53521fa4406ce6df50e287718d2c5cc4545882432173425f', 'size_bytes': 11256}}
NOT_CHECKED = ['execution_authentication', 'source_observation_truth', 'plan_authentication',
               'source_authentication', 'global_event_completeness', 'core_coverage',
               'environment_compatibility', 'release_permission', 'activation_permission',
               'semantic_correction_resolution', 'release_decisions']


class _Stop(Exception):
    def __init__(self, code, unsupported=False):
        self.code, self.unsupported = code, unsupported


def _ref(data):
    return dict(sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))


def _load():
    for path, expected in ENTRY_PINS.items():
        with (BASE / path).open('rb') as stream:
            data = stream.read(expected['size_bytes'] + 1)
        if _ref(data) != expected:
            raise _Stop('INSTALLED_ENTRY_CHANGED', True)
    entry = runpy.run_path(str(BASE / 'validation/ent-0009/r0001/execute.py'))
    try:
        tools = entry['_load']()
    except entry['PlanBlocked'] as error:
        raise _Stop(error.code, error.unsupported) from None
    return entry, tools


def _parse(raw, parse):
    if type(raw) is not bytes or len(raw) > LIMIT:
        raise _Stop('DOCUMENT_TYPE_OR_LIMIT')
    if not raw.endswith(b'\n') or raw.endswith(b'\n\n') or b'\r' in raw:
        raise _Stop('DOCUMENT_SERIALIZATION')
    return parse(raw)


def _pinned(raw, expected):
    if (type(expected) is not dict or set(expected) != {'sha256', 'size_bytes'}
            or type(expected['size_bytes']) is not int or type(expected['sha256']) is not str
            or re.fullmatch('[0-9a-f]{64}', expected['sha256']) is None
            or _ref(raw) != expected):
        raise _Stop('EXTERNAL_REFERENCE_MISMATCH')


def _directory(value, logical):
    if type(value) is not dict or set(value) != {'path', 'entries', 'links', 'resolved_path', 'device', 'inode', 'fingerprint'}:
        raise _Stop('DIRECTORY_CLAIM_SHAPE')
    if value['path'] != 'catalog/approvals' or type(value['resolved_path']) is not str:
        raise _Stop('DIRECTORY_CLAIM_SHAPE')
    fp = value['fingerprint']
    if (type(fp) is not list or len(fp) != 7 or any(type(n) is not int for n in fp)
            or type(value['device']) is not int or type(value['inode']) is not int
            or value['device'] != fp[0] or value['inode'] != fp[1]
            or fp[0] < 0 or fp[1] < 1 or not stat.S_ISDIR(fp[2]) or fp[3] < 0 or fp[4] < 0):
        raise _Stop('DIRECTORY_CLAIM_SHAPE')
    if type(value['links']) is not list or len(value['links']) > 40:
        raise _Stop('DIRECTORY_CLAIM_SHAPE')
    if value['resolved_path'] != '':
        logical(value['resolved_path'])
    for link in value['links']:
        if (type(link) is not dict or set(link) != {'path', 'link_type', 'target'}
                or link['link_type'] != 'symbolic_link' or type(link['target']) is not str or not link['target']):
            raise _Stop('DIRECTORY_CLAIM_SHAPE')
        logical(link['path'])


def verify_bundle(report_bytes, expected_report, expected_plan, documents, payloads):
    """No root/source locator, writes, network, callbacks or execution of input code.

    payloads is a separate caller-supplied archive of ALL declared file bytes
    when acquisition passed, otherwise empty. It is not produced by ENT-0009.
    """
    result = dict(schema_version='1', layer='recorded_bundle_consistency', status='failed',
                  overall_admission='not_evaluated', transition_allowed=False,
                  recorded_status=None, checks=[], diagnostics=[], not_checked=list(NOT_CHECKED))
    try:
        if type(report_bytes) is not bytes or len(report_bytes) > LIMIT:
            raise _Stop('DOCUMENT_TYPE_OR_LIMIT')
        expected_report = dict(expected_report) if type(expected_report) is dict else expected_report
        expected_plan = dict(expected_plan) if type(expected_plan) is dict else expected_plan
        _pinned(report_bytes, expected_report)
        if type(documents) is not dict or type(payloads) is not dict:
            raise _Stop('BUNDLE_TYPE_OR_LIMIT')
        documents, payloads = dict(documents), dict(payloads)
        if len(documents) > 3 or len(payloads) > 10000:
            raise _Stop('BUNDLE_TYPE_OR_LIMIT')
        if (any(type(b) is not bytes or len(b) > LIMIT for b in documents.values())
                or any(type(b) is not bytes or len(b) > LIMIT for b in payloads.values())
                or sum(map(len, payloads.values())) > 64 * 1024 * 1024):
            raise _Stop('BUNDLE_TYPE_OR_LIMIT')
        for digest, raw in documents.items():
            if type(digest) is not str or _ref(raw)['sha256'] != digest:
                raise _Stop('CONTENT_ADDRESS_MISMATCH')
        entry, (parse, (plan_validator, report_validator), reader, checker, _) = _load()
        report = _parse(report_bytes, parse)
        if not report_validator.is_valid(report):
            raise _Stop('RUN_SCHEMA')
        pointers = [report['plan'], *[s['evidence'] for s in report['stages'].values() if 'evidence' in s]]
        if set(documents) != {p['sha256'] for p in pointers}:
            raise _Stop('DOCUMENT_SET_MISMATCH')
        for pointer in pointers:
            _pinned(documents[pointer['sha256']], pointer)
        plan_raw = documents[report['plan']['sha256']]
        _pinned(plan_raw, expected_plan)
        try:
            plan = entry['_plan'](plan_raw, expected_plan, parse, plan_validator)
        except entry['PlanBlocked'] as error:
            raise _Stop(error.code, error.unsupported) from None
        if report['plan_id'] != plan['plan_id'] or report['execution_profile'] != plan['execution_profile']:
            raise _Stop('PLAN_BINDING_MISMATCH')
        result['recorded_status'] = report['status']
        result['checks'].extend(['exact_references', 'plan_preflight', 'run_shape_and_identity'])
        acquisition, binding = report['stages']['acquisition'], report['stages']['binding']
        if acquisition['status'] == 'passed_known_inputs':
            declared = [plan['registry'], *plan['artifacts'], *plan['decisions']]
            if set(payloads) != {a['path'] for a in declared}:
                raise _Stop('PAYLOAD_SET_MISMATCH')
            evidence = _parse(documents[acquisition['evidence']['sha256']], parse)
            expected_keys = {'schema_version', 'layer', 'source_consistency', 'overall_admission',
                             'transition_allowed', 'same_root_capability', 'directory_before',
                             'directory_after', 'inputs', 'not_checked'}
            if type(evidence) is not dict or set(evidence) != expected_keys or evidence['schema_version'] != '1':
                raise _Stop('ACQUISITION_CLAIM_SHAPE')
            if evidence['not_checked'] != ['source_authentication', 'global_event_completeness',
                    'registry_binding', 'dependency_graph', 'restriction_semantics', 'core_coverage',
                    'environment_compatibility', 'release_permission', 'activation_permission']:
                raise _Stop('ACQUISITION_OBLIGATIONS_MISMATCH')
            def logical(path):
                try:
                    reader['_logical_parts'](path)
                except reader['ReadBlocked']:
                    raise _Stop('DIRECTORY_CLAIM_SHAPE') from None
            _directory(evidence['directory_before'], logical)
            _directory(evidence['directory_after'], logical)
            captured = dict(artifacts={a['path']: payloads[a['path']] for a in [plan['registry'], *plan['artifacts']]},
                            decisions={a['path']: payloads[a['path']] for a in plan['decisions']}, evidence=evidence)
            try:
                entry['_acquired'](captured, plan)
            except entry['PlanBlocked'] as error:
                raise _Stop(error.code) from None
            result['checks'].extend(['archived_payload_integrity', 'acquisition_claim_consistency'])
            if 'evidence' in binding:
                child = _parse(documents[binding['evidence']['sha256']], parse)
                index = payloads[plan['registry']['path']]
                if parse(index)['catalog_id'] != plan['catalog_id']:
                    raise _Stop('SOURCE_CATALOG_MISMATCH')
                replay = checker(index, captured['decisions'],
                                 {a['path']: payloads[a['path']] for a in plan['artifacts']},
                                 plan['selection'], **plan['context'])
                if replay['status'] == 'unsupported':
                    raise _Stop('REPLAY_UNSUPPORTED', True)
                if child != replay or binding['status'] != child['status']:
                    raise _Stop('BINDING_REPLAY_MISMATCH')
                codes = ([dict(code='KNOWN_SCOPE_BLOCK')] if child['status'] == 'blocked_known_scope'
                         else child['diagnostics'])
                if binding['diagnostics'] != codes:
                    raise _Stop('BINDING_DIAGNOSTICS_MISMATCH')
                result['checks'].append('semantic_replay')
            elif binding['status'] != 'not_run':
                result['checks'].append('binding_failure_claim_only')
        else:
            if payloads:
                raise _Stop('UNEXPECTED_PAYLOADS')
            if 'evidence' in acquisition:
                raise _Stop('ACQUISITION_FAILURE_EVIDENCE_UNSUPPORTED', True)
            result['checks'].append('acquisition_not_completed_claim_only')
        result['status'] = 'consistent_recorded_bundle'
    except _Stop as error:
        result['status'] = 'unsupported' if error.unsupported else 'failed'
        result['diagnostics'] = [dict(code=error.code)]
    except ImportError:
        result['status'] = 'unsupported'
        result['diagnostics'] = [dict(code='ENGINE_UNAVAILABLE')]
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, RecursionError):
        result['diagnostics'] = [dict(code='BUNDLE_OR_INSTALLATION_INVALID')]
    return result
