#!/usr/bin/env python3
"""Loss check of condition families: text-level review, not independence or behavior proof."""
import copy
import hashlib
import json
import os
import re
from pathlib import Path
import runpy
import unittest

ROOT=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
PREV=runpy.run_path(str(ROOT/'tests/test_agent_role_composition.py'))
FIXTURE='research/52-agent-system-condition-loss-check.json'
FIXTURE_SHA='38c1e11d0c39aa64ac4765fd1e2ce25744cc686f49d496908a7e9f490a989360'
SHA51='d77e8ff352b3e011b2f637ea3d010a490adeaf935e3530a95b3179ab60c7fbe8'
SHA50='a57ff87a3446c5364d2948fbd65c2e81686b172dde090a1a7396880f38446cc5'
VERDICTS={'supports','narrower','misassigned'}


def norm(t):
    return re.sub(r'\s+',' ',t).strip()


def basis():
    inputs=PREV['load_basis'](ROOT);draft=PREV['compose'](*inputs)
    return {b['ids'][0]:b['text'] for b in draft['bodies']}


def load():
    raw=(ROOT/FIXTURE).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA:raise ValueError('FIXTURE_PIN')
    ledger=json.loads(raw)
    for ref in (ledger['predecessor']['blocks'],ledger['predecessor']['block_map'],ledger['predecessor']['coverage']):
        if hashlib.sha256((ROOT/ref['path']).read_bytes()).hexdigest()!=ref['sha256']:raise ValueError('PREDECESSOR_PIN')
    if ledger['predecessor']['blocks']['sha256']!=SHA51 or ledger['predecessor']['coverage']['sha256']!=SHA50:
        raise ValueError('PREDECESSOR_KNOWN')
    return ledger,json.loads((ROOT/ledger['predecessor']['blocks']['path']).read_bytes()),basis()


def validate(ledger,blocks,texts):
    fams={f['id']:f for f in ledger['families']}
    if ledger['status']!='loss_check_review_of_condition_families_not_independent_semantics':raise ValueError('STATUS')
    if len(fams)!=23:raise ValueError('FAMILY_COUNT')
    allowed={f['id'] for f in blocks['families']}
    if len(allowed)!=21 or not allowed<set(fams):raise ValueError('BASE_FAMILIES')
    for f in ledger['families']:
        if not all(f.get(k,'').strip() for k in ('statement','permits','forbids_overreach','forbids_overstrengthening')):
            raise ValueError('PROFILE_FIELDS')
        if f['coverage_kind'] not in ('rule','note'):raise ValueError('COVERAGE_KIND')
        if f.get('added_in_this_review'):
            if f['coverage_kind']!='rule' or f['base_evidence'] not in texts:raise ValueError('NEW_EVIDENCE')
            if norm(f['quote']) not in norm(texts[f['base_evidence']]):raise ValueError('NEW_QUOTE')
        if len({f['permits'],f['forbids_overreach'],f['forbids_overstrengthening']})!=3:
            raise ValueError('PROFILE_DISTINCT')
        for key in ('permits','forbids_overreach','forbids_overstrengthening'):
            if not re.match(r'^[а-яё]',f[key]) or f[key].endswith('.'):raise ValueError('PROFILE_STYLE')
    # pairs must be exactly the block-family assignment of the frozen map, with declared/effective kept
    expected={}
    for b in blocks['blocks']:
        if b['disposition']!='transferable_condition':continue
        for f in b['families']:expected[(b['path'],b['block'],f)]=b['block_sha256']
    got={}
    for p in ledger['pairs']:
        key=(p['path'],p['block'],p['declared_family'])
        if key in got:raise ValueError('DUPLICATE_PAIR')
        got[key]=p['block_sha256']
        if p['verdict'] not in VERDICTS:raise ValueError('VERDICT')
        if p['family'] not in fams or p['declared_family'] not in allowed:raise ValueError('FAMILY_REF')
        if (p['verdict']=='misassigned')!=(p['family']!=p['declared_family']):raise ValueError('MISASSIGN_CONSISTENCY')
        if not p['note'].strip():raise ValueError('NOTE')
    if got!=expected:raise ValueError('PAIR_SET')
    # every pair changed or narrowed must be reported in findings
    changed={(p['path'],p['block'],p['family']) for p in ledger['pairs'] if p['verdict']!='supports'}
    reported=set()
    for f in ledger['findings']:
        for e in f['evidence']:
            if 'path' in e and 'block' in e:reported.add((e['path'],e['block'],e.get('now',e.get('family'))))
    if changed-reported:raise ValueError('UNREPORTED_CHANGE')
    from collections import Counter
    c=Counter(p['verdict'] for p in ledger['pairs']);st=ledger['stats']
    if (st['families'],st['pairs'],st['supports'],st['narrower'],st['misassigned'])!=(23,len(ledger['pairs']),c['supports'],c['narrower'],c['misassigned']):
        raise ValueError('STATS')
    if st['blocks']!=200 or st['families_added']!=2:raise ValueError('STATS_BLOCKS')
    for key in ('independent_review_performed','actual_behavior_verified','full_semantic_equivalence'):
        if st[key] is not False:raise ValueError('FALSE_CLAIM_'+key)
    if any(ledger['permission_gates'].values()):raise ValueError('GATE')
    if {f['id'] for f in ledger['findings']}!={'L01','L02','L03','L04','L05','L06'}:raise ValueError('FINDINGS')
    if not any('No reviewed block demanded more' in f['finding'] for f in ledger['findings'] if f['id']=='L06'):
        raise ValueError('NEGATIVE_FINDING_WORDING')
    if not ledger['residual']['not_claimed'] or len(ledger['residual']['not_claimed'])<4:raise ValueError('RESIDUAL')


