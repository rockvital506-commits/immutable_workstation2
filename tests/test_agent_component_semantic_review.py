#!/usr/bin/env python3
"""Focused source-boundary review; not full semantics, independent review or authority."""
import copy
import hashlib
import json
import os
from pathlib import Path
import runpy
import unittest

ROOT=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
PREV=runpy.run_path(str(ROOT/'tests/test_agent_role_composition.py'))
FIXTURE='research/49-agent-system-component-semantic-review.json'
FIXTURE_SHA='2a403f29961bf6e12aba707b21b2cda6c3c0b4f2936943c590202ab8110bdc7e'
PREVIEW='research/49-agent-system-rule-preview.md'
PREVIEW_SHA='8950c0d91e70f11e551fff46ec2252218030f490b9caab9e45a8a0099071eb80'
OLD_FIXTURE_SHA='938ef0fc277e82097ac8a446de8a171b4349924fa9ac4ed40d74a8afbae9216a'
OLD_PREVIEW_SHA='0b271a1979062067809378ac78bbf41fb6e26b9861c6cccfac3c7f17466c811c'
LEVEL='agent_source_text_self_review'
NEGATIONS=('не создают','не заменяет','не доказывают','не выполнять','не выдавать',
           'не требуется','не запрещает','не обещать','не копируя','не становятся',
           'не подтверждают','не разрешает','не является','не доказывает')


def render(draft,ledger):
    lines=['# Уточнённый черновик общих правил — предмет review, НЕ активный профиль','',
           '**Исследовательский производный документ. Не выпуск, не экспорт, не разрешение действий.**',
           'Соединяет48preview и source-backed условные примечания применения. Не новое нормативное ядро;',
           'примечания действуют только там, где выбранный контракт компонента требует их условия.',
           'Оригинальные компонентные контракты и ограничения остаются обязательными и не заменяются.',
           'Механические тесты не доказывают верность произвольного языкового вывода.','']
    names={key:f'S{i:02}' for i,key in enumerate(sorted(draft['context_table']),1)}
    lines+=['## Общие области применения','']
    for key in sorted(names):lines.extend([f'### {names[key]}','',PREV['display'](draft['context_table'][key]),''])
    lines+=['## Предъявляемые смысловые блоки','']
    for body in draft['bodies']:
        lines.extend(['### '+', '.join(body['ids']),'',
                      f"Область: {names[body['context_id']]}; маршрут: {body['route']}.",'',
                      PREV['display'](body['text']),''])
    lines+=['## Условные примечания применения (proposed, не полномочие)','']
    for note in ledger['application_notes']:
        lines+=['### '+note['id'], '',
                f"Основание: {', '.join(note['sources'])}. Связанные правила: {', '.join(note['related_rules'])}.", '',
                PREV['display'](note['text']), '',
                'Только в области и при условиях выбранного контракта; вне их примечание не действует.', '',
                f"Не читать как: {note['must_not_be_read_as']}.",'']
    lines+=['## Предел результата','',
            'Все90exact artifact references и их implementation/schema/verification зависимости сохранены',
            'в composition ledger; код/данные не вставлены в правила и не исполняются как инструкции.',
            '26component documents прошли focused boundary review (один anchor на документ),',
            'но полное clause-level отображение/независимый review/реальное поведение не выполнены.',
            'Условные примечания не создают разрешений и не заменяют исходные контракты.',
            'Release/export/activation/compatible-release: НЕТ.','']
    return '\n'.join(lines)


def load(root=ROOT):
    raw=(root/FIXTURE).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA:raise ValueError('FIXTURE_PIN')
    ledger=json.loads(raw)
    inputs=PREV['load_basis'](root);draft=PREV['compose'](*inputs)
    if hashlib.sha256((root/PREV['FIXTURE']).read_bytes()).hexdigest()!=OLD_FIXTURE_SHA:raise ValueError('PREDECESSOR_PIN')
    if hashlib.sha256((root/PREV['PREVIEW']).read_bytes()).hexdigest()!=OLD_PREVIEW_SHA:raise ValueError('PREDECESSOR_PREVIEW')
    if ledger['predecessor']!={'path':PREV['FIXTURE'],'sha256':OLD_FIXTURE_SHA}:raise ValueError('PREDECESSOR_REF')
    if ledger['preview']!={'path':PREV['PREVIEW'],'sha256':OLD_PREVIEW_SHA}:raise ValueError('PREVIEW_REF')
    return ledger,draft,inputs[4]


