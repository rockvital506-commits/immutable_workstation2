#!/usr/bin/env python3
"""Executable structural regression tests; NOT a catalog permission validator."""
import copy
import hashlib
from importlib import metadata
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry

BASE = Path(__file__).resolve().parents[3]
SCHEMA_PATH = BASE / 'specification/ent-0003/r0002/catalog-base.schema.json'
SCHEMA_SHA256 = '42fab3c453930ad9128b2b422837b82d84db9ed6092872765bd7fe1ffaf9a820'


def reject_constant(_value):
    raise ValueError('Non-JSON number')


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def strict_json(data):
    # Explicit UTF-8 also rejects UTF-16/32 accepted by json.loads(bytes).
    return json.loads(data.decode('utf-8'), object_pairs_hook=unique_object,
                      parse_constant=reject_constant)


def no_retrieval(_uri):
    raise ValueError('External schema retrieval forbidden')


def local_validator(schema):
    def refs(value):
        if isinstance(value, dict):
            for key in ('$ref', '$dynamicRef'):
                if key in value and not value[key].startswith('#'):
                    raise ValueError('External schema reference forbidden')
            for child in value.values():
                refs(child)
        elif isinstance(value, list):
            for child in value:
                refs(child)
    if schema.get('$schema') != 'https://json-schema.org/draft/2020-12/schema':
        raise ValueError('Unsupported schema dialect')
    refs(schema)
    Draft202012Validator.check_schema(schema)
    checker = FormatChecker(formats=['date'])
    if checker.conforms('2026-02-30', 'date'):
        raise ValueError('Required date checker unavailable')
    return Draft202012Validator(schema, format_checker=checker,
                                registry=Registry(retrieve=no_retrieval))


class StructuralSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = SCHEMA_PATH.read_bytes()
        if hashlib.sha256(data).hexdigest() != SCHEMA_SHA256:
            raise ValueError('Approved schema bytes changed')
        cls.schema = strict_json(data)
        cls.validator = local_validator(cls.schema)
        cls.registry = strict_json((BASE / 'catalog/registry.json').read_bytes())
        # Synthetic, non-private base; one mutation per negative subcase.
        cls.approval = {
            'schema_version': '1',
            'decision_id': 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
            'decision_type': 'approve_revision',
            'subject': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221',
                        'entity_id': 'ENT-9999', 'revision': 'r0001'},
            'artifacts': [{'path': 'fixtures/file.md', 'sha256': 'a' * 64,
                           'size_bytes': 1}],
            'actor_role': 'owner', 'recorded_by': 'agent',
            'decision_date': '2026-11-07', 'statement': 'Synthetic approval',
            'statement_form': 'summary', 'basis': 'Isolated fixture, not permission'}

    def valid(self, instance):
        self.assertFalse(any(self.validator.iter_errors(instance)),
                         'Unexpected structural rejection')

    def invalid(self, instance):
        self.assertTrue(any(self.validator.iter_errors(instance)),
                        'Expected structural rejection')

    def test_engine_and_schema(self):
        self.assertEqual(metadata.version('jsonschema'), '4.26.0')
        Draft202012Validator.check_schema(self.schema)
        self.valid(self.approval)
        self.valid({'schema_version': '1', 'catalog_id': self.approval['subject']['catalog_id'],
                    'entities': []})

    def test_current_registry_and_known_decisions(self):
        self.valid(self.registry)
        paths = sorted((BASE / 'catalog/approvals').glob('*.json'))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(document=path.name):
                self.valid(strict_json(path.read_bytes()))

    def test_strict_parser_positive(self):
        self.assertEqual(strict_json(b'{"a":1}'), {'a': 1})
        self.assertEqual(strict_json('{"text":"тест"}'.encode()), {'text': 'тест'})

    def test_strict_parser_negative(self):
        for data in [b'{"a":1,"a":2}', b'{"a":{"x":1,"x":2}}',
                     b'NaN', b'Infinity', b'-Infinity', b'{} trailing',
                     b'\xff', b'\xef\xbb\xbf{}', '{}'.encode('utf-16')]:
            with self.subTest(case=data.hex()), self.assertRaises(ValueError):
                strict_json(data)

    def test_required_closed_fields_and_types(self):
        for key in self.approval:
            doc = copy.deepcopy(self.approval)
            del doc[key]
            with self.subTest(missing=key):
                self.invalid(doc)
        for field, value in [('unknown', True), ('schema_version', 1),
                             ('artifacts', []), ('decision_type', 'release_approval')]:
            doc = copy.deepcopy(self.approval)
            doc[field] = value
            with self.subTest(field=field):
                self.invalid(doc)
        for field, value in [('size_bytes', True), ('size_bytes', -1),
                             ('sha256', 'A' * 64), ('role', 'normative')]:
            doc = copy.deepcopy(self.approval)
            doc['artifacts'][0][field] = value
            with self.subTest(artifact_field=field, value=value):
                self.invalid(doc)

    def test_calendar_dates(self):
        for value in ['2024-02-29', '2026-11-07']:
            doc = dict(self.approval, decision_date=value)
            self.valid(doc)
        for value in ['2026-02-29', '2026-02-30', '2026-13-01', '2026-1-07',
                      '2026-11-07T00:00:00Z', '2026-11-07\n']:
            with self.subTest(date=value):
                self.invalid(dict(self.approval, decision_date=value))

    def test_logical_paths(self):
        for value in ['fixtures/file.md', 'каталог/файл.md']:
            doc = copy.deepcopy(self.approval)
            doc['artifacts'][0]['path'] = value
            self.valid(doc)
        for value in ['', '/file', '../file', 'a/../file', 'a/./file', 'a//file',
                      'a/', 'a\\file', 'C:/file', 'a\n', 'a\x00b']:
            doc = copy.deepcopy(self.approval)
            doc['artifacts'][0]['path'] = value
            with self.subTest(path=repr(value)):
                self.invalid(doc)

    def test_symlink_metadata_positive(self):
        # Structural fixtures only, no physical link traversal is being tested.
        for links in [
            [{'path': 'fixtures/link', 'link_type': 'symbolic_link', 'target': 'file.md'}],
            [{'path': 'alias', 'link_type': 'symbolic_link', 'target': 'fixtures'}],
            [{'path': 'alias', 'link_type': 'symbolic_link', 'target': 'fixtures'},
             {'path': 'fixtures/link', 'link_type': 'symbolic_link', 'target': '../real/file.md'}],
        ]:
            doc = copy.deepcopy(self.approval)
            doc['artifacts'][0].update(links=links, resolved_path='real/file.md')
            self.valid(doc)

    def test_symlink_metadata_negative(self):
        variants = [dict(links=[]), dict(resolved_path='real/file.md'),
                    dict(links=[], resolved_path='real/file.md'),
                    dict(links=[{'path': 'link', 'link_type': 'junction', 'target': 'real'}],
                         resolved_path='real/file.md'),
                    dict(links=[{'path': 'link', 'link_type': 'symbolic_link'}],
                         resolved_path='real/file.md')]
        for i, fields in enumerate(variants):
            doc = copy.deepcopy(self.approval)
            doc['artifacts'][0].update(fields)
            with self.subTest(case=i):
                self.invalid(doc)

    def test_structural_success_is_not_filesystem_admission(self):
        doc = copy.deepcopy(self.approval)
        doc['artifacts'][0].update(
            links=[{'path': 'link', 'link_type': 'symbolic_link', 'target': '/outside/private'}],
            resolved_path='claimed/file.md')
        # Expected: structure alone accepts target text. Nothing opens this path.
        with patch('pathlib.Path.open', side_effect=AssertionError('File read attempted')):
            self.valid(doc)

    def test_other_events_are_not_accepted_as_approvals(self):
        for kind in ['restrict_use', 'revoke_use', 'correct_record',
                     'lift_restriction', 'unknown_future_event']:
            with self.subTest(kind=kind):
                self.invalid(dict(self.approval, decision_type=kind))

    def test_no_external_schema_retrieval(self):
        for key in ['$ref', '$dynamicRef']:
            schema = copy.deepcopy(self.schema)
            schema[key] = 'https://example.invalid/never-fetch'
            with patch('socket.socket', side_effect=AssertionError('Network attempted')):
                with self.assertRaises(ValueError):
                    local_validator(schema)
        # The real schema also compiles and validates without socket access.
        with patch('socket.socket', side_effect=AssertionError('Network attempted')):
            self.assertTrue(local_validator(self.schema).is_valid(self.approval))

    def test_locked_versions_and_declared_licenses(self):
        expected_licenses = {
            'jsonschema': 'MIT', 'attrs': 'MIT', 'jsonschema-specifications': 'MIT',
            'referencing': 'MIT', 'rpds-py': 'MIT', 'typing_extensions': 'PSF-2.0'}
        lock = Path(__file__).with_name('requirements-linux-cp311.lock').read_text()
        entries = [line for line in lock.splitlines() if line and not line.startswith('#')]
        self.assertEqual(len(entries), 6)
        for line in entries:
            pin, hash_field = line.split()
            name, version = pin.split('==')
            self.assertEqual(metadata.version(name), version)
            self.assertTrue(hash_field.startswith('--hash=sha256:'))
            self.assertEqual(len(hash_field.removeprefix('--hash=sha256:')), 64)
            distribution = metadata.distribution(name)
            self.assertEqual(distribution.metadata.get('License-Expression'),
                             expected_licenses[name])
            self.assertTrue(any('license' in str(f).lower() or 'copying' in str(f).lower()
                                for f in distribution.files))

    def test_unknown_dialect_rejected(self):
        schema = copy.deepcopy(self.schema)
        schema['$schema'] = 'unknown'
        with self.assertRaises(ValueError):
            local_validator(schema)


if __name__ == '__main__':
    unittest.main(verbosity=2)
