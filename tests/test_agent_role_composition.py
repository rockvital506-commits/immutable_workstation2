#!/usr/bin/env python3
"""Role-aware research composition, never permission or general NLP equivalence."""
import copy
import hashlib
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
PREV=runpy.run_path(str(ROOT/'tests/test_agent_mixed_governance.py'))
FIXTURE='research/48-agent-system-role-aware-composition.json'
FIXTURE_SHA='938ef0fc277e82097ac8a446de8a171b4349924fa9ac4ed40d74a8afbae9216a'
PREVIEW='research/48-agent-system-rule-preview.md'
canonical=PREV['canonical'];extract=PREV['extract']


def read_pin(root,ref):
    raw=(root/ref['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ref['sha256'] or len(raw)!=ref['size_bytes']:
        raise ValueError('REFERENCE_PIN')
    return raw


def capture_inventory(root,ledger,previous_capture):
    # Trusted local laboratory root; not hostile-tree acquisition or atomic snapshot.
    directory=root/'agent_system/catalog/approvals'
    expected={Path(r['path']).name for r in ledger['known_decisions']}
    if set(os.listdir(directory))!=expected:raise ValueError('LEDGER_INVENTORY')
    capture={}
    for row in ledger['roles']:
        ref={**row['reference'],'path':'agent_system/'+row['reference']['path']}
        raw=(previous_capture[ref['path']].encode('utf-8') if ref['path'] in previous_capture
             else read_pin(root,ref))
        if hashlib.sha256(raw).hexdigest()!=ref['sha256'] or len(raw)!=ref['size_bytes']:
            raise ValueError('REFERENCE_PIN')
        capture[ref['path']]=raw
    for ref in ledger['known_decisions']:read_pin(root,ref)
    if set(os.listdir(directory))!=expected:raise ValueError('LEDGER_INVENTORY')
    return capture


def load_basis(root=ROOT):
    raw=(root/FIXTURE).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA:raise ValueError('FIXTURE_PIN')
    ledger=json.loads(raw)
    for ref in ledger['predecessors']:read_pin(root,ref)
    old,basis,previous_capture=PREV['load_basis'](root)
    registry=json.loads(read_pin(root,ledger['registry']))
    table={(e['entity_id'],r['revision']):r for e in registry['entities'] for r in e['revisions']}
    expected={a['path']:a for n in basis['declared_closure']
              for a in table[n['entity_id'],n['revision']]['artifacts']}
    if len(ledger['roles'])!=len(expected) or {r['reference']['path']:r['reference'] for r in ledger['roles']}!=expected:
        raise ValueError('COMPOSITION_MEMBERSHIP')
    capture=capture_inventory(root,ledger,previous_capture)
    core=capture[ledger['core_source']['path']]
    if hashlib.sha256(core).hexdigest()!=ledger['core_source']['sha256'] or len(core)!=ledger['core_source']['size_bytes']:
        raise ValueError('CORE_PIN')
    paths=json.loads(read_pin(root,ledger['predecessors'][1]))
    external=next(u for u in PREV['assemble'](old,basis,previous_capture)['unresolved_external'] if u['id']=='D04')
    source=ledger['path_group']['source']
    if external['origins']!=[source] or extract(previous_capture,source)!=paths['source']['quote']:
        raise ValueError('D04_SOURCE')
    if ledger['path_group']['source_sha256']!=paths['source']['sha256']:
        raise ValueError('D04_PIN')
    if ledger['path_group']['unit_ids']!=[u['id'] for u in paths['units']]:raise ValueError('D04_UNITS')
    # Every byte read is referenced data. No inventory Python/schema/prompt is executed.
    return ledger,old,basis,previous_capture,capture,paths


def compose(ledger,old,basis,previous_capture,capture,paths):
    previous=PREV['assemble'](old,basis,previous_capture)
    draft=copy.deepcopy(previous)
    draft['status']='role_aware_research_candidate_not_exportable'
    draft['unresolved_external']=[]
    draft.pop('unselected_artifact_gaps')
    for unit in paths['units']:
        source=paths['source'];start=source['start_offset']+unit['start'];end=source['start_offset']+unit['end']
        origin=dict(path=source['path'],start=start,end=end)
        observed=capture[origin['path']].decode('utf-8')[start:end]
        if unit['route']=='preserve' and observed!=unit['output']:raise ValueError('D04_PRESERVE')
        context_id=hashlib.sha256(unit['scope'].encode()).hexdigest()
        draft['context_table'][context_id]=unit['scope']
        draft['bodies'].append(dict(ids=['D04/'+unit['id']],text=observed if unit['route']=='preserve' else unit['output'],
                                    context_id=context_id,origins=[origin],route=unit['route']))
    text_capture={p:data.decode('utf-8') for p,data in capture.items() if p.endswith('.md')}
    scope=extract(text_capture,ledger['core_scope']);context_id=hashlib.sha256(scope.encode()).hexdigest()
    draft['context_table'][context_id]=scope
    for unit in ledger['core_units']:
        draft['bodies'].append(dict(ids=[unit['id']],text=extract(text_capture,unit['source']),context_id=context_id,
                                   origins=[unit['source']],route='preserve'))
    draft['meaning_links']=[dict(id='D04/'+u['id'],linked=['D04/'+x for x in u['linked_units']]) for u in paths['units']]
    draft['role_inventory']=ledger['roles']
    draft['known_decision_refs']=ledger['known_decisions']
    draft['semantic_review_queue']=[r['reference'] for r in ledger['roles'] if r['rule_view']=='semantic_review_required']
    draft['role_inventory_complete']=True
    draft['inventory_consistency']='observed_fixed_pins_not_atomic_or_globally_current'
    draft['role_is_not_universality_grade']=True
    draft['remaining_semantic_gaps']=['component_contracts_procedures_prompts_review',
                                     'source_to_meaning_independent_review_not_performed',
                                     'actual_target_rendering_and_behavior_unverified',
                                     'implementation_and_format_behavior_not_qualified_by_role_inventory',
                                     'actual_authority_readiness_actuator_result_unqualified']
    return draft


def verify(candidate):return canonical(candidate)==canonical(compose(*load_basis()))


def display(text):
    # Presentation-only whitespace; structured body and source bytes remain unchanged.
    return '\n'.join(line.rstrip() for line in text.strip().splitlines())


def render_preview(draft):
    lines=['# Черновик общих правил — предмет review, НЕ активный профиль',
           '', '**Исследовательский производный документ. Не выпуск, не экспорт, не разрешение действий.**',
           'Согласованность/pins не доказывают semantic equivalence или поведение агента.',
           'Компонентные контракты и процедуры ещё в очереди review; полномочия не возникают из чтения.',
           'Источником нормы остаётся точная утверждённая версия, не этот preview.',
           'Отображение убирает только краевые пробелы; structured bodies/source spans сохранены отдельно.',
           '', '## Общие области применения', '']
    names={key:f'S{i:02}' for i,key in enumerate(sorted(draft['context_table']),1)}
    for key in sorted(names):lines.extend([f'### {names[key]}', '', display(draft['context_table'][key]),''])
    lines.extend(['## Предъявляемые смысловые блоки',''])
    for body in draft['bodies']:
        lines.extend(['### '+', '.join(body['ids']), '',
                      f"Область: {names[body['context_id']]}; маршрут: {body['route']}.", '',
                      display(body['text']),''])
    lines.extend(['## Предел результата','',
                  'Все exact implementation/schema/verification dependencies сохранены в composition ledger,',
                  'но их код/данные не вставлены в правила. Role inventory не классифицирует их смысл.',
                  f"В очереди semantic review: {len(draft['semantic_review_queue'])} component documents.",
                  'Нужны отдельные semantic review и проверка реального применения.',
                  'Release/export/activation/compatible-release разрешения: НЕТ.',''])
    return '\n'.join(lines)


class RoleCompositionTests(unittest.TestCase):
    def setUp(self):
        self.inputs=load_basis();self.ledger=self.inputs[0];self.draft=compose(*self.inputs)

    def test_all_ninety_references_retained(self):
        self.assertEqual(90,len(self.draft['role_inventory']))
        self.assertTrue(all(r['composition']=='retain_exact_reference' for r in self.draft['role_inventory']))
        self.assertEqual(24,len(self.draft['declared_closure']))
        self.assertTrue(verify(self.draft))

    def test_role_is_not_semantic_completion(self):
        self.assertTrue(self.draft['role_inventory_complete'])
        self.assertTrue(self.draft['role_is_not_universality_grade'])
        self.assertFalse(self.draft['full_semantic_coverage'])
        self.assertEqual(26,len(self.draft['semantic_review_queue']))
        self.assertTrue(self.draft['remaining_semantic_gaps'])

    def test_d04_join_keeps_all_scopes_links_and_routes(self):
        parts=[b for b in self.draft['bodies'] if b['ids'][0].startswith('D04/')]
        self.assertEqual(17,len(parts));self.assertEqual(14,sum(b['route']=='preserve' for b in parts))
        self.assertEqual(17,len(self.draft['meaning_links']))
        self.assertEqual([],self.draft['unresolved_external'])

    def test_complete_core_not_only_numbered_requirements(self):
        bodies={b['ids'][0]:b for b in self.draft['bodies']}
        for uid in [f'C{i:02}' for i in range(1,11)]+['C-purpose','C-application','C-check','C-uncertainty']:
            self.assertIn(uid,bodies);self.assertEqual('preserve',bodies[uid]['route'])
        text=self.inputs[4][self.ledger['core_source']['path']].decode()
        covered=[u['source'] for u in self.ledger['core_units']]+[self.ledger['core_scope']]
        positions=set(i for span in covered for i in range(span['start'],span['end']))
        rest=''.join(ch if i not in positions else '\n' for i,ch in enumerate(text))
        self.assertTrue(all(not line.strip() or line.startswith('#') for line in rest.splitlines()))

    def test_preview_is_actual_reproducible_materialization(self):
        self.assertEqual((ROOT/PREVIEW).read_text(),render_preview(self.draft))
        self.assertEqual(86,len(self.draft['bodies']))
        self.assertEqual(5,len(self.draft['context_table']))

    def test_code_schema_and_fixture_not_copied_as_rules(self):
        allowed={r['reference']['path'] for r in self.ledger['roles'] if r['role']=='rule_source'}
        for body in self.draft['bodies']:
            for origin in body['origins']:self.assertIn(origin['path'].removeprefix('agent_system/'),allowed)
        self.assertFalse(any('.py'==Path(o['path']).suffix for b in self.draft['bodies'] for o in b['origins']))

    def test_known_ledger_is_full_snapshot_not_selected_approvals_only(self):
        self.assertEqual(31,len(self.draft['known_decision_refs']))
        self.assertEqual('observed_fixed_pins_not_atomic_or_globally_current',self.draft['inventory_consistency'])

    def test_missing_or_laundered_dependency_rejected(self):
        for mode in ('drop','launder'):
            candidate=copy.deepcopy(self.draft)
            if mode=='drop':candidate['role_inventory'].pop()
            else:next(r for r in candidate['role_inventory'] if r['role']=='implementation')['role']='rule_source'
            self.assertFalse(verify(candidate))

    def test_component_semantics_cannot_be_dismissed_by_extension(self):
        self.draft['semantic_review_queue']=[];self.assertFalse(verify(self.draft))

    def test_code_injection_rejected(self):
        self.draft['bodies'].append(dict(ids=['INJECTED'],text='exec(foreign_source)',context_id='',origins=[],route='preserve'))
        self.assertFalse(verify(self.draft))

    def test_schema_not_removed_as_nonuniversal(self):
        self.draft['role_inventory']=[r for r in self.draft['role_inventory'] if r['role']!='schema']
        self.assertFalse(verify(self.draft))

    def test_lost_decision_reference_rejected(self):
        self.draft['known_decision_refs'].pop();self.assertFalse(verify(self.draft))

    def test_new_unexpected_non_json_ledger_name_not_filtered(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);ledger=root/'agent_system/catalog/approvals';ledger.mkdir(parents=True)
            for ref in self.ledger['known_decisions']:(ledger/Path(ref['path']).name).touch()
            (ledger/'unexpected.txt').touch()
            with self.assertRaisesRegex(ValueError,'LEDGER_INVENTORY'):capture_inventory(root,self.ledger,{})

    def test_missing_known_ledger_name_is_not_safe_absence(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);folder=root/'agent_system/catalog/approvals';folder.mkdir(parents=True)
            for ref in self.ledger['known_decisions'][:-1]:(folder/Path(ref['path']).name).touch()
            with self.assertRaisesRegex(ValueError,'LEDGER_INVENTORY'):capture_inventory(root,self.ledger,{})

    def test_changed_implementation_and_decision_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            refs=[dict(**{k:v for k,v in row['reference'].items() if k!='path'},
                       path='agent_system/'+row['reference']['path']) for row in self.ledger['roles']]
            refs+=self.ledger['known_decisions']
            for ref in refs:
                target=root/ref['path'];target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((ROOT/ref['path']).read_bytes())
            code=next(row['reference']['path'] for row in self.ledger['roles'] if row['role']=='implementation')
            for path in ['agent_system/'+code,self.ledger['known_decisions'][0]['path']]:
                target=root/path;original=target.read_bytes()
                target.write_bytes(bytes([(original[0]+1)%256])+original[1:])
                with self.subTest(path=path),self.assertRaisesRegex(ValueError,'REFERENCE_PIN'):
                    capture_inventory(root,self.ledger,self.inputs[3])
                target.write_bytes(original)

    def test_all_referenced_bytes_are_data_not_executed(self):
        from unittest.mock import patch
        with patch('builtins.exec',side_effect=AssertionError('EXECUTED_INVENTORY')):
            captured=capture_inventory(ROOT,self.ledger,self.inputs[3])
        self.assertEqual(90,len(captured))

    def test_composition_does_not_reread_source_after_capture(self):
        from unittest.mock import patch
        with patch.object(Path,'read_bytes',side_effect=AssertionError('REREAD')):
            self.assertEqual(canonical(self.draft),canonical(compose(*self.inputs)))

    def test_false_qualification_and_authority_rejected(self):
        for key,value in [('full_semantic_coverage',True),('actual_behavior_verified',True),
                          ('release_allowed',True),('export_allowed',True),('activation_allowed',True),
                          ('compatible_release_allowed',True),('review','independent_review')]:
            candidate=copy.deepcopy(self.draft);candidate[key]=value;self.assertFalse(verify(candidate))

    def test_d04_link_loss_does_not_self_qualify(self):
        self.draft['meaning_links']=[];self.assertFalse(verify(self.draft))

    def test_local_delegation_and_capability_limits_still_retained(self):
        text='\n'.join(b['text'] for b in self.draft['bodies'])
        self.assertIn('не создаёт делегирование в другой среде',text)
        self.assertTrue(self.draft['retained_constraints'])
        self.assertTrue(self.draft['original_contracts_retained'])


if __name__=='__main__':unittest.main(verbosity=2)
