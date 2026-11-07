#!/usr/bin/env python3
"""Pure check of supplied bytes: identities, approval binding, exact dependency graph.

Not source acquisition, complete event history, release or activation permission.
"""
import copy
import hashlib
from importlib import metadata
from pathlib import Path
import runpy

BASE = Path(__file__).resolve().parents[3]
TOOLS = BASE / 'validation/ent-0004/r0002/verify.py'
TOOLS_SHA256 = '1523ca399a9aee8f89656591b62e1d776504385fe025131c818c694ebb32aedf'
SCHEMA = BASE / 'specification/ent-0003/r0002/catalog-base.schema.json'
SCHEMA_SHA256 = '42fab3c453930ad9128b2b422837b82d84db9ed6092872765bd7fe1ffaf9a820'
NOT_CHECKED = ['source_acquisition_boundary', 'global_event_completeness',
               'restriction_semantics', 'core_coverage', 'environment_compatibility',
               'release_permission', 'activation_permission']


class _Stop(Exception):
    def __init__(self, code, unsupported=False):
        self.code, self.unsupported = code, unsupported


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _tools():
    # These are installed trusted dependencies, not code from the input catalog.
    # Verify bytes before running the existing parser/schema helpers.
    if metadata.version('jsonschema') != '4.26.0':
        raise _Stop('UNSUPPORTED_ENGINE', True)
    data = TOOLS.read_bytes()
    if _sha(data) != TOOLS_SHA256:
        raise _Stop('INSTALLED_DEPENDENCY_CHANGED')
    helpers = runpy.run_path(str(TOOLS))
    data = SCHEMA.read_bytes()
    if _sha(data) != SCHEMA_SHA256:
        raise _Stop('INSTALLED_SCHEMA_CHANGED')
    parse = helpers['strict_json']
    validator = helpers['local_validator'](parse(data))
    return parse, validator


def _artifact_tuple(record):
    return {k: v for k, v in record.items() if k != 'role'}


def _composition(artifacts):
    result = {}
    for artifact in artifacts:
        path = artifact['path']
        if path in result:
            raise _Stop('DUPLICATE_ARTIFACT_PATH')
        result[path] = _artifact_tuple(artifact)
    return result


