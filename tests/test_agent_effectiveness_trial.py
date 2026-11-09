#!/usr/bin/env python3
"""Bounded effectiveness trial: discrimination, not behavioural proof."""
import copy
import hashlib
import json
import os
import re
from pathlib import Path
import unittest

ROOT=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
FIXTURE='research/55-agent-system-effectiveness-trial.json'
FIXTURE_SHA='0bd2be27b6c959cc4965afb068a29edfe045e542921368db4ee52b6813fa0418'
RULES='research/53-agent-system-condition-rules.md'
RULES_SHA='ede459ee165575948d1710591ac8422d78570ac9f4f9b9f2eae34109f5bf15bb'
ROLES={'permissive','correct','forbidding'}


def words(t):
    return re.findall(r'[а-яёa-z0-9]+',t.lower())


def longest_common(a,b):
    A,B=words(a),words(b);best=0
    for i in range(len(A)):
        for j in range(len(B)):
            k=0
            while i+k<len(A) and j+k<len(B) and A[i+k]==B[j+k]:k+=1
            best=max(best,k)
    return best


def load():
    raw=(ROOT/FIXTURE).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA:raise ValueError('FIXTURE_PIN')
    ledger=json.loads(raw)
    if hashlib.sha256((ROOT/ledger['accepted_text']['path']).read_bytes()).hexdigest()!=ledger['accepted_text']['sha256']:
        raise ValueError('RULES_CHANGED')
    return ledger,json.loads((ROOT/'research/53-agent-system-condition-rules.json').read_bytes())


def validate(ledger,rules):
    if ledger['status']!='bounded_effectiveness_trial_author_judged_not_independent':raise ValueError('STATUS')
    cases=ledger['cases'];ids={r['id'] for r in rules['rules']}
    if len(cases)!=16 or len({c['id'] for c in cases})!=16:raise ValueError('CASE_IDS')
    positions=set();used=set()
    for c in cases:
        if set(c['options'])!={'A','B','C'}:raise ValueError('OPTIONS')
        if len(set(c['options'].values()))!=3:raise ValueError('OPTION_DISTINCT')
        if c['options'][c['answer_key']['correct']]!=c['options'][c['expected']]:raise ValueError('EXPECTED_TEXT')
        role=c['option_role']
        if set(role.values())!=ROLES or set(role)!={'A','B','C'}:raise ValueError('ROLE_MAP')
        if c['answer_key']['correct']!=c['expected']:raise ValueError('EXPECTED_POINTS_TO_CORRECT')
        if set(c['answer_key'])!=ROLES or set(c['answer_key'].values())!={'A','B','C'}:
            raise ValueError('ANSWER_KEY')
        if not set(c['rules'])<=ids:raise ValueError('RULE_REF')
        used|=set(c['rules'])
        positions.add(c['expected'])
        if len(c['trap'].split('/'))!=2:raise ValueError('TRAP')
    if positions!={'A','B','C'}:raise ValueError('POSITION_BIAS')
    if used!=ids:raise ValueError('RULE_COVERAGE')
    # held-out: cases must not quote the rule text
    text=' '.join(r['statement']+' '+r['permits']+' '+r['forbids_overreach']+' '+r['forbids_overstrengthening'] for r in rules['rules'])
    worst=max(longest_common(c['prompt'],text) for c in cases)
    if worst>=9:raise ValueError('LEAKAGE')
    m=ledger['metrics']
    def correct(fn):return sum(1 for c in cases if fn(c)==c['expected'])
    expect={'permissive_all':0,'forbidding_all':0}
    if m['baselines']['permissive_all']['correct']!=0 or m['baselines']['forbidding_all']['correct']!=0:
        raise ValueError('BASELINE')
    for name in ('always_A','always_B','always_C'):
        if m['baselines'][name]['correct']!=correct(lambda c,n=name:n[-1]):raise ValueError('FIXED_BASELINE_'+name)
    if m['rules']['correct']!=len(cases):raise ValueError('RULES_SCORE')
    if m['discrimination_vs_permissive']!=len(cases) or m['discrimination_vs_forbidding']!=len(cases):
        raise ValueError('DISCRIMINATION')
    if m['rules_unused'] or m['rules_used']!=23:raise ValueError('UNUSED_RULES')
    d=ledger['design']
    if 'always-B' not in d['first_draft_defect']:raise ValueError('DEFECT_DISCLOSURE')
    if 'rotated' not in d['option_order']:raise ValueError('ROTATION')
    lim=ledger['limits']
    for key in ('independent_review_performed','independent_execution','actual_agent_behavior_verified','statistical_generalisation'):
        if lim[key] is not False:raise ValueError('FALSE_CLAIM_'+key)
    if lim['author_judged'] is not True:raise ValueError('AUTHOR_JUDGED')
    if any(ledger['permission_gates'].values()):raise ValueError('GATE')
    if 'readiness' not in ' '.join(ledger['not_granted']):raise ValueError('NOT_GRANTED')


