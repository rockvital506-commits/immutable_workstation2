#!/usr/bin/env python3
"""Evaluate a known entity-decision ledger for one explicit operation/area.

No global admission, event discovery, source authentication, release or activation.
"""
import hashlib
from importlib import metadata
from pathlib import Path
import re
import runpy

BASE = Path(__file__).resolve().parents[3]
HELPERS = BASE / 'validation/ent-0004/r0002/verify.py'
HELPERS_SHA = '1523ca399a9aee8f89656591b62e1d776504385fe025131c818c694ebb32aedf'
BASE_SCHEMA = BASE / 'specification/ent-0003/r0002/catalog-base.schema.json'
BASE_SHA = '42fab3c453930ad9128b2b422837b82d84db9ed6092872765bd7fe1ffaf9a820'
EVENT_SCHEMA = Path(__file__).with_name('decision-events.schema.json')
EVENT_SHA = '4cce54eaff0d12e1e59a4aeb0eb1dd9f0f0b951f43968317c70adb7c714005c1'
KINDS = {'approve_revision', 'restrict_use', 'revoke_use', 'lift_restriction', 'correct_record'}


class _Stop(Exception):
    def __init__(self, code, unsupported=False):
        self.code, self.unsupported = code, unsupported


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _load():
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    if metadata.version('jsonschema') != '4.26.0':
        raise _Stop('UNSUPPORTED_ENGINE', True)
    if _sha(HELPERS.read_bytes()) != HELPERS_SHA:
        raise _Stop('INSTALLED_DEPENDENCY_CHANGED')
    helpers = runpy.run_path(str(HELPERS))
    parse = helpers['strict_json']
    base_data, event_data = BASE_SCHEMA.read_bytes(), EVENT_SCHEMA.read_bytes()
    if _sha(base_data) != BASE_SHA or _sha(event_data) != EVENT_SHA:
        raise _Stop('INSTALLED_SCHEMA_CHANGED')
    base, schema = parse(base_data), parse(event_data)
    checker = helpers['local_validator'](base).format_checker
    Draft202012Validator.check_schema(schema)
    def deny(_uri):
        raise ValueError('Unregistered schema retrieval forbidden')
    resources = Registry(retrieve=deny).with_resources([
        (base['$id'], Resource.from_contents(base)),
        (schema['$id'], Resource.from_contents(schema))])
    validator = Draft202012Validator(schema, format_checker=checker, registry=resources)
    return parse, validator, base


def _subject(record):
    s = record['subject']
    return (s['catalog_id'], s['entity_id'], s['revision'])


def _composition(record):
    result = {}
    for artifact in record['artifacts']:
        if artifact['path'] in result:
            raise _Stop('DUPLICATE_ARTIFACT_PATH')
        result[artifact['path']] = artifact
    return result


def _matches(scope, operation, area):
    return all('*' in scope[k] or value in scope[k]
               for k, value in [('operations', operation), ('areas', area)])


def _subset(smaller, larger):
    return all('*' in larger[k] or set(smaller[k]).issubset(larger[k])
               for k in ('operations', 'areas'))


