#!/usr/bin/env python3
"""Integrity/traceability of manually reviewed methodology vectors, NOT agent evaluation."""
import hashlib
import json
from pathlib import Path
import re
import unittest

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[2]
WORK_SHA = '06923c52d5e7311556e8276cea473af71284f985476f970dced83d085a70cbb4'
SCENARIO_SHA = '441d2505e822cdbf37d534a17b4b89c32a54853ff4442d9e019104c0b3ea5f50'
CORE_SHA = '684e18cc01dc6b1ffd66899615df03b01e756f40f1354f3ac82a81563a944773'
EXPECTED_DISPOSITIONS = {
    'S01': 'stop_affected', 'S02': 'stop_affected', 'S03': 'continue_bounded',
    'S04': 'candidate_only', 'S05': 'stop_affected', 'S06': 'candidate_only',
    'S07': 'implement_bounded', 'S08': 'fix_and_retest', 'S09': 'ask_owner',
    'S10': 'record_deferred', 'S11': 'scope_limited', 'S12': 'continue_bounded',
    'S13': 'continue_bounded', 'S14': 'scope_limited'}


def unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('Duplicate JSON key')
        value[key] = item
    return value


def reject(_value):
    raise ValueError('Non-JSON constant')


class WorkMethodologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        work = (HERE/'work.md').read_bytes()
        raw = (HERE/'scenarios.json').read_bytes()
        core = (BASE/'catalog/contracts/agent_system/ent-0001/r0001.md').read_bytes()
        for data, digest in [(work,WORK_SHA),(raw,SCENARIO_SHA),(core,CORE_SHA)]:
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('Exact normative bytes changed')
        cls.work = work.decode('utf-8')
        cls.raw = raw
        cls.data = json.loads(raw.decode('utf-8'),object_pairs_hook=unique,parse_constant=reject)
        cls.cases = {c['case_id']:c for c in cls.data['cases']}

    def test_exact_identity_and_shape(self):
        self.assertEqual(set(self.data),{'schema_version','entity_id','revision','verification_level',
                                        'agent_behavior_verified','overall_admission','transition_allowed','cases'})
        self.assertEqual((self.data['schema_version'],self.data['entity_id'],self.data['revision']),
                         ('1','ENT-0011','r0001'))

    def test_model_review_never_claims_behavior_or_activation(self):
        self.assertEqual(self.data['verification_level'],'model_review')
        self.assertIs(self.data['agent_behavior_verified'],False)
        self.assertEqual(self.data['overall_admission'],'not_evaluated')
        self.assertIs(self.data['transition_allowed'],False)

    def test_all_clause_ids_present_once(self):
        headings = re.findall(r'^## (W\d{2})\.',self.work,re.MULTILINE)
        self.assertEqual(headings,[f'W{i:02d}' for i in range(10)])

    def test_every_work_capability_has_reviewed_scenario(self):
        covered={item for case in self.cases.values() for item in case['clauses']}
        self.assertEqual(covered,{f'W{i:02d}' for i in range(10)})

    def test_unique_case_ids_and_traceability(self):
        self.assertEqual(len(self.cases),len(self.data['cases']))
        self.assertEqual(set(self.cases),set(EXPECTED_DISPOSITIONS))
        for case in self.cases.values():
            self.assertEqual(set(case),{'case_id','clauses','situation','expected_disposition',
                                        'required_actions','forbidden_inference','reviewed_response'})
            self.assertTrue(case['clauses'])
            self.assertEqual(len(case['clauses']),len(set(case['clauses'])))
            self.assertTrue(all(f'## {clause}.' in self.work for clause in case['clauses']))

    def test_reviewed_dispositions_match_control_oracle(self):
        for case_id, expected in EXPECTED_DISPOSITIONS.items():
            with self.subTest(case_id=case_id):
                self.assertEqual(self.cases[case_id]['expected_disposition'],expected)

    def test_reviews_have_reason_and_forbidden_inference(self):
        for case in self.cases.values():
            for key in ['situation','forbidden_inference','reviewed_response']:
                self.assertIsInstance(case[key],str)
                self.assertTrue(case[key].strip())
            self.assertTrue(case['required_actions'])
            self.assertEqual(len(set(case['required_actions'])),len(case['required_actions']))
            for action in case['required_actions']:
                self.assertRegex(action,r'^[a-z][a-z_]+$')

    def test_delegation_not_new_authority(self):
        self.assertIn('use_existing_delegation',self.cases['S07']['required_actions'])
        self.assertIn('keep_release_activation_separate',self.cases['S07']['required_actions'])
        self.assertIn('ask_specific_question',self.cases['S09']['required_actions'])

    def test_failure_not_retroactive_success(self):
        self.assertEqual(self.cases['S08']['expected_disposition'],'fix_and_retest')
        self.assertIn('retain_failure_evidence',self.cases['S08']['required_actions'])
        self.assertIn('repeat_affected_and_regression_checks',self.cases['S08']['required_actions'])

    def test_coverage_not_truth_or_practice(self):
        self.assertIn('keep_environment_not_checked',self.cases['S11']['required_actions'])
        self.assertIn('keep_observation_truth_not_checked',self.cases['S14']['required_actions'])
        self.assertEqual(self.cases['S14']['expected_disposition'],'scope_limited')

    def test_deferred_scope_and_self_application(self):
        self.assertIn('continue_only_active_scope',self.cases['S10']['required_actions'])
        self.assertIn('apply_same_method_to_system',self.cases['S13']['required_actions'])
        self.assertIn('exclude_private_architecture',self.cases['S13']['required_actions'])

    def test_proportionate_work_and_reuse(self):
        self.assertIn('reuse_applicable_evidence',self.cases['S03']['required_actions'])
        self.assertIn('investigate_specific_gap',self.cases['S03']['required_actions'])
        self.assertIn('avoid_fictitious_research',self.cases['S12']['required_actions'])

    def test_raw_serialization(self):
        for path in [HERE/'work.md',HERE/'scenarios.json',HERE/'verify.py']:
            data=path.read_bytes()
            data.decode('utf-8')
            self.assertFalse(data.startswith(b'\xef\xbb\xbf'))
            self.assertTrue(data.endswith(b'\n'))
            self.assertFalse(data.endswith(b'\n\n'))
            self.assertNotIn(b'\r',data)

    def test_examples_not_real_approval_records(self):
        self.assertNotIn('decision_type',self.data)
        for case in self.cases.values():
            self.assertNotIn('actor_role',case)
            self.assertNotIn('decision_type',case)


if __name__=='__main__':
    unittest.main(verbosity=2)
