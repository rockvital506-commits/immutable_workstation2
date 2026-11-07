#!/usr/bin/env python3
"""Real private trial read tests; consistent bytes do not authenticate stage execution."""
import copy
import json
import os
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest
from unittest.mock import patch
import uuid

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[2]
MODULE=runpy.run_path(str(HERE/'read.py'))
read=MODULE['read_trial'];G=read.__globals__;ref=MODULE['reference']
FIX={'class':runpy.run_path(str(BASE/'candidates/ent-0013/r0001/verify.py'))['CandidateCoverageTests']}
WRITER=runpy.run_path(str(BASE/'staging/ent-0015/r0001/stage.py'))


def encode(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()


class TrialReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        FIX['class'].setUpClass();f=FIX['class']
        cls.cache=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.cache.cleanup)
        root=Path(cls.cache.name)
        def fd():return os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        with patch.dict(WRITER['stage_trial'].__globals__,_base_fd=fd):
            r=WRITER['stage_trial'](f.candidate_bytes,ref(f.candidate_bytes),f.registry_bytes,f.witnesses,f.declared_payloads)
        assert r['status']=='staged_trial_only',r
        cls.local_ref=r['local_ref'];cls.pin=r['manifest']

    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)/'install';shutil.copytree(self.cache.name,self.root)
        self.outside=Path(tmp.name)/'outside';self.outside.mkdir();(self.outside/'sentinel').write_bytes(b'untouched')
        self.run=self.root/self.local_ref;self.run_id=self.run.name
        self.manifest=json.loads((self.run/'trial.json').read_bytes());self.expected=dict(self.pin)

    def save_manifest(self):
        raw=encode(self.manifest);(self.run/'trial.json').write_bytes(raw);self.expected=ref(raw)

    def run_read(self):
        def fd():return os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        with patch.dict(G,_base_fd=fd):r=read(self.run_id,self.expected)
        for flag in ['transition_allowed','release_allowed','export_allowed','activation_allowed']:self.assertIs(r[flag],False)
        self.assertEqual(r['current_permissions'],'not_evaluated');self.assertEqual(r['overall_admission'],'not_evaluated')
        self.assertEqual((self.outside/'sentinel').read_bytes(),b'untouched');return r

    def failed(self):
        r=self.run_read();self.assertEqual(r['status'],'failed',r);return r

    def test_positive_captured_archive(self):
        r=self.run_read();self.assertEqual(r['status'],'consistent_archived_trial',r)
        self.assertEqual(r['payload_count'],34);self.assertEqual(r['manifest'],self.expected)
        self.assertNotIn('payloads',r)

    def test_no_explicit_writes_creates_chmod_or_fsync(self):
        with patch('os.write',side_effect=AssertionError('write')),patch('os.mkdir',side_effect=AssertionError('mkdir')),patch('os.fchmod',side_effect=AssertionError('chmod')),patch('os.fsync',side_effect=AssertionError('fsync')):
            self.assertEqual(self.run_read()['status'],'consistent_archived_trial')

    def test_external_manifest_pin_mismatch(self):
        self.expected['sha256']='0'*64;self.failed()

    def test_invalid_uuid_before_open(self):
        with patch.dict(G,_base_fd=lambda:self.fail('opened root')):r=read('../../outside',self.expected)
        self.assertEqual(r['status'],'failed')

    def test_native_size_not_boolean_or_float(self):
        for size in [True,float(self.expected['size_bytes'])]:
            self.expected['size_bytes']=size;self.failed()

    def test_missing_run_does_not_create(self):
        self.run_id=str(uuid.uuid4());self.failed();self.assertFalse((self.root/'local/trials'/self.run_id).exists())

    def test_local_symlink(self):
        (self.root/'local').rename(self.root/'saved');(self.root/'local').symlink_to(self.outside,target_is_directory=True);self.failed()

    def test_trials_symlink(self):
        trials=self.root/'local/trials';trials.rename(trials.with_name('saved'));trials.symlink_to(self.outside,target_is_directory=True);self.failed()

    def test_run_symlink(self):
        self.run.rename(self.run.with_name('saved'));self.run.symlink_to(self.outside,target_is_directory=True);self.failed()

    def test_objects_symlink(self):
        p=self.run/'objects';p.rename(p.with_name('saved'));p.symlink_to(self.outside,target_is_directory=True);self.failed()

    def test_manifest_symlink(self):
        p=self.run/'trial.json';p.unlink();p.symlink_to(self.outside/'sentinel');self.failed()

    def test_object_symlink(self):
        p=next((self.run/'objects').iterdir());p.unlink();p.symlink_to(self.outside/'sentinel');self.failed()

    def test_object_fifo_nonblocking(self):
        p=next((self.run/'objects').iterdir());p.unlink();os.mkfifo(p,0o600);self.failed()

    def test_object_hardlink_rejected(self):
        p=next((self.run/'objects').iterdir());os.link(p,self.outside/'link');self.failed()

    def test_nonprivate_trials_rejected_without_chmod(self):
        p=self.root/'local/trials';p.chmod(0o755);self.failed();self.assertEqual(p.stat().st_mode&0o777,0o755)

    def test_nonprivate_file_rejected(self):
        next((self.run/'objects').iterdir()).chmod(0o644);self.failed()

    def test_extra_object(self):
        (self.run/'objects'/('0'*64)).write_bytes(b'extra');self.failed()

    def test_missing_object(self):
        next((self.run/'objects').iterdir()).unlink();self.failed()

    def test_extra_run_file(self):
        (self.run/'receipt.json').write_bytes(b'extra');self.failed()

    def test_same_size_corruption_with_restored_mtime(self):
        p=next((self.run/'objects').iterdir());before=p.stat();raw=p.read_bytes();p.write_bytes(bytes([raw[0]^1])+raw[1:]);os.utime(p,ns=(before.st_atime_ns,before.st_mtime_ns));self.failed()

    def test_unknown_manifest_field(self):
        self.manifest['owner_grant']=True;self.save_manifest();self.failed()

    def test_permission_claim(self):
        self.manifest['export_allowed']=True;self.save_manifest();self.failed()

    def test_profile_and_run_binding(self):
        self.manifest['run_id']=str(uuid.uuid4());self.save_manifest();self.failed()

    def test_duplicate_logical_paths(self):
        self.manifest['payloads'].append(copy.deepcopy(self.manifest['payloads'][0]));self.save_manifest();self.failed()

    def test_native_manifest_sizes(self):
        self.manifest['candidate']['size_bytes']=float(self.manifest['candidate']['size_bytes']);self.save_manifest();self.failed()

    def test_oversized_object_reference(self):
        self.manifest['candidate']['size_bytes']=MODULE['LIMIT']+1;self.save_manifest();self.failed()

    def test_inconsistent_digest_sizes(self):
        self.manifest['registry']=dict(self.manifest['candidate'],size_bytes=1);self.save_manifest();self.failed()

    def test_payload_logical_traversal_is_not_opened(self):
        self.manifest['payloads'][0]['path']='../../outside/sentinel'
        self.manifest['payloads'].sort(key=lambda x:x['path']);self.save_manifest();self.failed()

    def append_archived_block(self,operation):
        candidate=json.loads((self.run/'objects'/self.manifest['candidate']['sha256']).read_bytes())
        path=candidate['components'][-1]['record']['approval']['reference']['path']
        item=next(r for r in self.manifest['decisions'] if r['path']==path)
        event=json.loads((self.run/'objects'/item['sha256']).read_bytes())
        # Fixture only: clone the approved subject/artifacts, add an explicit synthetic scope.
        event.update(decision_id='ffffffff-ffff-4fff-8fff-ffffffffffff',decision_type='revoke_use',reason='Synthetic only',
                     scope=dict(operations=[operation],areas=['agent_system.trial']))
        raw=encode(event);r=ref(raw);p=self.run/'objects'/r['sha256'];p.write_bytes(raw);p.chmod(0o600)
        self.manifest['decisions'].append(dict(path='catalog/approvals/'+event['decision_id']+'.json',**r))
        self.manifest['decisions'].sort(key=lambda x:x['path']);self.save_manifest()

    def test_archived_read_scope_block(self):
        self.append_archived_block('read_trial');r=self.run_read()
        self.assertEqual(r['status'],'blocked_known_scope',r)
        self.assertEqual(r['diagnostics'],[dict(code='ARCHIVED_KNOWN_SCOPE_BLOCK')])

    def test_archived_stage_scope_block(self):
        self.append_archived_block('stage_trial');self.assertEqual(self.run_read()['status'],'blocked_known_scope')

    def test_duplicate_json_keys_rejected(self):
        p=self.run/'trial.json';raw=p.read_bytes().replace(b'{',b'{"schema_version":"1",',1);p.write_bytes(raw);self.expected=ref(raw);self.failed()

    def test_double_trailing_lf_rejected(self):
        p=self.run/'trial.json';raw=p.read_bytes()+b'\n';p.write_bytes(raw);self.expected=ref(raw);self.failed()

    def test_directory_binding_replaced(self):
        original=MODULE['_read'];changed=[]
        def mutate(directory,name,expected,entry):
            raw=original(directory,name,expected,entry)
            if name=='trial.json' and not changed:self.run.rename(self.run.with_name('moved'));self.run.mkdir(mode=0o700);changed.append(1)
            return raw
        with patch.dict(G,_read=mutate):self.failed()

    def test_fabricated_coherent_archive_not_execution_proof(self):
        new_id=str(uuid.uuid4());destination=self.run.with_name(new_id);self.run.rename(destination)
        self.run=destination;self.run_id=new_id;self.manifest['run_id']=new_id;self.save_manifest()
        r=self.run_read();self.assertEqual(r['status'],'consistent_archived_trial')
        self.assertIn('execution_authentication',r['not_checked'])

    def test_live_unknown_ledger_is_not_silently_checked(self):
        p=self.root/'catalog/approvals/unknown';p.parent.mkdir(parents=True);p.write_bytes(b'not in archived ledger')
        r=self.run_read();self.assertEqual(r['status'],'consistent_archived_trial')
        self.assertIn('current_decisions',r['not_checked'])

    def test_post_capture_object_mutation_detected(self):
        original=MODULE['_read'];changed=[]
        def mutate(directory,name,expected,entry):
            raw=original(directory,name,expected,entry)
            if name!='trial.json' and not changed:
                p=self.run/'objects'/name;p.write_bytes(bytes([raw[0]^1])+raw[1:]);changed.append(1)
            return raw
        with patch.dict(G,_read=mutate):self.failed()

    def test_inventory_mutation_detected(self):
        original=MODULE['_read'];changed=[]
        def mutate(directory,name,expected,entry):
            raw=original(directory,name,expected,entry)
            if name!='trial.json' and not changed:(self.run/'objects'/'unlisted').write_bytes(b'x');changed.append(1)
            return raw
        with patch.dict(G,_read=mutate):self.failed()

    def test_read_error_no_mutation(self):
        before=(self.run/'trial.json').read_bytes()
        with patch('os.read',side_effect=OSError('injected read failure')):self.failed()
        self.assertEqual((self.run/'trial.json').read_bytes(),before)

    def test_installed_pins_changed(self):
        pins=copy.deepcopy(MODULE['PINS']);next(iter(pins.values()))['sha256']='0'*64
        with patch.dict(G,PINS=pins):self.assertEqual(self.run_read()['status'],'unsupported')

    def test_unsupported_platform(self):
        with patch('platform.system',return_value='Windows'):self.assertEqual(self.run_read()['status'],'unsupported')

    def test_fd_count_restored_after_failures(self):
        self.run_read();before=len(os.listdir('/proc/self/fd'));self.expected['sha256']='0'*64
        for _ in range(3):self.failed()
        self.assertEqual(len(os.listdir('/proc/self/fd')),before)


if __name__=='__main__':unittest.main(verbosity=2)
