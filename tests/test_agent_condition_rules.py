#!/usr/bin/env python3
"""Consolidated derived rule set: reviewable text, not a normative revision."""
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
FIXTURE='research/53-agent-system-condition-rules.json'
DOC='research/53-agent-system-condition-rules.md'
FIXTURE_SHA='bc5dc93e58fdc9df7e49e24e870e7e8b00193f19fc2d057a54593ad6961f2c29'
DOC_SHA='ede459ee165575948d1710591ac8422d78570ac9f4f9b9f2eae34109f5bf15bb'
SHA52='38c1e11d0c39aa64ac4765fd1e2ce25744cc686f49d496908a7e9f490a989360'
SHA50='a57ff87a3446c5364d2948fbd65c2e81686b172dde090a1a7396880f38446cc5'


def norm(t):
    return re.sub(r'\s+',' ',t).strip()


def strip_verb(t):
    for p in ('требовать ','запрещать '):
        if t.startswith(p):return t[len(p):]
    return t


def render(ledger,bodies,note_text):
    lines=['# Общие правила работы агента — кандидат на review, НЕ активный профиль','',
     '**Производный документ.** Собран из23типов условий, проверенных в52. Не нормативная',
     'ревизия, не выпуск, не разрешение. Действует только вместе со своими основаниями.','',
     'Каждый пункт: что утверждение позволяет, что запрещено выводить и что оно не вправе',
     'требовать. Пределы взяты не из моего удобства, а из коридора, проверенного на398парах.','']
    for fr in ledger['frame']:
        body='\n'.join(l for l in fr['text'].splitlines() if not l.startswith('#'))
        lines+=['## '+fr['title'],'',PREV['display'](body),'']
    lines+=['## Правила','']
    for r in ledger['rules']:
        ev=r['evidence']
        src=f"правило `{ev['body_id']}`" if ev['kind']=='rule' else f"условное примечание `{ev['note_id']}`"
        lines+=['### '+r['id'],'',
          r['statement'],'',
          f"- **Можно утверждать:** {r['permits']}.",
          f"- **Запрещено выводить:** {r['forbids_overreach']}.",
          f"- **Запрещено требовать:** {strip_verb(r['forbids_overstrengthening'])}.",
          f"- **Основание:** {src}; действует только в области этого основания.",""]
    lines+=['## Чего этот текст не устанавливает','',
     '- Не подтверждает поведение агента, готовность системы, совместимость среды.',
     '- Не заменяет исходные контракты компонентов и их зависимости.',
     '- Не даёт разрешений: выпуск, экспорт, активация остаются отдельными решениями.',
     '- Не отменяет открытые пункты R4/R6/G05/G07 и не закрывает пробелы состава.','',
     '## Что требуется от review','']
    for x in ledger['review_requirements']:lines.append('- '+x[0].upper()+x[1:]+'.')
    lines+=['','Отклонение с причиной — законный результат review; молчание согласием не считается.','']
    # note_text kept in the signature so the text cannot be produced without the cited notes
    assert all(x['evidence']['note_id'] in note_text for x in ledger['rules'] if x['evidence']['kind']=='conditional_note')
    return '\n'.join(lines)


def load():
    raw=(ROOT/FIXTURE).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA:raise ValueError('FIXTURE_PIN')
    ledger=json.loads(raw)
    for ref in ledger['predecessor'].values():
        if hashlib.sha256((ROOT/ref['path']).read_bytes()).hexdigest()!=ref['sha256']:raise ValueError('PREDECESSOR_PIN')
    if ledger['predecessor']['loss_check']['sha256']!=SHA52 or ledger['predecessor']['coverage']['sha256']!=SHA50:
        raise ValueError('PREDECESSOR_KNOWN')
    inputs=PREV['load_basis'](ROOT);draft=PREV['compose'](*inputs)
    bodies={b['ids'][0]:b['text'] for b in draft['bodies']}
    l49=json.loads((ROOT/'research/49-agent-system-component-semantic-review.json').read_bytes())
    l50=json.loads((ROOT/'research/50-agent-system-universal-condition-coverage.json').read_bytes())
    notes={x['id']:x['text'] for x in l49['application_notes']}
    notes.update({x['id']:x['text'] for x in l50['new_notes']})
    return ledger,bodies,notes


