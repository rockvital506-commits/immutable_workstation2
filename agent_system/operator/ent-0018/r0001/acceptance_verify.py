"""Additional I4 integration cases; synthetic events/approvals stay in temp fixtures."""
import copy
import json
from pathlib import Path
import runpy
import shutil
import unittest
from unittest.mock import patch
import uuid

HERE=Path(__file__).resolve().parent
F=runpy.run_path(str(HERE/'runner_verify.py'))
R=F['R'];enc=F['enc'];ref=F['ref'];run=F['run'];Blocked=F['Blocked']


class AcceptanceTests(unittest.TestCase):
    setUp=F['RunnerTests'].setUp
    invoke=F['RunnerTests'].invoke
    success=F['RunnerTests'].success
    update_plan=F['RunnerTests'].update_plan
    add_block=F['RunnerTests'].add_block

    def event(self,root,kind,operation='export',area='agent_system.transfer',target=None):
        row=self.add_block(root,operation,area);p=root/row['path'];event=json.loads(p.read_bytes())
        event['decision_type']=kind
        if target:
            raw=(root/target['path']).read_bytes()
            event['target']=dict(decision_id=json.loads(raw)['decision_id'],sha256=ref(raw)['sha256'])
        raw=enc(event);p.write_bytes(raw);return dict(path=row['path'],**ref(raw))

    def plan_for(self,root,original=None):
        plan=copy.deepcopy(original or self.plan);plan['plan_id']=str(uuid.uuid4())
        plan['decisions']=[dict(path='catalog/approvals/'+p.name,**ref(p.read_bytes())) for p in sorted((root/'catalog/approvals').glob('*.json'))]
        return enc(plan)

    def with_b(self,root):
        raw=self.plan_for(root);self.session.update(plan_b=ref(raw),query=dict(operation='export',area='agent_system.transfer'))
        self.docs[ref(raw)['sha256']]=raw;session=enc(self.session)
        return run(self.source,session,ref(session),self.docs,source_b_root=root)

    def test_t07_unknown_event_a_no_stage(self):
        self.event(self.source,'unknown_future_event')
        raw=self.plan_for(self.source);self.session['plan_a']=ref(raw);self.docs={ref(raw)['sha256']:raw}
        value=self.invoke();self.assertEqual(value['status'],'unsupported');self.assertEqual(value['validated_captures'],0)
        self.assertEqual(value['steps']['stage']['status'],'not_run')

    def test_t07_known_validate_block_a_no_capture(self):
        self.add_block(self.source,'validate','agent_system.operator_trial')
        raw=self.plan_for(self.source);self.session['plan_a']=ref(raw);self.docs={ref(raw)['sha256']:raw}
        value=self.invoke();self.assertEqual(value['status'],'blocked_known_scope');self.assertEqual(value['validated_captures'],0)
        self.assertEqual(value['steps']['candidate']['status'],'not_run')

    def test_t08_binding_fail_no_acquisition_reuse(self):
        registry=json.loads((self.source/'catalog/registry.json').read_bytes())
        own=next(e for e in registry['entities'] if e['entity_id']=='ENT-0018')['revisions'][0]
        own['approval']['reference']['sha256']='0'*64
        raw=enc(registry);(self.source/'catalog/registry.json').write_bytes(raw)
        self.plan['registry']=dict(path='catalog/registry.json',**ref(raw));self.update_plan()
        value=self.invoke();self.assertEqual(value['status'],'failed');self.assertEqual(value['source_acquisition_calls'],1)
        self.assertEqual(value['validated_captures'],0);self.assertEqual(value['steps']['stage']['status'],'not_run')
        receipt=value['evidence'];index,objects=self.t['e']['_read_evidence'](receipt['run_id'],receipt['index'],with_capture=True)
        journal=json.loads(objects[index['metadata']['journal']['sha256']]);step=journal['terminal_claim']['steps']['source_a']
        bundle=json.loads(objects[step['document']['sha256']]);self.assertIsNone(bundle['inputs'])

    def test_t20_exact_lift_not_latest_date(self):
        b=self.root/'source_b';shutil.copytree(self.source,b)
        block=self.event(b,'revoke_use');self.event(b,'lift_restriction',target=block)
        value=self.with_b(b)
        self.assertEqual(value['status'],'trial_checked_with_known_query_no_admission');self.assertFalse(value['export_allowed'])

    def test_t20_lifting_one_of_two_leaves_other(self):
        b=self.root/'source_b';shutil.copytree(self.source,b)
        block=self.event(b,'revoke_use');self.event(b,'revoke_use');self.event(b,'lift_restriction',target=block)
        value=self.with_b(b);self.assertEqual(value['status'],'blocked_known_scope');self.assertEqual(value['validated_captures'],2)

    def test_t21_archive_negative_cannot_disappear_in_b(self):
        self.event(self.source,'revoke_use',operation='activate',area='unrelated.literal')
        raw=self.plan_for(self.source);self.session['plan_a']=ref(raw);self.docs={ref(raw)['sha256']:raw}
        b=self.root/'source_b';shutil.copytree(self.source,b)
        # A includes the unrelated archived negative; removing it in B is not a grant.
        original=set(x['path'] for x in self.plan['decisions'])
        for p in (b/'catalog/approvals').glob('*.json'):
            if 'catalog/approvals/'+p.name not in original:p.unlink()
        value=self.with_b(b)
        self.assertEqual(value['status'],'failed');self.assertEqual(value['steps']['comparison']['status'],'failed')

    def test_t22_old_view_with_two_acquisitions_not_freshness(self):
        value=self.success(True)
        self.assertIn('freshness',value['not_checked']);self.assertEqual(value['current_permissions'],'not_evaluated')
        self.assertFalse(value['transition_allowed'])

    def test_t06_changed_descriptor_metadata_stops_preflight(self):
        self.session['candidate']=dict(self.session['candidate'],sha256='0'*64)
        with self.assertRaises(Blocked):self.invoke()
        self.assertFalse((self.install/'local').exists())

    def test_t13_real_post_read_corruption_no_handoff(self):
        reader=self.t['reader'];g=reader['capture_trial'].__globals__;old=g['_read'];changed=[]
        def change(directory,name,expected,entry):
            raw=old(directory,name,expected,entry)
            if name!='trial.json' and not changed:
                # Name is a fixed SHA, directory is an already opened private CAS.
                fd=F['os'].open(name,F['os'].O_WRONLY,dir_fd=directory)
                try:F['os'].write(fd,bytes([raw[0]^1])+raw[1:])
                finally:F['os'].close(fd)
                changed.append(1)
            return raw
        with patch.dict(g,_read=change):value=self.invoke(True)
        self.assertEqual(value['status'],'failed');self.assertEqual(value['steps']['handoff']['status'],'not_run')
        self.assertEqual(value['capture_invocations'],1)

    def test_t24_claim_collision_does_not_read_source(self):
        e=self.t['e'];store=e['EvidenceStore']()
        with store:store.put(b'keep');store.seal({})
        with patch.object(e['EvidenceStore'].__init__.__globals__['uuid'],'uuid4',return_value=uuid.UUID(store.run_id)):
            value=self.invoke()
        self.assertEqual(value['status'],'evidence_write_failed');self.assertEqual(value['capture_invocations'],0)
        self.assertTrue((self.install/'local/operator-runs'/store.run_id/'index.json').exists())

    def test_t24_declared_caps_exact_no_dependency_change(self):
        e=self.t['e'];self.assertEqual((e['LIMIT'],e['TOTAL'],e['FILES']),(16*1024*1024,128*1024*1024,20064))
        self.assertEqual(len(self.t['s']['PINS']),57)

    def test_t30_lab_requires_explicit_trust_not_source_discovery(self):
        lab=runpy.run_path(str(HERE/'lab.py'))
        with self.assertRaises(lab['LabBlocked']):lab['run_trusted_lab']()
        self.assertFalse((self.install/'local').exists())

    def test_t05_extra_or_wrong_selection_rejected_before_claim(self):
        for change in ['extra','selection']:
            with self.subTest(change=change):
                plan=copy.deepcopy(self.plan)
                if change=='extra':plan['artifacts'].append(dict(path='unlisted/extra',sha256='0'*64,size_bytes=1))
                else:plan['selection']=[dict(catalog_id=plan['catalog_id'],entity_id='ENT-0017',revision='r0001')]
                raw=enc(plan);self.session['plan_a']=ref(raw);self.docs={ref(raw)['sha256']:raw}
                with self.assertRaises(Blocked):self.invoke()
                self.assertFalse((self.install/'local').exists())

    def test_t06_installed_own_prompt_hash_mismatch(self):
        (self.install/'operator/ent-0018/r0001/prompt.md').write_bytes(b'changed installed prompt')
        with self.assertRaises(Blocked):self.invoke()
        self.assertFalse((self.install/'local').exists())

    def test_t18_wrong_b_document_stops_before_a(self):
        plan=copy.deepcopy(self.plan);plan['plan_id']=str(uuid.uuid4());raw=enc(plan)
        self.session.update(plan_b=ref(raw),query=dict(operation='export',area='agent_system.transfer'))
        self.docs[ref(raw)['sha256']]=b'wrong B bytes';session=enc(self.session)
        with self.assertRaises(Blocked):run(self.source,session,ref(session),self.docs,source_b_root=self.source)
        self.assertFalse((self.install/'local').exists())

    def test_t19_new_revoke_does_not_change_archive(self):
        b=self.root/'source_b';shutil.copytree(self.source,b);self.event(b,'revoke_use')
        original=self.t['n']['capture_plan'];calls=[];before={}
        def capture(*a):
            calls.append(1)
            if len(calls)==2:
                root=self.install/'local/trials'
                before.update({str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()})
            return original(*a)
        with patch.dict(self.t['n'],capture_plan=capture):value=self.with_b(b)
        root=self.install/'local/trials';after={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
        self.assertTrue(before);self.assertEqual(before,after)
        self.assertEqual(value['status'],'blocked_known_scope');self.assertFalse(value['export_allowed'])

    def test_t30_cli_without_trust_is_safe_in_any_registration_state(self):
        import subprocess,sys
        value=subprocess.run([sys.executable,str(HERE/'lab.py')],capture_output=True,text=True)
        self.assertEqual(value.returncode,2);self.assertIn('EXPLICIT_TRUSTED_CHECKOUT_ACK_REQUIRED',value.stderr)
        self.assertNotIn('Traceback',value.stderr);self.assertFalse((self.install/'local').exists())

    def test_t30_documented_lab_entry_on_prospective_installation(self):
        # No loader/child injection: the copied installed client loads only its
        # own protected copied code. The fixture approval is still synthetic.
        lab=runpy.run_path(str(self.install/'operator/ent-0018/r0001/lab.py'))
        import sys
        calls=[];previous=sys.getprofile()
        def observe(frame,event,arg):
            if event=='call' and frame.f_code.co_name=='read_set' and frame.f_code.co_filename.endswith('adapters/ent-0005/r0003/reader.py'):calls.append(1)
        sys.setprofile(observe)
        try:value=lab['run_trusted_lab'](trust_this_checkout=True,with_query=True)
        finally:sys.setprofile(previous)
        self.assertEqual(value['operator_result']['status'],'trial_checked_with_known_query_no_admission')
        self.assertEqual(len(calls),2);self.assertTrue(value['replay']['full_replay'])
        self.assertFalse(value['operator_result']['export_allowed'])
        self.assertNotIn(str(self.install),value['human_report'])

    def test_t10_export_transfer_context_is_not_generic_trial(self):
        plan=copy.deepcopy(self.plan);plan['context']=dict(operation='export',area='agent_system.transfer')
        raw=enc(plan);self.session['plan_a']=ref(raw);self.docs={ref(raw)['sha256']:raw}
        with self.assertRaises(Blocked):self.invoke()
        self.assertFalse((self.install/'local').exists())


if __name__=='__main__':unittest.main(verbosity=2)