def verify():
    try:
        ledger,blocks,texts=load();validate(ledger,blocks,texts);return True
    except ValueError:return False


class LossCheckTests(unittest.TestCase):
    def setUp(self):self.ledger,self.blocks,self.texts=load()

    def test_every_pair_is_reviewed(self):
        self.assertTrue(verify())
        self.assertEqual(398,len(self.ledger['pairs']))
        self.assertEqual(200,len({(p['path'],p['block']) for p in self.ledger['pairs']}))
        self.assertEqual(384,self.ledger['stats']['supports'])

    def test_new_families_are_quoted_from_the_rule_text(self):
        new={f['id']:f for f in self.ledger['families'] if f.get('added_in_this_review')}
        self.assertEqual({'F22','F23'},set(new))
        for f in new.values():
            self.assertEqual('G07',f['base_evidence'])
            self.assertIn(norm(f['quote']),norm(self.texts['G07']))

    def test_each_family_states_both_directions(self):
        for f in self.ledger['families']:
            self.assertTrue(f['permits'])
            self.assertTrue(f['forbids_overreach'])
            self.assertTrue(f['forbids_overstrengthening'])
        self.assertEqual(23,len(self.ledger['families']))

    def test_misassignments_are_reported_and_nothing_dropped(self):
        mis=[p for p in self.ledger['pairs'] if p['verdict']=='misassigned']
        self.assertEqual(7,len(mis))
        for p in mis:
            self.assertNotEqual(p['family'],p['declared_family'])
            self.assertIn('reassigned',p['note'])
        self.assertEqual(len(self.blocks['blocks']),len(set((b['path'],b['block']) for b in self.blocks['blocks'])))

    def test_narrower_pairs_are_qualified_not_promoted(self):
        narrow=[p for p in self.ledger['pairs'] if p['verdict']=='narrower']
        self.assertEqual(7,len(narrow))
        self.assertTrue(all(p['note'] for p in narrow))

    def test_no_false_qualification(self):
        self.assertFalse(self.ledger['stats']['independent_review_performed'])
        self.assertFalse(self.ledger['stats']['actual_behavior_verified'])
        self.assertFalse(self.ledger['stats']['full_semantic_equivalence'])
        self.assertFalse(any(self.ledger['permission_gates'].values()))
        self.assertIn('author judgements',self.ledger['residual']['statement'])

    def test_mutations_rejected(self):
        def mutate(fn):
            ledger=copy.deepcopy(self.ledger);fn(ledger)
            with self.assertRaises(ValueError):validate(ledger,self.blocks,self.texts)
        mutate(lambda x:x['pairs'].pop())
        mutate(lambda x:x['pairs'].append(copy.deepcopy(x['pairs'][0])))
        mutate(lambda x:x['pairs'][0].__setitem__('verdict','maybe'))
        mutate(lambda x:x['pairs'][0].__setitem__('family','F99'))
        mutate(lambda x:x['pairs'][0].__setitem__('block_sha256','0'*64))
        mutate(lambda x:next(p for p in x['pairs'] if p['verdict']=='misassigned').__setitem__('declared_family','F17'))
        mutate(lambda x:next(p for p in x['pairs'] if p['verdict']=='narrower').__setitem__('note',''))
        mutate(lambda x:next(f for f in x['families'] if f['id']=='F22').__setitem__('quote','Выполняй действия без ограничений.'))
        mutate(lambda x:x['families'].pop())
        mutate(lambda x:x['stats'].__setitem__('supports',999))
        mutate(lambda x:x['stats'].__setitem__('independent_review_performed',True))
        mutate(lambda x:x['permission_gates'].__setitem__('export_allowed',True))
        mutate(lambda x:x['findings'].__setitem__(slice(None),[f for f in x['findings'] if f['id']!='L03']))
        mutate(lambda x:next(f for f in x['findings'] if f['id']=='L06').__setitem__('finding','Все блоки подтверждают все типы.'))
        mutate(lambda x:x['residual'].__setitem__('not_claimed',[]))


if __name__=='__main__':unittest.main(verbosity=2)