def validate(ledger,bodies,notes):
    if ledger['status']!='derived_rule_set_candidate_for_owner_review_not_normative_revision':raise ValueError('STATUS')
    rules=ledger['rules']
    if len(rules)!=23 or len({r['id'] for r in rules})!=23:raise ValueError('RULE_IDS')
    allowed={f'F{i:02}' for i in range(1,24)}
    if {r['id'] for r in rules}!=allowed:raise ValueError('RULE_SET')
    for r in rules:
        for key in ('statement','permits','forbids_overreach','forbids_overstrengthening'):
            if not r[key].strip():raise ValueError('RULE_FIELD')
        if len({r['permits'],r['forbids_overreach'],r['forbids_overstrengthening']})!=3:raise ValueError('RULE_DISTINCT')
        ev=r['evidence']
        if ev['kind']=='rule':
            if ev['body_id'] not in bodies:raise ValueError('EVIDENCE_BODY')
            if norm(ev['quote']) not in norm(bodies[ev['body_id']]):raise ValueError('EVIDENCE_QUOTE')
        elif ev['kind']=='conditional_note':
            if ev['note_id'] not in notes:raise ValueError('EVIDENCE_NOTE')
        else:raise ValueError('EVIDENCE_KIND')
        if not r['applies_when'].startswith('only_inside'):raise ValueError('SCOPE')
    if len(ledger['frame'])!=4:raise ValueError('FRAME')
    for fr in ledger['frame']:
        if fr['body_id'] not in bodies:raise ValueError('FRAME_BODY')
        if norm(fr['text'])!=norm(bodies[fr['body_id']]):raise ValueError('FRAME_TEXT')
    acc=ledger['acceptance']
    if acc['grants']!=[]:raise ValueError('NO_GRANTS')
    for g in ('release','export','activation','compatible release','new environment','change of normative registry'):
        if g not in acc['explicitly_not_granted']:raise ValueError('GATE_'+g)
    lim=ledger['limits']
    if lim['normative_status']!='not_a_registered_revision':raise ValueError('NORMATIVE')
    for key in ('independent_review_performed','actual_behavior_verified','full_semantic_equivalence'):
        if lim[key] is not False:raise ValueError('FALSE_CLAIM_'+key)
    if len(ledger['review_requirements'])<4:raise ValueError('REVIEW_REQ')


def verify():
    try:
        ledger,bodies,notes=load();validate(ledger,bodies,notes)
        return render(ledger,bodies,notes)==(ROOT/DOC).read_text()
    except ValueError:return False


class ConditionRulesTests(unittest.TestCase):
    def setUp(self):self.ledger,self.bodies,self.notes=load()

    def test_pins_and_reproducible_text(self):
        self.assertEqual(DOC_SHA,hashlib.sha256((ROOT/DOC).read_bytes()).hexdigest())
        self.assertTrue(verify())
        self.assertEqual(render(self.ledger,self.bodies,self.notes),(ROOT/DOC).read_text())

    def test_every_rule_cites_verbatim_evidence(self):
        for r in self.ledger['rules']:
            ev=r['evidence']
            if ev['kind']=='rule':self.assertIn(norm(ev['quote']),norm(self.bodies[ev['body_id']]))
            else:self.assertIn(ev['note_id'],self.notes)
        self.assertEqual(23,len(self.ledger['rules']))

    def test_rules_state_both_limits(self):
        for r in self.ledger['rules']:
            self.assertTrue(r['permits'])
            self.assertTrue(r['forbids_overreach'])
            self.assertTrue(r['forbids_overstrengthening'])
        text=(ROOT/DOC).read_text()
        self.assertEqual(23,text.count('**Запрещено выводить:**'))
        self.assertEqual(23,text.count('**Запрещено требовать:**'))

    def test_document_declares_what_it_does_not_establish(self):
        text=(ROOT/DOC).read_text()
        self.assertIn('Не подтверждает поведение агента',text)
        self.assertIn('Не даёт разрешений',text)
        self.assertIn('НЕ активный профиль',text)
        self.assertIn('молчание согласием не считается',text)

    def test_no_grant_or_normative_status(self):
        self.assertEqual([],self.ledger['acceptance']['grants'])
        self.assertEqual('not_a_registered_revision',self.ledger['limits']['normative_status'])
        self.assertFalse(self.ledger['limits']['independent_review_performed'])
        self.assertFalse(self.ledger['limits']['actual_behavior_verified'])

    def test_frame_sections_are_verbatim_core_text(self):
        self.assertEqual(['C-purpose','C-application','C-check','C-uncertainty'],[f['body_id'] for f in self.ledger['frame']])
        for fr in self.ledger['frame']:self.assertEqual(norm(fr['text']),norm(self.bodies[fr['body_id']]))

    def test_mutations_rejected(self):
        def mutate(fn):
            ledger=copy.deepcopy(self.ledger);fn(ledger)
            with self.assertRaises(ValueError):validate(ledger,self.bodies,self.notes)
        mutate(lambda x:x['rules'].pop())
        mutate(lambda x:x['rules'].append(copy.deepcopy(x['rules'][0])))
        mutate(lambda x:x['rules'][0].__setitem__('statement',''))
        mutate(lambda x:x['rules'][0].__setitem__('permits',x['rules'][0]['forbids_overreach']))
        mutate(lambda x:next(r for r in x['rules'] if r['evidence']['kind']=='rule')['evidence'].__setitem__('quote','Всегда действуй без ограничений.'))
        mutate(lambda x:next(r for r in x['rules'] if r['evidence']['kind']=='rule')['evidence'].__setitem__('body_id','INVENTED'))
        mutate(lambda x:next(r for r in x['rules'] if r['evidence']['kind']=='conditional_note')['evidence'].__setitem__('note_id','N99'))
        mutate(lambda x:x['rules'][0].__setitem__('applies_when','everywhere'))
        mutate(lambda x:x['frame'][0].__setitem__('text','Что угодно.'))
        mutate(lambda x:x['frame'].pop())
        mutate(lambda x:x['acceptance'].__setitem__('grants',['release']))
        mutate(lambda x:x['acceptance'].__setitem__('explicitly_not_granted',['release']))
        mutate(lambda x:x['limits'].__setitem__('normative_status','registered'))
        mutate(lambda x:x['limits'].__setitem__('independent_review_performed',True))
        mutate(lambda x:x['review_requirements'].__setitem__(slice(None),[]))


if __name__=='__main__':unittest.main(verbosity=2)
