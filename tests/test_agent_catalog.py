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
                         {'ENT-0001', 'ENT-0002'})
        self.assertEqual(len(self.registry['entities']), 2)
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
        self.assertEqual([r['revision'] for r in self.entity['revisions']], ['r0002'])
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


if __name__ == '__main__':
    unittest.main()