def check_catalog(registry_blob, witness_blobs, artifact_blobs, selection):
    """Check explicit known input bytes; never enumerate or fetch source files.

    Acquisition/trust of this snapshot are caller obligations. All input bytes
    must have been obtained within the approved boundary. No atomicity is implied.
    """
    report = {'schema_version': '1', 'layer': 'catalog_binding_and_graph',
              'status': 'failed', 'source_consistency': 'mutable_tree_observations',
              'overall_admission': 'not_evaluated', 'transition_allowed': False,
              'not_checked': list(NOT_CHECKED), 'diagnostics': [],
              'inputs': [], 'selected_closure': [], 'checked_artifacts': [],
              'unreferenced_approvals': []}
    try:
        if (type(registry_blob) is not bytes or type(witness_blobs) is not dict
                or type(artifact_blobs) is not dict or type(selection) is not list
                or not selection):
            raise _Stop('INVALID_INPUT')
        witnesses, payloads = dict(witness_blobs), dict(artifact_blobs)
        selection = copy.deepcopy(selection)
        if len(witnesses) + len(payloads) > 10000:
            raise _Stop('INPUT_LIMIT')
        blobs = [registry_blob, *witnesses.values(), *payloads.values()]
        if any(type(b) is not bytes for b in blobs):
            raise _Stop('INVALID_INPUT')
        if any(len(b) > 16 * 1024 * 1024 for b in blobs) or sum(map(len, blobs)) > 64 * 1024 * 1024:
            raise _Stop('INPUT_LIMIT')
        parse, validator = _tools()
        path_validator = validator.evolve(schema=validator.schema['$defs']['path'])
        for path in [*witnesses, *payloads]:
            if not path_validator.is_valid(path):
                raise _Stop('INVALID_INPUT_PATH')
        if set(witnesses) & set(payloads) or 'catalog/registry.json' in {*witnesses, *payloads}:
            raise _Stop('INPUT_PATH_CONFLICT')
        for path, data in [('catalog/registry.json', registry_blob),
                           *sorted(witnesses.items()), *sorted(payloads.items())]:
            report['inputs'].append({'path': path, 'sha256': _sha(data), 'size_bytes': len(data)})
        registry = parse(registry_blob)
        if not validator.is_valid(registry) or 'entities' not in registry:
            raise _Stop('INVALID_REGISTRY')
        cid = registry['catalog_id']
        versions, entity_ids, physical_paths = {}, set(), {}
        for entity in registry['entities']:
            eid = entity['entity_id']
            if not eid[4:].strip('0') or eid in entity_ids:
                raise _Stop('INVALID_OR_DUPLICATE_ENTITY')
            entity_ids.add(eid)
            for rev in entity['revisions']:
                key = (eid, rev['revision'])
                if not rev['revision'][1:].strip('0') or key in versions:
                    raise _Stop('INVALID_OR_DUPLICATE_REVISION')
                versions[key] = rev
                composition = _composition(rev['artifacts'])
                for path, artifact in composition.items():
                    if path in physical_paths and physical_paths[path] != artifact:
                        raise _Stop('CONFLICTING_ARTIFACT_PATH')
                    physical_paths[path] = artifact
        if len(versions) > 10000:
            raise _Stop('GRAPH_LIMIT')

        decisions, decision_ids = {}, set()
        for path, data in sorted(witnesses.items()):
            decision = parse(data)
            if not isinstance(decision, dict):
                raise _Stop('INVALID_DECISION')
            if decision.get('decision_type') != 'approve_revision':
                raise _Stop('UNSUPPORTED_DECISION', True)
            if not validator.is_valid(decision):
                raise _Stop('INVALID_DECISION')
            did = decision['decision_id']
            if did in decision_ids:
                raise _Stop('DUPLICATE_DECISION_ID')
            decision_ids.add(did)
            if path != 'catalog/approvals/' + did + '.json':
                raise _Stop('DECISION_PATH_MISMATCH')
            subject = decision['subject']
            key = (subject['entity_id'], subject['revision'])
            if subject['catalog_id'] != cid or key not in versions:
                raise _Stop('DECISION_SUBJECT_MISMATCH')
            if _composition(decision['artifacts']) != _composition(versions[key]['artifacts']):
                raise _Stop('APPROVED_COMPOSITION_MISMATCH')
            decisions[path] = decision
        referenced = set()
        for key, rev in versions.items():
            reference = rev['approval']['reference']
            path = reference['path']
            if path not in decisions:
                raise _Stop('MISSING_APPROVAL')
            if _sha(witnesses[path]) != reference['sha256']:
                raise _Stop('APPROVAL_DIGEST_MISMATCH')
            subject = decisions[path]['subject']
            if (subject['entity_id'], subject['revision']) != key:
                raise _Stop('APPROVAL_SUBJECT_MISMATCH')
            referenced.add(path)
        report['unreferenced_approvals'] = sorted(set(decisions) - referenced)

        graph = {key: [] for key in versions}
        edges = 0
        for key, rev in versions.items():
            for relation in rev['relations']:
                edges += 1
                if edges > 50000:
                    raise _Stop('GRAPH_LIMIT')
                target = relation['target']
                dest = (target['entity_id'], target['revision'])
                if target['catalog_id'] != cid:
                    raise _Stop('FOREIGN_CATALOG')
                if dest not in versions:
                    raise _Stop('MISSING_RELATION_TARGET')
                if relation['type'] == 'depends_on':
                    graph[key].append(dest)
        colors = {}
        for start in graph:
            stack = [(start, False)]
            while stack:
                node, exiting = stack.pop()
                if exiting:
                    colors[node] = 2
                elif colors.get(node) == 1:
                    raise _Stop('DEPENDENCY_CYCLE')
                elif colors.get(node) != 2:
                    colors[node] = 1
                    stack.append((node, True))
                    stack.extend((target, False) for target in graph[node])
        closure, todo = set(), []
        for subject in selection:
            if not isinstance(subject, dict) or set(subject) != {'catalog_id', 'entity_id', 'revision'}:
                raise _Stop('INVALID_SELECTION')
            key = (subject['entity_id'], subject['revision'])
            if subject['catalog_id'] != cid or key not in versions:
                raise _Stop('INVALID_SELECTION')
            todo.append(key)
        while todo:
            key = todo.pop()
            if key not in closure:
                closure.add(key)
                todo.extend(graph[key])
        report['selected_closure'] = [{'catalog_id': cid, 'entity_id': e, 'revision': r}
                                      for e, r in sorted(closure)]
        for key in sorted(closure):
            for artifact in versions[key]['artifacts']:
                path = artifact['path']
                if path not in payloads:
                    raise _Stop('MISSING_SELECTED_ARTIFACT')
                data = payloads[path]
                if len(data) != artifact['size_bytes'] or _sha(data) != artifact['sha256']:
                    raise _Stop('ARTIFACT_BYTES_MISMATCH')
                report['checked_artifacts'].append(_artifact_tuple(artifact))
        report['status'] = 'passed_known_inputs'
    except _Stop as error:
        report['status'] = 'unsupported' if error.unsupported else 'failed'
        report['diagnostics'] = [{'code': error.code}]
    except (ImportError, metadata.PackageNotFoundError):
        report['status'] = 'unsupported'
        report['diagnostics'] = [{'code': 'ENGINE_UNAVAILABLE'}]
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        report['diagnostics'] = [{'code': 'INPUT_OR_DEPENDENCY_UNAVAILABLE'}]
    return report
