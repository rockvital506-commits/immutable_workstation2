#!/usr/bin/env python3
"""Structural protocol regressions only. Not a run executor/evidence validator."""
import copy
import hashlib
from importlib import metadata
from pathlib import Path
import runpy
import unittest

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

BASE = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
HELPERS = BASE / 'validation/ent-0004/r0002/verify.py'
HELPERS_SHA = '1523ca399a9aee8f89656591b62e1d776504385fe025131c818c694ebb32aedf'
BASE_SCHEMA = BASE / 'specification/ent-0003/r0002/catalog-base.schema.json'
BASE_SHA = '42fab3c453930ad9128b2b422837b82d84db9ed6092872765bd7fe1ffaf9a820'
PLAN_SHA = 'e53e11315ebe54566edc5a395e7c4eee57cb82bdac86f9573feed57a0602664b'
REPORT_SHA = '7dece17f75d695484b2814c89f17f4e1623f6fec033d24c92953c740540da8bc'
PROFILE = 'linux-observed-set-5r3-6r3'
CID = '83bd5866-5e17-477f-9671-4e6a91481221'
ID = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
NOT_CHECKED = ['plan_authentication', 'source_authentication', 'global_event_completeness',
               'core_coverage', 'environment_compatibility', 'release_permission',
               'activation_permission', 'semantic_correction_resolution', 'release_decisions']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def deny(_uri):
    raise ValueError('Unregistered retrieval forbidden')


def load():
    if metadata.version('jsonschema') != '4.26.0':
        raise ValueError('Unsupported engine')
    if sha(HELPERS.read_bytes()) != HELPERS_SHA:
        raise ValueError('Installed helper changed')
    tools = runpy.run_path(str(HELPERS))
    parse = tools['strict_json']
    inputs = [(BASE_SCHEMA, BASE_SHA), (HERE / 'validation-plan.schema.json', PLAN_SHA),
              (HERE / 'validation-run-report.schema.json', REPORT_SHA)]
    schemas = []
    for path, digest in inputs:
        raw = path.read_bytes()
        if sha(raw) != digest:
            raise ValueError('Installed schema changed')
        schema = parse(raw)
        Draft202012Validator.check_schema(schema)
        schemas.append(schema)
    checker = tools['local_validator'](schemas[0]).format_checker
    registry = Registry(retrieve=deny).with_resources(
        [(s['$id'], Resource.from_contents(s)) for s in schemas])
    validators = [Draft202012Validator(s, registry=registry, format_checker=checker)
                  for s in schemas[1:]]
    return parse, validators, schemas


def tuple_for(path):
    return dict(path=path, sha256='a' * 64, size_bytes=1)


def plan_fixture():
    return dict(schema_version='1', kind='validation_plan', plan_id=ID, catalog_id=CID,
                execution_profile=PROFILE, expectation_authority='caller_supplied_not_authenticated',
                context=dict(operation='export', area='agent_system.validation'),
                selection=[dict(catalog_id=CID, entity_id='ENT-0006', revision='r0003')],
                registry=tuple_for('catalog/registry.json'), artifacts=[tuple_for('fixtures/core.md')],
                decisions=[tuple_for('catalog/approvals/' + ID + '.json')])


def stage_fixture(status):
    stage = dict(status=status, diagnostics=[])
    if status != 'not_run':
        stage['evidence'] = dict(sha256='b' * 64, size_bytes=10)
    if status in ('failed', 'unsupported', 'blocked_known_scope'):
        stage['diagnostics'] = [dict(code='KNOWN_SCOPE_BLOCK' if status == 'blocked_known_scope'
                                     else 'SYNTHETIC_FAILURE')]
    return stage


def report_fixture(status='passed_known_inputs', acquisition='passed_known_inputs', binding='passed_known_inputs'):
    return dict(schema_version='1', kind='validation_run_report', run_id=CID, plan_id=ID,
                plan=dict(sha256='c' * 64, size_bytes=123), execution_profile=PROFILE,
                source_consistency='mutable_tree_observations', status=status,
                overall_admission='not_evaluated', transition_allowed=False,
                stages=dict(acquisition=stage_fixture(acquisition), binding=stage_fixture(binding)),
                not_checked=list(NOT_CHECKED))


class PlanReportSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parse, (cls.plan_validator, cls.report_validator), cls.schemas = load()
        cls.parse = staticmethod(parse)

    def valid_plan(self, value):
        return self.plan_validator.is_valid(value)

    def valid_report(self, value):
        return self.report_validator.is_valid(value)

    def test_plan_shape_positive(self):
        self.assertTrue(self.valid_plan(plan_fixture()))

    def test_report_shape_positive_not_execution(self):
        self.assertTrue(self.valid_report(report_fixture()))

    def test_required_fields(self):
        for fixture, validate in [(plan_fixture, self.valid_plan), (report_fixture, self.valid_report)]:
            for key in fixture():
                with self.subTest(key=key, kind=fixture.__name__):
                    value = fixture()
                    del value[key]
                    self.assertFalse(validate(value))

    def test_unknown_fields_never_ignored(self):
        for key in ['source_root', 'command', 'activation', 'approved', 'latest', 'timestamp']:
            for fixture, validate in [(plan_fixture, self.valid_plan), (report_fixture, self.valid_report)]:
                value = fixture()
                value[key] = 'untrusted'
                self.assertFalse(validate(value))

    def test_profile_is_exact_not_fallback(self):
        for profile in ['latest', 'linux', 'linux-observed-set-5r2-6r2', '*', '']:
            for fixture, validate in [(plan_fixture, self.valid_plan), (report_fixture, self.valid_report)]:
                value = fixture()
                value['execution_profile'] = profile
                self.assertFalse(validate(value))

    def test_authority_cannot_self_approve(self):
        for authority in ['approved', 'owner_authenticated', True, None]:
            value = plan_fixture()
            value['expectation_authority'] = authority
            self.assertFalse(self.valid_plan(value))

    def test_context_concrete_identifiers(self):
        for key in ['operation', 'area']:
            for bad in ['*', '', 'Export', 'a/b', 'a\n', 'a' * 129, None]:
                value = plan_fixture()
                value['context'][key] = bad
                self.assertFalse(self.valid_plan(value))

    def test_selection_exact_nonempty_unique(self):
        for selection in [[], [dict(catalog_id=CID, entity_id='ENT-0006', revision='latest')],
                          plan_fixture()['selection'] * 2]:
            value = plan_fixture()
            value['selection'] = selection
            self.assertFalse(self.valid_plan(value))

    def test_registry_path_fixed(self):
        value = plan_fixture()
        value['registry']['path'] = 'other/registry.json'
        self.assertFalse(self.valid_plan(value))

    def test_artifact_cannot_hide_decision(self):
        for path in ['catalog/approvals', 'catalog/approvals/.hidden', 'catalog/approvals/' + ID + '.json']:
            value = plan_fixture()
            value['artifacts'][0]['path'] = path
            self.assertFalse(self.valid_plan(value))

    def test_decisions_flat_lowercase_uuid_only(self):
        for path in ['catalog/approvals/other.json', 'catalog/approvals/' + ID.upper() + '.json',
                     'catalog/approvals/nested/' + ID + '.json', 'catalog/approvals/.hidden',
                     'elsewhere/' + ID + '.json']:
            value = plan_fixture()
            value['decisions'][0]['path'] = path
            self.assertFalse(self.valid_plan(value))

    def test_relative_paths_and_exact_digest(self):
        for path in ['/private/a', '../escape', 'x/../a', 'a//b', 'a\\b', 'a\n']:
            value = plan_fixture()
            value['artifacts'][0]['path'] = path
            self.assertFalse(self.valid_plan(value))
        for digest in ['a' * 63, 'A' * 64, 'a' * 64 + '\n']:
            value = plan_fixture()
            value['artifacts'][0]['sha256'] = digest
            self.assertFalse(self.valid_plan(value))

    def test_size_bound_and_no_role(self):
        for size in [-1, True, 16 * 1024 * 1024 + 1]:
            value = plan_fixture()
            value['artifacts'][0]['size_bytes'] = size
            self.assertFalse(self.valid_plan(value))
        value = plan_fixture()
        value['artifacts'][0]['role'] = 'normative'
        self.assertFalse(self.valid_plan(value))

    def test_links_use_base_tuple_without_duplicate_definitions(self):
        value = plan_fixture()
        item = value['artifacts'][0]
        item.update(links=[dict(path=item['path'], link_type='symbolic_link', target='core-v2.md')],
                    resolved_path='fixtures/core-v2.md')
        self.assertTrue(self.valid_plan(value))
        del item['resolved_path']
        self.assertFalse(self.valid_plan(value))

    def test_empty_decisions_plan_is_not_semantic_approval(self):
        value = plan_fixture()
        value['decisions'] = []
        self.assertTrue(self.valid_plan(value))

    def test_complete_status_matrix(self):
        matrix = {('not_run', 'not_run'): 'incomplete',
                  ('passed_known_inputs', 'not_run'): 'incomplete',
                  ('passed_known_inputs', 'passed_known_inputs'): 'passed_known_inputs',
                  ('passed_known_inputs', 'blocked_known_scope'): 'blocked_known_scope',
                  ('failed', 'not_run'): 'failed', ('unsupported', 'not_run'): 'unsupported',
                  ('passed_known_inputs', 'failed'): 'failed',
                  ('passed_known_inputs', 'unsupported'): 'unsupported'}
        for acquisition in ['not_run', 'passed_known_inputs', 'failed', 'unsupported']:
            for binding in ['not_run', 'passed_known_inputs', 'blocked_known_scope', 'failed', 'unsupported']:
                for status in ['passed_known_inputs', 'blocked_known_scope', 'failed', 'unsupported', 'incomplete']:
                    with self.subTest(acquisition=acquisition, binding=binding, status=status):
                        self.assertEqual(self.valid_report(report_fixture(status, acquisition, binding)),
                                         matrix.get((acquisition, binding)) == status)

    def test_not_run_cannot_reuse_evidence(self):
        value = report_fixture('incomplete', 'not_run', 'not_run')
        value['stages']['acquisition']['evidence'] = dict(sha256='a' * 64, size_bytes=10)
        self.assertFalse(self.valid_report(value))

    def test_success_requires_evidence_no_diagnostics(self):
        for key in ['acquisition', 'binding']:
            value = report_fixture()
            del value['stages'][key]['evidence']
            self.assertFalse(self.valid_report(value))
            value = report_fixture()
            value['stages'][key]['diagnostics'] = [dict(code='FAILURE')]
            self.assertFalse(self.valid_report(value))

    def test_failure_without_child_report_supported(self):
        value = report_fixture('failed', 'failed', 'not_run')
        del value['stages']['acquisition']['evidence']
        self.assertTrue(self.valid_report(value))
        value['stages']['acquisition']['diagnostics'] = []
        self.assertFalse(self.valid_report(value))

    def test_blocked_summary_code_is_explicit(self):
        value = report_fixture('blocked_known_scope', 'passed_known_inputs', 'blocked_known_scope')
        value['stages']['binding']['diagnostics'] = [dict(code='OTHER_CODE')]
        self.assertFalse(self.valid_report(value))

    def test_private_diagnostic_text_rejected(self):
        for code in ['/private/source', 'file contents', 'FAIL\n', 'a' * 100]:
            value = report_fixture('failed', 'failed', 'not_run')
            value['stages']['acquisition']['diagnostics'] = [dict(code=code)]
            self.assertFalse(self.valid_report(value))

    def test_admission_never_granted(self):
        for key, bad in [('overall_admission', 'passed'), ('transition_allowed', True),
                         ('source_consistency', 'atomic_snapshot')]:
            value = report_fixture()
            value[key] = bad
            self.assertFalse(self.valid_report(value))

    def test_unchecked_obligations_cannot_disappear(self):
        for obligation in NOT_CHECKED:
            value = report_fixture()
            value['not_checked'].remove(obligation)
            self.assertFalse(self.valid_report(value))

    def test_references_are_bytes_not_retrieval_paths(self):
        value = report_fixture()
        value['plan']['path'] = '/private/plan.json'
        self.assertFalse(self.valid_report(value))

    def test_strict_json_rejects_ambiguous_encodings_and_constants(self):
        for raw in [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}',
                    b'\xef\xbb\xbf{}', '{}'.encode('utf-16')]:
            with self.assertRaises((ValueError, UnicodeError)):
                self.parse(raw)

    def test_local_resources_only(self):
        schema = copy.deepcopy(self.schemas[1])
        schema['properties']['plan_id'] = {'$ref': 'https://invalid.example/schema.json'}
        requests = []
        def closed(uri):
            requests.append(uri)
            raise ValueError('Unregistered retrieval forbidden')
        registry = Registry(retrieve=closed)
        validator = Draft202012Validator(schema, registry=registry)
        with self.assertRaises(Exception):
            list(validator.iter_errors(plan_fixture()))
        self.assertEqual(requests, ['https://invalid.example/schema.json'])

    def test_raw_bytes_not_reserialized_hash(self):
        one, two = b'{"x":1}\n', b'{ "x":1 }\n'
        self.assertEqual(self.parse(one), self.parse(two))
        self.assertNotEqual(sha(one), sha(two))

    def test_shape_does_not_prove_cross_document_binding(self):
        value = report_fixture()
        value['plan_id'] = CID  # No raw plan/evidence was supplied to Schema.
        value['plan']['sha256'] = '0' * 64
        self.assertTrue(self.valid_report(value))
        plan = plan_fixture()
        plan['artifacts'].append(dict(plan['artifacts'][0], sha256='b' * 64))
        self.assertTrue(self.valid_plan(plan))  # Path uniqueness needs semantic validation.

    def test_shape_does_not_prove_catalog_identity_or_aggregate_limit(self):
        value = plan_fixture()
        value['selection'][0]['catalog_id'] = ID
        value['artifacts'] = [dict(path='fixtures/' + str(i), sha256='a' * 64,
                                   size_bytes=16 * 1024 * 1024) for i in range(5)]
        self.assertTrue(self.valid_plan(value))  # >64 MiB: executor must reject before acquisition.


if __name__ == '__main__':
    unittest.main(verbosity=2)
