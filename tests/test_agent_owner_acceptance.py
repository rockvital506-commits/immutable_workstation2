#!/usr/bin/env python3
"""Owner acceptance of the derived candidate text: byte-bound, not a registration or grant."""
import copy
import hashlib
import json
import os
from pathlib import Path
import unittest

ROOT=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
FIXTURE='research/54-agent-system-owner-acceptance.json'
FIXTURE_SHA='525dc3b2c415927b308debf3d665770dad99f7a13b72eac85f70124feee673e6'
RULES='research/53-agent-system-condition-rules.md'
LEDGER='research/53-agent-system-condition-rules.json'
RULES_SHA='ede459ee165575948d1710591ac8422d78570ac9f4f9b9f2eae34109f5bf15bb'
LEDGER_SHA='bc5dc93e58fdc9df7e49e24e870e7e8b00193f19fc2d057a54593ad6961f2c29'
REQUIRED_NOT_GRANTED={'registration as normative revision','release','export','activation',
                      'compatible release','new environment','change of the normative registry'}


def sha(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def load():
    raw=(ROOT/FIXTURE).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA:raise ValueError('FIXTURE_PIN')
    rec=json.loads(raw);validate(rec);return rec


def validate(rec):
    if rec['kind']!='owner_acceptance_of_derived_candidate_text':raise ValueError('KIND')
    if rec['decision']['outcome']!='accepted':raise ValueError('OUTCOME')
    if rec['owner_statement']['verbatim']!='принять':raise ValueError('OWNER_WORD')
    pins={p['path']:p for p in rec['accepted']}
    if set(pins)!={RULES,LEDGER}:raise ValueError('ACCEPTED_SET')
    if pins[RULES]['sha256']!=RULES_SHA or pins[LEDGER]['sha256']!=LEDGER_SHA:raise ValueError('ACCEPTED_PINS')
    for p in pins.values():
        raw=(ROOT/p['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=p['sha256'] or len(raw)!=p['size_bytes']:
            raise ValueError('ACCEPTED_BYTES_CHANGED')
    d=rec['decision']
    if d['normative_status_after']!='not_a_registered_revision':raise ValueError('NORMATIVE_STATUS')
    if 'owner_accepted_candidate' not in d['effect_on_status']:raise ValueError('EFFECT')
    ng=rec['explicitly_not_granted']
    if not REQUIRED_NOT_GRANTED<=set(ng):raise ValueError('NOT_GRANTED')
    if any(w in ' '.join(ng).lower() for w in ('grant:','разрешено:')):raise ValueError('GRANT_LEAK')
    v=rec['verification']
    for k in ('independent_review_performed','actual_behavior_verified','full_semantic_equivalence','owner_identity_authenticated'):
        if v[k] is not False:raise ValueError('FALSE_CLAIM_'+k)
    if rec['limits']['not_a_catalog_approval'] is not True:raise ValueError('CATALOG_APPROVAL')
    if not rec['conditions'] or len(rec['conditions'])<4:raise ValueError('CONDITIONS')
    if any('аннулирует' not in c for c in rec['conditions'] if 'байт' in c):raise ValueError('BYTE_BINDING_CONDITION')
    if len(rec['open_items'])<6:raise ValueError('OPEN_ITEMS')
    if not rec['acceptance_id'] or len(rec['acceptance_id'])!=36:raise ValueError('ACCEPTANCE_ID')
    if rec['recorded_by']!='agent_on_behalf_of_conversation_record':raise ValueError('RECORDER')


class AcceptanceTests(unittest.TestCase):
    def setUp(self):self.rec=load()

    def test_acceptance_is_bound_to_exact_bytes(self):
        self.assertEqual(self.rec['decision']['outcome'],'accepted')
        self.assertEqual(RULES_SHA,sha(RULES))
        self.assertEqual(LEDGER_SHA,sha(LEDGER))

    def test_owner_word_and_scope(self):
        self.assertEqual('принять',self.rec['owner_statement']['verbatim'])
        self.assertEqual('accepted',self.rec['decision']['outcome'])
        self.assertIn('только текст',self.rec['decision']['scope'])

    def test_acceptance_grants_nothing(self):
        ng=set(self.rec['explicitly_not_granted'])
        self.assertTrue(REQUIRED_NOT_GRANTED<=ng)
        self.assertEqual('not_a_registered_revision',self.rec['decision']['normative_status_after'])
        self.assertTrue(self.rec['limits']['not_a_catalog_approval'])
        self.assertFalse(self.rec['verification']['owner_identity_authenticated'])
        self.assertFalse(self.rec['verification']['actual_behavior_verified'])

    def test_record_does_not_claim_independence(self):
        self.assertFalse(self.rec['verification']['independent_review_performed'])
        self.assertFalse(self.rec['verification']['full_semantic_equivalence'])
        self.assertIn('не аутентифицирует личность',self.rec['limits']['statement'])

    def test_editing_the_text_invalidates_the_acceptance(self):
        self.assertTrue(any('изменение текста аннулирует' in c for c in self.rec['conditions']))
        self.assertTrue(any('нового решения' in c for c in self.rec['conditions']))

    def test_mutations_rejected(self):
        def mutate(fn):
            rec=copy.deepcopy(self.rec);fn(rec)
            with self.assertRaises(ValueError):validate(rec)
        mutate(lambda x:x['accepted'][0].__setitem__('sha256','0'*64))
        mutate(lambda x:x['accepted'].pop())
        mutate(lambda x:x['accepted'].append(dict(path='research/48-agent-system-role-aware-composition.json',sha256='0'*64,size_bytes=1)))
        mutate(lambda x:x['decision'].__setitem__('outcome','rejected'))
        mutate(lambda x:x['decision'].__setitem__('normative_status_after','registered'))
        mutate(lambda x:x['owner_statement'].__setitem__('verbatim','продолжай'))
        mutate(lambda x:x['explicitly_not_granted'].remove('release'))
        mutate(lambda x:x['verification'].__setitem__('actual_behavior_verified',True))
        mutate(lambda x:x['verification'].__setitem__('owner_identity_authenticated',True))
        mutate(lambda x:x['limits'].__setitem__('not_a_catalog_approval',False))
        mutate(lambda x:x['conditions'].__setitem__(slice(None),[c for c in x['conditions'] if 'аннулирует' not in c]))
        mutate(lambda x:x.__setitem__('recorded_by','owner_authenticated'))
        mutate(lambda x:x.__setitem__('open_items',[]))


if __name__=='__main__':unittest.main(verbosity=2)
