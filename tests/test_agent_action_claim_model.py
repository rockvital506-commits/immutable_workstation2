#!/usr/bin/env python3
"""I2b finite MODEL ONLY. No durable claims, readiness verifier or actuator.

Gate facts/receipt_verified are axioms, never production authorization inputs.
The serial model cannot prove OS atomicity/concurrency/durability/source truth.
"""
import copy
import os
from dataclasses import dataclass, replace
from itertools import product
from pathlib import Path
import runpy
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
BASE = Path(ROOT)


@dataclass(frozen=True)
class Binding:
    namespace: str = 'model-authority'
    action: str = 'export'
    subject: str = 'model-subject-pin'
    release_grant: str = 'model-parent-release'
    grant: str = 'model-export-grant'
    export_id: str = 'model-export-id'
    descriptor: str = 'model-descriptor-pin'
    destination: str = 'model-destination-pin'
    procedure: str = 'model-procedure-pin'
    prompt: str = 'model-prompt-pin'

    def keys(self):
        if self.action not in ('release', 'export'):
            raise ValueError('MODEL_ACTION_UNSUPPORTED')
        if any(type(v) is not str or not v for v in vars(self).values()):
            raise ValueError('MODEL_BINDING_SYMBOL_INVALID')
        if self.action == 'release' and self.grant != self.release_grant:
            raise ValueError('MODEL_RELEASE_GRANT_BINDING')
        keys = {('grant', self.namespace, self.action, self.grant)}
        if self.action == 'export':
            keys.add(('export_id', self.namespace, self.export_id))
        return keys


@dataclass(frozen=True)
class GateAxioms:
    source: bool = True
    permission: bool = True
    entity: bool = True
    readiness: bool = True
    current: bool = True
    procedure: bool = True
    parent: bool = True
    destination: bool = True

    def holds(self, action):
        fields = ['source', 'permission', 'entity', 'readiness', 'current', 'procedure']
        if action == 'export':
            fields += ['parent', 'destination']
        return all(getattr(self, k) is True for k in fields)


class ModelBook:
    """Single logical transition at a time; in-memory, NOT a permission service."""
    def __init__(self):
        self.claims = {}
        self.consumed = set()

    def reserve(self, request, binding, basis, current, gates):
        keys = binding.keys()
        if (type(request) is not str or not request or request in self.claims
                or type(basis) is not str or not basis or type(current) is not str
                or basis != current or not gates.holds(binding.action)
                or keys & self.consumed):
            return False
        self.consumed.update(keys)
        self.claims[request] = dict(binding=binding, basis=basis, state='reserved', starts=0)
        return True

    def start(self, request, binding, current, gates):
        row = self.claims.get(request)
        if row is None or row['state'] != 'reserved':
            return False
        if (binding != row['binding'] or current != row['basis']
                or not gates.holds(binding.action)):
            row['state'] = 'failed'
            return False
        row.update(state='executing', starts=1)
        return True

    def finish(self, request, binding, outcome, *, receipt_verified=False):
        row = self.claims.get(request)
        if (row is None or row['binding'] != binding
                or row['state'] not in ('reserved', 'executing')
                or outcome not in ('failed', 'outcome_unknown', 'succeeded')):
            return False
        if outcome == 'succeeded' and (row['state'] != 'executing' or receipt_verified is not True):
            return False
        row['state'] = outcome
        return True

    def crash(self):
        for row in self.claims.values():
            if row['state'] in ('reserved', 'executing'):
                row['state'] = 'outcome_unknown'

    def snapshot(self):
        return (tuple(sorted(self.consumed)), tuple(sorted(
            (k, repr(v['binding']), v['basis'], v['state'], v['starts'])
            for k, v in self.claims.items())))

    def safe_model_report(self):
        return dict(verification_level='model_review', durable_claim_created=False,
                    agent_behavior_verified=False, overall_admission='not_evaluated',
                    performed=False, transition_allowed=False, release_allowed=False,
                    export_allowed=False, activation_allowed=False)


