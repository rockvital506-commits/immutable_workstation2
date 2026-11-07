#!/usr/bin/env python3
"""Synthetic ledger tests: never record a real restriction or alter history."""
import copy
import hashlib
import json
from pathlib import Path
import random
import runpy
import unittest
from unittest.mock import patch
import uuid

BASE = Path(__file__).resolve().parents[3]
evaluate = runpy.run_path(str(Path(__file__).with_name('events.py')))['evaluate_decisions']
GLOBALS = evaluate.__globals__
CID = '83bd5866-5e17-477f-9671-4e6a91481221'


def encode(value):
    return (json.dumps(value, sort_keys=True) + '\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


class DecisionEventTests(unittest.TestCase):
    def setUp(self):
        self.blobs, self.counter = {}, 0
        self.subject = dict(catalog_id=CID, entity_id='ENT-0001', revision='r0001')
        self.approval = self.add('approve_revision')

    def path(self, did):
        return 'catalog/approvals/' + did + '.json'

    def document(self, did):
        return json.loads(self.blobs[self.path(did)])

    def replace(self, did, document):
        self.blobs[self.path(did)] = encode(document)

    def add(self, kind, *, target=None, scope=None, changes=None, subject=None, **extra):
        self.counter += 1
        did = str(uuid.UUID(int=self.counter))
        record = dict(schema_version='1', decision_id=did, decision_type=kind,
                      subject=copy.deepcopy(subject or self.subject),
                      artifacts=[dict(path='fixtures/file.md', sha256=sha(b'fixture'), size_bytes=7)],
                      actor_role='owner', recorded_by='agent', decision_date='2026-11-07',
                      statement='Synthetic fixture', statement_form='summary', basis='Test only')
        if kind != 'approve_revision':
            record['reason'] = 'Synthetic reason, not a real owner restriction'
        if kind in ('restrict_use', 'revoke_use', 'lift_restriction'):
            record['scope'] = scope or dict(operations=['export'], areas=['*'])
        if target is not None:
            record['target'] = dict(decision_id=target, sha256=sha(self.blobs[self.path(target)]))
        if changes is not None:
            record['changes'] = changes
        record.update(extra)
        self.replace(did, record)
        return did

    def result(self, operation='export', area='agent_system.validation', subjects=None):
        return evaluate(self.blobs, subjects or [self.subject], operation=operation, area=area)

    def assert_status(self, status, **kwargs):
        report = self.result(**kwargs)
        self.assertEqual(report['status'], status)
        self.assertFalse(report['transition_allowed'])
        self.assertEqual(report['overall_admission'], 'not_evaluated')
        return report

    def assert_code(self, code, unsupported=False):
        report = self.assert_status('unsupported' if unsupported else 'failed')
        self.assertEqual(report['diagnostics'], [dict(code=code)])

    def test_positive_only_is_not_global_permission(self):
        self.assert_status('no_known_block_in_scope')

    def test_restrict_and_revoke(self):
        self.add('restrict_use')
        self.add('revoke_use')
        report = self.assert_status('blocked_known_scope')
        self.assertEqual(len(report['active_blocks']), 2)

    def test_operation_and_area_exact(self):
        self.add('restrict_use', scope=dict(operations=['export'], areas=['agent_system']))
        self.assert_status('no_known_block_in_scope')
        self.assert_status('blocked_known_scope', area='agent_system')
        self.assert_status('no_known_block_in_scope', operation='activate', area='agent_system')

    def test_wildcard_scope(self):
        self.add('revoke_use', scope=dict(operations=['*'], areas=['*']))
        self.assert_status('blocked_known_scope', operation='activate')

    def test_lift_one_does_not_lift_another(self):
        first = self.add('restrict_use')
        second = self.add('revoke_use')
        lift = self.add('lift_restriction', target=first)
        report = self.assert_status('blocked_known_scope')
        self.assertEqual([b['decision_id'] for b in report['active_blocks']], [second])
        self.assertEqual(report['applied_lifts'], [lift])

    def test_full_lift_still_not_activation(self):
        block = self.add('revoke_use')
        self.add('lift_restriction', target=block)
        self.assert_status('no_known_block_in_scope')

    def test_partial_lift(self):
        block = self.add('restrict_use', scope=dict(operations=['export', 'activate'], areas=['*']))
        self.add('lift_restriction', target=block,
                 scope=dict(operations=['export'], areas=['agent_system.validation']))
        self.assert_status('no_known_block_in_scope')
        self.assert_status('blocked_known_scope', operation='activate')
        self.assert_status('blocked_known_scope', area='agent_system.governance')

    def test_lift_cannot_exceed_target(self):
        block = self.add('restrict_use', scope=dict(operations=['export'], areas=['local']))
        self.add('lift_restriction', target=block, scope=dict(operations=['*'], areas=['*']))
        self.assert_code('LIFT_EXCEEDS_TARGET_SCOPE')

    def test_lift_must_target_a_block(self):
        self.add('lift_restriction', target=self.approval)
        self.assert_code('INVALID_LIFT_TARGET')

    def test_missing_target(self):
        block = self.add('revoke_use')
        self.add('lift_restriction', target=block)
        del self.blobs[self.path(block)]
        self.assert_code('MISSING_TARGET')

    def test_target_hash_exact(self):
        block = self.add('revoke_use')
        self.add('lift_restriction', target=block)
        record = self.document(block)
        record['statement'] = 'changed after reference'
        self.replace(block, record)
        self.assert_code('TARGET_DIGEST_MISMATCH')

    def test_date_and_order_not_priority(self):
        block = self.add('revoke_use', decision_date='2026-01-01')
        self.add('approve_revision', decision_date='2026-12-31')
        report = self.assert_status('blocked_known_scope')
        self.assertEqual(report['active_blocks'][0]['decision_id'], block)
        reference = report
        for i in range(5):
            items = list(self.blobs.items())
            random.Random(i).shuffle(items)
            self.blobs = dict(items)
            self.assertEqual(self.result(), reference)

    def test_new_revision_does_not_clear_old_revoke(self):
        self.add('revoke_use')
        next_subject = dict(self.subject, revision='r0002')
        self.add('approve_revision', subject=next_subject)
        self.assert_status('blocked_known_scope')
        self.assert_status('no_known_block_in_scope', subjects=[next_subject])

    def test_subject_and_artifact_composition(self):
        did = self.add('restrict_use')
        record = self.document(did)
        record['artifacts'][0]['size_bytes'] = 8
        self.replace(did, record)
        self.assert_code('SUBJECT_OR_COMPOSITION_MISMATCH')

    def test_missing_approval(self):
        self.add('revoke_use')
        del self.blobs[self.path(self.approval)]
        self.assert_code('MISSING_APPROVAL')

    def test_conflicting_positive_composition(self):
        did = self.add('approve_revision')
        record = self.document(did)
        record['artifacts'][0]['sha256'] = 'a' * 64
        self.replace(did, record)
        self.assert_code('CONFLICTING_APPROVAL_COMPOSITION')

    def test_documentary_correction_preserves_original_bytes(self):
        before = self.blobs[self.path(self.approval)]
        correction = self.add('correct_record', target=self.approval,
                              changes=[dict(path='/decision_date', old_value='2026-11-07', new_value='2026-11-06')])
        report = self.assert_status('no_known_block_in_scope')
        self.assertEqual(report['corrections'][0]['decision_id'], correction)
        self.assertEqual(self.blobs[self.path(self.approval)], before)
        self.assertEqual(self.document(self.approval)['decision_date'], '2026-11-07')

    def test_statement_form_correction(self):
        self.add('correct_record', target=self.approval,
                 changes=[dict(path='/statement_form', old_value='summary', new_value='quote')])
        self.assert_status('no_known_block_in_scope')

    def test_conflicting_corrections_no_last_wins(self):
        for date in ['2026-11-06', '2026-11-05']:
            self.add('correct_record', target=self.approval,
                     changes=[dict(path='/decision_date', old_value='2026-11-07', new_value=date)])
        self.assert_code('CONFLICTING_CORRECTIONS')

    def test_identical_documentary_corrections_not_conflict(self):
        for _ in range(2):
            self.add('correct_record', target=self.approval,
                     changes=[dict(path='/decision_date', old_value='2026-11-07', new_value='2026-11-06')])
        self.assert_status('no_known_block_in_scope')

    def test_semantic_correction_requires_resolution(self):
        self.add('correct_record', target=self.approval,
                 changes=[dict(path='/subject/revision', old_value='r0001', new_value='r0002')])
        self.assert_code('SEMANTIC_CORRECTION_REQUIRES_RESOLUTION', unsupported=True)

    def test_correction_old_value_and_calendar(self):
        did = self.add('correct_record', target=self.approval,
                       changes=[dict(path='/decision_date', old_value='wrong', new_value='2026-11-06')])
        self.assert_code('CORRECTION_OLD_VALUE_MISMATCH')
        record = self.document(did)
        record['changes'][0].update(old_value='2026-11-07', new_value='2026-02-30')
        self.replace(did, record)
        self.assert_code('INVALID_CORRECTED_METADATA')

    def test_duplicate_correction_field(self):
        change = dict(path='/decision_date', old_value='2026-11-07', new_value='2026-11-06')
        self.add('correct_record', target=self.approval, changes=[change, change])
        self.assert_code('DUPLICATE_CORRECTION_FIELD')

    def test_unknown_event_not_ignored_even_for_other_subject(self):
        self.add('unknown_future_event')
        self.assert_code('UNSUPPORTED_DECISION', unsupported=True)

    def test_unknown_predicate_not_ignored(self):
        self.add('restrict_use', conditions={'script': 'never execute'})
        self.assert_code('INVALID_DECISION')

    def test_invalid_event_calendar(self):
        self.add('restrict_use', decision_date='2026-02-30')
        self.assert_code('INVALID_DECISION')

    def test_scope_cannot_be_empty_or_implicit(self):
        did = self.add('restrict_use', scope=dict(operations=[], areas=['*']))
        self.assert_code('INVALID_DECISION')
        del self.blobs[self.path(did)]
        report = self.result(operation='*')
        self.assertEqual(report['diagnostics'], [dict(code='EXPLICIT_CONTEXT_REQUIRED')])
        self.assertFalse(report['transition_allowed'])

    def test_duplicate_id_or_wrong_path(self):
        self.blobs['catalog/approvals/wrong.json'] = self.blobs[self.path(self.approval)]
        self.assert_code('DUPLICATE_DECISION')

    def test_no_network_or_source_mutation(self):
        block = self.add('revoke_use')
        self.add('lift_restriction', target=block)
        before = dict(self.blobs)
        with patch('socket.socket', side_effect=AssertionError('Network attempted')):
            self.assert_status('no_known_block_in_scope')
        self.assertEqual(self.blobs, before)

    def test_parser_and_dependency_failures(self):
        self.blobs[self.path(self.approval)] = b'{"a":1,"a":2}'
        self.assert_code('INPUT_OR_DEPENDENCY_UNAVAILABLE')
        def missing():
            raise ImportError('not to disclose')
        with patch.dict(GLOBALS, _load=missing):
            self.assert_code('ENGINE_UNAVAILABLE', unsupported=True)

    def test_no_secret_in_diagnostic(self):
        self.blobs['/private/never-echo'] = b'secret'
        report = self.result()
        self.assertEqual(report['diagnostics'], [dict(code='INVALID_INPUT_PATH')])
        self.assertNotIn('never-echo', json.dumps(report))
        self.assertNotIn('secret', json.dumps(report))

    def test_context_is_explicit_in_result(self):
        report = self.result(operation='validate', area='local')
        self.assertEqual(report['context'], dict(operation='validate', area='local', subjects=[self.subject]))
        self.assertIn('artifact_integrity', report['not_checked'])
        self.assertIn('dependency_graph', report['not_checked'])

    def test_target_must_have_same_subject(self):
        block = self.add('revoke_use')
        other = dict(self.subject, entity_id='ENT-0002')
        self.add('approve_revision', subject=other)
        self.add('lift_restriction', subject=other, target=block)
        self.assert_code('TARGET_SUBJECT_MISMATCH')

    def test_lift_of_lift_is_not_automatic_revoke(self):
        block = self.add('revoke_use')
        lift = self.add('lift_restriction', target=block)
        self.add('lift_restriction', target=lift)
        self.assert_code('INVALID_LIFT_TARGET')

    def test_zero_identity_not_permission(self):
        document = self.document(self.approval)
        document['subject']['entity_id'] = 'ENT-0000'
        self.replace(self.approval, document)
        self.assert_code('ZERO_IDENTITY')

    def test_limits_fail_closed(self):
        self.blobs = {f'file{i}': b'{}' for i in range(10001)}
        self.assert_code('INPUT_LIMIT_OR_TYPE')

    def test_actual_positive_ledger_stays_without_overall_admission(self):
        blobs = {p.relative_to(BASE).as_posix(): p.read_bytes()
                 for p in (BASE / 'catalog/approvals').glob('*.json')}
        report = evaluate(blobs, [self.subject], operation='export', area='agent_system.validation')
        self.assertEqual(report['status'], 'no_known_block_in_scope')
        self.assertFalse(report['transition_allowed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
