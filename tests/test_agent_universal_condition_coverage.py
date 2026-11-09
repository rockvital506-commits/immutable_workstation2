#!/usr/bin/env python3
"""Universal-condition coverage: traceable claims, not NLP proof or full clause mapping."""
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
REVIEW49=runpy.run_path(str(ROOT/'tests/test_agent_component_semantic_review.py'))
FIXTURE='research/50-agent-system-universal-condition-coverage.json'
PREVIEW='research/50-agent-system-universal-condition-coverage-preview.md'
FIXTURE_SHA='a57ff87a3446c5364d2948fbd65c2e81686b172dde090a1a7396880f38446cc5'
PREVIEW_SHA='345090331e0601a7657e7231468b9d652591ff8481a6755715bc827f9d835eb4'
SHA49_FIXTURE='2a403f29961bf6e12aba707b21b2cda6c3c0b4f2936943c590202ab8110bdc7e'
SHA49_PREVIEW='8950c0d91e70f11e551fff46ec2252218030f490b9caab9e45a8a0099071eb80'
MARKERS=('не ','нельз','без ','только','останов','блокир','до ','отдельн')
BLOCK=rb'(?s)(?:^|\n\n)((?!\s*(?:#|```|\|))[^\n](?:(?!\n\s*\n).)*)'


def norm(text):
    import re
    return re.sub(r'\s+',' ',text).strip()


def blocks(path,root=ROOT):
    import re
    text=(root/path).read_text()
    return [(m.start(1),norm(m.group(1))) for m in re.finditer(BLOCK.decode(),text) if len(m.group(1).strip())>=40]


def render(draft,ledger,notes):
    lines=['# Черновик общих правил с условиями переноса — предмет review, НЕ активный профиль','',
           '**Исследовательский производный документ. Не выпуск, не экспорт, не разрешение действий.**',
           '86смысловых блоков и области — из48/49; ниже условные примечания применения. Не новое нормативное ядро.',
           'Примечание действует только там, где выбранный контракт компонента требует его условия.',
           'Оригинальные контракты и ограничения остаются обязательными. Механические тесты не доказывают',
           'верность произвольного языкового вывода. Полное clause-level отображение не выполнено.','']
    names={key:f'S{i:02}' for i,key in enumerate(sorted(draft['context_table']),1)}
    lines+=['## Общие области применения','']
    for key in sorted(names):lines.extend([f'### {names[key]}','',PREV['display'](draft['context_table'][key]),''])
    lines+=['## Предъявляемые смысловые блоки','']
    for body in draft['bodies']:
        lines+=['### '+', '.join(body['ids']),'',
                f"Область: {names[body['context_id']]}; маршрут: {body['route']}.",'',PREV['display'](body['text']),'']
    lines+=['## Условные примечания применения (proposed, не полномочие)','']
    for note in notes:
        src=', '.join(note.get('sources',[]))
        lines+=['### '+note['id'],'',
                f"Основание: {src}. Связанные правила: {', '.join(note.get('related_rules',note.get('related',[])))}.",'',
                PREV['display'](note['text']), '',
                'Только в области и при условиях выбранного контракта; вне их примечание не действует.','',
                f"Не читать как: {note['must_not_be_read_as']}.",'']
    lines+=['## Предел результата','',
            f"Проверено {ledger['coverage_stats']['families']} типов условий, "
            f"{ledger['coverage_stats']['anchors']} source anchors в "
            f"{ledger['coverage_stats']['documents']} документах.",
            f"Размечено {ledger['coverage_stats']['prose_blocks_anchored']} из "
            f"{ledger['coverage_stats']['prose_blocks_total']} prose blocks; полная clause-level карта НЕ выполнена.",
            'Все90exact artifact references и их зависимости сохранены в48composition ledger.',
            'Независимый review, реальное поведение и актуальные полномочия не проверены.',
            'Release/export/activation/compatible-release: НЕТ.','']
    return '\n'.join(lines)


