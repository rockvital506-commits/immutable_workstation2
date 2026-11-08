#!/usr/bin/env python3
"""Pinned-source research draft assembly; not a generic semantic verifier/exporter."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
FIXTURE='research/46-agent-system-core-meaning-coverage.json'
FIXTURE_SHA='c94a1b52e01e24339ebdb896b7c78f99ee12900df635c7a21c3ab13618ea5655'


def canonical(data):
    return json.dumps(data,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))


def read_pinned(root,ref):
    # Trusted local laboratory roots, not a hostile-tree acquisition adapter.
    data=(root/ref['path']).read_bytes()
    if hashlib.sha256(data).hexdigest()!=ref['sha256'] or len(data)!=ref['size_bytes']:
        raise ValueError('PIN_MISMATCH')
    return data


def extract(capture,ref):
    text=capture[ref['path']]
    if not (0<=ref['start']<ref['end']<=len(text)):
        raise ValueError('SOURCE_SPAN')
    return text[ref['start']:ref['end']]


def derive_closure(registry,roots):
    table={(e['entity_id'],r['revision']):r for e in registry['entities'] for r in e['revisions']}
    pending=copy.deepcopy(roots);seen=set();result=[]
    while pending:
        target=pending.pop()
        if target['catalog_id']!=registry['catalog_id']:
            raise ValueError('DEPENDENCY_CATALOG')
        key=(target['entity_id'],target['revision'])
        if key in seen:continue
        seen.add(key);revision=table[key]
        deps=[r['target'] for r in revision['relations'] if r['type']=='depends_on']
        result.append(dict(entity_id=key[0],revision=key[1],depends_on=deps))
        pending.extend(deps)
    return sorted(result,key=lambda r:(r['entity_id'],r['revision']))


def load_basis(root=ROOT):
    raw=(root/FIXTURE).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA:
        raise ValueError('FIXTURE_PIN')
    basis=json.loads(raw)
    for ref in basis['predecessors']:read_pinned(root,ref)
    registry=json.loads(read_pinned(root,basis['registry']))
    if derive_closure(registry,basis['roots'])!=basis['declared_closure']:
        raise ValueError('DECLARED_CLOSURE')
    # Capture each selected source ONCE and assemble from these checked bytes.
    capture={ref['path']:read_pinned(root,ref).decode('utf-8') for ref in basis['sources']}
    table={(e['entity_id'],r['revision']):r for e in registry['entities'] for r in e['revisions']}
    artifacts={a['path']:a for node in basis['declared_closure']
               for a in table[node['entity_id'],node['revision']]['artifacts']}
    for ref in basis['sources']:
        artifact=artifacts[ref['path'].removeprefix('agent_system/')]
        if artifact['sha256']!=ref['sha256'] or artifact['size_bytes']!=ref['size_bytes']:
            raise ValueError('SOURCE_REGISTRY_BINDING')
    if set(basis['unselected_artifact_gaps'])!=set(artifacts)-{p.removeprefix('agent_system/') for p in capture}:
        raise ValueError('ARTIFACT_GAPS')
    ids=set()
    for unit in basis['units']:
        if unit['id'] in ids:raise ValueError('DUPLICATE_UNIT')
        ids.add(unit['id'])
        bodies=[extract(capture,ref) for ref in unit['origins']]
        scopes=[extract(capture,ref) for ref in unit['contexts']]
        if len(set(bodies))!=1 or len(set(scopes))!=1:
            raise ValueError('UNSAFE_ALIAS')
        if unit['route']=='generalize' and not unit['generated_body']:
            raise ValueError('GENERALIZATION_MISSING')
    return basis,capture


def unmapped_spans(basis,capture):
    gaps=[]
    for path,text in capture.items():
        ranges=sorted((r['start'],r['end']) for u in basis['units']
                      for r in u['origins']+u['contexts'] if r['path']==path)
        pos=0
        for start,end in ranges+[(len(text),len(text))]:
            if start>pos and text[pos:start].strip():
                gaps.append(dict(path=path,start=pos,end=start,status='not_semantically_mapped'))
            pos=max(pos,end)
    return gaps


def assemble(basis,capture):
    bodies=[];pending=[]
    for unit in basis['units']:
        if unit['route'] in ('hold','external_reference'):
            pending.append(dict(id=unit['id'],route=unit['route'],origins=unit['origins']))
            continue
        # No reread by source names; no duplicate high texts embedded in ledger.
        text=(extract(capture,unit['origins'][0]) if unit['route']=='preserve'
              else unit['generated_body'])
        bodies.append(dict(id=unit['id'],text=text,scope=extract(capture,unit['contexts'][0]),
                           origins=unit['origins'],contexts=unit['contexts'],route=unit['route']))
    return dict(status='partial_research_draft_not_exportable',bodies=bodies,unresolved=pending,
                roots=basis['roots'],declared_closure=basis['declared_closure'],
                unselected_artifact_gaps=basis['unselected_artifact_gaps'],
                unmapped_source_spans=unmapped_spans(basis,capture),
                related_not_merged=basis['related_not_merged'],
                authority_guard='text_is_not_a_grant',review='agent_self_review_not_independent',
                full_semantic_coverage=False,semantic_equivalence='not_established',
                release_allowed=False,export_allowed=False,activation_allowed=False,
                compatible_release_allowed=False)


def verify_draft(candidate):
    basis,capture=load_basis()
    return canonical(candidate)==canonical(assemble(basis,capture))


class CoreMeaningCoverageTests(unittest.TestCase):
    def setUp(self):
        self.basis,self.capture=load_basis()
        self.draft=assemble(self.basis,self.capture)

    def body(self,uid):return next(u for u in self.draft['bodies'] if u['id']==uid)

    def test_positive_draft_with_explicit_gaps(self):
        self.assertTrue(verify_draft(self.draft))
        self.assertEqual(39,len(self.basis['units']))
        self.assertEqual(32,len(self.draft['bodies']))
        self.assertEqual(7,len(self.draft['unresolved']))
        self.assertTrue(self.draft['unmapped_source_spans'])
        self.assertFalse(self.draft['full_semantic_coverage'])

    def test_all_ent2_requirements_accounted_for(self):
        self.assertEqual([f'D{i:02}' for i in range(1,11)],
                         [u['id'] for u in self.basis['units'] if u['id'].startswith('D')])
        self.assertIn(dict(id='D04',route='external_reference',origins=next(u['origins'] for u in self.basis['units'] if u['id']=='D04')),self.draft['unresolved'])

    def test_all_w_groups_accounted_for(self):
        expected={f'W{i:02}' for i in range(10)}-{'W06'}|{'W06a','W06b','W06c'}
        self.assertEqual(expected,{u['id'] for u in self.basis['units'] if u['id'].startswith('W') and u['id'] not in {'WR','WR2-practice'}})

    def test_duplicate_bodies_have_both_exact_origins(self):
        shared=[u for u in self.draft['bodies'] if len(u['origins'])==2]
        self.assertEqual(13,len(shared))
        for unit in shared:
            self.assertEqual(1,len({extract(self.capture,r) for r in unit['origins']}))
            self.assertTrue(any('/r0001/' in r['path'] for r in unit['origins']))
            self.assertTrue(any('/r0002/' in r['path'] for r in unit['origins']))

    def test_r1_and_r2_dependencies_remain_distinct(self):
        nodes={(n['entity_id'],n['revision']):n for n in self.draft['declared_closure']}
        r1=nodes['ENT-0012','r0001']['depends_on'];r2=nodes['ENT-0012','r0002']['depends_on']
        self.assertIn(('ENT-0011','r0001'),[(r['entity_id'],r['revision']) for r in r1])
        self.assertNotIn(('ENT-0011','r0002'),[(r['entity_id'],r['revision']) for r in r1])
        self.assertIn(('ENT-0011','r0002'),[(r['entity_id'],r['revision']) for r in r2])
        self.assertEqual(24,len(nodes));self.assertEqual(85,len(self.draft['unselected_artifact_gaps']))

    def test_practice_extension_is_not_deduplicated_away(self):
        ext=self.body('WR2-practice')
        self.assertEqual(1,len(ext['origins']))
        self.assertIn('practice.md',ext['text'])
        self.assertIn('/r0002/',ext['origins'][0]['path'])
        self.draft['bodies'].remove(ext);self.assertFalse(verify_draft(self.draft))

    def test_local_delegation_is_conditional_not_a_new_grant(self):
        unit=self.body('W06b')
        self.assertEqual('generalize',unit['route'])
        self.assertIn('Если владелец отдельно предоставил',unit['text'])
        self.assertIn('не создаёт делегирование в другой среде',unit['text'])
        self.assertNotIn('В этой системе действует ранее данное условие',unit['text'])
        self.assertIn('Источником полномочия',self.body('W06c')['text'])
        unit['text']='Разрешено внедрять по умолчанию в любой новой среде.'
        self.assertFalse(verify_draft(self.draft))

    def test_dropped_origin_not_silently_deduplicated(self):
        self.body('W00')['origins'].pop();self.assertFalse(verify_draft(self.draft))

    def test_different_scope_cannot_be_merged(self):
        self.body('W00')['scope']='Применяется везде без ограничений.'
        self.assertFalse(verify_draft(self.draft))

    def test_similar_but_different_norms_remain_separate(self):
        for left,right in self.draft['related_not_merged']:
            self.assertNotEqual(self.body(left)['text'],self.body(right)['text'])
        self.draft['bodies']=[u for u in self.draft['bodies'] if u['id']!='G01']
        self.assertFalse(verify_draft(self.draft))

    def test_latest_retarget_rejected(self):
        self.draft['declared_closure'][0]['revision']='latest'
        self.assertFalse(verify_draft(self.draft))

    def test_missing_hold_and_missing_artifact_gap_rejected(self):
        for name in ('unresolved','unselected_artifact_gaps','unmapped_source_spans'):
            candidate=copy.deepcopy(self.draft);candidate[name]=[]
            self.assertFalse(verify_draft(candidate))

    def test_full_governance_not_claimed(self):
        holds={u['id'] for u in self.draft['unresolved']}
        self.assertEqual({'D04','PR04','G00','G04','G05','G08','G09'},holds)

    def test_loss_of_condition_or_exception_rejected(self):
        for uid in ('D08','W07','G02','G06','G07'):
            candidate=copy.deepcopy(self.draft)
            next(u for u in candidate['bodies'] if u['id']==uid)['text']='Всегда продолжать.'
            self.assertFalse(verify_draft(candidate))

    def test_no_added_rule_metadata_or_authority(self):
        candidate=copy.deepcopy(self.draft);candidate['new_grant']='automatic'
        self.assertFalse(verify_draft(candidate))
        for flag in ('release_allowed','export_allowed','activation_allowed','compatible_release_allowed','full_semantic_coverage'):
            candidate=copy.deepcopy(self.draft);candidate[flag]=True
            self.assertFalse(verify_draft(candidate))

    def test_coherent_false_source_pin_does_not_self_approve(self):
        unit=self.body('W06c');unit['text']='Молчание даёт разрешение.'
        unit['origins'][0]['sha256']=hashlib.sha256(unit['text'].encode()).hexdigest()
        self.assertFalse(verify_draft(self.draft))

    def test_render_uses_checked_capture_not_reread(self):
        # Capture is frozen by independently pinned source reads; assembly has no I/O.
        from unittest.mock import patch
        with patch.object(Path,'read_bytes',side_effect=AssertionError('REREAD')):
            self.assertEqual(canonical(self.draft),canonical(assemble(self.basis,self.capture)))

    def test_source_and_predecessor_mutations_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            refs=[dict(path=FIXTURE)]+self.basis['sources']+self.basis['predecessors']+[self.basis['registry']]
            for ref in refs:
                target=root/ref['path'];target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((ROOT/ref['path']).read_bytes())
            target=root/self.basis['sources'][0]['path'];original=target.read_bytes()
            target.write_bytes(original+b'\n')
            with self.assertRaisesRegex(ValueError,'PIN_MISMATCH'):load_basis(root)
            target.write_bytes(original)
            target=root/self.basis['predecessors'][0]['path'];target.write_bytes(target.read_bytes()+b'\n')
            with self.assertRaisesRegex(ValueError,'PIN_MISMATCH'):load_basis(root)


if __name__=='__main__':
    unittest.main(verbosity=2)
