#!/usr/bin/env python3
"""Regression checks for the implemented catalog fragment.

Not a general catalog/event validator, behavior test, or proof of authorship.
The artifact reader below is only a fixture helper, not the symlink validator
required by ENT-0002 r0002.
"""
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import unittest
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
ROOT = Path(ROOT)
BASE = ROOT / 'agent_system'
CATALOG_ID = '83bd5866-5e17-477f-9671-4e6a91481221'
DIGEST = '684e18cc01dc6b1ffd66899615df03b01e756f40f1354f3ac82a81563a944773'


def artifact_bytes(item):
    path = item['path']
    parts = PurePosixPath(path)
    if (not path or parts.is_absolute() or '\\' in path or ':' in path
            or any(p in ('', '.', '..') for p in path.split('/'))):
        raise ValueError('Unsafe relative path')
    full = BASE / path
    if not full.resolve().is_relative_to(BASE.resolve()):
        raise ValueError('Path escapes catalog')
    data = full.read_bytes()
    if hashlib.sha256(data).hexdigest() != item['sha256']:
        raise ValueError('Digest mismatch')
    if 'size_bytes' in item and len(data) != item['size_bytes']:
        raise ValueError('Size mismatch')
    return data


class FirstCatalogTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads((BASE / 'catalog/registry.json').read_bytes())
        self.entity = next(e for e in self.registry['entities']
                           if e['entity_id'] == 'ENT-0001')
        self.rev = self.entity['revisions'][0]
        self.reference = self.rev['approval']['reference']
        self.decision = json.loads(artifact_bytes(self.reference))

    def test_identity_and_initial_scope(self):
        self.assertEqual(self.registry['schema_version'], '1')
        self.assertEqual(str(uuid.UUID(self.registry['catalog_id'])), CATALOG_ID)
        self.assertEqual({e['entity_id'] for e in self.registry['entities']},
                         {'ENT-0001', 'ENT-0002', 'ENT-0003', 'ENT-0004', 'ENT-0005', 'ENT-0006', 'ENT-0007', 'ENT-0008', 'ENT-0009', 'ENT-0010', 'ENT-0011', 'ENT-0012', 'ENT-0013', 'ENT-0014', 'ENT-0015', 'ENT-0016', 'ENT-0017', 'ENT-0018'})
        self.assertEqual(len(self.registry['entities']), 18)
        self.assertEqual(self.entity['entity_id'], 'ENT-0001')
        self.assertEqual(self.rev['revision'], 'r0001')
        self.assertEqual(self.rev['kind'], 'contract')
        self.assertEqual(self.rev['relations'], [])

    def test_exact_presented_bytes(self):
        self.assertEqual(len(self.rev['artifacts']), 1)
        artifact = self.rev['artifacts'][0]
        data = artifact_bytes(artifact)
        self.assertEqual(artifact['sha256'], DIGEST)
        self.assertEqual(len(data), 7564)
        self.assertEqual(artifact['role'], 'normative')
        self.assertFalse(data.startswith(b'\xef\xbb\xbf'))
        self.assertNotIn(b'\r', data)
        self.assertTrue(data.endswith(b'\n') and not data.endswith(b'\n\n'))
        text = (ROOT / 'research/30-agent-system-discovery.md').read_text()
        presented = text.split('### 25.2.', 1)[1].split('```markdown\n', 1)[1].split('```', 1)[0]
        self.assertEqual(data, presented.encode('utf-8'))

    def test_decision_subject_and_complete_artifacts(self):
        d = self.decision
        self.assertEqual(d['subject'], dict(catalog_id=CATALOG_ID,
                                          entity_id='ENT-0001', revision='r0001'))
        artifacts = [{k: a[k] for k in ('path', 'sha256', 'size_bytes')}
                     for a in self.rev['artifacts']]
        self.assertEqual(d['artifacts'], artifacts)
        for a in d['artifacts']:
            artifact_bytes(a)
        self.assertEqual(self.reference['path'], 'catalog/approvals/' + d['decision_id'] + '.json')
        self.assertEqual(str(uuid.UUID(d['decision_id'])), d['decision_id'])

    def test_actual_owner_statement_not_activation(self):
        d = self.decision
        self.assertEqual(self.rev['approval']['status'], 'approved')
        self.assertEqual(d['decision_type'], 'approve_revision')
        self.assertEqual(d['actor_role'], 'owner')
        self.assertEqual(d['recorded_by'], 'agent')
        self.assertEqual(d['statement_form'], 'quote')
        self.assertEqual(d['statement'], 'Оставить текущую версию и внедрить')
        self.assertEqual(d['decision_date'], '2026-11-07')
        self.assertIn('не выпуск и не активация', d['basis'])

    def test_bad_hash_and_size_rejected(self):
        for field, value in [('sha256', '0' * 64), ('size_bytes', 7565)]:
            item = copy.deepcopy(self.rev['artifacts'][0])
            item[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                artifact_bytes(item)
        ref = dict(self.reference, sha256='0' * 64)
        with self.assertRaises(ValueError):
            artifact_bytes(ref)

    def test_unsafe_paths_rejected(self):
        for path in ['../README.md', '/README.md', 'a/../b', 'a//b',
                     './README.md', 'C:/data', 'a\\b']:
            with self.subTest(path=path), self.assertRaises(ValueError):
                artifact_bytes(dict(path=path, sha256=DIGEST))


class ValidationContractTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads((BASE / 'catalog/registry.json').read_bytes())
        self.entity = next(e for e in self.registry['entities']
                           if e['entity_id'] == 'ENT-0002')
        self.rev = self.entity['revisions'][0]
        self.decision = json.loads(artifact_bytes(self.rev['approval']['reference']))

    def test_exact_revision_and_dependency(self):
        self.assertEqual([r['revision'] for r in self.entity['revisions']], ['r0002', 'r0003'])
        self.assertFalse((BASE / 'catalog/contracts/agent_system/ent-0002/r0001.md').exists())
        self.assertEqual(self.rev['kind'], 'contract')
        self.assertEqual(self.rev['relations'], [dict(type='depends_on', target=dict(
            catalog_id=CATALOG_ID, entity_id='ENT-0001', revision='r0001'))])
        target = self.rev['relations'][0]['target']
        dependency = next(e for e in self.registry['entities']
                          if e['entity_id'] == target['entity_id'])
        self.assertIn(target['revision'], [r['revision'] for r in dependency['revisions']])

    def test_exact_presented_bytes(self):
        self.assertEqual(len(self.rev['artifacts']), 1)
        a = self.rev['artifacts'][0]
        self.assertEqual(a['path'], 'catalog/contracts/agent_system/ent-0002/r0002.md')
        self.assertEqual(a['sha256'],
                         '915ec302c0cb2e294ea1014582f6007aee463c33032af3ea25540a21ce0fa145')
        self.assertEqual(a['size_bytes'], 15377)
        data = artifact_bytes(a)
        self.assertFalse(data.startswith(b'\xef\xbb\xbf'))
        self.assertNotIn(b'\r', data)
        self.assertTrue(data.endswith(b'\n') and not data.endswith(b'\n\n'))
        text = (ROOT / 'research/30-agent-system-discovery.md').read_text()
        presented = text.split('### 28.2.', 1)[1].split('```markdown\n', 1)[1].split('```', 1)[0]
        self.assertEqual(data, presented.encode('utf-8'))

    def test_decision_binding_and_authority(self):
        d = self.decision
        self.assertEqual(d['subject'], dict(catalog_id=CATALOG_ID,
                                          entity_id='ENT-0002', revision='r0002'))
        self.assertEqual(d['artifacts'], [{k: a[k] for k in ('path', 'sha256', 'size_bytes')}
                                         for a in self.rev['artifacts']])
        self.assertEqual(self.rev['approval']['status'], 'approved')
        self.assertEqual(d['schema_version'], '1')
        self.assertEqual(d['decision_type'], 'approve_revision')
        self.assertEqual(d['statement_form'], 'quote')
        self.assertEqual(d['statement'], 'оставить и внедрить')
        self.assertEqual(d['decision_date'], '2026-11-07')
        self.assertEqual((d['actor_role'], d['recorded_by']), ('owner', 'agent'))
        self.assertIn('не реализация валидатора, не выпуск и не активация', d['basis'])
        self.assertEqual(str(uuid.UUID(d['decision_id'])), d['decision_id'])
        self.assertEqual(self.rev['approval']['reference']['path'],
                         'catalog/approvals/' + d['decision_id'] + '.json')

    def test_corrupt_artifact_or_evidence_rejected(self):
        for item, key, value in [(self.rev['artifacts'][0], 'sha256', '0' * 64),
                                 (self.rev['artifacts'][0], 'size_bytes', 15378),
                                 (self.rev['approval']['reference'], 'sha256', '0' * 64)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                artifact_bytes(dict(item, **{key: value}))


class BaseSchemaArtifactTests(unittest.TestCase):
    # These tests verify deployment bytes and references, not Schema execution.
    EXPECTED = {
        'catalog-base.schema.json': (8696, '42fab3c453930ad9128b2b422837b82d84db9ed6092872765bd7fe1ffaf9a820'),
        'usage.md': (8650, 'f54ae129b412ea54fbeaea945c24ff1cf11ee7ede54ac704e49ffe57317ccd59'),
    }

    def setUp(self):
        self.registry = json.loads((BASE / 'catalog/registry.json').read_bytes())
        entity = next(e for e in self.registry['entities'] if e['entity_id'] == 'ENT-0003')
        self.assertEqual([r['revision'] for r in entity['revisions']], ['r0001', 'r0002'])
        self.rev = entity['revisions'][0]
        self.decision = json.loads(artifact_bytes(self.rev['approval']['reference']))

    def test_exact_two_file_presented_composition(self):
        self.assertEqual(self.rev['revision'], 'r0001')
        self.assertEqual(self.rev['kind'], 'schema')
        self.assertEqual(len(self.rev['artifacts']), 2)
        report = (ROOT / 'research/30-agent-system-discovery.md').read_text()
        for a, (name, (size, digest)) in zip(self.rev['artifacts'], self.EXPECTED.items()):
            self.assertEqual(a, dict(path='specification/ent-0003/r0001/' + name,
                                     sha256=digest, size_bytes=size, role='normative'))
            data = artifact_bytes(a)
            lang = 'json' if name.endswith('.json') else 'markdown'
            presented = report.split('Полный артефакт ' + name, 1)[1].split(
                '```' + lang + '\n', 1)[1].split('```', 1)[0].encode('utf-8')
            self.assertEqual(data, presented)
            self.assertFalse(data.startswith(b'\xef\xbb\xbf'))
            self.assertNotIn(b'\r', data)
            self.assertTrue(data.endswith(b'\n') and not data.endswith(b'\n\n'))

    def test_complete_decision_and_authority(self):
        d = self.decision
        self.assertEqual(d['subject'], dict(catalog_id=CATALOG_ID,
                                          entity_id='ENT-0003', revision='r0001'))
        self.assertEqual(d['artifacts'], [{k: a[k] for k in ('path', 'sha256', 'size_bytes')}
                                         for a in self.rev['artifacts']])
        self.assertEqual(d['statement'], 'оставить и внедрить')
        self.assertEqual(d['statement_form'], 'quote')
        self.assertEqual(d['decision_type'], 'approve_revision')
        self.assertEqual(d['decision_date'], '2026-11-07')
        self.assertEqual((d['actor_role'], d['recorded_by']), ('owner', 'agent'))
        self.assertEqual(self.rev['approval']['status'], 'approved')
        self.assertEqual(str(uuid.UUID(d['decision_id'])), d['decision_id'])
        self.assertEqual(self.rev['approval']['reference']['path'],
                         'catalog/approvals/' + d['decision_id'] + '.json')
        self.assertIn('не установка стороннего движка', d['basis'])
        self.assertIn('не выпуск и не активация', d['basis'])

    def test_exact_dependencies_exist(self):
        targets = [dict(catalog_id=CATALOG_ID, entity_id=e, revision=r)
                   for e, r in [('ENT-0001', 'r0001'), ('ENT-0002', 'r0002')]]
        self.assertEqual(self.rev['relations'], [dict(type='depends_on', target=t)
                                                for t in targets])
        for target in targets:
            entity = next(e for e in self.registry['entities']
                          if e['entity_id'] == target['entity_id'])
            self.assertIn(target['revision'], [r['revision'] for r in entity['revisions']])

    def test_schema_json_and_local_references(self):
        schema = json.loads(artifact_bytes(self.rev['artifacts'][0]))
        self.assertEqual(schema['$schema'], 'https://json-schema.org/draft/2020-12/schema')
        refs = []

        def walk(value):
            if isinstance(value, dict):
                if '$ref' in value:
                    ref = value['$ref']
                    self.assertTrue(ref.startswith('#/$defs/'))
                    self.assertIn(ref[len('#/$defs/'):], schema['$defs'])
                    refs.append(ref)
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(schema)
        self.assertEqual(len(refs), 28)
        self.assertEqual(schema['oneOf'], [{'$ref': '#/$defs/registry'},
                                          {'$ref': '#/$defs/approve_revision'}])

    def test_corrupt_either_file_or_witness_rejected(self):
        for a in self.rev['artifacts'] + [self.rev['approval']['reference']]:
            with self.subTest(path=a['path']), self.assertRaises(ValueError):
                artifact_bytes(dict(a, sha256='0' * 64))
        for a in self.rev['artifacts']:
            with self.subTest(path=a['path']), self.assertRaises(ValueError):
                artifact_bytes(dict(a, size_bytes=a['size_bytes'] + 1))


class StructuralCheckDeploymentTests(unittest.TestCase):
    EXPECTED = {
        'verify.py': (10872, '995309346354263828e7de22e112c519708a56f139be4be3dc1a8c9ad02111ea'),
        'requirements-linux-cp311.lock': (746, '4f0eda8261647c9bc18d2f013ef914737290e20c6a82de15f476108b6a528e71'),
        'usage.md': (7164, '50271abc545b7e99a5a42bfcd7034dede3ebcb249629de7ec536e5a335ad4101'),
    }

    def setUp(self):
        self.registry = json.loads((BASE / 'catalog/registry.json').read_bytes())
        entity = next(e for e in self.registry['entities'] if e['entity_id'] == 'ENT-0004')
        self.assertEqual([r['revision'] for r in entity['revisions']], ['r0001', 'r0002'])
        self.rev = entity['revisions'][0]
        self.decision = json.loads(artifact_bytes(self.rev['approval']['reference']))

    def test_exact_artifact_bytes(self):
        self.assertEqual(len(self.rev['artifacts']), 3)
        for a, (name, (size, digest)) in zip(self.rev['artifacts'], self.EXPECTED.items()):
            self.assertEqual(a, dict(path='validation/ent-0004/r0001/' + name,
                                     size_bytes=size, sha256=digest, role='normative'))
            data = artifact_bytes(a)
            self.assertNotIn(b'\r', data)
            self.assertFalse(data.startswith(b'\xef\xbb\xbf'))
            self.assertTrue(data.endswith(b'\n') and not data.endswith(b'\n\n'))

    def test_exact_dependency(self):
        self.assertEqual((self.rev['revision'], self.rev['kind']), ('r0001', 'check'))
        self.assertEqual(self.rev['relations'], [dict(type='depends_on', target=dict(
            catalog_id=CATALOG_ID, entity_id='ENT-0003', revision='r0001'))])

    def test_conditional_permission_not_fake_quote(self):
        d = self.decision
        self.assertEqual(d['subject'], dict(catalog_id=CATALOG_ID,
                                          entity_id='ENT-0004', revision='r0001'))
        self.assertEqual(d['statement_form'], 'summary')
        self.assertEqual(d['decision_type'], 'approve_revision')
        self.assertEqual(d['decision_date'], '2026-11-07')
        self.assertEqual((d['actor_role'], d['recorded_by']), ('owner', 'agent'))
        self.assertIn('Это не отдельная реплика владельца', d['statement'])
        self.assertIn('14 структурных тестов', d['basis'])
        self.assertIn('не выпуск и не активация', d['basis'])
        self.assertEqual(d['artifacts'], [{k: a[k] for k in ('path', 'sha256', 'size_bytes')}
                                         for a in self.rev['artifacts']])
        self.assertEqual(str(uuid.UUID(d['decision_id'])), d['decision_id'])
        self.assertEqual(self.rev['approval']['reference']['path'],
                         'catalog/approvals/' + d['decision_id'] + '.json')

    def test_corruption_rejected(self):
        for a in self.rev['artifacts'] + [self.rev['approval']['reference']]:
            with self.subTest(path=a['path']), self.assertRaises(ValueError):
                artifact_bytes(dict(a, sha256='0' * 64))


class MutableTreeDeploymentTests(unittest.TestCase):
    EXPECTED = {'ENT-0002': {'revision': 'r0003', 'kind': 'contract', 'artifacts': [{'path': 'catalog/contracts/agent_system/ent-0002/r0003.md', 'sha256': 'bfdea24314d9f5b26cd54ddaa41fe9aea9843c0f669417c040c1c80991188a1a', 'size_bytes': 17780, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0001', 'revision': 'r0001'}}, {'type': 'supersedes', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0002', 'revision': 'r0002'}}]}, 'ENT-0003': {'revision': 'r0002', 'kind': 'schema', 'artifacts': [{'path': 'specification/ent-0003/r0002/catalog-base.schema.json', 'sha256': '42fab3c453930ad9128b2b422837b82d84db9ed6092872765bd7fe1ffaf9a820', 'size_bytes': 8696, 'role': 'normative'}, {'path': 'specification/ent-0003/r0002/usage.md', 'sha256': 'a8e6c818ec4bda9eb4d38b3b9abb8ec9e3d694a42329771109931bbc8c5c6ceb', 'size_bytes': 9053, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0001', 'revision': 'r0001'}}, {'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0002', 'revision': 'r0003'}}, {'type': 'supersedes', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0003', 'revision': 'r0001'}}]}, 'ENT-0004': {'revision': 'r0002', 'kind': 'check', 'artifacts': [{'path': 'validation/ent-0004/r0002/verify.py', 'sha256': '1523ca399a9aee8f89656591b62e1d776504385fe025131c818c694ebb32aedf', 'size_bytes': 10872, 'role': 'normative'}, {'path': 'validation/ent-0004/r0002/requirements-linux-cp311.lock', 'sha256': '4f0eda8261647c9bc18d2f013ef914737290e20c6a82de15f476108b6a528e71', 'size_bytes': 746, 'role': 'normative'}, {'path': 'validation/ent-0004/r0002/usage.md', 'sha256': '78807c10e4ad843472a1413df661c27cdbbd92a889446a000fbc1e9566e1d369', 'size_bytes': 7567, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0003', 'revision': 'r0002'}}, {'type': 'supersedes', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0004', 'revision': 'r0001'}}]}, 'ENT-0005': {'revision': 'r0002', 'kind': 'adapter', 'artifacts': [{'path': 'adapters/ent-0005/r0002/reader.py', 'sha256': '03a47fab9301222c3bf9b4304c8595aaeb2fa88d2aa72c5ea96c6702433cdb8c', 'size_bytes': 8623, 'role': 'normative'}, {'path': 'adapters/ent-0005/r0002/verify.py', 'sha256': '325d7aac88492ca75ceefb919383a2ecec4bb3f8e10b97088247f255418952af', 'size_bytes': 13470, 'role': 'normative'}, {'path': 'adapters/ent-0005/r0002/usage.md', 'sha256': '522e3223737e1fe901b7c94cc85ba58c2f10b0d538e274e85f6d3f4d076bf835', 'size_bytes': 8728, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0002', 'revision': 'r0003'}}, {'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0003', 'revision': 'r0002'}}]}}

    def setUp(self):
        self.registry = json.loads((BASE / 'catalog/registry.json').read_bytes())

    def revisions(self):
        for entity_id, expected in self.EXPECTED.items():
            entity = next(e for e in self.registry['entities'] if e['entity_id'] == entity_id)
            revision = next(r for r in entity['revisions'] if r['revision'] == expected['revision'])
            yield entity_id, expected, revision

    def test_exact_deployment_and_conditional_evidence(self):
        for entity_id, expected, revision in self.revisions():
            for key in expected:
                self.assertEqual(revision[key], expected[key])
            for artifact in revision['artifacts']:
                artifact_bytes(artifact)
                self.assertNotIn('created-', artifact['path'])
            decision = json.loads(artifact_bytes(revision['approval']['reference']))
            self.assertEqual(decision['subject'], dict(catalog_id=CATALOG_ID,
                                                     entity_id=entity_id, revision=revision['revision']))
            self.assertEqual(decision['statement_form'], 'summary')
            self.assertIn('Владелец явно выбрал B', decision['statement'])
            self.assertEqual(decision['artifacts'], [{k: a[k] for k in ('path', 'sha256', 'size_bytes')}
                                                   for a in revision['artifacts']])

    def test_new_dependency_closure_does_not_pull_old_contract(self):
        by_key = {(e['entity_id'], r['revision']): r
                  for e in self.registry['entities'] for r in e['revisions']}
        seen = set()
        def visit(key):
            if key in seen:
                return
            seen.add(key)
            for relation in by_key[key]['relations']:
                if relation['type'] == 'depends_on':
                    target = relation['target']
                    self.assertEqual(target['catalog_id'], CATALOG_ID)
                    visit((target['entity_id'], target['revision']))
        visit(('ENT-0005', 'r0002'))
        visit(('ENT-0004', 'r0002'))
        self.assertEqual(seen, {('ENT-0001', 'r0001'), ('ENT-0002', 'r0003'),
                                ('ENT-0003', 'r0002'), ('ENT-0004', 'r0002'),
                                ('ENT-0005', 'r0002')})

    def test_new_contract_states_the_narrow_guarantee(self):
        text = (BASE / 'catalog/contracts/agent_system/ent-0002/r0003.md').read_text()
        self.assertIn('до чтения задаются ожидаемые', text)
        self.assertIn('Он не гарантирует отсутствие всех изменений', text)
        self.assertIn('атомарный снимок дерева', text)
        self.assertIn('Обнаруженная подмена', text)
        self.assertIn('Безопасная граница чтения обязательна', text)


class GraphCheckDeploymentTests(unittest.TestCase):
    EXPECTED = {'revision': 'r0001', 'kind': 'check', 'artifacts': [{'path': 'validation/ent-0006/r0001/check.py', 'sha256': 'd2d61ef073aebe99f81fd62b620a657b748f03915022d54462dd8ec5bd24d7e8', 'size_bytes': 10144, 'role': 'normative'}, {'path': 'validation/ent-0006/r0001/verify.py', 'sha256': 'd5af8877f45818966225eebcce89d2f749d39a45e4f0ac0e52ff2bcfcb92c189', 'size_bytes': 14721, 'role': 'normative'}, {'path': 'validation/ent-0006/r0001/usage.md', 'sha256': '865aa405bcd4647cf3eec780ede1eb60b8feeb28ce30958a2c654745de9bc5be', 'size_bytes': 10919, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0004', 'revision': 'r0002'}}, {'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0005', 'revision': 'r0002'}}]}

    def test_exact_composition_dependency_and_summary(self):
        registry = json.loads((BASE / 'catalog/registry.json').read_bytes())
        entity = next(e for e in registry['entities'] if e['entity_id'] == 'ENT-0006')
        self.assertEqual([r['revision'] for r in entity['revisions']], ['r0001', 'r0002', 'r0003'])
        revision = entity['revisions'][0]
        for key, value in self.EXPECTED.items():
            self.assertEqual(revision[key], value)
        for artifact in revision['artifacts']:
            artifact_bytes(artifact)
        decision = json.loads(artifact_bytes(revision['approval']['reference']))
        self.assertEqual(decision['subject'], dict(catalog_id=CATALOG_ID,
                                                 entity_id='ENT-0006', revision='r0001'))
        self.assertEqual(decision['statement_form'], 'summary')
        self.assertIn('Это summary делегирования', decision['statement'])
        self.assertEqual(decision['artifacts'], [{k: a[k] for k in ('path', 'sha256', 'size_bytes')}
                                               for a in revision['artifacts']])

    def test_corruption_rejected(self):
        for artifact in self.EXPECTED['artifacts']:
            with self.subTest(path=artifact['path']), self.assertRaises(ValueError):
                artifact_bytes(dict(artifact, sha256='0' * 64))


class EventProtocolDeploymentTests(unittest.TestCase):
    EXPECTED = {'ENT-0007': {'revision': 'r0001', 'kind': 'protocol', 'artifacts': [{'path': 'specification/ent-0007/r0001/decision-events.schema.json', 'sha256': '4cce54eaff0d12e1e59a4aeb0eb1dd9f0f0b951f43968317c70adb7c714005c1', 'size_bytes': 12322, 'role': 'normative'}, {'path': 'specification/ent-0007/r0001/events.py', 'sha256': '26a7dee29f5f5196fd458da90246f343035f2843bed5434f2e71340abb0eaabe', 'size_bytes': 11016, 'role': 'normative'}, {'path': 'specification/ent-0007/r0001/verify.py', 'sha256': 'fca460f867777250da0348845bbedc1cc6804a57988abfb1c50f6db32dc18378', 'size_bytes': 13994, 'role': 'normative'}, {'path': 'specification/ent-0007/r0001/usage.md', 'sha256': 'ddaa2074aa5dfe6595f95b24f0e937871a2430be84f9a2c416f87d5d2974b4df', 'size_bytes': 10376, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0004', 'revision': 'r0002'}}]}, 'ENT-0006': {'revision': 'r0002', 'kind': 'check', 'artifacts': [{'path': 'validation/ent-0006/r0002/check.py', 'sha256': 'd94e2c85c2bd40ff31b5d7edd2f0c9755cf5eb3ce6ab42488aeaff4feb8c275c', 'size_bytes': 12042, 'role': 'normative'}, {'path': 'validation/ent-0006/r0002/verify.py', 'sha256': 'accc799767fe84367c554937de1ae5e0923521348c23d5b6ac9df5019b398f34', 'size_bytes': 17421, 'role': 'normative'}, {'path': 'validation/ent-0006/r0002/usage.md', 'sha256': '69aada3c8f03c892bbada23791a7cf02fc2a90e610c40fe6578240b972730929', 'size_bytes': 12139, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0004', 'revision': 'r0002'}}, {'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0005', 'revision': 'r0002'}}, {'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0007', 'revision': 'r0001'}}, {'type': 'supersedes', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0006', 'revision': 'r0001'}}]}}

    def test_exact_versions_and_decision_boundaries(self):
        registry = json.loads((BASE / 'catalog/registry.json').read_bytes())
        for eid, expected in self.EXPECTED.items():
            entity = next(e for e in registry['entities'] if e['entity_id'] == eid)
            revision = next(r for r in entity['revisions'] if r['revision'] == expected['revision'])
            for key, value in expected.items():
                self.assertEqual(revision[key], value)
            for artifact in revision['artifacts']:
                artifact_bytes(artifact)
            decision = json.loads(artifact_bytes(revision['approval']['reference']))
            self.assertEqual(decision['subject'], dict(catalog_id=CATALOG_ID,
                                                     entity_id=eid, revision=revision['revision']))
            self.assertEqual(decision['statement_form'], 'summary')
            self.assertIn('не создание реального ограничения', decision['statement'])
            self.assertEqual(decision['artifacts'], [{k: a[k] for k in ('path', 'sha256', 'size_bytes')}
                                                   for a in revision['artifacts']])

    def test_event_schema_is_local_and_does_not_replace_base(self):
        schema = json.loads((BASE / 'specification/ent-0007/r0001/decision-events.schema.json').read_bytes())
        self.assertEqual(schema['$id'], 'urn:agent-system:schema:decision-events:1')
        self.assertEqual(set(schema['$defs']), {'restrict_use', 'revoke_use', 'lift_restriction', 'correct_record'})
        self.assertTrue((BASE / 'specification/ent-0003/r0002/catalog-base.schema.json').exists())


class SourceAcquisitionDeploymentTests(unittest.TestCase):
    EXPECTED = {'ENT-0005': {'revision': 'r0003', 'kind': 'adapter', 'artifacts': [{'path': 'adapters/ent-0005/r0003/reader.py', 'sha256': '0ddfb68d81eaf9e3ba56ca20b909462958b8e9de938d230a02d3a14e8b76fc7f', 'size_bytes': 15565, 'role': 'normative'}, {'path': 'adapters/ent-0005/r0003/verify.py', 'sha256': '3a8faf2098e99433223678f2dee92e94af3b511ccc946998024e98c943e55336', 'size_bytes': 22384, 'role': 'normative'}, {'path': 'adapters/ent-0005/r0003/usage.md', 'sha256': '489b9247257472d69ec0266a031edcac09d38e00c117de627a3a38d837262f14', 'size_bytes': 12063, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0002', 'revision': 'r0003'}}, {'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0003', 'revision': 'r0002'}}, {'type': 'supersedes', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0005', 'revision': 'r0002'}}]}, 'ENT-0006': {'revision': 'r0003', 'kind': 'check', 'artifacts': [{'path': 'validation/ent-0006/r0003/check.py', 'sha256': 'd94e2c85c2bd40ff31b5d7edd2f0c9755cf5eb3ce6ab42488aeaff4feb8c275c', 'size_bytes': 12042, 'role': 'normative'}, {'path': 'validation/ent-0006/r0003/verify.py', 'sha256': '9a76cb7cb7d6bb5c5aefdba003cf9c57979ae2f3f9d626dd6e2aeb54ee674e51', 'size_bytes': 18332, 'role': 'normative'}, {'path': 'validation/ent-0006/r0003/usage.md', 'sha256': '89b80b152f5651bdf6ba1880b24f7175a0e7e2c9fa9915e2b306993204d9bff3', 'size_bytes': 13351, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0004', 'revision': 'r0002'}}, {'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0005', 'revision': 'r0003'}}, {'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0007', 'revision': 'r0001'}}, {'type': 'supersedes', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0006', 'revision': 'r0002'}}]}}

    def test_exact_source_acquisition_composition(self):
        registry = json.loads((BASE / 'catalog/registry.json').read_bytes())
        for entity_id, expected in self.EXPECTED.items():
            entity = next(e for e in registry['entities'] if e['entity_id'] == entity_id)
            revision = next(r for r in entity['revisions'] if r['revision'] == 'r0003')
            for key, value in expected.items():
                self.assertEqual(revision[key], value)
            for artifact in revision['artifacts']:
                artifact_bytes(artifact)
            decision = json.loads(artifact_bytes(revision['approval']['reference']))
            self.assertEqual(decision['subject'], dict(catalog_id=CATALOG_ID, entity_id=entity_id, revision='r0003'))
            self.assertEqual(decision['statement_form'], 'summary')
            self.assertEqual(decision['artifacts'], [{k: a[k] for k in ('path', 'sha256', 'size_bytes')}
                                                   for a in revision['artifacts']])

    def test_unchanged_semantic_algorithm(self):
        directory = BASE / 'validation/ent-0006'
        self.assertEqual((directory / 'r0002/check.py').read_bytes(), (directory / 'r0003/check.py').read_bytes())


class PlanReportDeploymentTests(unittest.TestCase):
    EXPECTED = {'revision': 'r0001', 'kind': 'protocol', 'artifacts': [{'path': 'specification/ent-0008/r0001/validation-plan.schema.json', 'sha256': 'e53e11315ebe54566edc5a395e7c4eee57cb82bdac86f9573feed57a0602664b', 'size_bytes': 3590, 'role': 'normative'}, {'path': 'specification/ent-0008/r0001/validation-run-report.schema.json', 'sha256': '7dece17f75d695484b2814c89f17f4e1623f6fec033d24c92953c740540da8bc', 'size_bytes': 15972, 'role': 'normative'}, {'path': 'specification/ent-0008/r0001/verify.py', 'sha256': '7196efe0f6b59f74ba791f80f497ce827d517d344e2c84556991db2f7f54a026', 'size_bytes': 14770, 'role': 'normative'}, {'path': 'specification/ent-0008/r0001/usage.md', 'sha256': 'f775530264c1fa0a76b368a264ce4b343405b6b7b6b0e1a39002e97ea3ea0c65', 'size_bytes': 14765, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0004', 'revision': 'r0002'}}, {'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0005', 'revision': 'r0003'}}, {'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0006', 'revision': 'r0003'}}]}

    def test_exact_protocol_composition(self):
        registry = json.loads((BASE / 'catalog/registry.json').read_bytes())
        entity = next(e for e in registry['entities'] if e['entity_id'] == 'ENT-0008')
        self.assertEqual(len(entity['revisions']), 1)
        rev = entity['revisions'][0]
        for key, value in self.EXPECTED.items():
            self.assertEqual(rev[key], value)
        for artifact in rev['artifacts']:
            artifact_bytes(artifact)
        decision = json.loads(artifact_bytes(rev['approval']['reference']))
        self.assertEqual(decision['subject'], dict(catalog_id=CATALOG_ID, entity_id='ENT-0008', revision='r0001'))
        self.assertEqual(decision['statement_form'], 'summary')
        self.assertEqual(decision['artifacts'], [{k: a[k] for k in ('path', 'sha256', 'size_bytes')}
                                               for a in rev['artifacts']])
        self.assertIn('структурного протокола', decision['statement'])


class PlanExecutorDeploymentTests(unittest.TestCase):
    EXPECTED = {'revision': 'r0001', 'kind': 'check', 'artifacts': [{'path': 'validation/ent-0009/r0001/execute.py', 'sha256': '1a4340e4dfe4b01841702ffcb88a65caa0f8ccc05d6adce03c1e4b3d2e6ebdf9', 'size_bytes': 12955, 'role': 'normative'}, {'path': 'validation/ent-0009/r0001/verify.py', 'sha256': 'a082eeb938a62f4005d83f3664d027c403055c1f7851ff73a3a6517a09f41268', 'size_bytes': 11721, 'role': 'normative'}, {'path': 'validation/ent-0009/r0001/usage.md', 'sha256': '6c9ed888e4d5538a53521fa4406ce6df50e287718d2c5cc4545882432173425f', 'size_bytes': 11256, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0008', 'revision': 'r0001'}}]}

    def test_exact_executor_composition(self):
        registry = json.loads((BASE / 'catalog/registry.json').read_bytes())
        entity = next(e for e in registry['entities'] if e['entity_id'] == 'ENT-0009')
        self.assertEqual([r['revision'] for r in entity['revisions']], ['r0001', 'r0002'])
        rev = entity['revisions'][0]
        for key, value in self.EXPECTED.items():
            self.assertEqual(rev[key], value)
        for artifact in rev['artifacts']:
            artifact_bytes(artifact)
        decision = json.loads(artifact_bytes(rev['approval']['reference']))
        self.assertEqual(decision['subject'], dict(catalog_id=CATALOG_ID, entity_id='ENT-0009', revision='r0001'))
        self.assertEqual(decision['statement_form'], 'summary')
        self.assertEqual(decision['artifacts'], [{k: a[k] for k in ('path', 'sha256', 'size_bytes')}
                                               for a in rev['artifacts']])

    def test_installed_pins_cover_exact_profile(self):
        import runpy
        registry = json.loads((BASE / 'catalog/registry.json').read_bytes())
        selected = {('ENT-0001', 'r0001'), ('ENT-0002', 'r0003'), ('ENT-0003', 'r0002'),
                    ('ENT-0004', 'r0002'), ('ENT-0005', 'r0003'), ('ENT-0006', 'r0003'),
                    ('ENT-0007', 'r0001'), ('ENT-0008', 'r0001')}
        pins = {a['path']: {k: a[k] for k in ('sha256', 'size_bytes')}
                for e in registry['entities'] for v in e['revisions']
                if (e['entity_id'], v['revision']) in selected for a in v['artifacts']}
        installed = runpy.run_path(str(BASE / 'validation/ent-0009/r0001/execute.py'))['PINS']
        self.assertEqual(installed, pins)
        self.assertEqual(len(installed), 21)


class BundleVerifierDeploymentTests(unittest.TestCase):
    EXPECTED = {'revision': 'r0001', 'kind': 'check', 'artifacts': [{'path': 'validation/ent-0010/r0001/bundle.py', 'sha256': 'edfe812458cce41dbcbcdffa6bd568a57ac287506969cc315e2d8a8a999eba08', 'size_bytes': 10655, 'role': 'normative'}, {'path': 'validation/ent-0010/r0001/verify.py', 'sha256': '6056350c72c9b94a76d9a7c86cff9890947ea9261f3e5e4936ef4053ca05e544', 'size_bytes': 10526, 'role': 'normative'}, {'path': 'validation/ent-0010/r0001/usage.md', 'sha256': '8b9d39a9824ce41bb68e3aeecb2bffad2b272d556c95c2148ac8ded6cf19d6d1', 'size_bytes': 12047, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0009', 'revision': 'r0001'}}]}

    def test_exact_bundle_verifier_composition(self):
        registry = json.loads((BASE / 'catalog/registry.json').read_bytes())
        entity = next(e for e in registry['entities'] if e['entity_id'] == 'ENT-0010')
        self.assertEqual(len(entity['revisions']), 1)
        rev = entity['revisions'][0]
        for key, value in self.EXPECTED.items():
            self.assertEqual(rev[key], value)
        for artifact in rev['artifacts']:
            artifact_bytes(artifact)
        decision = json.loads(artifact_bytes(rev['approval']['reference']))
        self.assertEqual(decision['subject'], dict(catalog_id=CATALOG_ID, entity_id='ENT-0010', revision='r0001'))
        self.assertEqual(decision['statement_form'], 'summary')
        self.assertEqual(decision['artifacts'], [{k: a[k] for k in ('path', 'sha256', 'size_bytes')}
                                               for a in rev['artifacts']])

    def test_exact_installed_entry_pins(self):
        import runpy
        registry = json.loads((BASE / 'catalog/registry.json').read_bytes())
        entry = next(e for e in registry['entities'] if e['entity_id'] == 'ENT-0009')['revisions'][0]
        expected = {a['path']: {k: a[k] for k in ('sha256', 'size_bytes')} for a in entry['artifacts']}
        installed = runpy.run_path(str(BASE / 'validation/ent-0010/r0001/bundle.py'))['ENTRY_PINS']
        self.assertEqual(installed, expected)
        self.assertEqual(len(installed), 3)


class WorkProtocolDeploymentTests(unittest.TestCase):
    EXPECTED = {'revision': 'r0001', 'kind': 'protocol', 'artifacts': [{'path': 'protocols/ent-0011/r0001/work.md', 'sha256': '06923c52d5e7311556e8276cea473af71284f985476f970dced83d085a70cbb4', 'size_bytes': 22549, 'role': 'normative'}, {'path': 'protocols/ent-0011/r0001/scenarios.json', 'sha256': '441d2505e822cdbf37d534a17b4b89c32a54853ff4442d9e019104c0b3ea5f50', 'size_bytes': 12480, 'role': 'normative'}, {'path': 'protocols/ent-0011/r0001/verify.py', 'sha256': '3984ddb43a4ac7b45694608b891ac17e331bfc3fb8a624bc716bbd0ded834348', 'size_bytes': 6777, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0001', 'revision': 'r0001'}}]}

    def test_exact_work_protocol_composition(self):
        registry = json.loads((BASE / 'catalog/registry.json').read_bytes())
        entity = next(e for e in registry['entities'] if e['entity_id'] == 'ENT-0011')
        self.assertEqual([v['revision'] for v in entity['revisions']], ['r0001','r0002'])
        rev = entity['revisions'][0]
        for key, value in self.EXPECTED.items():
            self.assertEqual(rev[key], value)
        for artifact in rev['artifacts']:
            artifact_bytes(artifact)
        decision = json.loads(artifact_bytes(rev['approval']['reference']))
        self.assertEqual(decision['subject'], dict(catalog_id=CATALOG_ID, entity_id='ENT-0011', revision='r0001'))
        self.assertEqual(decision['statement_form'], 'summary')
        self.assertEqual(decision['artifacts'], [{k: a[k] for k in ('path', 'sha256', 'size_bytes')}
                                               for a in rev['artifacts']])

    def test_scenarios_do_not_claim_behavior_or_authority(self):
        data = json.loads((BASE / 'protocols/ent-0011/r0001/scenarios.json').read_bytes())
        self.assertEqual(data['verification_level'], 'model_review')
        self.assertIs(data['agent_behavior_verified'], False)
        self.assertEqual(data['overall_admission'], 'not_evaluated')
        self.assertIs(data['transition_allowed'], False)


class GovernanceProtocolDeploymentTests(unittest.TestCase):
    EXPECTED = {'revision': 'r0001', 'kind': 'protocol', 'artifacts': [{'path': 'protocols/ent-0012/r0001/governance.md', 'sha256': '2402346a739436871ba22b90306cf86c3836eb54f3ddb3801bbfa78398bbc0f9', 'size_bytes': 21236, 'role': 'normative'}, {'path': 'transfer/ent-0012/r0001/prompt.md', 'sha256': '8ce3983ed99058bfa1d1c559142fd884c60bb92b27331b58d2759e47b6e5866a', 'size_bytes': 4825, 'role': 'normative'}, {'path': 'transfer/ent-0012/r0001/prepare.py', 'sha256': 'ec2f904f93b15ed234f19b21a87d6a0e8cebc02c538c693c268241dd2420785a', 'size_bytes': 5468, 'role': 'normative'}, {'path': 'protocols/ent-0012/r0001/verify.py', 'sha256': '82acb918e2b4f99171bc421b3fd028fbb0d0eefef68626fd7adccf65399d9d8c', 'size_bytes': 8946, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0011', 'revision': 'r0001'}}, {'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0009', 'revision': 'r0001'}}]}

    def test_exact_governance_and_preparation_composition(self):
        registry = json.loads((BASE / 'catalog/registry.json').read_bytes())
        entity = next(e for e in registry['entities'] if e['entity_id'] == 'ENT-0012')
        self.assertEqual(len(entity['revisions']), 1)
        rev = entity['revisions'][0]
        for key, value in self.EXPECTED.items():
            self.assertEqual(rev[key], value)
        for artifact in rev['artifacts']:
            artifact_bytes(artifact)
        decision = json.loads(artifact_bytes(rev['approval']['reference']))
        self.assertEqual(decision['subject'], dict(catalog_id=CATALOG_ID, entity_id='ENT-0012', revision='r0001'))
        self.assertEqual(decision['statement_form'], 'summary')
        self.assertEqual(decision['artifacts'], [{k: a[k] for k in ('path', 'sha256', 'size_bytes')}
                                               for a in rev['artifacts']])

    def test_exact_preparation_pins_and_component_identity(self):
        import runpy
        registry = json.loads((BASE / 'catalog/registry.json').read_bytes())
        module = runpy.run_path(str(BASE / 'transfer/ent-0012/r0001/prepare.py'))
        expected = {}
        for e in registry['entities']:
            if e['entity_id'] in ('ENT-0009', 'ENT-0011'):
                for a in e['revisions'][0]['artifacts']:
                    expected[a['path']] = {k: a[k] for k in ('sha256', 'size_bytes')}
        for a in self.EXPECTED['artifacts'][:2]:
            expected[a['path']] = {k: a[k] for k in ('sha256', 'size_bytes')}
        self.assertEqual(module['PINS'], expected)
        self.assertEqual(set(module['COMPONENT']), {a['path'] for a in self.EXPECTED['artifacts']})
        self.assertEqual(len(module['PINS']), 8)


class CandidateProtocolDeploymentTests(unittest.TestCase):
    EXPECTED = {'revision': 'r0001', 'kind': 'protocol', 'artifacts': [{'path': 'candidates/ent-0013/r0001/candidate.json', 'sha256': '3a9231b668cc63b1d4a60d032dfe49fb61223a3b2c81b3fd79a42a1ee1b7f428', 'size_bytes': 69062, 'role': 'normative'}, {'path': 'candidates/ent-0013/r0001/check.py', 'sha256': 'f185875d034bc61697d926c45eedbb4764d281ccb96a8dca8cc7488dea42a660', 'size_bytes': 12871, 'role': 'normative'}, {'path': 'candidates/ent-0013/r0001/verify.py', 'sha256': '0292c5c700714d7db0cbf27b2e76a56d9d0f1e69e3f19d3488527313dda8a86e', 'size_bytes': 8484, 'role': 'normative'}, {'path': 'candidates/ent-0013/r0001/usage.md', 'sha256': '080abfa5143db3920ed9eec80380e21e31ac43f99fb8236dc678fd4c009cafca', 'size_bytes': 15101, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0012', 'revision': 'r0001'}}, {'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0010', 'revision': 'r0001'}}]}

    def test_exact_candidate_protocol_composition(self):
        registry=json.loads((BASE/'catalog/registry.json').read_bytes())
        entity=next(e for e in registry['entities'] if e['entity_id']=='ENT-0013')
        self.assertEqual(len(entity['revisions']),1)
        revision=entity['revisions'][0]
        for key,value in self.EXPECTED.items():
            self.assertEqual(revision[key],value)
        for artifact in revision['artifacts']:
            artifact_bytes(artifact)
        decision=json.loads(artifact_bytes(revision['approval']['reference']))
        self.assertEqual(decision['subject'],dict(catalog_id=CATALOG_ID,entity_id='ENT-0013',revision='r0001'))
        self.assertEqual(decision['artifacts'],[{k:a[k] for k in ('path','sha256','size_bytes')} for a in revision['artifacts']])
        self.assertEqual(decision['statement_form'],'summary')

    def test_descriptor_is_external_to_frozen_payload(self):
        data=json.loads((BASE/'candidates/ent-0013/r0001/candidate.json').read_bytes())
        self.assertIs(data['descriptor_in_payload'],False)
        self.assertNotIn('ENT-0013',{c['subject']['entity_id'] for c in data['components']})
        self.assertEqual(data['readiness'],'incomplete_candidate')
        self.assertEqual(len(data['coverage']),16)
        self.assertEqual(len(data['conditions']),9)


class PermissionProtocolDeploymentTests(unittest.TestCase):
    EXPECTED = {'revision': 'r0001', 'kind': 'protocol', 'artifacts': [{'path': 'permissions/ent-0014/r0001/proposal.schema.json', 'sha256': '142a2a628ed5125229ac48a9e1d6768f62cf21ff138cc12a83fa1c220369ac39', 'size_bytes': 4320, 'role': 'normative'}, {'path': 'permissions/ent-0014/r0001/check.py', 'sha256': '18d47b251a0709ebd021a9473553c7faeb12b8e977d90ed41b20899dde9df1d2', 'size_bytes': 7333, 'role': 'normative'}, {'path': 'permissions/ent-0014/r0001/verify.py', 'sha256': 'd94ce36432537ce5e13f4d059fc6f0a0772c0e8fc6cbfb19734aa59e1937ed1e', 'size_bytes': 8170, 'role': 'normative'}, {'path': 'permissions/ent-0014/r0001/usage.md', 'sha256': '3ba366a47b00d576bfb1254dee15404b6e3c245437f3097be301907326eb2fd1', 'size_bytes': 15107, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0013', 'revision': 'r0001'}}]}

    def test_exact_permission_protocol_composition(self):
        registry=json.loads((BASE/'catalog/registry.json').read_bytes())
        entity=next(e for e in registry['entities'] if e['entity_id']=='ENT-0014')
        self.assertEqual(len(entity['revisions']),1)
        revision=entity['revisions'][0]
        for key,value in self.EXPECTED.items():self.assertEqual(revision[key],value)
        for artifact in revision['artifacts']:artifact_bytes(artifact)
        decision=json.loads(artifact_bytes(revision['approval']['reference']))
        self.assertEqual(decision['subject'],dict(catalog_id=CATALOG_ID,entity_id='ENT-0014',revision='r0001'))
        self.assertEqual(decision['statement_form'],'summary')
        self.assertEqual(decision['artifacts'],[{k:a[k] for k in ['path','sha256','size_bytes']} for a in revision['artifacts']])

    def test_exact_dependency_and_schema_pins(self):
        import runpy
        registry=json.loads((BASE/'catalog/registry.json').read_bytes())
        revision=next(e for e in registry['entities'] if e['entity_id']=='ENT-0013')['revisions'][0]
        expected={a['path']:{k:a[k] for k in ['sha256','size_bytes']} for a in revision['artifacts']}
        artifact=self.EXPECTED['artifacts'][0]
        expected[artifact['path']]={k:artifact[k] for k in ['sha256','size_bytes']}
        module=runpy.run_path(str(BASE/'permissions/ent-0014/r0001/check.py'))
        self.assertEqual(module['PINS'],expected)
        self.assertEqual(len(expected),5)


class TrialStagingDeploymentTests(unittest.TestCase):
    EXPECTED = {'revision': 'r0001', 'kind': 'protocol', 'artifacts': [{'path': 'staging/ent-0015/r0001/stage.py', 'sha256': '2cf729cc03e65a4b28e5dbf1afac99de305c75b3422a08181b48c43392f3b9a0', 'size_bytes': 9215, 'role': 'normative'}, {'path': 'staging/ent-0015/r0001/verify.py', 'sha256': '46c3101cc2b6dd57b879e5e7aa1f9441943b74619ab6875f34bc5cc6d7a20a71', 'size_bytes': 13661, 'role': 'normative'}, {'path': 'staging/ent-0015/r0001/usage.md', 'sha256': '6e0bb1c173921c269d11da522e1ef290b6995e27cfc6857e16b849445151c14a', 'size_bytes': 14234, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0014', 'revision': 'r0001'}}]}

    def test_exact_trial_staging_composition(self):
        registry=json.loads((BASE/'catalog/registry.json').read_bytes())
        entity=next(e for e in registry['entities'] if e['entity_id']=='ENT-0015')
        self.assertEqual(len(entity['revisions']),1)
        revision=entity['revisions'][0]
        for key,value in self.EXPECTED.items():self.assertEqual(revision[key],value)
        for artifact in revision['artifacts']:artifact_bytes(artifact)
        decision=json.loads(artifact_bytes(revision['approval']['reference']))
        self.assertEqual(decision['subject'],dict(catalog_id=CATALOG_ID,entity_id='ENT-0015',revision='r0001'))
        self.assertEqual(decision['statement_form'],'summary')
        self.assertEqual(decision['artifacts'],[{k:a[k] for k in ['path','sha256','size_bytes']} for a in revision['artifacts']])

    def test_exact_staging_dependency_pins(self):
        import runpy
        registry=json.loads((BASE/'catalog/registry.json').read_bytes())
        revision=next(e for e in registry['entities'] if e['entity_id']=='ENT-0014')['revisions'][0]
        expected={a['path']:{k:a[k] for k in ['sha256','size_bytes']} for a in revision['artifacts']}
        module=runpy.run_path(str(BASE/'staging/ent-0015/r0001/stage.py'))
        self.assertEqual(module['PINS'],expected)
        self.assertEqual(len(expected),4)


class TrialReaderDeploymentTests(unittest.TestCase):
    EXPECTED = {'revision': 'r0001', 'kind': 'protocol', 'artifacts': [{'path': 'staging/ent-0016/r0001/read.py', 'sha256': '942839d7e292cd7f744346f27693cd4e7cc573961d1599f66df4c566548545cf', 'size_bytes': 9691, 'role': 'normative'}, {'path': 'staging/ent-0016/r0001/verify.py', 'sha256': 'f06e8a76da5f2c9005934d47b0f439b4b8751a0bc50a921bd773bbbd6305967f', 'size_bytes': 11917, 'role': 'normative'}, {'path': 'staging/ent-0016/r0001/usage.md', 'sha256': '3dccac0b1705a6a9723d8d72228733010c710a2e3a012ad84c1412b3e6210251', 'size_bytes': 12738, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0015', 'revision': 'r0001'}}]}

    def test_exact_trial_reader_composition(self):
        registry=json.loads((BASE/'catalog/registry.json').read_bytes())
        entity=next(e for e in registry['entities'] if e['entity_id']=='ENT-0016')
        self.assertEqual([r['revision'] for r in entity['revisions']],['r0001','r0002'])
        revision=entity['revisions'][0]
        for key,value in self.EXPECTED.items():self.assertEqual(revision[key],value)
        for artifact in revision['artifacts']:artifact_bytes(artifact)
        decision=json.loads(artifact_bytes(revision['approval']['reference']))
        self.assertEqual(decision['subject'],dict(catalog_id=CATALOG_ID,entity_id='ENT-0016',revision='r0001'))
        self.assertEqual(decision['statement_form'],'summary')
        self.assertEqual(decision['artifacts'],[{k:a[k] for k in ['path','sha256','size_bytes']} for a in revision['artifacts']])

    def test_exact_trial_reader_dependency_pins(self):
        import runpy
        registry=json.loads((BASE/'catalog/registry.json').read_bytes())
        revision=next(e for e in registry['entities'] if e['entity_id']=='ENT-0015')['revisions'][0]
        expected={a['path']:{k:a[k] for k in ['sha256','size_bytes']} for a in revision['artifacts']}
        module=runpy.run_path(str(BASE/'staging/ent-0016/r0001/read.py'))
        self.assertEqual(module['PINS'],expected)
        self.assertEqual(len(expected),3)


class KnownViewDeploymentTests(unittest.TestCase):
    EXPECTED = {'revision': 'r0001', 'kind': 'protocol', 'artifacts': [{'path': 'validation/ent-0017/r0001/compare.py', 'sha256': '65cee528ca1e9ab3594f43476ad21c89ac1ce44d40e6511724ec3c7555dcc95c', 'size_bytes': 9453, 'role': 'normative'}, {'path': 'validation/ent-0017/r0001/verify.py', 'sha256': 'eaeeafe2f135f5a325ee4f1dd6d49cc9fd80707aaff74ba6efee1193d1208aa3', 'size_bytes': 10622, 'role': 'normative'}, {'path': 'validation/ent-0017/r0001/usage.md', 'sha256': '401ff21a4d3a449ccb81bc865701a4f84abcb8232527e10a230c83e5a9306ad9', 'size_bytes': 11698, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0016', 'revision': 'r0001'}}]}

    def test_exact_known_view_composition(self):
        registry=json.loads((BASE/'catalog/registry.json').read_bytes())
        entity=next(e for e in registry['entities'] if e['entity_id']=='ENT-0017')
        self.assertEqual(len(entity['revisions']),1)
        revision=entity['revisions'][0]
        for key,value in self.EXPECTED.items():self.assertEqual(revision[key],value)
        for artifact in revision['artifacts']:artifact_bytes(artifact)
        decision=json.loads(artifact_bytes(revision['approval']['reference']))
        self.assertEqual(decision['subject'],dict(catalog_id=CATALOG_ID,entity_id='ENT-0017',revision='r0001'))
        self.assertEqual(decision['statement_form'],'summary')
        self.assertEqual(decision['artifacts'],[{k:a[k] for k in ['path','sha256','size_bytes']} for a in revision['artifacts']])

    def test_exact_known_view_dependency_pins(self):
        import runpy
        registry=json.loads((BASE/'catalog/registry.json').read_bytes())
        revision=next(e for e in registry['entities'] if e['entity_id']=='ENT-0016')['revisions'][0]
        expected={a['path']:{k:a[k] for k in ['sha256','size_bytes']} for a in revision['artifacts']}
        module=runpy.run_path(str(BASE/'validation/ent-0017/r0001/compare.py'))
        self.assertEqual(module['PINS'],expected)
        self.assertEqual(len(expected),3)


class CaptureWorkerDeploymentTests(unittest.TestCase):
    EXPECTED = {'revision': 'r0002', 'title': 'Исполнитель плана с контролируемой передачей исходных bytes', 'kind': 'check', 'scopes': ['agent_system.validation'], 'artifacts': [{'path': 'validation/ent-0009/r0002/execute.py', 'sha256': 'e28329880072ce4a13b4306bfa5c423860ad8e959147b9653f9ed13650be20ba', 'size_bytes': 14202, 'role': 'normative'}, {'path': 'validation/ent-0009/r0002/verify.py', 'sha256': '54a77f771b518a8af9a0d430b03c49e4f32182a180ee71981970ca550dd74296', 'size_bytes': 19812, 'role': 'normative'}, {'path': 'validation/ent-0009/r0002/usage.md', 'sha256': '9e8c100d8126c1cda232ddd169a90a95844e62f896bac9b415102c0deb0522c0', 'size_bytes': 7482, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0008', 'revision': 'r0001'}}, {'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0009', 'revision': 'r0001'}}, {'type': 'supersedes', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0009', 'revision': 'r0001'}}], 'approval': {'status': 'approved', 'reference': {'path': 'catalog/approvals/31457a0e-2fe7-41ca-a6c4-dab12960fe57.json', 'sha256': 'fc3809c03afc42e9abc5d412d4783f28c5ac730b20c564e7b944c51699171da2'}}, 'provenance': {'summary': 'I1 проекта M1, D05–D07: новая immutable revision по заданию и условному делегированию. Общий worker без runtime r1 patch/reread; старый producer сохранён, source raw maps только при успешных final guards. Без нового допуска/выпуска/активации.'}}

    def test_exact_capture_revision_and_approval(self):
        registry = json.loads((BASE/'catalog/registry.json').read_bytes())
        entity = next(e for e in registry['entities'] if e['entity_id'] == 'ENT-0009')
        actual = next(r for r in entity['revisions'] if r['revision'] == 'r0002')
        self.assertEqual(actual, self.EXPECTED)
        for artifact in actual['artifacts']:
            artifact_bytes(artifact)
        decision = json.loads(artifact_bytes(actual['approval']['reference']))
        self.assertEqual(decision['subject'], dict(catalog_id=CATALOG_ID, entity_id='ENT-0009', revision='r0002'))
        self.assertEqual(decision['statement_form'], 'summary')
        self.assertEqual(decision['artifacts'], [{k:a[k] for k in ['path','sha256','size_bytes']} for a in actual['artifacts']])

    def test_shared_legacy_dependency_pins(self):
        import ast
        import runpy
        old = runpy.run_path(str(BASE/'validation/ent-0009/r0001/execute.py'))
        new = runpy.run_path(str(BASE/'validation/ent-0009/r0002/execute.py'))
        self.assertEqual(new['PINS'], old['PINS'])
        self.assertEqual(len(new['PINS']), 21)
        tree = ast.parse((BASE/'validation/ent-0009/r0002/execute.py').read_text())
        acquisitions = [n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Subscript) and isinstance(n.func.slice,ast.Constant) and n.func.slice.value == 'read_set']
        self.assertEqual(len(acquisitions), 1)


class TrialCaptureDeploymentTests(unittest.TestCase):
    EXPECTED = {'revision': 'r0002', 'title': 'Read-only private trial capture после всех guards', 'kind': 'protocol', 'scopes': ['agent_system.trial'], 'artifacts': [{'path': 'staging/ent-0016/r0002/read.py', 'sha256': '3d5377fa1884631e88e3da51abb44222639809be95695f74ca9fa912543b1e33', 'size_bytes': 10620, 'role': 'normative'}, {'path': 'staging/ent-0016/r0002/verify.py', 'sha256': '3738c49bf88078c5b1e2215e6f107fd1efd00c7da0b7b7bc52281424404035ea', 'size_bytes': 18927, 'role': 'normative'}, {'path': 'staging/ent-0016/r0002/usage.md', 'sha256': '6b189d32946b6fa33ac8fcf74546262cb703602e9244a5f8a461b6425e382d15', 'size_bytes': 7007, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0015', 'revision': 'r0001'}}, {'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0016', 'revision': 'r0001'}}, {'type': 'supersedes', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0016', 'revision': 'r0001'}}], 'approval': {'status': 'approved', 'reference': {'path': 'catalog/approvals/8efe7a35-25fb-4a42-9900-b16a99af8700.json', 'sha256': '992aa71966c3605b4c2c524ae3aec3f5c70de7def564becbc7bca25274d1098c'}}, 'provenance': {'summary': 'I2 проекта M1 D08–D09 по заданию B и условному делегированию после проверок. Общий guarded worker/metadata projection; первые bytes только после late readback/bindings/cleanup. Старые r1/ENT17 pins сохранены; не current permissions/atomicity/новый формат архива.'}}

    def test_exact_revision_and_summary_approval(self):
        registry=json.loads((BASE/'catalog/registry.json').read_bytes())
        entity=next(e for e in registry['entities'] if e['entity_id']=='ENT-0016')
        actual=next(r for r in entity['revisions'] if r['revision']=='r0002')
        self.assertEqual(actual,self.EXPECTED)
        for artifact in actual['artifacts']:artifact_bytes(artifact)
        decision=json.loads(artifact_bytes(actual['approval']['reference']))
        self.assertEqual(decision['subject'],dict(catalog_id=CATALOG_ID,entity_id='ENT-0016',revision='r0002'))
        self.assertEqual(decision['statement_form'],'summary')
        self.assertEqual(decision['artifacts'],[{k:a[k] for k in ['path','sha256','size_bytes']} for a in actual['artifacts']])

    def test_runtime_pins_and_consumer_coexistence(self):
        import runpy
        old=runpy.run_path(str(BASE/'staging/ent-0016/r0001/read.py'))
        new=runpy.run_path(str(BASE/'staging/ent-0016/r0002/read.py'))
        self.assertEqual(old['PINS'],new['PINS']);self.assertEqual(len(new['PINS']),3)
        self.assertEqual(new['PROFILE'],'ent-0016-r0002-private-trial-capture')
        compare=runpy.run_path(str(BASE/'validation/ent-0017/r0001/compare.py'))
        self.assertTrue(all('r0001' in p for p in compare['PINS']))



class OperatorTrialDeploymentTests(unittest.TestCase):
    EXPECTED = {'revision': 'r0001', 'title': 'Ограниченный operator trial с byte handoff и отдельным semantic replay', 'kind': 'protocol', 'scopes': ['agent_system.operator_trial'], 'artifacts': [{'path': 'operator/ent-0018/r0001/acceptance_verify.py', 'sha256': '479dcc4a54d3ca5d2f7cf5a8a844d987ce6b90050955a66abfcea4b66c94aae9', 'size_bytes': 11722, 'role': 'normative'}, {'path': 'operator/ent-0018/r0001/evidence.py', 'sha256': '255bffc084d40ce598248ddda687249dcf548992ab4bc386a12cdaeb997f972f', 'size_bytes': 9453, 'role': 'normative'}, {'path': 'operator/ent-0018/r0001/lab.py', 'sha256': 'b14bebf61d26e2e2f6291db9c4d7d2a982b907488682c06a4acb7675cb98cc0f', 'size_bytes': 4182, 'role': 'normative'}, {'path': 'operator/ent-0018/r0001/procedure.md', 'sha256': '54f41439a8399f89e6d11dd7fd8ac95569e0bfce96667df5c3bb7bb4e2d0ccbd', 'size_bytes': 7077, 'role': 'normative'}, {'path': 'operator/ent-0018/r0001/prompt.md', 'sha256': '87f5ca9e72f58442981602d7910178c13b49f80ab931333d373f4f20c58be378', 'size_bytes': 2307, 'role': 'normative'}, {'path': 'operator/ent-0018/r0001/replay.py', 'sha256': '95ce2ad08944b1a8fe6d74b27a30f97f087b12b6ff159397b8b1876144fe5e37', 'size_bytes': 12615, 'role': 'normative'}, {'path': 'operator/ent-0018/r0001/replay_verify.py', 'sha256': 'b2ecd0a50dfb99452ffc910f89954f17a0e4700f61c198895a3dffcb5051a864', 'size_bytes': 8421, 'role': 'normative'}, {'path': 'operator/ent-0018/r0001/run.py', 'sha256': '68d3251e7b212b673b6705b32855f554829d76147467a18262e208635b4b1c00', 'size_bytes': 23614, 'role': 'normative'}, {'path': 'operator/ent-0018/r0001/runner_verify.py', 'sha256': 'd7451bdf77d030f11811472f83ccc3d43e1fb05004832b181a6029a05fa2df6e', 'size_bytes': 17076, 'role': 'normative'}, {'path': 'operator/ent-0018/r0001/session.py', 'sha256': '789a60c5b09744f804bfb3e9685eb63796fbfdeb561376aace5fc2bca8e82aad', 'size_bytes': 12464, 'role': 'normative'}, {'path': 'operator/ent-0018/r0001/session.schema.json', 'sha256': '76a3030a1f107a92e24cc80af978b0b1c9a0c5c0f16718829b8907a51a66e76f', 'size_bytes': 2856, 'role': 'normative'}, {'path': 'operator/ent-0018/r0001/usage.md', 'sha256': '13eeeab847fa30e15e6cce444a1b2cdd9982cf5147035aed8dfa25aadac12679', 'size_bytes': 12012, 'role': 'normative'}, {'path': 'operator/ent-0018/r0001/verify.py', 'sha256': '444b7ea06dd237a1720573ff0cb9e88d12a3b97cd30e7987372c7d931a71ee3a', 'size_bytes': 13735, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0009', 'revision': 'r0002'}}, {'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0013', 'revision': 'r0001'}}, {'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0015', 'revision': 'r0001'}}, {'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0016', 'revision': 'r0002'}}, {'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0017', 'revision': 'r0001'}}], 'approval': {'status': 'approved', 'reference': {'path': 'catalog/approvals/77e27297-3504-42b5-bee6-5db1cd4ac8ac.json', 'sha256': '5b1d80f01fc2ee2e5fe9c5c23c0f15532f7ab23cd4c022a475ad0587b6e39a7e'}}, 'provenance': {'summary': 'M1/I3–I4 по заданию B, дизайну D01–D18 и условному делегированию владельца. Exact implementation после prequalification; actual native practice отдельно после bootstrap registration. Local bounded trial/replay, не permission/release/activation.'}}

    def test_exact_revision_and_conditional_summary_approval(self):
        registry=json.loads((BASE/'catalog/registry.json').read_bytes())
        actual=next(e for e in registry['entities'] if e['entity_id']=='ENT-0018')['revisions'][0]
        self.assertEqual(actual,self.EXPECTED)
        self.assertEqual(len(actual['artifacts']),13)
        for a in actual['artifacts']:artifact_bytes(a)
        decision=json.loads(artifact_bytes(actual['approval']['reference']))
        self.assertEqual(decision['subject'],dict(catalog_id=CATALOG_ID,entity_id='ENT-0018',revision='r0001'))
        self.assertEqual(decision['decision_type'],'approve_revision')
        self.assertEqual(decision['statement_form'],'summary')
        self.assertEqual(decision['artifacts'],[{k:a[k] for k in ['path','sha256','size_bytes']} for a in actual['artifacts']])

    def test_exact_installed_profile_and_coexisting_revisions(self):
        import runpy
        runner=runpy.run_path(str(BASE/'operator/ent-0018/r0001/run.py'))
        profile,records=runner['_bootstrap'](runner['_load']())
        self.assertEqual(profile['selection'],[dict(catalog_id=CATALOG_ID,entity_id='ENT-0018',revision='r0001')])
        self.assertEqual((len(records),len(profile['artifacts']),len(runner['OWN'])),(20,70,13))
        self.assertEqual(runner['DEPENDENCIES'],{('ENT-0009','r0002'),('ENT-0016','r0002'),('ENT-0013','r0001'),('ENT-0015','r0001'),('ENT-0017','r0001')})
        for entity in ['ENT-0009','ENT-0016']:
            self.assertIn((entity,'r0001'),records);self.assertIn((entity,'r0002'),records)



class WorkPracticeDeploymentTests(unittest.TestCase):
    EXPECTED = {'revision': 'r0002', 'title': 'Методология с соразмерной процедурой наблюдаемой практической оценки', 'kind': 'protocol', 'scopes': ['agent_system.work', 'agent_system.governance'], 'artifacts': [{'path': 'protocols/ent-0011/r0002/work.md', 'sha256': '93a3c228c82db2e0af531804388871f222004aa85f3ddbfdeb8c0b1accee6c3d', 'size_bytes': 25060, 'role': 'normative'}, {'path': 'protocols/ent-0011/r0002/scenarios.json', 'sha256': '2e4697a26e6e7484b5ee5e94f65feb986b44e72bb93ec9ada10e68853d8e61df', 'size_bytes': 12480, 'role': 'normative'}, {'path': 'protocols/ent-0011/r0002/verify.py', 'sha256': '032a7626aef61300b6c2b2f6b0d9834d855d4e102ed993c2d850fd0e3ce61b69', 'size_bytes': 9127, 'role': 'normative'}, {'path': 'protocols/ent-0011/r0002/practice.md', 'sha256': '2cf74ac39c81a74db85196051f836a5f78797bc60c735aa733970a3a8d56e256', 'size_bytes': 5493, 'role': 'normative'}], 'relations': [{'type': 'depends_on', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0001', 'revision': 'r0001'}}, {'type': 'supersedes', 'target': {'catalog_id': '83bd5866-5e17-477f-9671-4e6a91481221', 'entity_id': 'ENT-0011', 'revision': 'r0001'}}], 'approval': {'status': 'approved', 'reference': {'path': 'catalog/approvals/5ba39be0-7106-4df0-8ed9-08305f6a3bda.json', 'sha256': 'bf5e45c7048b9c261c49bef669a26989375bfa61bfdce5fce7ecf7f92e3391e0'}}, 'provenance': {'summary': 'Универсальное расширение W09 по согласованному R3 и conditional delegation, не новый core/agent evaluator. Предварительно frozen S/D, открытая учебная практика и self-review с явными ограничениями; старые consumers не переключены.'}}

    def test_exact_full_revision_summary(self):
        registry=json.loads((BASE/'catalog/registry.json').read_bytes())
        actual=next(v for e in registry['entities'] if e['entity_id']=='ENT-0011' for v in e['revisions'] if v['revision']=='r0002')
        self.assertEqual(actual,self.EXPECTED)
        for a in actual['artifacts']:artifact_bytes(a)
        decision=json.loads(artifact_bytes(actual['approval']['reference']))
        self.assertEqual(decision['statement_form'],'summary')
        self.assertEqual(decision['decision_type'],'approve_revision')
        self.assertEqual(decision['subject'],dict(catalog_id=CATALOG_ID,entity_id='ENT-0011',revision='r0002'))
        self.assertEqual(decision['artifacts'],[{k:a[k] for k in ['path','sha256','size_bytes']} for a in actual['artifacts']])

    def test_existing_consumers_not_switched(self):
        registry=json.loads((BASE/'catalog/registry.json').read_bytes())
        versions={(e['entity_id'],v['revision']):v for e in registry['entities'] for v in e['revisions']}
        for e in ['ENT-0012','ENT-0013']:
            closure=set();todo=[(e,'r0001')]
            while todo:
                key=todo.pop()
                if key in closure:continue
                closure.add(key)
                todo += [(rel['target']['entity_id'],rel['target']['revision']) for rel in versions[key]['relations'] if rel['type']=='depends_on']
            self.assertIn(('ENT-0011','r0001'),closure)
            self.assertNotIn(('ENT-0011','r0002'),closure)
        import runpy
        runner=runpy.run_path(str(BASE/'operator/ent-0018/r0001/run.py'))
        profile,records=runner['_bootstrap'](runner['_load']())
        self.assertEqual((len(records),len(profile['artifacts'])),(20,70))
        self.assertIn(('ENT-0011','r0001'),records);self.assertNotIn(('ENT-0011','r0002'),records)


if __name__ == '__main__':
    unittest.main()
