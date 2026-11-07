#!/usr/bin/env python3
"""Offline bundle consistency tests, not source/execution authentication."""
import copy
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[2]
MODULE = runpy.run_path(str(HERE/'bundle.py'))
verify = MODULE['verify_bundle']
G = verify.__globals__
ref = MODULE['_ref']
FIXTURES = runpy.run_path(str(BASE/'validation/ent-0009/r0001/verify.py'))


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode()


class BundleConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.fixture = FIXTURES['PlanExecutionTests']()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.capture()

    def capture(self):
        self.fixture.run_plan()
        self.report_bytes = self.fixture.result['report_bytes']
        self.documents = dict(self.fixture.result['documents'])
        self.report = json.loads(self.report_bytes)
        self.expected_plan = self.report['plan']
        self.payloads = {}
        if self.report['stages']['acquisition']['status'] == 'passed_known_inputs':
            self.payloads = {a['path']:(self.fixture.root/a['path']).read_bytes()
                             for a in [self.fixture.plan['registry'], *self.fixture.plan['artifacts'],
                                       *self.fixture.plan['decisions']]}

    def finish(self):
        self.report_bytes = encode(self.report)

    def change_child(self, stage, change):
        pointer = self.report['stages'][stage]['evidence']
        value = json.loads(self.documents.pop(pointer['sha256']))
        change(value)
        raw = encode(value)
        pointer = ref(raw)
        self.documents[pointer['sha256']] = raw
        self.report['stages'][stage]['evidence'] = pointer
        self.finish()

    def check(self):
        result = verify(self.report_bytes,ref(self.report_bytes),self.expected_plan,self.documents,self.payloads)
        self.assertFalse(result['transition_allowed'])
        self.assertEqual(result['overall_admission'],'not_evaluated')
        return result

    def failed(self):
        result = self.check()
        self.assertEqual(result['status'],'failed',result)
        self.assertNotIn(str(self.fixture.root),json.dumps(result))
        return result

    def test_positive_replay(self):
        result = self.check()
        self.assertEqual(result['status'],'consistent_recorded_bundle')
        self.assertIn('semantic_replay',result['checks'])
        self.assertIn('source_observation_truth',result['not_checked'])

    def test_no_source_needed(self):
        self.fixture.doCleanups()
        self.assertEqual(self.check()['status'],'consistent_recorded_bundle')

    def test_report_external_pin(self):
        result=verify(self.report_bytes,dict(ref(self.report_bytes),sha256='0'*64),self.expected_plan,self.documents,self.payloads)
        self.assertEqual(result['diagnostics'],[dict(code='EXTERNAL_REFERENCE_MISMATCH')])

    def test_plan_external_pin(self):
        self.expected_plan=dict(self.expected_plan,sha256='0'*64)
        self.failed()

    def test_missing_document(self):
        self.documents.pop(self.report['stages']['binding']['evidence']['sha256'])
        self.failed()

    def test_extra_document(self):
        raw=b'{}\n';self.documents[ref(raw)['sha256']]=raw
        self.failed()

    def test_content_address_mismatch(self):
        digest=next(iter(self.documents));self.documents[digest]=b'{}\n'
        self.failed()

    def test_reference_size_mismatch(self):
        self.report['stages']['binding']['evidence']['size_bytes']+=1;self.finish();self.failed()

    def test_missing_payload(self):
        self.payloads.pop(next(iter(self.payloads)));self.failed()

    def test_extra_payload(self):
        self.payloads['unplanned']=b'secret';self.failed()

    def test_payload_hash_mismatch(self):
        self.payloads[self.fixture.plan['artifacts'][0]['path']]=b'forged';self.failed()

    def test_plan_id_mismatch(self):
        self.report['plan_id']=self.fixture.plan['catalog_id'];self.finish();self.failed()

    def test_context_substitution_after_rehash(self):
        self.change_child('binding',lambda c:c['restriction_evaluation']['context'].update(operation='activate'))
        self.failed()

    def test_extra_closure_after_rehash(self):
        self.change_child('binding',lambda c:c['selected_closure'].append(dict(catalog_id=self.fixture.plan['catalog_id'],entity_id='ENT-9999',revision='r0001')))
        self.failed()

    def test_checked_artifact_substitution_after_rehash(self):
        self.change_child('binding',lambda c:c['checked_artifacts'][0].update(sha256='0'*64))
        self.failed()

    def test_child_obligations_cannot_disappear(self):
        self.change_child('binding',lambda c:c.update(not_checked=[]));self.failed()

    def test_child_unknown_field(self):
        self.change_child('binding',lambda c:c.update(approved=True));self.failed()

    def test_inventory_substitution(self):
        self.change_child('acquisition',lambda c:c['directory_after'].update(entries=[]));self.failed()

    def test_directory_fingerprint_inconsistency(self):
        def changed(c):
            c['directory_before']['fingerprint'][1]+=1
            c['directory_after']=copy.deepcopy(c['directory_before'])
        self.change_child('acquisition',changed);self.failed()

    def test_acquisition_obligations_preserved(self):
        self.change_child('acquisition',lambda c:c.update(not_checked=[]));self.failed()

    def test_extra_acquisition_claim(self):
        self.change_child('acquisition',lambda c:c.update(authenticated=True));self.failed()

    def test_consistent_observations_still_not_execution_proof(self):
        def forged(c):
            for name in ['directory_before','directory_after']:
                c[name]['fingerprint'][5]=123456
        self.change_child('acquisition',forged)
        result=self.check()
        self.assertEqual(result['status'],'consistent_recorded_bundle')
        self.assertIn('execution_authentication',result['not_checked'])
        self.assertIn('source_observation_truth',result['not_checked'])

    def test_scope_block_replays_without_permission(self):
        self.fixture.fixture.add_restriction();self.fixture.sync();self.capture()
        result=self.check();self.assertEqual(result['status'],'consistent_recorded_bundle')
        self.assertEqual(result['recorded_status'],'blocked_known_scope')

    def test_failure_without_child_claim_only(self):
        (self.fixture.root/'catalog/approvals/.hidden').write_bytes(b'unexpected')
        self.capture();result=self.check()
        self.assertEqual(result['status'],'consistent_recorded_bundle')
        self.assertEqual(result['recorded_status'],'failed')
        self.assertNotIn('semantic_replay',result['checks'])

    def test_failed_acquisition_no_unplanned_payloads(self):
        (self.fixture.root/'catalog/approvals/.hidden').write_bytes(b'unexpected')
        self.capture();self.payloads={'secret':b'private'};self.failed()

    def test_incomplete_is_not_pass(self):
        for stage in ['acquisition','binding']:
            pointer=self.report['stages'][stage]['evidence'];self.documents.pop(pointer['sha256'])
            self.report['stages'][stage]=dict(status='not_run',diagnostics=[])
        self.report['status']='incomplete';self.payloads={};self.finish()
        result=self.check();self.assertEqual(result['status'],'consistent_recorded_bundle')
        self.assertEqual(result['recorded_status'],'incomplete')

    def test_duplicate_keys_rejected(self):
        self.report_bytes=b'{"x":1,"x":2}\n';self.failed()

    def test_wrong_types_and_limits(self):
        for docs,payloads in [([],{}),({},[]),({},dict(x='not bytes'))]:
            result=verify(self.report_bytes,ref(self.report_bytes),self.expected_plan,docs,payloads)
            self.assertEqual(result['status'],'failed')
        raw=b' '*(MODULE['LIMIT']+1)
        self.assertEqual(verify(raw,{},self.expected_plan,{}, {})['status'],'failed')

    def test_installed_entry_changed(self):
        pins=copy.deepcopy(MODULE['ENTRY_PINS']);next(iter(pins.values()))['sha256']='0'*64
        with patch.dict(G,ENTRY_PINS=pins):result=self.check()
        self.assertEqual(result['status'],'unsupported')

    def test_failed_semantic_child_is_replayed(self):
        self.fixture.plan['selection'][0]['revision']='r0999'
        self.capture();result=self.check()
        self.assertEqual(result['status'],'consistent_recorded_bundle')
        self.assertEqual(result['recorded_status'],'failed')
        self.assertIn('semantic_replay',result['checks'])

    def test_unsupported_replay_stays_unsupported(self):
        key=next(iter(self.fixture.fixture.witnesses))
        record=json.loads(self.fixture.fixture.witnesses[key]);record['decision_type']='unknown_event'
        self.fixture.fixture.witnesses[key]=encode(record);self.fixture.sync();self.capture()
        self.assertEqual(self.check()['status'],'unsupported')

    def test_partial_acquisition_not_complete(self):
        pointer=self.report['stages']['binding']['evidence'];self.documents.pop(pointer['sha256'])
        self.report['stages']['binding']=dict(status='not_run',diagnostics=[])
        self.report['status']='incomplete';self.finish()
        result=self.check();self.assertEqual(result['status'],'consistent_recorded_bundle')
        self.assertEqual(result['recorded_status'],'incomplete')
        self.assertNotIn('semantic_replay',result['checks'])

    def test_directory_logical_path_uses_pinned_reader(self):
        def change(c):
            c['directory_before']['resolved_path']='../outside'
            c['directory_after']=copy.deepcopy(c['directory_before'])
        self.change_child('acquisition',change);self.failed()

    def test_missing_engine_is_unsupported(self):
        from importlib import metadata
        with patch.object(metadata,'version',side_effect=metadata.PackageNotFoundError('jsonschema')):
            result=self.check()
        self.assertEqual(result['status'],'unsupported')

    def test_no_input_mutation(self):
        before=copy.deepcopy((self.report_bytes,self.expected_plan,self.documents,self.payloads))
        self.check();self.assertEqual(before,(self.report_bytes,self.expected_plan,self.documents,self.payloads))


if __name__=='__main__':
    unittest.main(verbosity=2)
