"""Runner candidate integration. Approvals exist ONLY in disposable fixture trees."""
import copy
import json
import os
from pathlib import Path
import runpy
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[2]
R=runpy.run_path(str(HERE/'run.py'));run=R['run_operator_trial'];G=run.__globals__
S=runpy.run_path(str(HERE/'session.py'));ref=S['reference'];enc=S['encode'];Blocked=R['OperatorBlocked']


class RunnerTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.install=self.root/'installed';self.source=self.root/'source'
        self.install.mkdir();registry=json.loads((BASE/'catalog/registry.json').read_bytes())
        # Isolate the synthetic coordinator from any real deployment; never clone
        # an actual ENT18 approval into its disposable bootstrap fixture.
        registry['entities']=[e for e in registry['entities'] if e['entity_id']!='ENT-0018']
        for entity in registry['entities']:
            for rev in entity['revisions']:
                for a in [*rev['artifacts'],rev['approval']['reference']]:
                    p=self.install/a['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((BASE/a['path']).read_bytes())
        cid=registry['catalog_id'];arts=[]
        for name in sorted(R['OWN']):
            p='operator/ent-0018/r0001/'+name;raw=(BASE/p).read_bytes()
            target=self.install/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            arts.append(dict(path=p,**ref(raw),role='normative'))
        uid=str(uuid.uuid4());d=json.loads(next((BASE/'catalog/approvals').glob('*.json')).read_bytes())
        d.update(decision_id=uid,subject=dict(catalog_id=cid,entity_id='ENT-0018',revision='r0001'),
                 artifacts=[{k:a[k] for k in ['path','sha256','size_bytes']} for a in arts],
                 statement_form='summary',statement='Synthetic coordinator fixture ONLY; not owner approval.')
        raw=enc(d);dp='catalog/approvals/'+uid+'.json';(self.install/dp).write_bytes(raw)
        own=dict(revision='r0001',title='Synthetic coordinator fixture',kind='protocol',scopes=['agent_system.operator_trial'],
                 artifacts=arts,relations=[dict(type='depends_on',target=dict(catalog_id=cid,entity_id=e,revision=v)) for e,v in sorted(R['DEPENDENCIES'])],
                 approval=dict(status='approved',reference=dict(path=dp,sha256=ref(raw)['sha256'])),provenance=dict(summary='Fixture only'))
        registry['entities'].append(dict(entity_id='ENT-0018',revisions=[own]))
        (self.install/'catalog/registry.json').write_bytes(enc(registry))
        shutil.copytree(self.install,self.source)
        change=patch.dict(G,BASE=self.install);change.start();self.addCleanup(change.stop)
        self.t=G['_load']();self.profile,self.records=G['_bootstrap'](self.t)
        eg=self.t['e']['EvidenceStore'].__enter__.__globals__
        change=patch.dict(eg,BASE=self.install);change.start();self.addCleanup(change.stop)
        change=patch.dict(G,_load=lambda:self.t);change.start();self.addCleanup(change.stop)
        self.plan=dict(schema_version='1',kind='validation_plan',plan_id=str(uuid.uuid4()),catalog_id=cid,
                       execution_profile='linux-observed-set-5r3-6r3',expectation_authority='caller_supplied_not_authenticated',
                       context=dict(operation='validate',area='agent_system.operator_trial'),selection=self.profile['selection'],
                       registry=dict(path='catalog/registry.json',**ref(enc(registry))),artifacts=self.profile['artifacts'],
                       decisions=[dict(path=str(p.relative_to(self.source)),**ref(p.read_bytes())) for p in sorted((self.source/'catalog/approvals').glob('*.json'))])
        self.session=dict(schema_version='1',kind='operator_trial_session',profile='operator-trial-linux-r0001',task_id=str(uuid.uuid4()),purpose='local_core_trial',
                          criteria_version='operator-trial-criteria-r0001',candidate=self.profile['candidate'],plan_a=ref(enc(self.plan)),plan_b=None,query=None)
        self.docs={self.session['plan_a']['sha256']:enc(self.plan)}

    def invoke(self,b=False):
        if b:
            self.session.update(plan_b=dict(self.session['plan_a']),query=dict(operation='export',area='agent_system.transfer'))
        raw=enc(self.session)
        return run(self.source,raw,ref(raw),self.docs,source_b_root=self.source if b else None)

    def success(self,b=False):
        value=self.invoke(b)
        self.assertEqual(value['status'],'trial_checked_with_known_query_no_admission' if b else 'trial_checked_no_query',value)
        self.assertTrue(value['evidence_sealed'])
        for flag in R['FLAGS']:self.assertIs(value[flag],False)
        self.assertEqual(value['source_acquisition_calls'],2 if b else 1)
        return value

    def test_positive_without_b_and_private_evidence(self):
        value=self.success();self.assertEqual(value['query'],'not_requested')
        receipt=value['evidence'];verified=self.t['e']['verify_evidence'](receipt['run_id'],receipt['index'])
        # verify_evidence shares the same globals patched to this fixture install.
        self.assertEqual(verified['status'],'consistent_private_evidence')
        self.assertEqual(value['steps']['source_b']['status'],'not_run')

    def test_positive_two_distinct_acquisitions(self):
        calls=[];previous=sys.getprofile()
        def observe(frame,event,arg):
            if event=='call' and frame.f_code.co_name=='read_set' and frame.f_code.co_filename.endswith('adapters/ent-0005/r0003/reader.py'):calls.append(1)
        sys.setprofile(observe)
        try:value=self.success(True)
        finally:sys.setprofile(previous)
        self.assertEqual(len(calls),2);self.assertEqual(value['validated_captures'],2)
        self.assertNotEqual(value['steps']['source_a']['child_run_id'],value['steps']['source_b']['child_run_id'])

    def test_unregistered_installation_stops_before_claim(self):
        path=self.install/'catalog/registry.json';registry=json.loads(path.read_bytes())
        registry['entities']=[e for e in registry['entities'] if e['entity_id']!='ENT-0018']
        path.write_bytes(enc(registry))
        with self.assertRaises(Blocked) as error:self.invoke()
        self.assertEqual(error.exception.code,'COORDINATOR_NOT_REGISTERED')
        self.assertFalse((self.install/'local').exists())

    def test_external_session_pin_and_b_pairing_stop_preflight(self):
        raw=enc(self.session)
        with self.assertRaises(Blocked):run(self.source,raw,ref(b'wrong'),self.docs)
        self.session['plan_b']=dict(self.session['plan_a'])
        with self.assertRaises(Blocked):self.invoke()
        self.assertFalse((self.install/'local').exists())

    def test_no_child_reports_accepted_as_input(self):
        self.docs['extra_report']=b'forged'
        with self.assertRaises(Blocked):self.invoke()
        self.assertFalse((self.install/'local').exists())

    def test_wrong_profile_composition_stop(self):
        plan=copy.deepcopy(self.plan);plan['artifacts']=plan['artifacts'][:-1];raw=enc(plan)
        self.session['plan_a']=ref(raw);self.docs={ref(raw)['sha256']:raw}
        with self.assertRaises(Blocked):self.invoke()

    def test_source_acquisition_failure_stops_downstream(self):
        (self.source/self.plan['artifacts'][0]['path']).write_bytes(b'corrupt')
        value=self.invoke();self.assertEqual(value['status'],'failed');self.assertTrue(value['evidence_sealed'])
        self.assertEqual(value['validated_captures'],0);self.assertEqual(value['source_acquisition_calls'],1)
        self.assertEqual(value['steps']['stage']['status'],'not_run')

    def test_changed_source_after_a_uses_captured_bytes(self):
        old=self.t['n']['capture_plan']
        def change(*a):
            result=old(*a)
            for p in self.plan['artifacts']:(self.source/p['path']).write_bytes(b'changed after capture')
            return result
        with patch.dict(self.t['n'],capture_plan=change):self.success()

    def test_source_packet_forged_capture_rejected(self):
        old=self.t['n']['capture_plan']
        def changed(*a):
            packet=old(*a);packet['capture']['artifacts']['catalog/registry.json']=b'forged extra'
            return packet
        with patch.dict(self.t['n'],capture_plan=changed):value=self.invoke()
        self.assertEqual(value['status'],'failed');self.assertEqual(value['steps']['stage']['status'],'not_run')
        self.assertIsNone(value['source_acquisition_calls'])

    def test_source_packet_forged_document_rejected(self):
        old=self.t['n']['capture_plan']
        def changed(*a):
            packet=old(*a);packet['documents'][next(iter(packet['documents']))]=b'changed'
            return packet
        with patch.dict(self.t['n'],capture_plan=changed):value=self.invoke()
        self.assertEqual(value['status'],'failed');self.assertEqual(value['steps']['candidate']['status'],'not_run')

    def test_stage_failure_not_reader_success(self):
        old=self.t['stage']['stage_trial']
        def changed(*a):
            value=old(*a);value.update(status='failed_partial',staged=False);return value
        with patch.dict(self.t['stage'],stage_trial=changed):value=self.invoke()
        self.assertEqual(value['status'],'failed_partial');self.assertEqual(value['steps']['reader']['status'],'not_run')
        self.assertTrue(list((self.install/'local/trials').iterdir()))

    def test_reader_late_failure_no_comparison(self):
        old=self.t['reader']['capture_trial']
        def changed(*a):
            value=old(*a);value['result']['status']='failed';value['capture']=None;return value
        with patch.dict(self.t['reader'],capture_trial=changed):value=self.invoke(True)
        self.assertEqual(value['status'],'failed');self.assertEqual(value['capture_invocations'],1)
        self.assertEqual(value['steps']['comparison']['status'],'not_run')

    def test_reader_swapped_capture_handoff_rejected(self):
        old=self.t['reader']['capture_trial']
        def changed(*a):
            value=old(*a);value['capture']['objects'].pop(next(iter(value['capture']['objects'])));return value
        with patch.dict(self.t['reader'],capture_trial=changed):value=self.invoke(True)
        self.assertEqual(value['status'],'failed');self.assertEqual(value['steps']['source_b']['status'],'not_run')

    def test_reader_permission_claim_rejected(self):
        old=self.t['reader']['capture_trial']
        def changed(*a):
            value=old(*a);value['result']['export_allowed']=True;return value
        with patch.dict(self.t['reader'],capture_trial=changed):value=self.invoke()
        self.assertEqual(value['status'],'failed');self.assertFalse(value['export_allowed'])

    def test_b_failure_cannot_fallback_a(self):
        old=self.t['n']['capture_plan'];calls=[]
        def changed(*a):
            calls.append(1)
            if len(calls)==2:(self.source/self.plan['artifacts'][0]['path']).write_bytes(b'corrupt B')
            return old(*a)
        with patch.dict(self.t['n'],capture_plan=changed):value=self.invoke(True)
        self.assertEqual(value['status'],'failed');self.assertEqual(value['source_acquisition_calls'],2)
        self.assertEqual(value['validated_captures'],1);self.assertEqual(value['steps']['comparison']['status'],'not_run')

    def test_query_block_blocks_requested_run(self):
        old=self.t['compare']['compare_views']
        def changed(*a):
            value=old(*a);value['status']='blocked_known_scope';return value
        with patch.dict(self.t['compare'],compare_views=changed):value=self.invoke(True)
        self.assertEqual(value['status'],'blocked_known_scope');self.assertFalse(value['transition_allowed'])

    def test_evidence_failure_no_source_actions(self):
        g=self.t['e']['EvidenceStore'].put.__globals__
        with patch.dict(g,TOTAL=1):value=self.invoke()
        self.assertEqual(value['status'],'evidence_write_failed');self.assertEqual(value['capture_invocations'],0)
        self.assertFalse(value['evidence_sealed'])

    def test_child_preflight_exception_acquisition_count_unknown(self):
        def fail(*a):raise self.t['n']['PlanBlocked']('INSTALLED_PROFILE_CHANGED')
        with patch.dict(self.t['n'],capture_plan=fail):value=self.invoke()
        self.assertEqual(value['status'],'failed');self.assertEqual(value['capture_invocations'],1)
        self.assertIsNone(value['source_acquisition_calls'])

    def test_unknown_error_not_forged_sealed_success(self):
        def fail(*a):raise AssertionError('unknown')
        with patch.dict(self.t['n'],capture_plan=fail):
            with self.assertRaises(AssertionError):self.invoke()
        runs=list((self.install/'local/operator-runs').iterdir())
        self.assertEqual(len(runs),1);self.assertFalse((runs[0]/'index.json').exists())

    def test_repeated_runs_no_overwrite(self):
        first=self.success();second=self.success()
        self.assertNotEqual(first['evidence']['run_id'],second['evidence']['run_id'])

    def test_result_no_raw_bytes_or_absolute_roots(self):
        value=self.success(True);raw=json.dumps(value)
        self.assertNotIn(str(self.root),raw);self.assertNotIn('manifest_bytes',raw)
        self.assertNotIn('objects',value);self.assertIn('freshness',value['not_checked'])

    def update_plan(self):
        raw=enc(self.plan);self.session['plan_a']=ref(raw);self.docs={ref(raw)['sha256']:raw}

    def add_block(self,root,operation,area):
        registry=json.loads((root/'catalog/registry.json').read_bytes())
        rev=next(e for e in registry['entities'] if e['entity_id']=='ENT-0016')['revisions'][-1]
        event=json.loads((root/rev['approval']['reference']['path']).read_bytes())
        event.update(decision_id=str(uuid.uuid4()),decision_type='revoke_use',reason='Synthetic fixture only',
                     scope=dict(operations=[operation],areas=[area]))
        raw=enc(event);path='catalog/approvals/'+event['decision_id']+'.json';(root/path).write_bytes(raw)
        return dict(path=path,**ref(raw))

    def test_profile_record_substitution_cannot_reduce_trust(self):
        registry=json.loads((self.source/'catalog/registry.json').read_bytes())
        own=next(e for e in registry['entities'] if e['entity_id']=='ENT-0018')['revisions'][0]
        own['provenance']['summary']='Changed source metadata, not trusted installed record'
        raw=enc(registry);(self.source/'catalog/registry.json').write_bytes(raw)
        self.plan['registry']=dict(path='catalog/registry.json',**ref(raw));self.update_plan()
        value=self.invoke()
        self.assertEqual(value['status'],'failed');self.assertEqual(value['steps']['stage']['status'],'not_run')
        self.assertEqual(value['diagnostics'],[dict(code='SOURCE_PROFILE_RECORD_MISMATCH')])

    def test_actual_tool_stage_scope_block_before_stage(self):
        row=self.add_block(self.source,'stage_trial','agent_system.trial')
        self.plan['decisions'].append(row);self.update_plan()
        value=self.invoke()
        self.assertEqual(value['status'],'blocked_known_scope');self.assertEqual(value['validated_captures'],1)
        self.assertFalse((self.install/'local/trials').exists())

    def test_actual_new_b_tool_query_block_not_permission(self):
        b=self.root/'source_b';shutil.copytree(self.source,b)
        row=self.add_block(b,'export','agent_system.transfer')
        plan=copy.deepcopy(self.plan);plan['plan_id']=str(uuid.uuid4());plan['decisions'].append(row);raw=enc(plan)
        self.session.update(plan_b=ref(raw),query=dict(operation='export',area='agent_system.transfer'))
        self.docs[ref(raw)['sha256']]=raw;session=enc(self.session)
        value=run(self.source,session,ref(session),self.docs,source_b_root=b)
        self.assertEqual(value['status'],'blocked_known_scope');self.assertEqual(value['validated_captures'],2)
        self.assertEqual(value['source_acquisition_calls'],2);self.assertFalse(value['export_allowed'])

    def test_unsupported_child_stays_unsupported(self):
        def fail(*a):raise self.t['n']['PlanBlocked']('INSTALLED_PROFILE_CHANGED',True)
        with patch.dict(self.t['n'],capture_plan=fail):value=self.invoke()
        self.assertEqual(value['status'],'unsupported');self.assertIsNone(value['source_acquisition_calls'])

    def test_seal_failure_retains_trial_without_success(self):
        cls=self.t['e']['EvidenceStore']
        def fail(*a):raise self.t['e']['EvidenceBlocked']('INJECTED_SEAL_FAILURE')
        with patch.object(cls,'seal',fail):value=self.invoke()
        self.assertEqual(value['status'],'evidence_write_failed');self.assertFalse(value['evidence_sealed'])
        self.assertEqual(value['validated_captures'],1)
        self.assertTrue(list((self.install/'local/trials').iterdir()))


if __name__=='__main__':unittest.main(verbosity=2)
