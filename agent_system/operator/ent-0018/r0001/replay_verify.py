"""Replay tests: disposable prospective installations, not real coordinator approval."""
import copy
import json
import os
from pathlib import Path
import runpy
import shutil
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
F=runpy.run_path(str(HERE/'runner_verify.py'))
RP=runpy.run_path(str(HERE/'replay.py'));replay=RP['replay_operator_run'];Blocked=RP['ReplayBlocked']
enc=F['enc'];ref=F['ref']


class ReplayTests(unittest.TestCase):
    setUp=F['RunnerTests'].setUp
    invoke=F['RunnerTests'].invoke
    success=F['RunnerTests'].success

    def prepare(self,b=False):
        value=self.success(b)
        change=patch.dict(replay.__globals__,_load=lambda:(F['R'],self.t))
        change.start();self.addCleanup(change.stop)
        return value['evidence']

    def check(self,receipt):return replay(receipt['run_id'],receipt['index'])

    def repack(self,receipt,change,*,human_text=None):
        # Coherently rehash/reseal tampered claims: CAS alone will still pass.
        index,objects=self.t['e']['_read_evidence'](receipt['run_id'],receipt['index'],with_capture=True)
        objects=dict(objects);old_j=index['metadata']['journal'];journal=json.loads(objects.pop(old_j['sha256']))
        objects.pop(journal['human_report']['sha256'])
        def replace(pointer,value):
            objects.pop(pointer['sha256']);raw=enc(value);objects[ref(raw)['sha256']]=raw;return ref(raw)
        change(journal,objects,replace)
        with self.t['e']['EvidenceStore']() as store:
            journal['run_id']=store.run_id;journal['terminal_claim']['operator_run_id']=store.run_id
            human=F['R']['format_operator_result'](journal['terminal_claim']).encode() if human_text is None else human_text
            objects[ref(human)['sha256']]=human;journal['human_report']=ref(human)
            raw=enc(journal);objects[ref(raw)['sha256']]=raw
            for blob in objects.values():store.put(blob)
            result=store.seal(dict(kind='operator_run_index',journal=ref(raw)))
        self.assertEqual(self.t['e']['verify_evidence'](result['run_id'],result['index'])['status'],'consistent_private_evidence')
        return result

    def test_success_no_b_semantics(self):
        result=self.check(self.prepare())
        self.assertEqual(result['status'],'consistent_recorded_operator_run_no_admission')
        self.assertTrue(result['full_replay']);self.assertEqual(result['source_bundles'],1)
        self.assertFalse(result['transition_allowed'])

    def test_success_b_without_source_or_trial_or_live_ledger(self):
        receipt=self.prepare(True);shutil.rmtree(self.source);shutil.rmtree(self.install/'local/trials')
        original=F['R']['_installed']
        def protected_only(path):
            if path.startswith('catalog/'):raise AssertionError('live index/ledger read')
            return original(path)
        with patch.dict(F['R']['_installed'].__globals__,_installed=protected_only),patch('os.write',side_effect=AssertionError('write')),patch('os.mkdir',side_effect=AssertionError('mkdir')),patch('os.fchmod',side_effect=AssertionError('chmod')),patch('os.fsync',side_effect=AssertionError('fsync')):
            value=self.check(receipt)
        self.assertTrue(value['full_replay']);self.assertEqual(value['source_bundles'],2)
        self.assertIn('freshness',value['not_checked'])

    def test_coherent_copy_is_not_execution_authentication(self):
        receipt=self.prepare();copied=self.repack(receipt,lambda *a:None)
        value=self.check(copied)
        self.assertTrue(value['full_replay']);self.assertIn('execution_authentication',value['not_checked'])

    def test_counter_tamper_with_valid_cas_rejected(self):
        receipt=self.prepare()
        def change(j,*a):j['terminal_claim']['validated_captures']=0
        with self.assertRaises(Blocked):self.check(self.repack(receipt,change))

    def test_step_order_status_tamper_rejected(self):
        receipt=self.prepare()
        def change(j,*a):j['terminal_claim']['steps']['stage']['status']='passed'
        with self.assertRaises(Blocked):self.check(self.repack(receipt,change))

    def test_child_id_tamper_rejected(self):
        receipt=self.prepare()
        def change(j,*a):j['terminal_claim']['steps']['source_a']['child_run_id']='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
        with self.assertRaises(Blocked):self.check(self.repack(receipt,change))

    def test_candidate_claim_tamper_rejected(self):
        receipt=self.prepare()
        def change(j,objects,replace):
            step=j['terminal_claim']['steps']['candidate'];doc=json.loads(objects[step['document']['sha256']]);doc['checks']=[]
            step['document']=replace(step['document'],doc)
        with self.assertRaises(Blocked):self.check(self.repack(receipt,change))

    def test_reader_metadata_tamper_rejected(self):
        receipt=self.prepare()
        def change(j,objects,replace):
            step=j['terminal_claim']['steps']['reader'];doc=json.loads(objects[step['document']['sha256']]);doc['candidate']['sha256']='0'*64
            step['document']=replace(step['document'],doc)
        with self.assertRaises(Blocked):self.check(self.repack(receipt,change))

    def test_profile_record_omission_rejected(self):
        receipt=self.prepare()
        def change(j,objects,replace):
            snap=json.loads(objects[j['profile']['sha256']]);snap['records'].pop();j['profile']=replace(j['profile'],snap)
        with self.assertRaises(Blocked):self.check(self.repack(receipt,change))

    def test_derived_query_context_tamper_rejected(self):
        receipt=self.prepare(True)
        def change(j,objects,replace):
            step=j['terminal_claim']['steps']['comparison'];wrapper=json.loads(objects[step['document']['sha256']])
            plan=json.loads(objects[wrapper['plan']['sha256']]);plan['context']['operation']='activate'
            wrapper['plan']=replace(wrapper['plan'],plan);step['document']=replace(step['document'],wrapper)
        with self.assertRaises(Blocked):self.check(self.repack(receipt,change))

    def test_extra_valid_cas_object_rejected_semantically(self):
        receipt=self.prepare()
        def change(j,objects,replace):objects[ref(b'extra')['sha256']]=b'extra'
        with self.assertRaises(Blocked):self.check(self.repack(receipt,change))

    def test_failed_journal_not_full_semantic_success(self):
        (self.source/self.plan['artifacts'][0]['path']).write_bytes(b'corrupt')
        value=self.invoke();self.assertEqual(value['status'],'failed')
        change=patch.dict(replay.__globals__,_load=lambda:(F['R'],self.t));change.start();self.addCleanup(change.stop)
        checked=self.check(value['evidence'])
        self.assertEqual(checked['status'],'recorded_partial_run_no_full_replay');self.assertFalse(checked['full_replay'])
        self.assertFalse(checked['export_allowed'])

    def test_structural_store_is_not_operator_journal(self):
        self.prepare()
        with self.t['e']['EvidenceStore']() as store:receipt=store.seal({})
        with self.assertRaises(Blocked):self.check(receipt)

    def test_wrong_external_pin_rejected(self):
        receipt=self.prepare();receipt['index']['sha256']='0'*64
        with self.assertRaises(Blocked):self.check(receipt)

    def test_human_report_closed_safe_and_reproducible(self):
        value=self.success();formatter=F['R']['format_operator_result']
        text=formatter(value);self.assertNotIn(str(self.root),text);self.assertNotIn('manifest_bytes',text)
        value['diagnostics']=[dict(code='/private/path secret text')]
        self.assertEqual(formatter(value),text)  # free-form diagnostics are never copied
        value['validated_captures']=1.0
        with self.assertRaises(F['Blocked']):formatter(value)

    def test_coherent_human_text_substitution_rejected(self):
        receipt=self.prepare()
        with self.assertRaises(Blocked):self.check(self.repack(receipt,lambda *a:None,human_text=b'false summary\n'))

    def test_protocol_reference_substitution_rejected(self):
        receipt=self.prepare()
        def change(j,objects,replace):
            snapshot=json.loads(objects[j['profile']['sha256']]);snapshot['prompt']=j['session']
            j['profile']=replace(j['profile'],snapshot)
        with self.assertRaises(Blocked):self.check(self.repack(receipt,change))


if __name__=='__main__':unittest.main(verbosity=2)