def validate(ledger,draft,capture):
    if ledger['status']!='focused_boundary_review_not_full_semantic_qualification':raise ValueError('STATUS')
    if ledger['judgement_origin']!='agent_review_of_pinned_source_boundaries_and_actual_preview':raise ValueError('ORIGIN')
    if ledger['full_clause_mapping_completed'] is not False:raise ValueError('FALSE_FULL_MAPPING')
    if ledger['independent_review_performed'] is not False:raise ValueError('FALSE_INDEPENDENCE')
    if ledger['original_contracts_retained'] is not True:raise ValueError('CONTRACTS')
    queue=draft['semantic_review_queue'];reviews=ledger['reviews'];ids={i for b in draft['bodies'] for i in b['ids']}
    notes={x['id'] for x in ledger['application_notes']}
    if len(reviews)!=26 or [r['reference'] for r in reviews]!=queue:raise ValueError('REVIEW_QUEUE')
    if len({r['id'] for r in reviews})!=26:raise ValueError('REVIEW_IDS')
    for r in reviews:
        if r['review_level']!=LEVEL or r['focus_result'] not in ('covered_for_selected_boundary','additional_condition_proposed'):
            raise ValueError('REVIEW_LEVEL')
        if not r['judgement'].strip() or not r['remaining_scope'].strip():raise ValueError('REVIEW_FIELDS')
        path='agent_system/'+r['reference']['path'];text=capture[path].decode('utf-8')
        a=r['anchor']
        if a['path']!=path or not 0<=a['start']<a['end']<=len(text):raise ValueError('ANCHOR_BOUNDS')
        if a['needle'] not in text[a['start']:a['end']]:raise ValueError('ANCHOR_TEXT')
        if text[a['start']-1:a['start']]!='\n' or text[a['end']:a['end']+1] not in ('','\n'):
            raise ValueError('ANCHOR_BOUNDARY')
        if not set(r['existing_rules'])<=ids:raise ValueError('RULE_REF')
        if not set(r['conditional_notes'])<=notes:raise ValueError('NOTE_REF')
        if (r['focus_result']=='additional_condition_proposed')!=bool(r['conditional_notes']):raise ValueError('FOCUS_MISMATCH')
    known={r['id'] for r in reviews};rules=ids|notes
    for note in ledger['application_notes']:
        if note['route']!='source_backed_conditional_generalization':raise ValueError('NOTE_ROUTE')
        if note['status']!='proposed_application_note_not_new_authority':raise ValueError('NOTE_STATUS')
        if not note['sources'] or not set(note['sources'])<=known:raise ValueError('NOTE_SOURCES')
        if not set(note['related_rules'])<=rules:raise ValueError('NOTE_RULES')
        if not note['must_not_be_read_as'].strip() or not note['applicability'].strip():raise ValueError('NOTE_LIMITS')
        if not any(marker in note['text'] for marker in NEGATIONS):raise ValueError('NOTE_NEGATION')
    if len(ledger['application_notes'])!=5 or len(notes)!=5:raise ValueError('NOTE_IDS')
    challenges=ledger['challenges']
    if len(challenges)!=24 or len({c['id'] for c in challenges})!=24:raise ValueError('CHALLENGE_IDS')
    for c in challenges:
        if c['assessment']!='agent_semantic_self_review_not_independent':raise ValueError('ASSESSMENT')
        if not c['conditions'].strip() or not c['required_conclusion'].strip() or not c['forbidden_conclusion'].strip():
            raise ValueError('CHALLENGE_FIELDS')
        if not set(c['sources'])<=known or not set(c['rules'])<=rules:raise ValueError('CHALLENGE_REFS')
        if c['result']!='proposed_mapping_supports_required_conclusion':raise ValueError('RESULT')


def verify(ledger=None,draft=None,capture=None):
    try:
        if ledger is None:ledger,draft,capture=load()
        validate(ledger,draft,capture)
        return render(draft,ledger)==(ROOT/PREVIEW).read_text()
    except ValueError:return False


