#!/usr/bin/env python3
"""Negative permission paths and exact proposal binding, not positive release tests."""
import copy
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[2]
MODULE=runpy.run_path(str(HERE/'check.py'))
check=MODULE['check_proposal'];ref=MODULE['reference'];encode=MODULE['_encode']
FIX={'class':runpy.run_path(str(BASE/'candidates/ent-0013/r0001/verify.py'))['CandidateCoverageTests']}


class PermissionProposalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        FIX['class'].setUpClass()

    def setUp(self):
        f=FIX['class'];self.candidate=f.candidate_bytes;self.registry=f.registry_bytes
        self.decisions=dict(f.witnesses);self.payloads=dict(f.declared_payloads);self.parent=None
        self.request=dict(schema_version='1',kind='permission_proposal',request_id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
                          authority='proposal_only',action='release',area='agent_system.release',candidate=ref(self.candidate),
                          registry=ref(self.registry),decisions=[dict(path=p,**ref(b)) for p,b in sorted(self.decisions.items())],
                          export_paths=None,release_request=None,transition_allowed=False)

    def export(self):
        self.parent=encode(self.request)
        self.request.update(action='export',area='agent_system.transfer',request_id='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
                            release_request=ref(self.parent),export_paths=sorted(self.payloads))

    def run_check(self):
        raw=encode(self.request)
        result=check(raw,ref(raw),self.candidate,ref(self.candidate),self.registry,self.decisions,self.payloads,self.parent)
        for flag in ['transition_allowed','release_allowed','export_allowed','activation_allowed','performed']:
            self.assertIs(result[flag],False)
        self.assertEqual(result['overall_admission'],'not_evaluated')
        return result

    def failed(self,code=None):
        result=self.run_check();self.assertEqual(result['status'],'failed',result)
        if code:self.assertEqual(result['diagnostics'],[dict(code=code)])

    def test_release_proposal_consistent_but_blocked(self):
        result=self.run_check();self.assertEqual(result['status'],'blocked_incomplete_candidate',result)
        self.assertEqual(result['checks'],['proposal_snapshot_and_parent_binding','candidate_consistency_not_readiness','known_requested_scopes_only'])

    def test_export_proposal_consistent_but_blocked(self):
        self.export();self.assertEqual(self.run_check()['status'],'blocked_incomplete_candidate')

    def test_no_owner_authority_from_proposal(self):
        self.request['authority']='owner_approved';self.failed('PROPOSAL_SCHEMA')

    def test_real_release_event_unsupported_here(self):
        self.request['kind']='authorize_release';self.failed('PROPOSAL_SCHEMA')

    def test_permission_flag_rejected(self):
        self.request['transition_allowed']=True;self.failed('PROPOSAL_SCHEMA')

    def test_activation_not_a_release_action(self):
        self.request['action']='activate';self.failed('PROPOSAL_SCHEMA')

    def test_action_list_not_joint_permission(self):
        self.request['action']=['release','export'];self.failed('PROPOSAL_SCHEMA')

    def test_unknown_field_rejected(self):
        self.request['export_allowed']=True;self.failed('PROPOSAL_SCHEMA')

    def test_candidate_pin_mismatch(self):
        self.request['candidate']['sha256']='0'*64;self.failed('CANDIDATE_REFERENCE_MISMATCH')

    def test_registry_pin_mismatch(self):
        self.request['registry']['sha256']='0'*64;self.failed('REGISTRY_REFERENCE_MISMATCH')

    def test_missing_decision_reference(self):
        self.request['decisions'].pop();self.failed('DECISION_REFERENCE_MISMATCH')

    def test_duplicate_decision_paths(self):
        d=copy.deepcopy(self.request['decisions'][0]);d['sha256']='0'*64
        self.request['decisions'].append(d);self.failed('DECISION_REFERENCE_SET')

    def test_native_integer_sizes(self):
        self.request['registry']['size_bytes']=float(self.request['registry']['size_bytes']);self.failed('REFERENCE_SIZE_TYPE')

    def test_scope_literal_not_prefix(self):
        self.request['area']='agent_system';self.failed('PROPOSAL_SCHEMA')

    def test_export_requires_exact_parent_bytes(self):
        self.export();self.parent+=b' ';self.failed('PROPOSAL_REFERENCE_MISMATCH')

    def test_export_without_parent(self):
        self.export();self.parent=None;self.failed('PROPOSAL_REFERENCE_MISMATCH')

    def test_release_with_parent_rejected(self):
        self.parent=encode(self.request);self.failed('UNEXPECTED_PARENT')

    def test_changed_parent_snapshot_rejected(self):
        self.export();parent=json.loads(self.parent);parent['candidate']['sha256']='0'*64
        self.parent=encode(parent);self.request['release_request']=ref(self.parent);self.failed('PARENT_SNAPSHOT_MISMATCH')

    def test_parent_request_id_distinct(self):
        self.export();self.request['request_id']=json.loads(self.parent)['request_id'];self.failed('INVALID_RELEASE_PARENT')

    def test_export_omitted_mandatory_path(self):
        self.export();self.request['export_paths'].pop();self.failed('EXPORT_PATH_SET_MISMATCH')

    def test_export_extra_path(self):
        self.export();self.request['export_paths'].append('private/unlisted');self.failed('EXPORT_PATH_SET_MISMATCH')

    def test_no_parent_chain_or_cycle(self):
        self.export();self.parent=encode(self.request);self.request['release_request']=ref(self.parent)
        self.failed('INVALID_RELEASE_PARENT')

    def test_known_export_scope_not_hidden_by_validate(self):
        candidate=json.loads(self.candidate);component=candidate['components'][-1]
        path=component['record']['approval']['reference']['path'];event=json.loads(self.decisions[path])
        event.update(decision_id='ffffffff-ffff-4fff-8fff-ffffffffffff',decision_type='revoke_use',
                     scope=dict(operations=['export'],areas=['agent_system.transfer']),reason='Synthetic only')
        self.decisions['catalog/approvals/'+event['decision_id']+'.json']=encode(event)
        self.request['decisions']=[dict(path=p,**ref(b)) for p,b in sorted(self.decisions.items())]
        self.export();result=self.run_check();self.assertEqual(result['status'],'blocked_known_scope',result)

    def test_mutated_candidate_does_not_become_ready(self):
        candidate=json.loads(self.candidate);candidate['readiness']='ready';self.candidate=encode(candidate)
        self.request['candidate']=ref(self.candidate);self.failed('CANDIDATE_GATE_MISMATCH')

    def test_checker_does_not_write_bytes(self):
        with patch('pathlib.Path.write_bytes',side_effect=AssertionError('write forbidden')):
            self.assertEqual(self.run_check()['status'],'blocked_incomplete_candidate')

    def test_input_python_payload_is_not_executed(self):
        path=next(p for p in self.payloads if p.endswith('.py'))
        self.payloads[path]=b'raise AssertionError("Input code executed")\n'
        self.failed()

    def test_input_data_not_mutated(self):
        before=copy.deepcopy((self.request,self.payloads,self.decisions))
        self.run_check();self.assertEqual(before,(self.request,self.payloads,self.decisions))

    def test_external_request_pin_required(self):
        raw=encode(self.request)
        r=check(raw,dict(ref(raw),sha256='0'*64),self.candidate,ref(self.candidate),self.registry,self.decisions,self.payloads)
        self.assertEqual(r['diagnostics'],[dict(code='PROPOSAL_REFERENCE_MISMATCH')])

    def test_installed_schema_or_dependency_change(self):
        pins=copy.deepcopy(MODULE['PINS']);next(iter(pins.values()))['sha256']='0'*64
        with patch.dict(check.__globals__,PINS=pins):result=self.run_check()
        self.assertEqual(result['status'],'unsupported')

    def test_limits_before_loading(self):
        self.assertEqual(check(b'x'*(MODULE['LIMIT']+1),{},b'',{},b'',{}, {})['status'],'failed')


if __name__=='__main__':unittest.main(verbosity=2)
