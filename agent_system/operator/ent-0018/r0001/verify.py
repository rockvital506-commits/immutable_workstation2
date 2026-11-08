"""I3 foundation tests only; no coordinator, permissions, or behavior proof."""
import copy
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch
import uuid

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[2]
S=runpy.run_path(str(HERE/'session.py'));E=runpy.run_path(str(HERE/'evidence.py'))
ref=S['reference'];enc=S['encode'];SessionBlocked=S['SessionBlocked'];EvidenceBlocked=E['EvidenceBlocked']
F=runpy.run_path(str(BASE/'validation/ent-0009/r0002/verify.py'))


class SessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.tools=S['_tools']()

    def setUp(self):
        fixture=F['PlanExecutionTests']();fixture.setUp();self.addCleanup(fixture.doCleanups)
        self.plan=copy.deepcopy(fixture.plan)
        self.plan['context']=dict(operation='validate',area='agent_system.operator_trial')
        self.profile=dict(catalog_id=self.plan['catalog_id'],selection=copy.deepcopy(self.plan['selection']),
                          artifacts=copy.deepcopy(self.plan['artifacts']),candidate=ref(b'fixed candidate'))
        self.session=dict(schema_version='1',kind='operator_trial_session',profile='operator-trial-linux-r0001',
                          task_id=str(uuid.uuid4()),purpose='local_core_trial',criteria_version='operator-trial-criteria-r0001',
                          candidate=dict(self.profile['candidate']),plan_a=ref(enc(self.plan)),plan_b=None,query=None)
        self.documents={self.session['plan_a']['sha256']:enc(self.plan)}
        loader=patch.dict(S['validate_session'].__globals__,_tools=lambda:self.tools)
        loader.start();self.addCleanup(loader.stop)

    def check(self,b=False):
        raw=enc(self.session)
        return S['validate_session'](raw,ref(raw),self.documents,self.profile,has_source_b=b)

    def test_valid_no_b(self):
        value=self.check();self.assertEqual(len(value['plans']),1);self.assertIsNone(value['session']['query'])

    def test_valid_b_same_plan_not_fallback(self):
        self.session.update(plan_b=dict(self.session['plan_a']),query=dict(operation='export',area='agent_system.transfer'))
        self.assertEqual(len(self.check(True)['plans']),2)

    def test_two_distinct_plans(self):
        plan=copy.deepcopy(self.plan);plan['plan_id']=str(uuid.uuid4());raw=enc(plan)
        self.documents[ref(raw)['sha256']]=raw
        self.session.update(plan_b=ref(raw),query=dict(operation='validate',area='agent_system.operator_trial'))
        self.assertNotEqual(*[p['plan_id'] for p in self.check(True)['plans']])

    def test_external_session_pin_required(self):
        raw=enc(self.session)
        with self.assertRaises(SessionBlocked):S['validate_session'](raw,ref(b'other'),self.documents,self.profile,has_source_b=False)

    def test_schema_rejections(self):
        for field,value in [('extra','untrusted'),('purpose','arbitrary'),('criteria_version','latest'),('task_id','../task'),('profile','latest'),('schema_version',2)]:
            with self.subTest(field=field):
                bad=dict(self.session);bad[field]=value
                with self.assertRaises(SessionBlocked):
                    raw=enc(bad);S['validate_session'](raw,ref(raw),self.documents,self.profile,has_source_b=False)

    def test_candidate_reference_and_native_size(self):
        for value in [dict(self.profile['candidate'],sha256='0'*64),dict(self.profile['candidate'],size_bytes=float(self.profile['candidate']['size_bytes']))]:
            with self.subTest(value=value):
                self.session['candidate']=value
                with self.assertRaises(SessionBlocked):self.check()

    def test_missing_or_extra_documents(self):
        for docs in [{},dict(self.documents,**{'0'*64:b'extra'})]:
            with self.subTest(docs=list(docs)):
                self.documents=docs
                with self.assertRaises(SessionBlocked):self.check()

    def test_wrong_document_bytes(self):
        self.documents[self.session['plan_a']['sha256']]=b'wrong'
        with self.assertRaises(SessionBlocked):self.check()

    def test_b_pairing(self):
        with self.assertRaises(SessionBlocked):self.check(True)
        self.session['plan_b']=dict(self.session['plan_a'])
        with self.assertRaises(SessionBlocked):self.check(False)
        self.session['query']=dict(operation='*',area='local')
        with self.assertRaises(SessionBlocked):self.check(True)

    def test_query_without_b(self):
        self.session['query']=dict(operation='export',area='local')
        with self.assertRaises(SessionBlocked):self.check()

    def test_profile_mismatch_before_any_source_read(self):
        for field,value in [('context',dict(operation='export',area='local')),('selection',[]),('artifacts',[])]:
            with self.subTest(field=field):
                plan=copy.deepcopy(self.plan);plan[field]=value;raw=enc(plan)
                self.session['plan_a']=ref(raw);self.documents={ref(raw)['sha256']:raw}
                with self.assertRaises(SessionBlocked):self.check()

    def test_plan_duplicate_path_and_non_native_size(self):
        for change in ['duplicate','float']:
            with self.subTest(change=change):
                plan=copy.deepcopy(self.plan)
                if change=='duplicate':plan['artifacts'].append(copy.deepcopy(plan['registry']))
                else:plan['registry']['size_bytes']=float(plan['registry']['size_bytes'])
                raw=enc(plan);self.session['plan_a']=ref(raw);self.documents={ref(raw)['sha256']:raw}
                with self.assertRaises(SessionBlocked):self.check()

    def test_ambiguous_or_noncanonical_session(self):
        raw=enc(self.session)
        for bad in [raw+b'\n',raw.rstrip(b'\n'),raw.replace(b'{',b'{"kind":"duplicate",',1),raw.replace(b'\n',b'\r\n')]:
            with self.subTest(size=len(bad)):
                with self.assertRaises(SessionBlocked):S['validate_session'](bad,ref(bad),self.documents,self.profile,has_source_b=False)

    def test_owned_mappings(self):
        value=self.check();value['documents'].clear();value['session']['candidate'].clear()
        self.assertTrue(self.documents);self.assertTrue(self.session['candidate'])

    def test_no_acquisition_or_filesystem_write(self):
        with patch('os.open',side_effect=AssertionError('source or output fd')):
            self.check()

    def test_installed_pins_changed(self):
        loader=S['_tools'];g=loader.__globals__
        one=next(iter(g['PINS']));pins={one:dict(g['PINS'][one],sha256='0'*64)}
        with patch.dict(g,PINS=pins):
            with self.assertRaises(SessionBlocked):loader()


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.tools=E['_tools']()

    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name)
        g=E['EvidenceStore'].__enter__.__globals__
        patched=patch.dict(g,BASE=self.root,_tools=lambda:self.tools);patched.start();self.addCleanup(patched.stop)

    def make(self):
        store=E['EvidenceStore']();store.__enter__();self.addCleanup(store.__exit__)
        return store

    def test_seal_readonly_check(self):
        store=self.make();store.put(b'input');receipt=store.seal(dict(status='foundation_only'))
        result=E['verify_evidence'](receipt['run_id'],receipt['index'])
        self.assertEqual(result['status'],'consistent_private_evidence');self.assertFalse(result['transition_allowed'])

    def test_private_permissions(self):
        store=self.make();r=store.put(b'data');store.seal({});root=self.root/'local/operator-runs'/store.run_id
        for p in [root,root/'objects']:self.assertEqual(p.stat().st_mode&0o777,0o700)
        for p in [root/'index.json',root/'objects'/r['sha256']]:self.assertEqual(p.stat().st_mode&0o777,0o600)

    def test_dedup_counts_actual_bytes(self):
        store=self.make();r=store.put(b'abcd');self.assertEqual(store.put(b'abcd'),r)
        self.assertEqual(store.bytes,4);self.assertEqual(len(store.objects),1)
        with patch.dict(E['EvidenceStore'].put.__globals__,TOTAL=4):self.assertEqual(store.put(b'abcd'),r)

    def test_new_run_per_claim(self):self.assertNotEqual(self.make().run_id,self.make().run_id)

    def test_no_resume_or_overwrite(self):
        store=self.make();store.put(b'keep')
        g=E['EvidenceStore'].__init__.__globals__
        with patch.object(g['uuid'],'uuid4',return_value=uuid.UUID(store.run_id)):
            with self.assertRaises(EvidenceBlocked):E['EvidenceStore']().__enter__()
        self.assertTrue((self.root/'local/operator-runs'/store.run_id).is_dir())

    def test_write_after_seal_rejected(self):
        store=self.make();store.seal({})
        with self.assertRaises(EvidenceBlocked):store.put(b'later')

    def test_byte_and_file_limits_poison_store(self):
        for cap in [dict(TOTAL=2),dict(FILES=1),dict(LIMIT=2)]:
            with self.subTest(cap=cap):
                store=self.make()
                with patch.dict(E['EvidenceStore'].put.__globals__,**cap):
                    with self.assertRaises(EvidenceBlocked):store.put(b'too long')
                with self.assertRaises(EvidenceBlocked):store.seal({})

    def test_budget_includes_index(self):
        store=self.make();store.put(b'x')
        with patch.dict(E['EvidenceStore'].seal.__globals__,TOTAL=1):
            with self.assertRaises(EvidenceBlocked):store.seal({})
        self.assertFalse((self.root/'local/operator-runs'/store.run_id/'index.json').exists())

    def test_disk_full_retains_partial_and_poison(self):
        store=self.make();r=store.put(b'keep')
        with patch('os.write',side_effect=OSError('disk full private details')):
            with self.assertRaises(EvidenceBlocked) as error:store.put(b'partial')
        self.assertNotIn('private',str(error.exception))
        self.assertTrue((self.root/'local/operator-runs'/store.run_id/'objects'/r['sha256']).exists())
        with self.assertRaises(EvidenceBlocked):store.seal({})

    def test_fsync_failure_not_sealed(self):
        store=self.make();store.put(b'keep')
        with patch('os.fsync',side_effect=OSError('fsync failure')):
            with self.assertRaises(EvidenceBlocked):store.seal({})
        self.assertFalse(store.sealed)

    def test_final_binding_failure_not_sealed(self):
        store=self.make();entry=store.stage
        def fail(*a):raise entry['_Stop']('rebound')
        with patch.dict(entry,_bound=fail):
            with self.assertRaises(EvidenceBlocked):store.seal({})
        self.assertFalse(store.sealed)

    def test_readonly_tamper_extra_missing_and_permissions(self):
        for kind in ['tamper','extra','missing','mode','hardlink','symlink','fifo']:
            with self.subTest(kind=kind):
                store=self.make();r=store.put(b'valid');receipt=store.seal({})
                folder=self.root/'local/operator-runs'/store.run_id/'objects';p=folder/r['sha256']
                if kind=='tamper':p.write_bytes(b'bad!!')
                elif kind=='extra':(folder/'extra').write_bytes(b'x')
                elif kind=='missing':p.unlink()
                elif kind=='mode':p.chmod(0o644)
                elif kind=='hardlink':os.link(p,self.root/str(uuid.uuid4()))
                elif kind=='symlink':p.unlink();p.symlink_to(self.root/'outside')
                else:p.unlink();os.mkfifo(p,0o600)
                with self.assertRaises(EvidenceBlocked):E['verify_evidence'](receipt['run_id'],receipt['index'])

    def test_unsafe_namespace_not_repaired(self):
        local=self.root/'local';local.mkdir();runs=local/'operator-runs';runs.mkdir(mode=0o755)
        with self.assertRaises(EvidenceBlocked):E['EvidenceStore']().__enter__()
        self.assertEqual(runs.stat().st_mode&0o777,0o755)

    def test_late_directory_permissions_not_sealed(self):
        store=self.make()
        (self.root/'local/operator-runs'/store.run_id).chmod(0o755)
        with self.assertRaises(EvidenceBlocked):store.seal({})
        self.assertFalse(store.sealed)

    def test_namespace_symlink_rejected(self):
        local=self.root/'local';local.mkdir();outside=self.root/'outside';outside.mkdir()
        (local/'operator-runs').symlink_to(outside,target_is_directory=True)
        with self.assertRaises(EvidenceBlocked):E['EvidenceStore']().__enter__()
        self.assertEqual(list(outside.iterdir()),[])

    def test_wrong_pin_and_invalid_run_id(self):
        store=self.make();receipt=store.seal({})
        for run,pin in [('../escape',receipt['index']),(receipt['run_id'],dict(receipt['index'],sha256='0'*64))]:
            with self.assertRaises(EvidenceBlocked):E['verify_evidence'](run,pin)

    def test_no_readonly_mutation(self):
        store=self.make();receipt=store.seal({})
        with patch('os.write',side_effect=AssertionError('write')),patch('os.mkdir',side_effect=AssertionError('mkdir')),patch('os.fchmod',side_effect=AssertionError('chmod')),patch('os.fsync',side_effect=AssertionError('fsync')):
            E['verify_evidence'](receipt['run_id'],receipt['index'])

    def test_partial_not_readable_as_sealed(self):
        store=self.make();store.put(b'partial')
        with self.assertRaises(EvidenceBlocked):E['verify_evidence'](store.run_id,ref(b'nonexistent index'))

    def test_fd_cleanup_success_and_failure(self):
        before=len(os.listdir('/proc/self/fd'))
        for _ in range(3):
            with E['EvidenceStore']() as store:store.put(b'fd');store.seal({})
        with self.assertRaises(EvidenceBlocked):E['verify_evidence']('not-a-uuid',ref(b'x'))
        self.assertEqual(before,len(os.listdir('/proc/self/fd')))


if __name__=='__main__':unittest.main(verbosity=2)