def evaluate_decisions(decision_blobs, subjects, *, operation, area):
    report = dict(schema_version='1', layer='known_entity_decisions', status='failed',
                  overall_admission='not_evaluated', transition_allowed=False,
                  source_consistency='mutable_tree_observations', context=None, inputs=[],
                  active_blocks=[], applied_lifts=[], corrections=[], diagnostics=[],
                  not_checked=['source_acquisition_boundary', 'source_authentication', 'registry_binding',
                               'artifact_integrity', 'dependency_graph', 'global_event_completeness',
                               'release_decisions', 'semantic_correction_resolution',
                               'core_coverage', 'environment_compatibility', 'activation_permission'])
    try:
        if (type(decision_blobs) is not dict or type(subjects) is not list or not subjects
                or not isinstance(operation, str) or not isinstance(area, str)
                or not re.fullmatch('[a-z][a-z0-9_.-]*', operation)
                or not re.fullmatch('[a-z][a-z0-9_.-]*', area)):
            raise _Stop('EXPLICIT_CONTEXT_REQUIRED')
        blobs = dict(decision_blobs)
        if len(blobs) > 10000 or any(type(b) is not bytes for b in blobs.values()):
            raise _Stop('INPUT_LIMIT_OR_TYPE')
        if any(len(b) > 16 * 1024 * 1024 for b in blobs.values()) or sum(map(len, blobs.values())) > 64 * 1024 * 1024:
            raise _Stop('INPUT_LIMIT_OR_TYPE')
        parse, validator, base = _load()
        path_check = validator.evolve(schema=base['$defs']['path'])
        subject_check = validator.evolve(schema={'$ref': base['$id'] + '#/$defs/subject'})
        chosen = set()
        for subject in subjects:
            if not subject_check.is_valid(subject):
                raise _Stop('INVALID_SUBJECT')
            chosen.add((subject['catalog_id'], subject['entity_id'], subject['revision']))
        report['context'] = dict(operation=operation, area=area, subjects=[
            dict(catalog_id=c, entity_id=e, revision=r) for c, e, r in sorted(chosen)])
        records, raw_by_id, approved = {}, {}, {}
        for path, data in sorted(blobs.items()):
            if not path_check.is_valid(path):
                raise _Stop('INVALID_INPUT_PATH')
            record = parse(data)
            if not isinstance(record, dict) or record.get('decision_type') not in KINDS:
                raise _Stop('UNSUPPORTED_DECISION', True)
            if not validator.is_valid(record):
                raise _Stop('INVALID_DECISION')
            did = record['decision_id']
            if did in records:
                raise _Stop('DUPLICATE_DECISION')
            if path != 'catalog/approvals/' + did + '.json':
                raise _Stop('DECISION_PATH_MISMATCH')
            subject = _subject(record)
            if not subject[1][4:].strip('0') or not subject[2][1:].strip('0'):
                raise _Stop('ZERO_IDENTITY')
            records[did], raw_by_id[did] = record, data
            report['inputs'].append(dict(path=path, sha256=_sha(data), size_bytes=len(data)))
            if record['decision_type'] == 'approve_revision':
                composition = _composition(record)
                if subject in approved and approved[subject] != composition:
                    raise _Stop('CONFLICTING_APPROVAL_COMPOSITION')
                approved[subject] = composition
        if not chosen.issubset(approved):
            raise _Stop('MISSING_APPROVAL')
        for record in records.values():
            subject = _subject(record)
            if subject not in approved or _composition(record) != approved[subject]:
                raise _Stop('SUBJECT_OR_COMPOSITION_MISMATCH')

        edges = {}
        for did, record in records.items():
            if record['decision_type'] not in ('lift_restriction', 'correct_record'):
                continue
            target = record['target']
            tid = target['decision_id']
            if tid not in records:
                raise _Stop('MISSING_TARGET')
            if _sha(raw_by_id[tid]) != target['sha256']:
                raise _Stop('TARGET_DIGEST_MISMATCH')
            if _subject(record) != _subject(records[tid]) or _composition(record) != _composition(records[tid]):
                raise _Stop('TARGET_SUBJECT_MISMATCH')
            edges[did] = tid
        # Follow exact references, independent of dates and input ordering.
        complete = set()
        for start in edges:
            trail, current = set(), start
            while current in edges and current not in complete:
                if current in trail:
                    raise _Stop('EVENT_CYCLE')
                trail.add(current)
                current = edges[current]
            complete.update(trail)

        lifts, overlays = {}, {}
        for did in sorted(records):
            record = records[did]
            kind = record['decision_type']
            if kind == 'lift_restriction':
                tid = record['target']['decision_id']
                target = records[tid]
                if target['decision_type'] not in ('restrict_use', 'revoke_use'):
                    raise _Stop('INVALID_LIFT_TARGET')
                if not _subset(record['scope'], target['scope']):
                    raise _Stop('LIFT_EXCEEDS_TARGET_SCOPE')
                lifts.setdefault(tid, []).append(did)
            elif kind == 'correct_record':
                tid = record['target']['decision_id']
                target = records[tid]
                seen_fields = set()
                for change in record['changes']:
                    path = change['path']
                    # Only documentary fields whose values cannot grant/revoke use.
                    if path not in ('/decision_date', '/statement_form'):
                        raise _Stop('SEMANTIC_CORRECTION_REQUIRES_RESOLUTION', True)
                    if path in seen_fields:
                        raise _Stop('DUPLICATE_CORRECTION_FIELD')
                    seen_fields.add(path)
                    field = path[1:]
                    if change['old_value'] != target[field]:
                        raise _Stop('CORRECTION_OLD_VALUE_MISMATCH')
                    overlay = dict(target, **{field: change['new_value']})
                    if not validator.is_valid(overlay):
                        raise _Stop('INVALID_CORRECTED_METADATA')
                    key = (tid, field)
                    if key in overlays and overlays[key] != change['new_value']:
                        raise _Stop('CONFLICTING_CORRECTIONS')
                    overlays[key] = change['new_value']
                report['corrections'].append(dict(decision_id=did, target_id=tid,
                                                  fields=sorted(seen_fields)))
        for did in sorted(records):
            record = records[did]
            if record['decision_type'] not in ('restrict_use', 'revoke_use') or _subject(record) not in chosen:
                continue
            if not _matches(record['scope'], operation, area):
                continue
            applicable = [lid for lid in lifts.get(did, [])
                          if _matches(records[lid]['scope'], operation, area)]
            if applicable:
                report['applied_lifts'].extend(applicable)
            else:
                report['active_blocks'].append(dict(decision_id=did, subject=dict(record['subject'])))
        report['applied_lifts'] = sorted(set(report['applied_lifts']))
        report['status'] = 'blocked_known_scope' if report['active_blocks'] else 'no_known_block_in_scope'
    except _Stop as error:
        report['status'] = 'unsupported' if error.unsupported else 'failed'
        report['diagnostics'] = [dict(code=error.code)]
    except (ImportError, metadata.PackageNotFoundError):
        report['status'] = 'unsupported'
        report['diagnostics'] = [dict(code='ENGINE_UNAVAILABLE')]
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        report['diagnostics'] = [dict(code='INPUT_OR_DEPENDENCY_UNAVAILABLE')]
    return report