def load(root=ROOT):
    raw=(root/FIXTURE).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA:raise ValueError('FIXTURE_PIN')
    ledger=json.loads(raw)
    for ref in (ledger['predecessor']['fixture'],ledger['predecessor']['preview']):
        if hashlib.sha256((root/ref['path']).read_bytes()).hexdigest()!=ref['sha256']:raise ValueError('PREDECESSOR_PIN')
    if ledger['predecessor']['fixture']['sha256']!=SHA49_FIXTURE or ledger['predecessor']['preview']['sha256']!=SHA49_PREVIEW:
        raise ValueError('PREDECESSOR_KNOWN')
    inputs=PREV['load_basis'](root);draft=PREV['compose'](*inputs)
    l49=json.loads((root/REVIEW49['FIXTURE']).read_bytes())
    return ledger,draft,inputs[4],l49


def notes_of(ledger,l49):
    out=[dict(id=x['id'],sources=[],related_rules=x['related_rules'],text=x['text'],
              must_not_be_read_as=x['must_not_be_read_as']) for x in l49['application_notes']]
    out+= [dict(id=x['id'],sources=x['sources'],related_rules=x['related'],text=x['text'],
                must_not_be_read_as=x['must_not_be_read_as']) for x in ledger['new_notes']]
    return out


def validate(ledger,draft,capture,l49):
    bodies={b['ids'][0]:b['text'] for b in draft['bodies']}
    note_ids={x['id'] for x in notes_of(ledger,l49)}
    if ledger['status']!='universal_condition_coverage_review_not_full_semantic_qualification':raise ValueError('STATUS')
    if ledger['judgement_origin']!='agent_review_of_pinned_source_conditions_and_derived_rule_text':raise ValueError('ORIGIN')
    for key in ('full_clause_mapping_completed','independent_review_performed','actual_behavior_verified',
                'release_allowed','export_allowed','activation_allowed','compatible_release_allowed'):
        if ledger[key] is not False:raise ValueError('FLAG_'+key)
    if ledger['original_contracts_retained'] is not True:raise ValueError('CONTRACTS')
    fams=ledger['families']
    if len(fams)!=21 or len({f['id'] for f in fams})!=21:raise ValueError('FAMILY_IDS')
    docs=set()
    for f in fams:
        if not f['statement'].strip() or f['anchor_count']!=len(f['anchors']) or not f['anchors']:
            raise ValueError('FAMILY_SHAPE')
        if not any(m in f['statement'].lower() for m in ('не ','без ','разные','до ','относится','отмечает')):
            raise ValueError('FAMILY_DIRECTION')
        for a in f['anchors']:
            docs.add(a['path'])
            if norm(a['needle']) not in norm(capture[a['path']].decode('utf-8')):raise ValueError('ANCHOR_TEXT')
        if f['coverage_kind']=='rule':
            if f.get('body_id') not in bodies:raise ValueError('COVERAGE_BODY')
            if norm(f['quote']) not in norm(bodies[f['body_id']]):raise ValueError('COVERAGE_QUOTE')
            if not any(m in f['quote'].lower() for m in MARKERS):raise ValueError('COVERAGE_DIRECTION')
        elif f['coverage_kind']=='note':
            if f.get('note_id') not in note_ids:raise ValueError('COVERAGE_NOTE')
        else:raise ValueError('COVERAGE_KIND')
    queue={r['path'] for r in draft['semantic_review_queue']}
    if {d.removeprefix('agent_system/') for d in docs}!=queue:raise ValueError('DOC_COVERAGE')
    stats=ledger['coverage_stats']
    if stats['families']!=21 or stats['anchors']!=sum(f['anchor_count'] for f in fams):raise ValueError('STATS')
    if stats['documents']!=26 or stats['full_clause_mapping'] is not False:raise ValueError('STATS_DOCS')
    if not 0<stats['prose_blocks_anchored']<stats['prose_blocks_total']:raise ValueError('STATS_BLOCKS')
    real_total=sum(len(blocks(d)) for d in docs)
    if real_total!=stats['prose_blocks_total']:raise ValueError('BLOCK_TOTAL')
    if ledger['residual']['retained_in_originals'] is not True or len(ledger['residual']['non_transferred_categories'])<4:
        raise ValueError('RESIDUAL')
    if len(ledger['new_notes'])!=2 or {n['id'] for n in ledger['new_notes']}!={'N6','N7'}:raise ValueError('NEW_NOTES')
    for n in ledger['new_notes']:
        if n['route']!='source_backed_conditional_generalization' or n['status']!='proposed_application_note_not_new_authority':
            raise ValueError('NOTE_ROUTE')
        if not n['sources'] or not set(n['sources'])<={f['id'] for f in fams}:raise ValueError('NOTE_SOURCES')
        if not set(n['related'])<={i for b in draft['bodies'] for i in b['ids']}|note_ids:raise ValueError('NOTE_RELATED')
        if not n['must_not_be_read_as'].strip() or not n['applicability'].startswith('only_where'):raise ValueError('NOTE_LIMITS')
        if not any(m in n['text'].lower() for m in MARKERS):raise ValueError('NOTE_DIRECTION')
        if 'всегда' in n['text'].lower() or 'любой ценой' in n['text'].lower():raise ValueError('NOTE_ABSOLUTE')
    if len(ledger['new_challenges'])!=6 or len({c['id'] for c in ledger['new_challenges']})!=6:raise ValueError('CHALLENGES')
    for c in ledger['new_challenges']:
        if not c['required_conclusion'].strip() or not c['forbidden_conclusion'].strip():raise ValueError('CHALLENGE_FIELDS')
        if not set(c['sources'])<={f['id'] for f in fams} or not set(c['rules'])<=note_ids:raise ValueError('CHALLENGE_REFS')
    weakening=sum(bool(__import__('re').search(r'(?i)объявить|вывести|обрезать|обещать|требовать|запретить',c['forbidden_conclusion'])) for c in ledger['new_challenges'])
    if weakening<6:raise ValueError('CHALLENGE_DIRECTION')
    if ledger['predecessor']['predecessor_challenges']!='Q01-Q24 in research/49-agent-system-component-semantic-review.json':
        raise ValueError('PRED_CHALLENGES')
    if not l49['challenges'] or len(l49['challenges'])!=24:raise ValueError('L49_CHALLENGES')