class TrialTests(unittest.TestCase):
    def setUp(self):self.ledger,self.rules=load()

    def test_pins_and_no_position_bias(self):
        self.assertEqual(RULES_SHA,hashlib.sha256((ROOT/RULES).read_bytes()).hexdigest())
        positions=[c['expected'] for c in self.ledger['cases']]
        self.assertEqual({'A','B','C'},set(positions))
        self.assertEqual(16,len(positions))

    def test_rules_outperform_chance_and_extremes(self):
        m=self.ledger['metrics']
        self.assertEqual(16,m['rules']['correct'])
        self.assertEqual(0,m['baselines']['permissive_all']['correct'])
        self.assertEqual(0,m['baselines']['forbidding_all']['correct'])
        for name in ('always_A','always_B','always_C'):
            self.assertLess(m['baselines'][name]['correct'],8)

    def test_every_rule_is_tested(self):
        self.assertEqual(23,self.ledger['metrics']['rules_used'])
        self.assertEqual([],self.ledger['metrics']['rules_unused'])

    def test_cases_are_held_out(self):
        text=' '.join(r['statement']+' '+r['permits']+' '+r['forbids_overreach']+' '+r['forbids_overstrengthening'] for r in self.rules['rules'])
        worst=max(longest_common(c['prompt'],text) for c in self.ledger['cases'])
        self.assertLess(worst,9)

    def test_earlier_design_defect_is_disclosed(self):
        self.assertIn('always-B',self.ledger['design']['first_draft_defect'])
        self.assertIn('12/12',self.ledger['design']['first_draft_defect'])

    def test_no_behavioural_or_independent_claim(self):
        lim=self.ledger['limits']
        self.assertFalse(lim['actual_agent_behavior_verified'])
        self.assertFalse(lim['independent_review_performed'])
        self.assertFalse(lim['independent_execution'])
        self.assertFalse(lim['statistical_generalisation'])
        self.assertFalse(any(self.ledger['permission_gates'].values()))

    def test_mutations_rejected(self):
        def mutate(fn):
            ledger=copy.deepcopy(self.ledger);fn(ledger)
            with self.assertRaises(ValueError):validate(ledger,self.rules)
        mutate(lambda x:x['cases'].pop())
        mutate(lambda x:next(c for c in x['cases'] if c['id']=='T03').__setitem__('expected','A'))
        mutate(lambda x:next(c for c in x['cases'] if c['id']=='T05').__setitem__('expected','C'))
        mutate(lambda x:next(c for c in x['cases'] if c['id']=='T07').__setitem__('rules',['F99']))
        mutate(lambda x:next(c for c in x['cases'] if c['id']=='T13').__setitem__('prompt','Когда выбранный контракт требует отдельного получения для нового запроса, архив, replay или совпавшие байты его не заменяют'))
        mutate(lambda x:x['metrics']['baselines']['always_B'].__setitem__('correct',16))
        mutate(lambda x:x['metrics'].__setitem__('rules_unused',['F04']))
        mutate(lambda x:x['metrics'].__setitem__('discrimination_vs_permissive',1))
        mutate(lambda x:x['limits'].__setitem__('actual_agent_behavior_verified',True))
        mutate(lambda x:x['permission_gates'].__setitem__('release_allowed',True))
        mutate(lambda x:x['design'].__setitem__('option_order','fixed'))
        mutate(lambda x:x['design'].__setitem__('first_draft_defect',''))
        mutate(lambda x:next(c for c in x['cases'] if c['id']=='T01')['option_role'].__setitem__('A','correct'))


if __name__=='__main__':unittest.main(verbosity=2)
