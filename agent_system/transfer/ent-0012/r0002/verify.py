"""Physical preparation fixtures with SYNTHETIC own approval, not real grants."""
import copy
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch
import uuid

HERE=Path(__file__).resolve().parent;BASE=HERE.parents[2]
M=runpy.run_path(str(HERE/'prepare.py'));G=M['prepare_inactive'].__globals__
ref=M['reference'];enc=M['encode'];Blocked=M['PreparationBlocked']


class PreparationTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name)
        self.registry=json.loads((BASE/'catalog/registry.json').read_bytes())
        self.decisions={p.name:p.read_bytes() for p in (BASE/'catalog/approvals').iterdir()}
        self.own=next(e for e in self.registry['entities'] if e['entity_id']=='ENT-0012')
        # Replace only fixture r2 if already registered; never alter real registry.
        self.own['revisions']=[v for v in self.own['revisions'] if v['revision']!='r0002']
        cid=self.registry['catalog_id'];u=str(uuid.uuid4());arts=[]
        for name in M['OWN']:
            p=M['HERE']+name;arts.append(dict(path=p,**ref((BASE/p).read_bytes()),role='normative'))
        d=dict(schema_version='1',decision_id=u,decision_type='approve_revision',subject=M['_subject'](cid,('ENT-0012','r0002')),
               artifacts=[{k:a[k] for k in ['path','sha256','size_bytes']} for a in arts],actor_role='owner',recorded_by='agent',
               decision_date='2026-10-07',statement_form='summary',statement='SYNTHETIC fixture approval ONLY, not actual owner approval.',basis='SYNTHETIC disposable test.')
        raw=enc(d);self.decisions[u+'.json']=raw
        self.record=dict(revision='r0002',title='SYNTHETIC fixture only',kind='protocol',scopes=list(self.own['revisions'][0]['scopes']),artifacts=arts,
                         relations=[dict(type='depends_on',target=M['_subject'](cid,k)) for k in M['DEPENDENCIES']]+[dict(type='supersedes',target=M['_subject'](cid,('ENT-0012','r0001')))],
                         approval=dict(status='approved',reference=dict(path='catalog/approvals/'+u+'.json',sha256=ref(raw)['sha256'])),provenance=dict(summary='SYNTHETIC not actual implementation approval.'))
        self.own['revisions'].append(self.record);self.sync()

    def sync(self):
        raw=enc(self.registry);self.maps={'catalog/approvals/'+p:b for p,b in self.decisions.items()}
        self.request,self.plan=M['make_packet'](raw,self.maps)
        self.plan_value=json.loads(self.plan)
        blobs=dict(self.maps);blobs['catalog/registry.json']=raw
        for a in self.plan_value['artifacts']:blobs[a['path']]=(BASE/a['path']).read_bytes()
        for name,data in blobs.items():
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)

    def run_prep(self):
        self.result=M['prepare_inactive'](self.root,self.request,ref(self.request),self.plan,ref(self.plan),acknowledge_inactive_only=True)
        return self.result

    def flags(self,manifest):
        for k,v in M['_flags']().items():self.assertEqual(type(manifest[k]),type(v));self.assertEqual(manifest[k],v)

    def change_plan(self,fn):
        plan=json.loads(self.plan);fn(plan);self.plan=enc(plan)
        req=json.loads(self.request);req['plan']=ref(self.plan);self.request=enc(req)

    def test_positive_exact_inactive_closure_not_payload_kit(self):
        r=self.run_prep();self.assertEqual(r['status'],'prepared_inactive');v=json.loads(r['manifest_bytes']);self.flags(v)
        self.assertEqual({a['path'] for a in v['observed_artifacts']},{a['path'] for a in self.plan_value['artifacts']})
        self.assertEqual(len(v['known_decisions']),len(self.maps));self.assertEqual(v['composition_coverage'],'not_evaluated')
        self.assertNotIn('capture',r);self.assertNotIn('payloads',r)
        self.assertEqual(ref(r['documents'][v['execution']['sha256']]),v['execution'])
        self.assertEqual(len(r['documents']),7)
        self.assertNotIn(str(self.root),r['manifest_bytes'].decode())

    def test_exact_true_and_external_pins_before_tools(self):
        for ack in (False,1,'true',None):
            with patch.dict(G,_tools=lambda:self.fail('tools called')),self.assertRaises(Blocked):
                M['prepare_inactive'](self.root,self.request,ref(self.request),self.plan,ref(self.plan),acknowledge_inactive_only=ack)
        with self.assertRaises(Blocked):M['prepare_inactive'](self.root,self.request,ref(b'wrong'),self.plan,ref(self.plan),acknowledge_inactive_only=True)

    def test_request_schema_unknown_ready_blank_purpose(self):
        original=self.request
        for changes in [dict(ready=True),dict(purpose=' '),dict(request_id='../x'),dict(export_allowed=True)]:
            req=json.loads(original);req.update(changes);self.request=enc(req)
            with self.assertRaises(Blocked):self.run_prep()

    def test_request_plan_procedure_prompt_seed_pins(self):
        original=self.request
        for field in ['plan','procedure','prompt','seed_candidate']:
            req=json.loads(original);req[field]=ref(b'wrong');self.request=enc(req)
            with self.assertRaises(Blocked):self.run_prep()

    def test_context_duplicate_roots_and_missing_own(self):
        original=self.plan;request=self.request
        for fn in [lambda p:p.update(context=dict(operation='validate',area='agent_system.transfer')),
                   lambda p:p['selection'].append(p['selection'][0]),lambda p:p['selection'][0].update(revision='r0001')]:
            self.plan=original;self.request=request;self.change_plan(fn)
            with self.assertRaises(Blocked):self.run_prep()

    def test_missing_own_component_preflight(self):
        self.change_plan(lambda p:p['artifacts'].pop(next(i for i,a in enumerate(p['artifacts']) if a['path']==M['HERE']+'prompt.md')))
        with self.assertRaises(Blocked):self.run_prep()

    def test_private_project_path_rejected_before_capture(self):
        for name in ['local/secret.json','../outside','research/private.md','ventoy-partition/build.txt','.git/config']:
            oldp,oldr=self.plan,self.request
            self.change_plan(lambda p:p['artifacts'].append(dict(path=name,**ref(b'private'))))
            with self.assertRaises(Blocked):self.run_prep()
            self.plan,self.request=oldp,oldr

    def test_private_unplanned_source_is_not_collected(self):
        p=self.root/'local/permission-authority/private';p.parent.mkdir(parents=True);p.write_text('PRIVATE_NOT_FOR_COLLECTION')
        r=self.run_prep();self.assertEqual(r['status'],'prepared_inactive')
        self.assertNotIn(b'PRIVATE_NOT_FOR_COLLECTION',b''.join(r['documents'].values()))

    def test_source_mutation_and_symlink_fail(self):
        p=self.root/(M['HERE']+'prompt.md');raw=p.read_bytes();p.write_bytes(raw+b'changed')
        self.assertNotEqual(self.run_prep()['status'],'prepared_inactive')
        p.unlink();p.symlink_to(self.root/'catalog/registry.json')
        self.assertNotEqual(self.run_prep()['status'],'prepared_inactive')

    def test_extra_declared_public_artifact_not_silently_admitted(self):
        name='protocols/not-selected.txt';raw=b'not in closure\n';p=self.root/name;p.parent.mkdir(exist_ok=True);p.write_bytes(raw)
        self.change_plan(lambda p:p['artifacts'].append(dict(path=name,**ref(raw))))
        with self.assertRaises(Blocked):self.run_prep()

    def test_known_negative_relevant_to_export_not_filtered(self):
        d=json.loads(next(iter(self.maps.values())))
        # Use exact own composition for an actual legacy restrict-use event shape.
        approval=self.record['approval']['reference']['path'].split('/')[-1];d=json.loads(self.decisions[approval])
        d.update(decision_id=str(uuid.uuid4()),decision_type='restrict_use',reason='SYNTHETIC test restriction',scope=dict(operations=['export'],areas=['agent_system.transfer']))
        self.decisions[d['decision_id']+'.json']=enc(d);self.sync()
        r=self.run_prep();self.assertEqual(r['status'],'blocked_known_scope');self.assertIsNone(r['manifest_bytes'])

    def test_unknown_extra_ledger_file_not_ignored(self):
        (self.root/'catalog/approvals/unexpected.json').write_bytes(b'{}\n')
        r=self.run_prep();self.assertNotEqual(r['status'],'prepared_inactive');self.assertIsNone(r['manifest_bytes'])

    def test_missing_ledger_file_blocks(self):
        (self.root/next(iter(self.maps))).unlink()
        self.assertNotEqual(self.run_prep()['status'],'prepared_inactive')

    def test_all_seed_rows_remain_historical_open(self):
        seed=json.loads((BASE/M['SEED']).read_bytes());v=json.loads(self.run_prep()['manifest_bytes'])
        self.assertEqual(v['historical_rows'],seed['coverage']+seed['conditions']);self.assertEqual(len(v['gap_to_check']),25)
        self.assertTrue(all(r['status']=='open_not_discharged' for r in v['gap_to_check']))
        self.assertEqual(v['gap_basis'],'historical_seed_not_current_coverage')

    def test_changed_profile_dependency_record_rejected(self):
        self.record['relations'].pop(0);self.sync()
        # The entity checker may fail first, otherwise the own exact profile record gate fails.
        try:r=self.run_prep()
        except Blocked:return
        self.assertNotEqual(r['status'],'prepared_inactive')

    def test_capture_once_same_capture_descriptor(self):
        tools=list(M['_tools']());entry=tools[0];original=entry['capture_plan'];calls=[]
        def wrapped(*a,**k):calls.append(1);return original(*a,**k)
        entry['capture_plan']=wrapped
        with patch.dict(G,_tools=lambda:tuple(tools)):self.run_prep()
        self.assertEqual(calls,[1])

    def test_platform_and_installed_pin_failure(self):
        with patch.object(G['platform'],'system',return_value='Other'),self.assertRaises(Blocked):self.run_prep()
        p=next(iter(G['PINS']));pins=copy.deepcopy(G['PINS']);pins[p]['sha256']='0'*64
        with patch.dict(G,PINS=pins),self.assertRaises(Blocked):self.run_prep()

    def test_private_evidence_metadata_only_physical_readback(self):
        r=self.run_prep();tools=list(M['_tools']());e=tools[-1]
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);stage,reader=e['_tools']()
        with patch.dict(e['EvidenceStore'].__enter__.__globals__,BASE=Path(t.name),_tools=lambda:(stage,reader)):
            with patch.dict(G,_tools=lambda:tuple(tools)):
                receipt=M['persist_preparation'](r,trust_private_namespace=True)
            self.flags(receipt);claim=receipt['evidence'];report=e['verify_evidence'](claim['run_id'],claim['index'])
            self.assertEqual(report['status'],'consistent_private_evidence')
            idx,_=e['_read_evidence'](claim['run_id'],claim['index'],with_capture=True)
        self.assertEqual(idx['metadata']['manifest'],ref(r['manifest_bytes']))
        body=[p.read_bytes() for p in (Path(t.name)/'local/operator-runs'/claim['run_id']/'objects').iterdir()]
        self.assertNotIn((BASE/(M['HERE']+'prompt.md')).read_bytes(),body)
        self.assertEqual(set(body),set(r['documents'].values()))

    def test_bad_persist_ack_and_forged_action_flag(self):
        r=self.run_prep()
        with self.assertRaises(Blocked):M['persist_preparation'](r)
        value=json.loads(r['manifest_bytes']);value['export_allowed']=True;r['manifest_bytes']=enc(value)
        with self.assertRaises(Blocked):M['persist_preparation'](r,trust_private_namespace=True)

    def test_installed_collector_ack_before_source(self):
        with patch.dict(G,_tools=lambda:self.fail('tools called')),self.assertRaises(Blocked):M['installed_packet']()

    def test_document_and_plan_budget_preflight(self):
        with self.assertRaises(Blocked):M['prepare_inactive'](self.root,b'x'*(M['LIMIT']+1),ref(b'x'),self.plan,ref(self.plan),acknowledge_inactive_only=True)
        self.change_plan(lambda p:p['artifacts'][0].update(size_bytes=64*1024*1024))
        with self.assertRaises(Blocked):self.run_prep()


    def test_native_request_size_and_duplicate_json_closed(self):
        req=json.loads(self.request);req['plan']['size_bytes']=float(req['plan']['size_bytes']);self.request=enc(req)
        with self.assertRaises(Blocked):self.run_prep()
        self.request=b'{"schema_version":"1","schema_version":"1"}\n'
        with self.assertRaises(Blocked):self.run_prep()

    def test_collector_observes_extra_ledger_and_rejects_symlink(self):
        tools=M['_tools']();p=self.root/'catalog/approvals'/('f'*8+'-'+ 'f'*4+'-'+ 'f'*4+'-'+ 'f'*4+'-'+ 'f'*12+'.json')
        p.write_bytes(b'{}\n')
        with patch.dict(G,BASE=self.root,_tools=lambda:tools):
            request,plan=M['installed_packet'](trust_installed_namespace=True)
            self.assertEqual(len(json.loads(plan)['decisions']),len(self.maps)+1)
            p.unlink();p.symlink_to(self.root/'catalog/registry.json')
            with self.assertRaises(Blocked):M['installed_packet'](trust_installed_namespace=True)

    def test_evidence_write_fault_retains_partial_namespace(self):
        r=self.run_prep();tools=list(M['_tools']());e=tools[-1];stage,reader=e['_tools']()
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);base=Path(t.name)
        def bad(*a,**k):raise OSError('SYNTHETIC write fault')
        with patch.dict(e['EvidenceStore'].__enter__.__globals__,BASE=base,_tools=lambda:(stage,reader)):
            with patch.dict(stage,_write_file=bad),patch.dict(G,_tools=lambda:tuple(tools)),self.assertRaises(Blocked):
                M['persist_preparation'](r,trust_private_namespace=True)
        self.assertTrue((base/'local/operator-runs').exists())
        self.assertEqual(len(list((base/'local/operator-runs').iterdir())),1)


    def test_persist_rejects_extra_raw_payload_and_missing_metadata(self):
        r=self.run_prep();raw=(BASE/(M['HERE']+'prompt.md')).read_bytes();r['documents'][ref(raw)['sha256']]=raw
        with self.assertRaises(Blocked):M['persist_preparation'](r,trust_private_namespace=True)
        del r['documents'][ref(raw)['sha256']];v=json.loads(r['manifest_bytes']);del r['documents'][v['execution']['sha256']]
        with self.assertRaises(Blocked):M['persist_preparation'](r,trust_private_namespace=True)


if __name__=='__main__':unittest.main(verbosity=2)