class ActionClaimModelTests(unittest.TestCase):
    def setUp(self):
        self.book = ModelBook(); self.binding = Binding(); self.gates = GateAxioms()

    def reserve(self, request='A', binding=None, current='current', gates=None):
        return self.book.reserve(request, binding or self.binding, 'current', current, gates or self.gates)

    def start(self, request='A', binding=None, current='current', gates=None):
        return self.book.start(request, binding or self.binding, current, gates or self.gates)

    def test_required_gate_truth_table(self):
        names = tuple(vars(self.gates))
        count = 0
        for action in ('release', 'export'):
            for values in product((False, True), repeat=len(names)):
                gates = GateAxioms(**dict(zip(names, values)))
                expected = all(values[:6]) and (action == 'release' or all(values[6:]))
                book = ModelBook(); binding = replace(self.binding, action=action, grant=self.binding.release_grant if action == 'release' else self.binding.grant)
                self.assertEqual(book.reserve('A', binding, 'v', 'v', gates), expected)
                self.assertEqual(len(book.claims), int(expected)); count += 1
        self.assertEqual(count, 512)

    def test_truthy_is_not_verified_gate(self):
        for field in vars(self.gates):
            for value in (1, 'ready', {}, None):
                book = ModelBook()
                self.assertFalse(book.reserve('A', self.binding, 'v', 'v', replace(self.gates, **{field:value})))
                self.assertFalse(book.consumed)

    def test_preflight_stale_does_not_consume(self):
        self.assertFalse(self.reserve(current='other'))
        self.assertFalse(self.book.consumed); self.assertTrue(self.reserve())

    def test_new_request_context_subject_cannot_replay_export(self):
        self.assertTrue(self.reserve())
        for binding in (self.binding, replace(self.binding, subject='other'),
                        replace(self.binding, destination='other'), replace(self.binding, descriptor='other')):
            self.assertFalse(self.book.reserve('B', binding, 'new', 'new', self.gates))
        self.assertEqual(len(self.book.claims), 1)

    def test_export_id_and_grant_each_independently_unique(self):
        self.assertTrue(self.reserve())
        self.assertFalse(self.reserve('B', replace(self.binding, grant='new-grant')))
        self.assertFalse(self.reserve('B', replace(self.binding, export_id='new-export')))
        self.assertTrue(self.reserve('B', replace(self.binding, grant='new-grant', export_id='new-export')))

    def test_same_request_id_not_available_for_other_binding(self):
        self.assertTrue(self.reserve())
        self.assertFalse(self.reserve('A', replace(self.binding, grant='new', export_id='new')))

    def test_namespace_scoping_not_global_completeness(self):
        self.assertTrue(self.reserve())
        self.assertTrue(self.reserve('B', replace(self.binding, namespace='independently-bootstrapped')))
        # Passing a different namespace is not proof that bootstrap is legitimate.

    def test_each_binding_field_is_exact_at_start(self):
        for name in vars(self.binding):
            self.book = ModelBook(); self.assertTrue(self.reserve())
            value = 'release' if name == 'action' else 'other'
            self.assertFalse(self.start(binding=replace(self.binding, **{name:value})))
            self.assertEqual(self.book.claims['A']['state'], 'failed')
            self.assertFalse(self.reserve('B'))

    def test_stale_or_new_negative_between_reserve_and_start(self):
        for name in vars(self.gates):
            self.book = ModelBook(); self.assertTrue(self.reserve())
            self.assertFalse(self.start(gates=replace(self.gates, **{name:False})))
            self.assertFalse(self.reserve('B'))
        self.book = ModelBook(); self.assertTrue(self.reserve())
        self.assertFalse(self.start(current='new-head')); self.assertFalse(self.reserve('B'))

    def test_start_is_once_success_requires_modeled_receipt(self):
        self.assertTrue(self.reserve())
        self.assertFalse(self.book.finish('A', self.binding, 'succeeded', receipt_verified=True))
        self.assertTrue(self.start()); self.assertFalse(self.start())
        for value in (False, 1, 'verified'):
            self.assertFalse(self.book.finish('A', self.binding, 'succeeded', receipt_verified=value))
        self.assertTrue(self.book.finish('A', self.binding, 'succeeded', receipt_verified=True))
        self.assertFalse(self.start()); self.assertFalse(self.reserve('B'))

    def test_terminal_outcomes_are_absorbing_and_consumed(self):
        for outcome in ('failed', 'outcome_unknown', 'succeeded'):
            self.book = ModelBook(); self.assertTrue(self.reserve()); self.assertTrue(self.start())
            self.assertTrue(self.book.finish('A', self.binding, outcome, receipt_verified=True))
            for other in ('failed', 'outcome_unknown', 'succeeded'):
                self.assertFalse(self.book.finish('A', self.binding, other, receipt_verified=True))
            self.book.crash(); self.assertEqual(self.book.claims['A']['state'], outcome)
            self.assertFalse(self.reserve('B'))

    def test_lost_reserve_receipt_or_crash_does_not_regrant(self):
        for started in (False, True):
            self.book = ModelBook(); self.assertTrue(self.reserve())
            if started: self.assertTrue(self.start())
            self.book.crash(); self.assertEqual(self.book.claims['A']['state'], 'outcome_unknown')
            self.assertFalse(self.start()); self.assertFalse(self.reserve('B'))

    def test_stop_after_start_records_failure_without_undo_claim(self):
        self.assertTrue(self.reserve()); self.assertTrue(self.start())
        self.assertTrue(self.book.finish('A', self.binding, 'failed'))
        self.assertFalse(self.book.finish('A', self.binding, 'succeeded', receipt_verified=True))
        self.assertFalse(self.reserve('B'))

    def test_release_and_two_exports_have_distinct_claim_keys(self):
        release = replace(self.binding, action='release', grant=self.binding.release_grant)
        self.assertTrue(self.reserve('release', release))
        self.assertTrue(self.reserve('export1'))
        self.assertTrue(self.reserve('export2', replace(self.binding, grant='export2', export_id='export2')))
        self.assertEqual(len(self.book.claims), 3)
        # Neither the parent permission nor these model reservations prove performed release.

    def test_unknown_action_and_blank_binding_symbols_rejected(self):
        for binding in (replace(self.binding, action='activate'), replace(self.binding, namespace='')):
            with self.assertRaises(ValueError): self.reserve(binding=binding)
        self.assertFalse(self.book.consumed)

    def test_model_outputs_never_actual_permission_or_execution(self):
        self.assertTrue(self.reserve()); self.assertTrue(self.start())
        self.assertTrue(self.book.finish('A', self.binding, 'succeeded', receipt_verified=True))
        report = self.book.safe_model_report()
        for k in ('durable_claim_created','performed','transition_allowed','release_allowed','export_allowed','activation_allowed'):
            self.assertIs(report[k], False)
        self.assertEqual(report['verification_level'], 'model_review')

    def test_exhaustive_bounded_two_caller_serial_interleavings(self):
        frontier = {self.book.snapshot(): self.book}; seen = set(frontier); edges = 0
        # Each command is an atomic MODEL step, not evidence of physical lock correctness.
        commands = [(op, who) for op in ('reserve','start','succeeded','failed','outcome_unknown') for who in ('A','B')]+[('crash','')]
        for _depth in range(7):
            following = {}
            for book in frontier.values():
                for op, who in commands:
                    new = copy.deepcopy(book)
                    if op == 'reserve': new.reserve(who, self.binding, 'current', 'current', self.gates)
                    elif op == 'start': new.start(who, self.binding, 'current', self.gates)
                    elif op == 'crash': new.crash()
                    else: new.finish(who, self.binding, op, receipt_verified=True)
                    edges += 1
                    self.assertLessEqual(len(new.claims), 1)
                    self.assertLessEqual(sum(v['starts'] for v in new.claims.values()), 1)
                    self.assertEqual(new.consumed, set().union(*(v['binding'].keys() for v in new.claims.values())))
                    key = new.snapshot(); seen.add(key); following[key] = new
            frontier = following
        # absent + 2 callers * (reserved, executing, succeeded,
        # failed-before/after-start, unknown-before/after-start).
        self.assertEqual(len(seen), 1 + 2 * 7)
        self.assertEqual(edges, 11 * (1 + 3 + 9 + 15 + 15 + 15 + 15))
        print(f'MODEL: depth7, callers2, commands11, unique_states={len(seen)}, explored_edges={edges}')


