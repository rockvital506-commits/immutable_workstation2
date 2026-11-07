#!/usr/bin/env python3
"""Real fd/symlink/local write tests; not publication, portability or agent certification."""
import copy
import hashlib
import json
import os
from pathlib import Path
import runpy
import stat
import tempfile
import unittest
from unittest.mock import patch
import uuid

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[2]
MODULE=runpy.run_path(str(HERE/'stage.py'))
stage=MODULE['stage_trial'];G=stage.__globals__;ref=MODULE['reference']
FIX={'class':runpy.run_path(str(BASE/'candidates/ent-0013/r0001/verify.py'))['CandidateCoverageTests']}


class TrialStagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):FIX['class'].setUpClass()

    def setUp(self):
        f=FIX['class'];self.candidate=f.candidate_bytes;self.registry=f.registry_bytes
        self.decisions=dict(f.witnesses);self.payloads=dict(f.declared_payloads)
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)/'install';self.root.mkdir()
        self.outside=Path(tmp.name)/'outside';self.outside.mkdir()
        (self.outside/'sentinel').write_bytes(b'untouched')

    def run_stage(self):
        def rootfd():return os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        with patch.dict(G,_base_fd=rootfd):
            r=stage(self.candidate,ref(self.candidate),self.registry,self.decisions,self.payloads)
        for flag in ['transition_allowed','release_allowed','export_allowed','activation_allowed']:
            self.assertIs(r[flag],False)
        self.assertEqual(r['overall_admission'],'not_evaluated')
        self.assertEqual((self.outside/'sentinel').read_bytes(),b'untouched')
        return r

    def successful(self):
        r=self.run_stage();self.assertEqual(r['status'],'staged_trial_only',r)
        self.assertIs(r['staged'],True);return r

    def test_success_exact_manifest_objects_and_modes(self):
        r=self.successful();run=self.root/r['local_ref'];raw=(run/'trial.json').read_bytes()
        self.assertEqual(ref(raw),r['manifest']);m=json.loads(raw)
        self.assertEqual(m['kind'],'incomplete_trial_snapshot');self.assertEqual(len(m['payloads']),34)
        expected={ref(b)['sha256']:b for b in [self.candidate,self.registry,*self.payloads.values(),*self.decisions.values()]}
        self.assertEqual(set(p.name for p in (run/'objects').iterdir()),set(expected))
        for sha,b in expected.items():
            p=run/'objects'/sha;self.assertEqual(p.read_bytes(),b)
            self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o600);self.assertEqual(p.stat().st_nlink,1)
        self.assertEqual(stat.S_IMODE(run.stat().st_mode),0o700)
        self.assertEqual(stat.S_IMODE((run/'objects').stat().st_mode),0o700)
        self.assertEqual(stat.S_IMODE((run/'trial.json').stat().st_mode),0o600)
        self.assertEqual(sorted(p.name for p in run.iterdir()),['objects','trial.json'])

    def test_fresh_runs_do_not_resume_or_share_hardlinks(self):
        a=self.successful();b=self.successful();self.assertNotEqual(a['local_ref'],b['local_ref'])
        x=next((self.root/a['local_ref']/'objects').iterdir());y=self.root/b['local_ref']/'objects'/x.name
        self.assertNotEqual(x.stat().st_ino,y.stat().st_ino)

    def test_bad_pin_no_output_root_open(self):
        with patch.dict(G,_base_fd=lambda:self.fail('output opened before preflight')):
            r=stage(self.candidate,dict(ref(self.candidate),sha256='0'*64),self.registry,self.decisions,self.payloads)
        self.assertEqual(r['status'],'failed');self.assertFalse((self.root/'local').exists())

    def test_corrupt_payload_no_output(self):
        self.payloads[next(iter(self.payloads))]=b'corrupt';self.assertEqual(self.run_stage()['status'],'failed')
        self.assertFalse((self.root/'local').exists())

    def test_input_python_never_executes(self):
        self.payloads[next(p for p in self.payloads if p.endswith('.py'))]=b'raise AssertionError("executed")\n'
        self.assertEqual(self.run_stage()['status'],'failed');self.assertFalse((self.root/'local').exists())

    def test_extra_payload_no_output(self):
        self.payloads['../../outside/sentinel']=b'forged';self.assertEqual(self.run_stage()['status'],'failed')
        self.assertFalse((self.root/'local').exists())

    def test_missing_payload_no_output(self):
        self.payloads.pop(next(iter(self.payloads)));self.assertEqual(self.run_stage()['status'],'failed')
        self.assertFalse((self.root/'local').exists())

    def test_trial_specific_known_revoke_blocks(self):
        candidate=json.loads(self.candidate);c=candidate['components'][-1]
        path=c['record']['approval']['reference']['path'];event=json.loads(self.decisions[path])
        event.update(decision_id='ffffffff-ffff-4fff-8fff-ffffffffffff',decision_type='revoke_use',reason='Synthetic only',
                     scope=dict(operations=['stage_trial'],areas=['agent_system.trial']))
        self.decisions['catalog/approvals/'+event['decision_id']+'.json']=(json.dumps(event)+'\n').encode()
        self.assertEqual(self.run_stage()['status'],'blocked_known_scope');self.assertFalse((self.root/'local').exists())

    def test_local_symlink_rejected(self):
        (self.root/'local').symlink_to(self.outside,target_is_directory=True)
        self.assertEqual(self.run_stage()['status'],'failed');self.assertEqual(len(list(self.outside.iterdir())),1)

    def test_trials_symlink_rejected(self):
        (self.root/'local').mkdir();(self.root/'local/trials').symlink_to(self.outside,target_is_directory=True)
        self.assertEqual(self.run_stage()['status'],'failed');self.assertEqual(len(list(self.outside.iterdir())),1)

    def test_local_regular_file_untouched(self):
        p=self.root/'local';p.write_bytes(b'old');self.assertEqual(self.run_stage()['status'],'failed');self.assertEqual(p.read_bytes(),b'old')

    def test_unsafe_local_parent_rejected_without_chmod(self):
        p=self.root/'local';p.mkdir();p.chmod(0o777)
        self.assertEqual(self.run_stage()['status'],'failed');self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o777)

    def test_nonprivate_trials_rejected(self):
        p=self.root/'local/trials';p.mkdir(parents=True);p.chmod(0o755)
        self.assertEqual(self.run_stage()['status'],'failed');self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o755)

    def test_uuid_collision_preserves_existing_run(self):
        with patch('uuid.uuid4',return_value=uuid.UUID('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa')):
            a=self.successful();old=(self.root/a['local_ref']/'trial.json').read_bytes();b=self.run_stage()
        self.assertEqual(b['status'],'failed');self.assertFalse(b['stage_created'])
        self.assertEqual((self.root/a['local_ref']/'trial.json').read_bytes(),old)

    def test_existing_object_never_overwritten(self):
        original=MODULE['_write_file'];injected=[]
        def conflict(fd,name,raw):
            if not injected:
                f=os.open(name,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600,dir_fd=fd);os.write(f,b'old');os.close(f);injected.append(name)
            return original(fd,name,raw)
        with patch.dict(G,_write_file=conflict):r=self.run_stage()
        self.assertEqual(r['status'],'failed_partial')
        self.assertEqual((self.root/r['local_ref']/'objects'/injected[0]).read_bytes(),b'old')

    def test_object_symlink_never_followed(self):
        original=MODULE['_write_file'];injected=[]
        def conflict(fd,name,raw):
            if not injected:os.symlink(str(self.outside/'sentinel'),name,dir_fd=fd);injected.append(name)
            return original(fd,name,raw)
        with patch.dict(G,_write_file=conflict):r=self.run_stage()
        self.assertEqual(r['status'],'failed_partial');self.assertEqual(len(list(self.outside.iterdir())),1)

    def test_objects_directory_symlink_rejected(self):
        original=MODULE['_directory']
        def redirect(parent,name,private,create=True):
            if name=='objects':os.symlink(str(self.outside),name,dir_fd=parent)
            return original(parent,name,private,create)
        with patch.dict(G,_directory=redirect):r=self.run_stage()
        self.assertEqual(r['status'],'failed_partial');self.assertEqual(len(list(self.outside.iterdir())),1)

    def test_fifo_object_rejected_without_blocking(self):
        original=MODULE['_write_file'];injected=[]
        def fifo(fd,name,raw):
            if not injected:os.mkfifo(name,0o600,dir_fd=fd);injected.append(1)
            return original(fd,name,raw)
        with patch.dict(G,_write_file=fifo):r=self.run_stage()
        self.assertEqual(r['status'],'failed_partial')

    def test_restrictive_umask_keeps_private_modes(self):
        before=os.umask(0o077)
        try:self.successful()
        finally:os.umask(before)

    def test_fault_retains_partial_without_manifest_or_rollback(self):
        original=MODULE['_write_file'];count=[]
        def fail(fd,name,raw):
            if count:raise OSError('injected disk failure')
            original(fd,name,raw);count.append(name)
        with patch.dict(G,_write_file=fail):r=self.run_stage()
        self.assertEqual(r['status'],'failed_partial');run=self.root/r['local_ref']
        self.assertFalse((run/'trial.json').exists());self.assertEqual(len(list((run/'objects').iterdir())),1)

    def test_partial_write_loop(self):
        fd=os.open(self.outside,os.O_RDONLY|os.O_DIRECTORY);self.addCleanup(os.close,fd);write=os.write
        with patch('os.write',side_effect=lambda f,b:write(f,b[:7])):MODULE['_write_file'](fd,'small',b'x'*123)
        self.assertEqual((self.outside/'small').read_bytes(),b'x'*123)

    def test_zero_write_stops(self):
        with patch('os.write',return_value=0):r=self.run_stage()
        self.assertEqual(r['status'],'failed_partial');self.assertFalse(r['staged'])

    def test_corruption_during_write_readback_detected(self):
        original=MODULE['_write_file']
        def corrupt(fd,name,raw):
            original(fd,name,raw)
            before=os.stat(name,dir_fd=fd,follow_symlinks=False)
            f=os.open(name,os.O_WRONLY|os.O_NOFOLLOW,dir_fd=fd);os.write(f,bytes([raw[0]^1])+raw[1:]);os.close(f)
            os.utime(name,ns=(before.st_atime_ns,before.st_mtime_ns),dir_fd=fd,follow_symlinks=False)
        with patch.dict(G,_write_file=corrupt):r=self.run_stage()
        self.assertEqual(r['status'],'failed_partial')

    def test_extra_inventory_detected(self):
        original=MODULE['_write_file'];injected=[]
        def extra(fd,name,raw):
            original(fd,name,raw)
            if not injected:
                f=os.open('unlisted',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600,dir_fd=fd);os.close(f);injected.append(1)
        with patch.dict(G,_write_file=extra):r=self.run_stage()
        self.assertEqual(r['status'],'failed_partial');self.assertEqual(r['diagnostics'],[dict(code='OUTPUT_INVENTORY_CHANGED')])

    def test_detected_hardlink_blocks_completion(self):
        original=MODULE['_write_file'];injected=[]
        def extra(fd,name,raw):
            original(fd,name,raw)
            if not injected:
                os.link(name,self.outside/'linked',src_dir_fd=fd,follow_symlinks=False);injected.append(1)
        with patch.dict(G,_write_file=extra):r=self.run_stage()
        self.assertEqual(r['status'],'failed_partial');self.assertEqual(r['diagnostics'],[dict(code='OUTPUT_METADATA_CHANGED')])

    def test_manifest_write_failure_retains_objects(self):
        original=MODULE['_write_file']
        def fail(fd,name,raw):
            if name=='trial.json':raise OSError('manifest failure')
            return original(fd,name,raw)
        with patch.dict(G,_write_file=fail):r=self.run_stage()
        self.assertEqual(r['status'],'failed_partial');self.assertFalse(r['staged'])

    def test_fsync_failure_not_success(self):
        with patch('os.fsync',side_effect=OSError('fsync failure')):r=self.run_stage()
        self.assertEqual(r['status'],'failed_partial');self.assertFalse(r['staged'])

    def test_directory_rebinding_detected(self):
        original=MODULE['_write_file'];changed=[]
        def rebind(fd,name,raw):
            original(fd,name,raw)
            if name=='trial.json' and not changed:
                run=next((self.root/'local/trials').iterdir());run.rename(run.with_name('moved'));run.mkdir(mode=0o700);changed.append(1)
        with patch.dict(G,_write_file=rebind):r=self.run_stage()
        self.assertEqual(r['status'],'failed_partial');self.assertEqual(r['diagnostics'],[dict(code='OUTPUT_DIRECTORY_REBOUND')])

    def test_input_mappings_unchanged(self):
        old=copy.deepcopy((self.payloads,self.decisions));self.successful();self.assertEqual(old,(self.payloads,self.decisions))

    def test_unsupported_platform_no_writes(self):
        with patch('platform.system',return_value='Windows'):r=self.run_stage()
        self.assertEqual(r['status'],'unsupported');self.assertFalse((self.root/'local').exists())

    def test_installed_pins_changed_no_writes(self):
        pins=copy.deepcopy(MODULE['PINS']);next(iter(pins.values()))['sha256']='0'*64
        with patch.dict(G,PINS=pins):r=self.run_stage()
        self.assertEqual(r['status'],'unsupported');self.assertFalse((self.root/'local').exists())

    def test_fd_count_restored_after_repeated_faults(self):
        self.run_stage();before=len(os.listdir('/proc/self/fd'))
        for _ in range(3):
            with patch.dict(G,_write_file=lambda *a:(_ for _ in ()).throw(OSError('fault'))):self.run_stage()
        self.assertEqual(len(os.listdir('/proc/self/fd')),before)


if __name__=='__main__':unittest.main(verbosity=2)
