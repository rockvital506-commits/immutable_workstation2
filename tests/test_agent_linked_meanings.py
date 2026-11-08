#!/usr/bin/env python3
"""U01 source coverage, linked meaning trace and finite DECLARED semantic model.

No NLP equivalence, filesystem actuation, release or target-environment verification.
Mappings/generalizations are an agent-reviewed research proposal, not new norms.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
FIXTURE = 'research/45-agent-system-linked-meaning-decomposition.json'
FIXTURE_SHA = '89656b5ad0f319d3f433120ad7c48e977301f23ebe1319dc5f9dada1aa65c3c7'


def canonical(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(',', ':'))


def check_partition(basis):
    original = basis['source']['quote']
    pos = 0
    ids = {u['id'] for u in basis['units']}
    if len(ids) != len(basis['units']):
        raise ValueError('DUPLICATE_UNIT')
    for unit in basis['units']:
        if (unit['start'] != pos or unit['end'] <= pos or
                original[unit['start']:unit['end']] != unit['source_quote']):
            raise ValueError('SOURCE_PARTITION')
        pos = unit['end']
        if unit['scope'] != basis['scope'] or not unit['meaning']:
            raise ValueError('SCOPE_OR_MEANING')
        if not unit['linked_units'] or any(i not in ids or i==unit['id'] for i in unit['linked_units']):
            raise ValueError('MEANING_LINK')
        if unit['route']=='preserve' and unit['output']!=unit['source_quote']:
            raise ValueError('HIGH_MEANING_CHANGED')
    if pos != len(original):
        raise ValueError('SOURCE_PARTITION')
    if ''.join(u['source_quote'] for u in basis['units']) != original:
        raise ValueError('SOURCE_PARTITION')
    lookup={u['id']:u for u in basis['units']}
    for unit in basis['units']:
        for other in unit['linked_units']:
            if unit['id'] not in lookup[other]['linked_units']:
                raise ValueError('MEANING_LINK')
    seen=set(); pending=[basis['units'][0]['id']]
    while pending:
        uid=pending.pop()
        if uid not in seen:
            seen.add(uid);pending.extend(lookup[uid]['linked_units'])
    if seen != ids:
        raise ValueError('DISCONNECTED_MEANING_GROUP')


def load_basis(root=ROOT):
    raw=(root/FIXTURE).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA:
        raise ValueError('FIXTURE_PIN')
    basis=json.loads(raw)
    pred=basis['predecessor'];oldraw=(root/pred['path']).read_bytes()
    if hashlib.sha256(oldraw).hexdigest()!=pred['sha256']:
        raise ValueError('PREDECESSOR_PIN')
    old=next(u for u in json.loads(oldraw)['units'] if u['id']==pred['unit'])
    if old['route']!='hold' or old['source']!=basis['source']:
        raise ValueError('PREDECESSOR_MEANING')
    source=basis['source'];raw=(root/source['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=source['sha256']:
        raise ValueError('SOURCE_PIN')
    text=raw.decode('utf-8')
    if text[source['start_offset']:source['end_offset']]!=source['quote']:
        raise ValueError('SOURCE_SPAN')
    if basis['scope'] not in text:
        raise ValueError('SOURCE_SCOPE')
    boundary=basis['dependency_boundary'];pin=boundary['registry']
    registry_raw=(root/pin['path']).read_bytes()
    if hashlib.sha256(registry_raw).hexdigest()!=pin['sha256']:
        raise ValueError('REGISTRY_PIN')
    registry=json.loads(registry_raw)
    selected=boundary['selected']
    if selected['catalog_id']!=registry['catalog_id']:
        raise ValueError('DEPENDENCY_CATALOG')
    revision=next(v for e in registry['entities'] if e['entity_id']==selected['entity_id']
                  for v in e['revisions'] if v['revision']==selected['revision'])
    targets=[r['target'] for r in revision['relations'] if r['type']=='depends_on']
    if targets!=boundary['required_targets']:
        raise ValueError('DEPENDENCY_TARGETS')
    expected_path=source['path'].removeprefix('agent_system/')
    if not any(a['path']==expected_path and a['sha256']==source['sha256'] for a in revision['artifacts']):
        raise ValueError('SOURCE_REGISTRY_BINDING')
    for target in targets:
        core=next(v for e in registry['entities'] if e['entity_id']==target['entity_id']
                  for v in e['revisions'] if v['revision']==target['revision'])
        for uid in boundary['core_coverage_units']:
            unit=next(u for u in json.loads(oldraw)['units'] if u['id']==uid)
            if not any('agent_system/'+a['path']==unit['source']['path'] and
                       a['sha256']==unit['source']['sha256'] for a in core['artifacts']):
                raise ValueError('CORE_COVERAGE_BINDING')
        for ref in core['artifacts']+[core['approval']['reference'],revision['approval']['reference']]:
            data=(root/'agent_system'/ref['path']).read_bytes()
            if hashlib.sha256(data).hexdigest()!=ref['sha256']:
                raise ValueError('DEPENDENCY_REFERENCE_PIN')
    check_partition(basis)
    return basis


def proposal(basis):
    return dict(status='proposed_decomposition_not_semantic_admission',
                predecessor=basis['predecessor'],
                dependency_boundary=basis['dependency_boundary'],
                source={k:v for k,v in basis['source'].items() if k!='quote'},
                review='agent_self_review_not_independent',
                original_contract_retained=True,
                full_closure_checked=False,
                semantic_equivalence='not_established',
                gaps=['source_to_meaning_self_review',
                      'generalizations_not_independently_verified',
                      'outside_requirement4_not_analyzed',
                      'actual_target_environment_unchecked'],
                release_allowed=False, export_allowed=False, activation_allowed=False,
                compatible_release_allowed=False,
                units=[dict(id=u['id'],start=u['start'],end=u['end'],scope=u['scope'],
                            universality=u['universality'],route=u['route'],
                            meaning=u['meaning'],linked_units=u['linked_units'],text=u['output'])
                       for u in basis['units']])


def verify_proposal(candidate):
    # Pinned expected source/mapping is not inferred from candidate claims.
    return canonical(candidate)==canonical(proposal(load_basis()))


ENUMS = dict(index_kind={'canonical','absolute','backslash','empty_segment','dot_segment','parent_segment','unknown'},
             root={'physical_directory','root_symlink','unavailable','unknown'},
             chain={'inside','outside','escape_return','unknown'},
             target={'relative_plain','relative_dot','internal_absolute','external_absolute','unknown'},
             relative_base={'containing_directory','incorrect_root','unknown'})
BOOL_FIELDS = {'actual_cycle','shared_target','targets_available','redirect_type_supported',
               'traversal_within_limits','path_conflict','expected_tuple','observations_match',
               'identity_replaced','metadata_replaced','link_chain_replaced','safe_boundary',
               'same_timestamps','intermediate_change_return','snapshot_basis_declared',
               'link_type_preservable','link_creation_permitted','replace_with_regular',
               'copy_private_absolute','bytes_normalized','link_metadata_approved','symlink_support'}


def evaluate_declared(state):
    """Finite model; state fields are assumptions, NOT measured observations.

    Passing gates is a model result, never authority, full readiness or actual I/O.
    Snapshot/external trust aren't verified here, even if state asserts a basis.
    """
    valid=(type(state) is dict and set(state)==set(ENUMS)|BOOL_FIELDS)
    if valid:
        valid=all(type(state[k]) is str and state[k] in values for k,values in ENUMS.items())
        valid=valid and all(type(state[k]) is bool for k in BOOL_FIELDS)
    local=False;transfer=False
    if valid:
        local=(state['index_kind']=='canonical' and
               state['root'] in {'physical_directory','root_symlink'} and
               state['chain']=='inside' and
               state['target'] in {'relative_plain','relative_dot','internal_absolute'} and
               (not state['target'].startswith('relative_') or state['relative_base']=='containing_directory') and
               not state['actual_cycle'] and state['targets_available'] and
               state['redirect_type_supported'] and state['traversal_within_limits'] and
               not state['path_conflict'] and state['expected_tuple'] and
               state['observations_match'] and not state['identity_replaced'] and
               not state['metadata_replaced'] and not state['link_chain_replaced'] and
               state['safe_boundary'] and not state['bytes_normalized'] and
               state['link_metadata_approved'] and state['symlink_support'])
        transfer=(local and state['link_type_preservable'] and state['link_creation_permitted'] and
                  not state['replace_with_regular'] and not state['copy_private_absolute'])
    return dict(input_valid=valid,
                local='declared_gates_satisfied' if local else 'blocked',
                transfer='declared_gates_satisfied' if transfer else 'blocked',
                integrity='matches_declared_observations_only' if local else 'not_established',
                snapshot='not_established', full_history='not_established',
                approval_created=False, release_allowed=False, export_allowed=False,
                activation_allowed=False, compatible_release_allowed=False)


class LinkedMeaningTests(unittest.TestCase):
    def setUp(self):
        self.basis=load_basis()
        self.candidate=proposal(self.basis)

    def unit(self,uid):
        return next(u for u in self.candidate['units'] if u['id']==uid)

    def test_source_partition_and_links(self):
        check_partition(self.basis)
        self.assertEqual(17,len(self.basis['units']))
        self.assertEqual(14,sum(u['route']=='preserve' for u in self.basis['units']))
        self.assertEqual(3,sum(u['route']=='generalize' for u in self.basis['units']))

    def test_positive_proposal_not_admission(self):
        self.assertTrue(verify_proposal(self.candidate))
        self.assertFalse(self.candidate['full_closure_checked'])
        self.assertTrue(self.candidate['gaps'])
        self.assertEqual('not_established',self.candidate['semantic_equivalence'])

    def test_finite_semantic_scenarios(self):
        covered=set()
        for case in self.basis['scenarios']:
            with self.subTest(name=case['name']):
                state={**self.basis['baseline'],**case['patch']}
                result=evaluate_declared(state)
                self.assertTrue(result['input_valid'])
                self.assertEqual(case['expected_local'],result['local'])
                self.assertEqual(case['expected_transfer'],result['transfer'])
                self.assertEqual('not_established',result['snapshot'])
                self.assertEqual('not_established',result['full_history'])
                for k in ['approval_created','release_allowed','export_allowed','activation_allowed','compatible_release_allowed']:
                    self.assertIs(False,result[k])
                covered.update(case['meaning_units'])
        self.assertEqual({u['id'] for u in self.basis['units']},covered)

    def test_unknown_enums_never_positive(self):
        for field in ('index_kind','root','chain','target'):
            with self.subTest(field=field):
                result=evaluate_declared({**self.basis['baseline'],field:'unknown'})
                self.assertEqual('blocked',result['local'])
                self.assertFalse(result['release_allowed'])

    def test_unknown_required_booleans_never_positive(self):
        for field in BOOL_FIELDS:
            with self.subTest(field=field):
                result=evaluate_declared({**self.basis['baseline'],field:None})
                self.assertFalse(result['input_valid'])
                self.assertEqual('blocked',result['local'])

    def test_undeclared_field_and_bool_integer_rejected(self):
        for patch in ({'safe_boundary':1},{'snapshot_verified':True}):
            self.assertFalse(evaluate_declared({**self.basis['baseline'],**patch})['input_valid'])

    def test_snapshot_claim_and_same_times_do_not_create_snapshot(self):
        for times in (False,True):
            for returned in (False,True):
                result=evaluate_declared({**self.basis['baseline'],'same_timestamps':times,
                                          'intermediate_change_return':returned,'snapshot_basis_declared':True})
                self.assertEqual('not_established',result['snapshot'])
                self.assertEqual('matches_declared_observations_only',result['integrity'])

    def test_alias_does_not_cancel_real_cycle(self):
        result=evaluate_declared({**self.basis['baseline'],'shared_target':True,'actual_cycle':True})
        self.assertEqual('blocked',result['local'])

    def test_no_silent_source_gaps_overlap_or_reorder(self):
        for mode in ('gap','overlap','order','truncate'):
            basis=copy.deepcopy(self.basis)
            if mode=='gap':basis['units'][1]['start']+=1
            elif mode=='overlap':basis['units'][1]['start']-=1
            elif mode=='order':basis['units'][1:3]=reversed(basis['units'][1:3])
            else:
                removed=basis['units'].pop()['id']
                for unit in basis['units']:
                    unit['linked_units']=[x for x in unit['linked_units'] if x!=removed]
            with self.subTest(mode=mode),self.assertRaisesRegex(ValueError,'SOURCE_PARTITION'):
                check_partition(basis)

    def test_detached_exception_link_rejected(self):
        self.unit('P05')['linked_units']=[]
        self.assertFalse(verify_proposal(self.candidate))

    def test_weakening_escape_return_rule(self):
        self.unit('P04')['text']='Разрешить escape, если final target внутри.'
        self.assertFalse(verify_proposal(self.candidate))

    def test_strengthening_absolute_target_rule(self):
        self.unit('P08')['text']='Все absolute targets запрещены даже локально.'
        self.assertFalse(verify_proposal(self.candidate))

    def test_generalized_index_does_not_cancel_original_format(self):
        self.candidate['original_contract_retained']=False
        self.assertFalse(verify_proposal(self.candidate))

    def test_private_path_or_platform_particulars_not_inserted(self):
        self.unit('P10')['text']='Всегда применять Windows Junction по /private/example.'
        self.assertFalse(verify_proposal(self.candidate))

    def test_normalization_not_integrity(self):
        self.unit('P17')['text']='Можно исправить переводы строк перед проверкой.'
        self.assertFalse(verify_proposal(self.candidate))

    def test_coherent_false_candidate_source_pin_rejected(self):
        self.unit('P16')['text']='Предварительного resolve достаточно.'
        self.candidate['source']['sha256']=hashlib.sha256(self.unit('P16')['text'].encode()).hexdigest()
        self.assertFalse(verify_proposal(self.candidate))

    def test_historical_hold_not_overwritten(self):
        p=self.basis['predecessor'];old=json.loads((ROOT/p['path']).read_bytes())
        unit=next(u for u in old['units'] if u['id']=='U01')
        self.assertEqual('hold',unit['route']);self.assertIsNone(unit['output'])

    def test_no_self_attested_qualification_or_action(self):
        for field,value in [('review','independent_owner_approved'),('full_closure_checked',True),
                            ('gaps',[]),('semantic_equivalence','established'),
                            ('release_allowed',True),('export_allowed',True),
                            ('activation_allowed',True),('compatible_release_allowed',True)]:
            with self.subTest(field=field):
                candidate=copy.deepcopy(self.candidate);candidate[field]=value
                self.assertFalse(verify_proposal(candidate))

    def test_exact_dependency_boundary_not_latest(self):
        boundary=self.basis['dependency_boundary']
        self.assertEqual([dict(catalog_id=boundary['selected']['catalog_id'],
                               entity_id='ENT-0001',revision='r0001')],boundary['required_targets'])
        self.assertEqual([1,2,3,5,6,7,8,9,10],boundary['other_requirement_gaps'])
        self.candidate['dependency_boundary']['required_targets'][0]['revision']='latest'
        self.assertFalse(verify_proposal(self.candidate))

    def test_predecessor_and_actual_source_pins(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            paths=[FIXTURE,self.basis['predecessor']['path'],self.basis['source']['path']]
            # The source-pin failure precedes registry/closure reads in this fixture.

            for path in paths:
                target=root/path;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((ROOT/path).read_bytes())
            src=root/self.basis['source']['path'];original=src.read_bytes();src.write_bytes(original+b'\n')
            with self.assertRaisesRegex(ValueError,'SOURCE_PIN'):load_basis(root)
            src.write_bytes(original)
            pred=root/self.basis['predecessor']['path'];pred.write_bytes(pred.read_bytes()+b'\n')
            with self.assertRaisesRegex(ValueError,'PREDECESSOR_PIN'):load_basis(root)


if __name__=='__main__':
    unittest.main(verbosity=2)