class ActionClaimExistingBoundaryTests(unittest.TestCase):
    def test_physical_r3_checks_do_not_consume_export(self):
        fixtures = runpy.run_path(str(BASE/'agent_system/permissions/ent-0014/r0003/verify.py'))
        f = fixtures['StateTests']('runTest'); f.setUp(); self.addCleanup(f.doCleanups)
        f.create(); raw, source, parent = f.event(); f.add(raw, source)
        subject = fixtures['json'].loads(f.subject)
        export = dict(export_id=fixtures['uid'](), paths=['payload/test.md'], destination=fixtures['ref'](b'SYNTHETIC destination\n'),
                      procedure=subject['procedure'], prompt=subject['prompt'])
        raw, source, grant = f.event('authorize_export','export',parent=parent,export=export); f.add(raw, source)
        first = f.check(grant, 'export', export); second = f.check(grant, 'export', export)
        for r in (first, second):
            self.assertTrue(r['check_result']['export_permission_recognized'])
            self.assertTrue(r['check_id_consumed']); self.assertFalse(r['action_claim_created'])
            self.assertFalse(r['check_result']['export_allowed']); self.assertFalse(r['check_result']['performed'])
        self.assertEqual(second['receipt']['checks_count'], 2)
        self.assertNotEqual(first['check_result']['request'], second['check_result']['request'])
        with f.open() as store: self.assertEqual(store.summary(), second['receipt'])

    def test_native_incomplete_guard_still_closed_without_readiness_injection(self):
        fixtures = runpy.run_path(str(BASE/'agent_system/permissions/ent-0014/r0002/verify.py'))
        for export in (False, True):
            with self.subTest(export=export):
                f = fixtures['NativeGuardTests']('runTest'); f.setUp(); f.fixture(export)
                r = f.check_native()
                self.assertEqual(r['status'], 'blocked_incomplete_candidate')
                self.assertEqual(r['readiness'], 'incomplete_candidate'); self.assertTrue(r['authority_valid'])
                self.assertFalse(r['performed']); self.assertFalse(r['release_allowed']); self.assertFalse(r['export_allowed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