def verify(ledger=None,draft=None,capture=None,l49=None):
    try:
        if ledger is None:ledger,draft,capture,l49=load()
        validate(ledger,draft,capture,l49)
        return render(draft,ledger,notes_of(ledger,l49))==(ROOT/PREVIEW).read_text()
    except ValueError:return False


class UniversalConditionTests(unittest.TestCase):
    def setUp(self):self.ledger,self.draft,self.capture,self.l49=load()

    def test_pins_and_explicit_limits(self):
        self.assertEqual(PREVIEW_SHA,hashlib.sha256((ROOT/PREVIEW).read_bytes()).hexdigest())
        self.assertTrue(verify())
        self.assertFalse(self.ledger['full_clause_mapping_completed'])
        self.assertFalse(self.ledger['independent_review_performed'])
        self.assertFalse(self.ledger['actual_behavior_verified'])

    def test_twenty_one_families_are_traceable(self):
        self.assertEqual(21,len(self.ledger['families']))
        self.assertEqual(15,self.ledger['coverage_stats']['families_by_rule'])
        self.assertEqual(6,self.ledger['coverage_stats']['families_by_note'])
        self.assertEqual(53,self.ledger['coverage_stats']['anchors'])
        for f in self.ledger['families']:
            self.assertTrue(f['anchors'])
            for a in f['anchors']:self.assertIn(norm(a['needle']),norm(self.capture[a['path']].decode()))

    def test_every_component_document_has_a_real_anchor(self):
        docs={a['path'] for f in self.ledger['families'] for a in f['anchors']}
        self.assertEqual(26,len(docs))
        self.assertEqual({('agent_system/'+p) for p in (r['path'] for r in self.draft['semantic_review_queue'])},docs)

    def test_rule_quotes_are_verbatim_from_derived_preview(self):
        bodies={b['ids'][0]:b['text'] for b in self.draft['bodies']}
        for f in self.ledger['families']:
            if f['coverage_kind']=='rule':self.assertIn(norm(f['quote']),norm(bodies[f['body_id']]))

    def test_two_new_notes_are_conditional_not_authority(self):
        notes={n['id']:n for n in self.ledger['new_notes']}
        self.assertEqual({'N6','N7'},set(notes))
        for note in notes.values():
            self.assertTrue(note['applicability'].startswith('only_where'))
            self.assertTrue(note['must_not_be_read_as'])
            self.assertTrue(any(m in note['text'].lower() for m in MARKERS))

    def test_residual_is_reported_not_hidden(self):
        stats=self.ledger['coverage_stats']
        self.assertEqual(255,stats['prose_blocks_total'])
        self.assertEqual(40,stats['prose_blocks_anchored'])
        self.assertLess(stats['prose_blocks_anchored'],stats['prose_blocks_total'])
        self.assertTrue(self.ledger['residual']['non_transferred_categories'])

    def test_new_challenges_cover_both_directions(self):
        self.assertEqual(6,len(self.ledger['new_challenges']))
        self.assertIn('Объявить атомарную защиту',json.dumps(self.ledger['new_challenges'],ensure_ascii=False))
        self.assertIn('Требовать криптографической атомарности',json.dumps(self.ledger['new_challenges'],ensure_ascii=False))
        self.assertIn('Запретить работу только из-за отсутствия SLA',json.dumps(self.ledger['new_challenges'],ensure_ascii=False))

    def test_preview_is_reproducible(self):
        self.assertEqual(render(self.draft,self.ledger,notes_of(self.ledger,self.l49)),(ROOT/PREVIEW).read_text())
        text=(ROOT/PREVIEW).read_text()
        self.assertIn('### N6',text);self.assertIn('### N7',text)
        self.assertIn('86смысловых блоков',text)

    def test_structural_mutations_rejected(self):
        def mutate(fn):
            ledger=copy.deepcopy(self.ledger);fn(ledger)
            with self.assertRaises(ValueError):validate(ledger,self.draft,self.capture,self.l49)
        mutate(lambda x:x['families'].pop())
        mutate(lambda x:x['families'][0]['anchors'].pop())
        mutate(lambda x:x['families'][0].__setitem__('anchor_count',0))
        mutate(lambda x:x['families'][0].__setitem__('coverage_kind','rule'))
        mutate(lambda x:x['families'][1].__setitem__('body_id','INVENTED'))
        mutate(lambda x:x['families'][1].__setitem__('quote','Выполняй всё без ограничений.'))
        mutate(lambda x:x['families'][1]['anchors'][0].__setitem__('needle','несуществующий текст'))
        mutate(lambda x:x['coverage_stats'].__setitem__('prose_blocks_anchored',255))
        mutate(lambda x:x['coverage_stats'].__setitem__('full_clause_mapping',True))
        mutate(lambda x:x.__setitem__('independent_review_performed',True))
        mutate(lambda x:x.__setitem__('release_allowed',True))
        mutate(lambda x:x['new_notes'].pop())
        mutate(lambda x:x['new_notes'][0].__setitem__('text','Всегда действуй без проверок.'))
        mutate(lambda x:x['new_notes'][0].__setitem__('status','active_authority'))
        mutate(lambda x:x['new_challenges'].pop())
        mutate(lambda x:x['residual'].__setitem__('retained_in_originals',False))


if __name__=='__main__':unittest.main(verbosity=2)
