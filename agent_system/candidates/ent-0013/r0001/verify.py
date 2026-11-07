#!/usr/bin/env python3
"""Candidate correspondence tests, not capability/agent or release certification."""
import copy
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[2]
MODULE=runpy.run_path(str(HERE/'check.py'))
check=MODULE['check_candidate']
G=check.__globals__
ref=MODULE['_ref']


def encode(value):
    return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()


class CandidateCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate_bytes=(HERE/'candidate.json').read_bytes()
        cls.registry_bytes=(BASE/'catalog/registry.json').read_bytes()
        data=json.loads(cls.candidate_bytes)
        cls.declared_payloads={a['path']:(BASE/a['path']).read_bytes() for c in data['components'] for a in c['record']['artifacts']}
        # Trusted-checkout fixture only; not an algorithm to authenticate a foreign ledger.
        cls.witnesses={p.relative_to(BASE).as_posix():p.read_bytes() for p in (BASE/'catalog/approvals').glob('*.json')}

    def setUp(self):
        self.candidate=json.loads(self.candidate_bytes)
        self.registry=json.loads(self.registry_bytes)
        self.payloads=dict(self.declared_payloads)
        self.decisions=dict(self.witnesses)

    def run_check(self):
        raw=encode(self.candidate)
        result=check(raw,ref(raw),encode(self.registry),self.decisions,self.payloads)
        for flag in ['transition_allowed','compatible_release_allowed','export_allowed','activation_allowed']:
            self.assertIs(result[flag],False)
        return result

    def failed(self,code=None):
        result=self.run_check();self.assertEqual(result['status'],'failed',result)
        if code:self.assertEqual(result['diagnostics'],[dict(code=code)])
        return result

    def test_positive_consistent_but_incomplete(self):
        result=self.run_check();self.assertEqual(result['status'],'consistent_incomplete_candidate',result)
        self.assertEqual(result['core_coverage'],'incomplete')
        self.assertEqual(len(result['blockers']),25)

    def test_exact_selected_composition(self):
        self.assertEqual(len(self.candidate['components']),12)
        self.assertEqual(len(self.payloads),34)
        self.assertNotIn('ENT-0013',{c['subject']['entity_id'] for c in self.candidate['components']})

    def test_external_pin_required(self):
        raw=encode(self.candidate)
        result=check(raw,dict(ref(raw),sha256='0'*64),encode(self.registry),self.decisions,self.payloads)
        self.assertEqual(result['diagnostics'],[dict(code='CANDIDATE_REFERENCE_MISMATCH')])

    def test_missing_ability_row(self):
        self.candidate['coverage'].pop();self.failed('COVERAGE_ROW_SET')

    def test_duplicate_ability_row(self):
        self.candidate['coverage'][-1]=copy.deepcopy(self.candidate['coverage'][0]);self.failed('COVERAGE_ROW_SET')

    def test_missing_crosscut_requirement(self):
        self.candidate['conditions'].pop();self.failed('COVERAGE_ROW_SET')

    def test_core_item_mismatch(self):
        self.candidate['coverage'][0]['core_item']=2;self.failed('CORE_ITEM_MISMATCH')

    def test_complete_claim_not_supported(self):
        self.candidate['coverage'][0]['status']='complete';self.failed('UNSUPPORTED_COMPLETENESS_CLAIM')

    def test_empty_gap_cannot_hide_blocker(self):
        self.candidate['coverage'][0]['gaps']=[];self.failed('COVERAGE_DETAIL_MISSING')

    def test_no_automatic_permission(self):
        for flag in ['compatible_release_allowed','export_allowed','activation_allowed','transition_allowed']:
            old=self.candidate[flag];self.candidate[flag]=True
            self.failed('CANDIDATE_PERMISSION_CLAIM');self.candidate[flag]=old

    def test_cannot_erase_blocked_transitions(self):
        self.candidate['blocked_transitions']=[];self.failed('CANDIDATE_GATE_MISMATCH')

    def test_check_definition_not_pass_result(self):
        self.candidate['coverage'][0]['checks'][0]['result']='passed';self.failed('UNATTESTED_CHECK_RESULT')

    def test_target_environment_level_not_attested(self):
        self.candidate['coverage'][0]['checks'][0]['level']='target_environment';self.failed('UNATTESTED_CHECK_RESULT')

    def test_missing_section_locator(self):
        self.candidate['coverage'][0]['clauses'][0]['locator']='## missing';self.failed('LOCATOR_NOT_FOUND')

    def test_missing_test_locator(self):
        self.candidate['coverage'][0]['checks'][0]['reference']['locator']='test_missing';self.failed('LOCATOR_NOT_FOUND')

    def test_missing_scenario(self):
        self.candidate['coverage'][7]['checks'][0]['reference']['locator']='S99';self.failed('LOCATOR_NOT_FOUND')

    def test_reference_not_in_composition(self):
        self.candidate['coverage'][0]['clauses'][0]['path']='private/outside.md';self.failed('REFERENCE_OUTSIDE_COMPOSITION')

    def test_frozen_record_metadata_changes_block(self):
        selected=self.candidate['components'][0]['subject']
        entity=next(e for e in self.registry['entities'] if e['entity_id']==selected['entity_id'])
        rev=next(v for v in entity['revisions'] if v['revision']==selected['revision'])
        rev['title']+=' changed';self.failed('FROZEN_COMPONENT_MISMATCH')

    def test_newer_revision_never_replaces_pinned(self):
        entity=next(e for e in self.registry['entities'] if e['entity_id']=='ENT-0012')
        entity['revisions'][0]['revision']='r9999';self.failed('FROZEN_COMPONENT_MISMATCH')

    def test_missing_root_coverage(self):
        self.candidate['roots']=self.candidate['roots'][:1];self.failed('CLOSURE_MISMATCH')

    def test_duplicate_roots(self):
        self.candidate['roots']*=2;self.failed('ROOT_SET')

    def test_corrupt_payload(self):
        self.payloads[next(iter(self.payloads))]=b'forged\n';self.failed()

    def test_extra_payload(self):
        self.payloads['private/unlisted']=b'secret';self.failed('PAYLOAD_SET_MISMATCH')

    def test_unknown_fields(self):
        self.candidate['activate']=True;self.failed('CANDIDATE_SHAPE')

    def test_self_inclusion_rejected(self):
        self.candidate['descriptor_in_payload']=True;self.failed('CANDIDATE_PERMISSION_CLAIM')

    def test_descriptor_cannot_enter_its_own_payload(self):
        component=copy.deepcopy(self.candidate['components'][0])
        component['subject']=self.candidate['descriptor_subject']
        self.candidate['components'].append(component)
        self.failed('DESCRIPTOR_SELF_INCLUSION')

    def test_claim_truth_remains_unchecked(self):
        self.candidate['coverage'][0]['gaps'][0]['detail']='A different unverified assertion.'
        result=self.run_check();self.assertEqual(result['status'],'consistent_incomplete_candidate')
        self.assertIn('coverage_claim_truth',result['not_checked'])
        self.assertIn('agent_behavior',result['not_checked'])

    def test_unknown_scope_request(self):
        self.candidate['context']['operation']='activate';self.failed('CANDIDATE_GATE_MISMATCH')

    def test_known_restriction_not_ignored(self):
        component=self.candidate['components'][-1]
        path=component['record']['approval']['reference']['path']
        event=json.loads(self.decisions[path])
        event.update(decision_id='ffffffff-ffff-4fff-8fff-ffffffffffff',decision_type='revoke_use',
                     scope=dict(operations=['validate'],areas=['agent_system.candidate']),reason='Synthetic only')
        self.decisions['catalog/approvals/'+event['decision_id']+'.json']=encode(event)
        result=self.run_check();self.assertEqual(result['status'],'blocked_known_scope',result)

    def test_installed_entry_change(self):
        pins=copy.deepcopy(MODULE['ENTRY_PINS']);next(iter(pins.values()))['sha256']='0'*64
        with patch.dict(G,ENTRY_PINS=pins):result=self.run_check()
        self.assertEqual(result['status'],'unsupported')

    def test_input_mutation_absent(self):
        before=copy.deepcopy((self.candidate,self.registry,self.payloads,self.decisions))
        self.run_check();self.assertEqual(before,(self.candidate,self.registry,self.payloads,self.decisions))

    def test_wrong_types_and_large_candidate(self):
        raw=b' '*(MODULE['LIMIT']+1)
        self.assertEqual(check(raw,{},b'',{}, {})['status'],'failed')
        self.candidate['coverage'][0]['clauses']=[[]];self.failed()


if __name__=='__main__':
    unittest.main(verbosity=2)
