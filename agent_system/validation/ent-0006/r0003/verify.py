#!/usr/bin/env python3
"""Isolated binding/graph tests plus integration on the trusted local checkout."""
import copy
import hashlib
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch
import uuid

BASE = Path(__file__).resolve().parents[3]
check_catalog = runpy.run_path(str(Path(__file__).with_name('check.py')))['check_catalog']
GLOBALS = check_catalog.__globals__
CID = '83bd5866-5e17-477f-9671-4e6a91481221'


def encode(value):
    return (json.dumps(value, sort_keys=True) + '\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


class BindingGraphTests(unittest.TestCase):
    def setUp(self):
        self.make_fixture(3)

    def make_fixture(self, count):
        self.registry = dict(schema_version='1', catalog_id=CID, entities=[])
        self.witnesses, self.artifacts = {}, {}
        for i in range(1, count + 1):
            entity_id = f'ENT-{i:04d}'
            path = f'fixtures/{entity_id.lower()}.md'
            payload = f'fixture {i}\n'.encode()
            self.artifacts[path] = payload
            artifact = dict(path=path, sha256=sha(payload), size_bytes=len(payload), role='normative')
            relations = [] if i == count else [dict(type='depends_on', target=self.subject(i + 1))]
            revision = dict(revision='r0001', title='Fixture', kind='rule', scopes=['test'],
                            artifacts=[artifact], relations=relations,
                            approval=dict(status='approved', reference=dict(path='pending', sha256='0' * 64)),
                            provenance=dict(summary='Synthetic fixture, not permission'))
            self.registry['entities'].append(dict(entity_id=entity_id, revisions=[revision]))
        self.synchronize()
        self.selection = [self.subject(1)]

    def subject(self, number, revision='r0001'):
        return dict(catalog_id=CID, entity_id=f'ENT-{number:04d}', revision=revision)

    def rev(self, number):
        return self.registry['entities'][number - 1]['revisions'][0]

    def synchronize(self):
        self.witnesses = {}
        for i, entity in enumerate(self.registry['entities'], 1):
            revision = entity['revisions'][0]
            did = str(uuid.UUID(int=i))
            path = f'catalog/approvals/{did}.json'
            decision = dict(schema_version='1', decision_id=did, decision_type='approve_revision',
                            subject=dict(catalog_id=CID, entity_id=entity['entity_id'], revision=revision['revision']),
                            artifacts=[{k: v for k, v in a.items() if k != 'role'} for a in revision['artifacts']],
                            actor_role='owner', recorded_by='agent', decision_date='2026-11-07',
                            statement='Synthetic', statement_form='summary', basis='Isolated test')
            self.witnesses[path] = encode(decision)
            revision['approval']['reference'] = dict(path=path, sha256=sha(self.witnesses[path]))

    def result(self):
        return check_catalog(encode(self.registry), self.witnesses, self.artifacts, self.selection)

    def assert_code(self, code, unsupported=False):
        report = self.result()
        self.assertEqual(report['status'], 'unsupported' if unsupported else 'failed')
        self.assertEqual(report['diagnostics'], [dict(code=code)])
        self.assertFalse(report['transition_allowed'])

    def test_valid_chain_and_no_global_admission(self):
        report = self.result()
        self.assertEqual(report['status'], 'passed_known_inputs')
        self.assertEqual(report['selected_closure'], [self.subject(i) for i in range(1, 4)])
        self.assertEqual(len(report['checked_artifacts']), 3)
        self.assertFalse(report['transition_allowed'])
        self.assertEqual(report['overall_admission'], 'not_evaluated')
        self.assertIn('global_event_completeness', report['not_checked'])
        self.assertIn('restriction_semantics', report['not_checked'])

    def test_duplicate_entity_identity(self):
        entity = copy.deepcopy(self.registry['entities'][0])
        entity['revisions'][0]['title'] = 'Different metadata, same ID'
        self.registry['entities'].append(entity)
        self.assert_code('INVALID_OR_DUPLICATE_ENTITY')

    def test_duplicate_revision_identity(self):
        revision = copy.deepcopy(self.rev(1))
        revision['title'] = 'Different metadata, same revision'
        self.registry['entities'][0]['revisions'].append(revision)
        self.assert_code('INVALID_OR_DUPLICATE_REVISION')

    def test_zero_entity_and_revision(self):
        self.registry['entities'][0]['entity_id'] = 'ENT-0000'
        self.synchronize()
        self.assert_code('INVALID_OR_DUPLICATE_ENTITY')
        self.make_fixture(3)
        self.rev(1)['revision'] = 'r0000'
        self.synchronize()
        self.assert_code('INVALID_OR_DUPLICATE_REVISION')

    def test_missing_approval(self):
        del self.witnesses[self.rev(1)['approval']['reference']['path']]
        self.assert_code('MISSING_APPROVAL')

    def test_changed_witness_bytes(self):
        path = self.rev(1)['approval']['reference']['path']
        doc = json.loads(self.witnesses[path])
        doc['statement'] = 'Changed'
        self.witnesses[path] = encode(doc)
        self.assert_code('APPROVAL_DIGEST_MISMATCH')

    def test_wrong_approval_subject(self):
        self.rev(1)['approval']['reference'] = copy.deepcopy(self.rev(2)['approval']['reference'])
        self.assert_code('APPROVAL_SUBJECT_MISMATCH')

    def test_approval_composition_not_just_status(self):
        path = self.rev(1)['approval']['reference']['path']
        doc = json.loads(self.witnesses[path])
        doc['artifacts'][0]['size_bytes'] += 1
        self.witnesses[path] = encode(doc)
        self.rev(1)['approval']['reference']['sha256'] = sha(self.witnesses[path])
        self.assert_code('APPROVED_COMPOSITION_MISMATCH')

    def test_full_multifile_composition(self):
        artifact = dict(path='fixtures/extra.md', sha256=sha(b'extra'), size_bytes=5, role='normative')
        self.rev(1)['artifacts'].append(artifact)
        self.artifacts[artifact['path']] = b'extra'
        self.synchronize()
        self.assertEqual(self.result()['status'], 'passed_known_inputs')
        path = self.rev(1)['approval']['reference']['path']
        doc = json.loads(self.witnesses[path])
        doc['artifacts'].pop()
        self.witnesses[path] = encode(doc)
        self.assert_code('APPROVED_COMPOSITION_MISMATCH')

    def test_link_metadata_is_bound_but_not_traversed(self):
        self.rev(1)['artifacts'][0].update(
            links=[dict(path='fixtures/link', link_type='symbolic_link', target='file.md')],
            resolved_path='fixtures/file.md')
        self.synchronize()
        self.assertEqual(self.result()['status'], 'passed_known_inputs')
        path = self.rev(1)['approval']['reference']['path']
        doc = json.loads(self.witnesses[path])
        doc['artifacts'][0]['links'][0]['target'] = 'other.md'
        self.witnesses[path] = encode(doc)
        self.assert_code('APPROVED_COMPOSITION_MISMATCH')

    def test_missing_or_corrupt_selected_payload(self):
        path = self.rev(2)['artifacts'][0]['path']
        original = self.artifacts.pop(path)
        self.assert_code('MISSING_SELECTED_ARTIFACT')
        self.artifacts[path] = original + b'x'
        self.assert_code('ARTIFACT_BYTES_MISMATCH')

    def test_transitive_dependency_missing_no_latest(self):
        self.rev(3)['revision'] = 'r0002'
        self.synchronize()
        self.assert_code('MISSING_RELATION_TARGET')

    def test_cycle(self):
        self.rev(3)['relations'] = [dict(type='depends_on', target=self.subject(1))]
        self.assert_code('DEPENDENCY_CYCLE')

    def test_informational_edges_not_executable_dependencies(self):
        for kind in ['derived_from', 'validated_by', 'supersedes', 'implements']:
            self.rev(1)['relations'] = [dict(type=kind, target=self.subject(2))]
            self.rev(3)['relations'] = [dict(type=kind, target=self.subject(1))]
            report = self.result()
            self.assertEqual(report['status'], 'passed_known_inputs')
            self.assertEqual(report['selected_closure'], [self.subject(1)])

    def test_foreign_catalog_not_implicitly_imported(self):
        self.rev(1)['relations'][0]['target']['catalog_id'] = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
        self.assert_code('FOREIGN_CATALOG')

    def test_unlinked_restriction_or_unknown_event_blocks(self):
        path = 'catalog/approvals/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa.json'
        for kind in ['unknown_event']:
            self.witnesses[path] = encode(dict(decision_type=kind, subject=self.subject(1)))
            self.assert_code('UNSUPPORTED_DECISION', unsupported=True)

    def test_unlinked_positive_approval_is_examined_and_reported(self):
        path = self.rev(1)['approval']['reference']['path']
        doc = json.loads(self.witnesses[path])
        doc['decision_id'] = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
        extra = 'catalog/approvals/' + doc['decision_id'] + '.json'
        self.witnesses[extra] = encode(doc)
        report = self.result()
        self.assertEqual(report['status'], 'passed_known_inputs')
        self.assertEqual(report['unreferenced_approvals'], [extra])
        self.assertFalse(report['transition_allowed'])

    def test_decision_filename_must_match_id(self):
        path = self.rev(1)['approval']['reference']['path']
        self.witnesses['catalog/approvals/wrong.json'] = self.witnesses.pop(path)
        self.assert_code('DECISION_PATH_MISMATCH')

    def test_unsafe_input_name_not_disclosed(self):
        self.witnesses['/private-key-do-not-echo'] = b'{}'
        report = self.result()
        self.assertEqual(report['diagnostics'], [dict(code='INVALID_INPUT_PATH')])
        self.assertNotIn('private-key-do-not-echo', json.dumps(report))

    def test_parser_failures_never_succeed(self):
        for blob in [b'{"x":1,"x":2}', b'NaN', b'\xff', b'\xef\xbb\xbf{}', b'[' * 2000]:
            report = check_catalog(blob, self.witnesses, self.artifacts, self.selection)
            self.assertEqual(report['status'], 'failed')
            self.assertFalse(report['transition_allowed'])

    def test_missing_engine_no_skip(self):
        def missing():
            raise ImportError('private details')
        with patch.dict(GLOBALS, _tools=missing):
            self.assert_code('ENGINE_UNAVAILABLE', unsupported=True)

    def test_no_network_or_mutation(self):
        before = encode([self.registry, {k: v.hex() for k, v in self.witnesses.items()}])
        with patch('socket.socket', side_effect=AssertionError('Network attempted')):
            self.assertEqual(self.result()['status'], 'passed_known_inputs')
        after = encode([self.registry, {k: v.hex() for k, v in self.witnesses.items()}])
        self.assertEqual(before, after)

    def test_diamond_not_false_cycle(self):
        self.make_fixture(4)
        self.rev(1)['relations'] = [dict(type='depends_on', target=self.subject(i)) for i in [2, 3]]
        self.rev(2)['relations'] = self.rev(3)['relations'] = [dict(type='depends_on', target=self.subject(4))]
        self.assertEqual(self.result()['status'], 'passed_known_inputs')

    def test_graph_longer_than_python_recursion_limit(self):
        self.make_fixture(1001)
        report = self.result()
        self.assertEqual(report['status'], 'passed_known_inputs')
        self.assertEqual(len(report['selected_closure']), 1001)

    def test_limits_and_explicit_selection(self):
        self.witnesses = {f'file{i}': b'' for i in range(10001)}
        self.assert_code('INPUT_LIMIT')
        self.make_fixture(3)
        self.selection = []
        self.assert_code('INVALID_INPUT')
        self.selection = [self.subject(1, 'latest')]
        self.assert_code('INVALID_SELECTION')

    def test_duplicate_artifact_path_even_with_different_role(self):
        extra = dict(self.rev(1)['artifacts'][0], role='supporting')
        self.rev(1)['artifacts'].append(extra)
        self.synchronize()
        self.assert_code('DUPLICATE_ARTIFACT_PATH')

    def test_conflicting_path_across_revisions(self):
        self.rev(2)['artifacts'][0]['path'] = self.rev(1)['artifacts'][0]['path']
        self.synchronize()
        self.assert_code('CONFLICTING_ARTIFACT_PATH')

    def test_duplicate_decision_id_not_hidden_by_another_filename(self):
        path = self.rev(1)['approval']['reference']['path']
        self.witnesses['catalog/approvals/wrong.json'] = self.witnesses[path]
        self.assert_code('DUPLICATE_DECISION_ID')

    def test_equal_multifile_set_accepts_different_list_order(self):
        artifact = dict(path='fixtures/extra.md', sha256=sha(b'extra'), size_bytes=5, role='normative')
        self.rev(1)['artifacts'].append(artifact)
        self.artifacts[artifact['path']] = b'extra'
        self.synchronize()
        path = self.rev(1)['approval']['reference']['path']
        decision = json.loads(self.witnesses[path])
        decision['artifacts'].reverse()
        self.witnesses[path] = encode(decision)
        self.rev(1)['approval']['reference']['sha256'] = sha(self.witnesses[path])
        self.assertEqual(self.result()['status'], 'passed_known_inputs')

    def add_restriction(self):
        path = self.rev(1)['approval']['reference']['path']
        event = json.loads(self.witnesses[path])
        event.update(decision_id='ffffffff-ffff-4fff-8fff-ffffffffffff',
                     decision_type='revoke_use', reason='Synthetic only',
                     scope=dict(operations=['export'], areas=['*']))
        self.witnesses['catalog/approvals/' + event['decision_id'] + '.json'] = encode(event)
        return event

    def test_valid_restriction_needs_explicit_context(self):
        self.add_restriction()
        self.assert_code('EXPLICIT_CONTEXT_REQUIRED', unsupported=True)

    def test_known_restriction_blocks_selected_dependency_closure(self):
        self.add_restriction()
        report = check_catalog(encode(self.registry), self.witnesses, self.artifacts,
                               self.selection, operation='export', area='local')
        self.assertEqual(report['status'], 'blocked_known_scope')
        self.assertFalse(report['transition_allowed'])
        self.assertNotIn('restriction_semantics', report['not_checked'])
        self.assertEqual(report['unreferenced_approvals'], [])

    def test_unaffected_scope_still_not_global_permission(self):
        self.add_restriction()
        report = check_catalog(encode(self.registry), self.witnesses, self.artifacts,
                               self.selection, operation='validate', area='local')
        self.assertEqual(report['status'], 'passed_known_inputs')
        self.assertFalse(report['transition_allowed'])
        self.assertEqual(report['restriction_evaluation']['context']['operation'], 'validate')

    def test_event_loader_failure_is_translated(self):
        class ChildStop(Exception):
            def __init__(self):
                self.code, self.unsupported = 'EVENT_ENGINE_UNAVAILABLE', True
        def fail():
            raise ChildStop()
        tools = {'_load': fail, '_Stop': ChildStop}
        with patch('runpy.run_path', return_value=tools):
            with self.assertRaises(GLOBALS['_Stop']) as context:
                GLOBALS['_event_tools']()
        self.assertEqual(context.exception.code, 'EVENT_ENGINE_UNAVAILABLE')
        self.assertTrue(context.exception.unsupported)

    def test_integration_with_declared_files_and_existing_schema(self):
        registry_blob = (BASE / 'catalog/registry.json').read_bytes()
        registry = json.loads(registry_blob)
        reader_tools = runpy.run_path(str(BASE / 'adapters/ent-0005/r0003/reader.py'))
        # Trusted-checkout fixture prepares a declared expectation set. This is
        # NOT a production algorithm to authenticate expectations from raw source.
        declared = [dict(path='catalog/registry.json', sha256=sha(registry_blob), size_bytes=len(registry_blob))]
        for entity in registry['entities']:
            for rev in entity['revisions']:
                declared.extend(rev['artifacts'])
        by_path = {a['path']: a for a in declared}
        decision_expectations = []
        for path in (BASE / 'catalog/approvals').glob('*.json'):
            data = path.read_bytes()
            decision_expectations.append(dict(path=path.relative_to(BASE).as_posix(),
                                              sha256=sha(data), size_bytes=len(data)))
        captured = reader_tools['read_set'](BASE, list(by_path.values()), decision_expectations)
        payloads = dict(captured['artifacts'])
        registry_blob = payloads.pop('catalog/registry.json')
        witnesses = captured['decisions']
        self.assertTrue(captured['evidence']['same_root_capability'])
        self.assertEqual(captured['evidence']['directory_before'], captured['evidence']['directory_after'])
        self.assertFalse(captured['evidence']['transition_allowed'])
        roots = [dict(catalog_id=CID, entity_id='ENT-0005', revision='r0002'),
                 dict(catalog_id=CID, entity_id='ENT-0004', revision='r0002')]
        entry = next((e for e in registry['entities'] if e['entity_id'] == 'ENT-0006'), None)
        if entry is not None:
            rev = next(r for r in ['r0003', 'r0002', 'r0001']
                       if any(item['revision'] == r for item in entry['revisions']))
            roots = [dict(catalog_id=CID, entity_id='ENT-0006', revision=rev)]
        report = check_catalog(registry_blob, witnesses, payloads, roots)
        self.assertEqual(report['status'], 'passed_known_inputs')
        self.assertEqual(report['unreferenced_approvals'], [])
        self.assertFalse(report['transition_allowed'])
        scoped = check_catalog(registry_blob, witnesses, payloads, roots,
                               operation='export', area='agent_system.validation')
        self.assertEqual(scoped['status'], 'passed_known_inputs')
        self.assertEqual(scoped['restriction_evaluation']['status'], 'no_known_block_in_scope')
        self.assertFalse(scoped['transition_allowed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