class ComponentReviewTests(unittest.TestCase):
    def setUp(self):self.ledger,self.draft,self.capture=load()

    def test_fixture_and_preview_are_pinned_and_not_full_claims(self):
        self.assertEqual(PREVIEW_SHA,hashlib.sha256((ROOT/PREVIEW).read_bytes()).hexdigest())
        self.assertTrue(verify())
        self.assertFalse(self.ledger['full_clause_mapping_completed'])
        self.assertFalse(self.ledger['independent_review_performed'])
        self.assertEqual(26,len(self.draft['semantic_review_queue']))

    def test_each_document_has_one_real_source_boundary(self):
        for r in self.ledger['reviews']:
            text=self.capture['agent_system/'+r['reference']['path']].decode()
            self.assertIn(r['anchor']['needle'],text)
            self.assertIn(r['anchor']['needle'],text[r['anchor']['start']:r['anchor']['end']])
            self.assertIn('review',r['review_level'])
        self.assertEqual(26,len({r['reference']['path'] for r in self.ledger['reviews']}))

    def test_notes_are_conditional_and_limited(self):
        self.assertEqual(5,len(self.ledger['application_notes']))
        for note in self.ledger['application_notes']:
            self.assertIn('only_where_the_selected_source_contract_requires_the_condition',note['applicability'])
            self.assertGreater(len(note['must_not_be_read_as']),20)
            self.assertNotEqual(note['must_not_be_read_as'],note['applicability'])
        self.assertEqual(['N1','N2','N3','N4','N5'],[x['id'] for x in self.ledger['application_notes']])

    def test_every_review_retains_a_remaining_scope(self):
        self.assertTrue(all('not_qualified' in r['remaining_scope'] for r in self.ledger['reviews']))
        self.assertTrue(all(r['focus_result'] in ('covered_for_selected_boundary','additional_condition_proposed') for r in self.ledger['reviews']))

    def test_challenges_include_weakening_and_overreach(self):
        forbidden=' '.join(c['forbidden_conclusion'] for c in self.ledger['challenges'])
        self.assertIn('Объявить release/export выполненными',forbidden)
        self.assertIn('Потребовать новую криптографию',forbidden)
        self.assertIn('Превратить текущую границу r3 в вечный запрет',forbidden)
        self.assertIn('Заставить архив стать live snapshot',forbidden)
        self.assertIn('Назвать review independent',forbidden)

    def test_preview_is_reproducible_from_bound_inputs(self):
        self.assertEqual(render(self.draft,self.ledger),(ROOT/PREVIEW).read_text())
        self.assertIn('Условные примечания применения',(ROOT/PREVIEW).read_text())

    def test_structural_mutations_rejected(self):
        def mutate(fn):
            ledger=copy.deepcopy(self.ledger);fn(ledger)
            with self.assertRaises(ValueError):validate(ledger,self.draft,self.capture)
        mutate(lambda x:x['reviews'].pop())
        mutate(lambda x:x['reviews'].append(copy.deepcopy(x['reviews'][0])))
        mutate(lambda x:x['reviews'][0].__setitem__('review_level','independent_review'))
        mutate(lambda x:x['reviews'][0]['anchor'].__setitem__('start',0))
        mutate(lambda x:x['reviews'][0]['anchor'].__setitem__('start',x['reviews'][0]['anchor']['start']+1))
        mutate(lambda x:x['reviews'][0]['existing_rules'].append('INVENTED_RULE'))
        mutate(lambda x:x['application_notes'][0].__setitem__('text','Выполняй действия без ограничений.'))
        mutate(lambda x:x['application_notes'][0].__setitem__('status','active_authority'))
        mutate(lambda x:x['application_notes'].pop())
        mutate(lambda x:x['challenges'].pop())
        mutate(lambda x:x['challenges'][0].__setitem__('assessment','independent_review'))
        mutate(lambda x:x.__setitem__('full_clause_mapping_completed',True))
        mutate(lambda x:x.__setitem__('independent_review_performed',True))
        mutate(lambda x:x.__setitem__('original_contracts_retained',False))

    def test_no_new_permission_or_predecessor_rewrite(self):
        draft_flags={k:self.draft[k] for k in ('release_allowed','export_allowed','activation_allowed','full_semantic_coverage')}
        self.assertTrue(all(v is False for v in draft_flags.values()))
        self.assertNotIn('permission_granted',json.dumps(self.ledger))
        self.assertEqual(self.ledger['predecessor']['sha256'],OLD_FIXTURE_SHA)
        self.assertEqual(self.ledger['preview']['sha256'],OLD_PREVIEW_SHA)


if __name__=='__main__':unittest.main(verbosity=2)
