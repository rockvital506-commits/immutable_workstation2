"""Physical disposable journal tests; assents are SYNTHETIC, never real owner grants."""
import copy
import json
import os
from pathlib import Path
import runpy
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid

HERE=Path(__file__).resolve().parent
M=runpy.run_path(str(HERE/'state.py'));G=M['create_store'].__globals__
ref=M['reference'];enc=M['encode'];Blocked=M['StateBlocked']


def uid():return str(uuid.uuid4())


class StateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);p=patch.dict(G,LOCAL_BASE=self.base);p.start();self.addCleanup(p.stop)
        self.receipt=None
        r=ref(b'synthetic input\n')
        self.subject=enc(dict(schema_version='1',kind='release_subject',candidate=r,registry=r,entity_decisions=[],
                             artifacts=[dict(path='payload/test.md',**r)],coverage_description=r,procedure=r,prompt=r))

    def create(self):
        self.receipt=M['create_store'](trust_owner_controlled_namespace=True)
        self.root=self.base/'local/permission-authority'/self.receipt['store_id']
        return self.receipt

    def open(self,receipt=None):
        r=receipt or self.receipt
        return M['AuthorityStore'](r['store_id'],r['head'],trust_owner_controlled_namespace=True)

    def event(self,kind='authorize_release',action='release',target=None,parent=None,export=None):
        v=dict(schema_version='1',kind='permission_event',event_id=uid(),decision=kind,action=action,subject=ref(self.subject),
               parent=parent,export=export,target=target)
        raw=enc(v);e=dict(event_id=v['event_id'],**ref(raw))
        source=enc(dict(schema_version='1',kind='local_owner_assent',basis_id=uid(),source_id=uid(),statement_form='summary',
                        statement='SYNTHETIC exact-event consent for tests only; not an owner grant.',event=e,
                        attestation='exact_event_reviewed_by_local_operator'))
        return raw,source,e

    def add(self,raw,source,receipt=None):
        with self.open(receipt) as store:
            self.receipt=store.import_assent(raw,ref(raw),source,ref(source),self.subject,ref(self.subject),attest_exact_owner_assent=True)
        return self.receipt

    def request(self,store,grant,action='release',export=None,request_id=None):
        packet=store.context_packet()
        return enc(dict(schema_version='1',kind='permission_check',request_id=request_id or uid(),action=action,
                        context=packet['expected_context'],generation=store.summary()['generation'],
                        subject=ref(self.subject),grant=grant,export=export))

    def check(self,grant,action='release',export=None):
        with self.open() as store:
            raw=self.request(store,grant,action,export)
            result=store.check_once(raw,ref(raw),self.subject,ref(self.subject))
            self.receipt=result['receipt'];self.last_request=raw
        return result

    def files(self):return {p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def flags(self,r):
        for flag in ['performed','transition_allowed','release_allowed','export_allowed','activation_allowed']:self.assertIs(r[flag],False)

    def test_ack_before_writes(self):
        for ack in [False,1,'true',None]:
            with self.subTest(ack=ack),self.assertRaises(Blocked):M['create_store'](trust_owner_controlled_namespace=ack)
        self.assertFalse((self.base/'local').exists())

    def test_bad_store_id_and_head_before_io(self):
        for store_id,head in [('../x',ref(b'x')),('bad',ref(b'x')),(uid(),{'sha256':'0'*64,'size_bytes':True})]:
            with self.subTest(store_id=store_id),self.assertRaises(Blocked):M['AuthorityStore'](store_id,head,trust_owner_controlled_namespace=True)
        self.assertFalse((self.base/'local').exists())

    def test_create_reopen_empty_private(self):
        r=self.create();self.flags(r);self.assertEqual((r['generation'],r['events_count'],r['checks_count']),(0,0,0))
        before=self.files()
        with self.open() as store:self.assertEqual(store.summary(),r)
        self.assertEqual(before,self.files())
        for p in self.root.rglob('*'):
            self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o700 if p.is_dir() else 0o600)

    def test_source_bytes_retained_and_no_raw_statement_summary(self):
        self.create();raw,source,event=self.event();self.add(raw,source)
        self.assertEqual((self.root/'objects'/ref(source)['sha256']).read_bytes(),source)
        self.assertNotIn('SYNTHETIC',json.dumps(self.receipt));self.flags(self.receipt)
        with self.open() as store:self.assertEqual(store.context_packet()['event_blobs'],{'permission-events/'+event['event_id']+'.json':raw})

    def test_missing_exact_attestation_no_writes(self):
        self.create();raw,source,_=self.event();before=self.files()
        with self.open() as store:
            with self.assertRaises(Blocked):store.import_assent(raw,ref(raw),source,ref(source),self.subject,ref(self.subject))
        self.assertEqual(before,self.files())

    def test_false_source_pin_no_persistence(self):
        self.create();raw,source,_=self.event();before=self.files()
        with self.open() as store:
            with self.assertRaises(Blocked):store.import_assent(raw,ref(raw),source,ref(b'other'),self.subject,ref(self.subject),attest_exact_owner_assent=True)
        self.assertEqual(before,self.files())

    def test_assent_event_subject_binding_and_blank_statement(self):
        self.create();raw,source,_=self.event();before=self.files()
        for field,value in [('statement','  '),('event',dict(event_id=uid(),**ref(raw)))]:
            packet=json.loads(source);packet[field]=value;b=enc(packet)
            with self.open() as store,self.assertRaises(Blocked):
                store.import_assent(raw,ref(raw),b,ref(b),self.subject,ref(self.subject),attest_exact_owner_assent=True)
        ev=json.loads(raw);ev['subject']=ref(b'other');raw=enc(ev)
        with self.open() as store,self.assertRaises(Blocked):
            store.import_assent(raw,ref(raw),source,ref(source),self.subject,ref(self.subject),attest_exact_owner_assent=True)
        self.assertEqual(before,self.files())

    def test_statement_form_and_unknown_source_fields_closed(self):
        self.create();raw,source,_=self.event()
        for change in [dict(statement_form='owner_approved'),dict(actor_role='owner')]:
            packet=json.loads(source);packet.update(change);b=enc(packet)
            with self.open() as store,self.assertRaises(Blocked):store.import_assent(raw,ref(raw),b,ref(b),self.subject,ref(self.subject),attest_exact_owner_assent=True)
        self.assertEqual(len(list((self.root/'generations').iterdir())),1)

    def test_duplicate_event_never_overwritten(self):
        self.create();raw,source,_=self.event();self.add(raw,source);before=self.files()
        with self.assertRaises(Blocked):self.add(raw,source)
        self.assertEqual(before,self.files())

    def test_import_dangling_revoke_or_export_fails_before_writes(self):
        self.create();before=self.files()
        for kind,kwargs in [('revoke_permission',dict(target=dict(event_id=uid(),**ref(b'wrong')))),('authorize_export',dict(action='export'))]:
            raw,source,_=self.event(kind,**kwargs)
            with self.assertRaises(Blocked):self.add(raw,source)
        self.assertEqual(before,self.files())

    def test_positive_check_once_replay_rejected(self):
        self.create();raw,source,event=self.event();self.add(raw,source)
        result=self.check(event);self.assertTrue(result['check_id_consumed']);self.assertFalse(result['action_claim_created'])
        self.assertEqual(result['check_result']['status'],'permission_granted_in_declared_context');self.flags(result['check_result'])
        before=self.files()
        with self.open() as store,self.assertRaises(Blocked):store.check_once(self.last_request,ref(self.last_request),self.subject,ref(self.subject))
        self.assertEqual(before,self.files())

    def test_check_id_collision_different_bytes_rejected(self):
        self.create();raw,source,event=self.event();self.add(raw,source);self.check(event)
        old=json.loads(self.last_request)
        with self.open() as store:
            new=self.request(store,event,request_id=old['request_id'])
            self.assertNotEqual(new,self.last_request)
            with self.assertRaises(Blocked):store.check_once(new,ref(new),self.subject,ref(self.subject))

    def test_failed_check_persisted_not_action_claim(self):
        self.create();event=dict(event_id=uid(),**ref(b'not imported'))
        r=self.check(event);self.assertEqual(r['check_result']['diagnostics'],['GRANT_REFERENCE']);self.assertFalse(r['action_claim_created'])
        with self.open() as store:self.assertEqual(store.summary()['checks_count'],1)

    def test_negative_records_cumulative_and_not_removed(self):
        self.create();raw,source,event=self.event();self.add(raw,source)
        for _ in range(2):
            r,s,e=self.event('deny_permission');self.add(r,s)
        self.assertEqual(self.check(event)['check_result']['status'],'blocked_known_permission')
        r,s,later=self.event();self.add(r,s)
        self.assertEqual(self.check(later)['check_result']['status'],'blocked_known_permission')
        self.assertEqual(self.receipt['events_count'],4)

    def test_exact_revoke_blocks_old_grant(self):
        self.create();raw,source,event=self.event();self.add(raw,source)
        r,s,_=self.event('revoke_permission',target=event);self.add(r,s)
        self.assertEqual(self.check(event)['check_result']['status'],'blocked_known_permission')

    def test_export_parent_and_descriptor_real_persistence(self):
        self.create();raw,source,event=self.event();self.add(raw,source)
        subject=json.loads(self.subject)
        export=dict(export_id=uid(),paths=['payload/test.md'],destination=ref(b'destination'),procedure=subject['procedure'],prompt=subject['prompt'])
        r,s,child=self.event('authorize_export','export',parent=event,export=export);self.add(r,s)
        value=self.check(child,'export',export);self.assertTrue(value['check_result']['export_permission_recognized']);self.flags(value['check_result'])

    def test_lock_nonblocking_and_fd_cleanup(self):
        self.create();before=len(os.listdir('/proc/self/fd'))
        with self.open():
            with self.assertRaises(Blocked) as err:
                with self.open():pass
            self.assertEqual(err.exception.code,'AUTHORITY_STATE_BUSY')
        self.assertEqual(len(os.listdir('/proc/self/fd')),before)

    def test_stale_external_head_rejected(self):
        initial=self.create();raw,source,_=self.event();self.add(raw,source)
        with self.assertRaises(Blocked):
            with self.open(initial):pass

    def test_old_request_context_rejected_under_current_head(self):
        self.create();raw,source,event=self.event();self.add(raw,source)
        with self.open() as store:request=self.request(store,event)
        r,s,_=self.event('deny_permission');self.add(r,s);before=self.files()
        with self.open() as store,self.assertRaises(Blocked):store.check_once(request,ref(request),self.subject,ref(self.subject))
        self.assertEqual(before,self.files())

    def test_rollback_missing_new_head_detected_by_external_pin(self):
        self.create();raw,source,_=self.event();self.add(raw,source)
        (self.root/'generations/00000001.json').unlink()  # disposable adversarial mutation only
        with self.assertRaises(Blocked):
            with self.open():pass

    def test_old_pin_can_accept_coherently_restored_whole_old_store(self):
        initial=self.create();backup=self.base/'backup';shutil.copytree(self.root,backup)
        raw,source,_=self.event();self.add(raw,source)
        shutil.rmtree(self.root);shutil.copytree(backup,self.root)  # test-only adversarial rollback
        with self.open(initial) as store:
            self.assertEqual(store.summary()['generation'],0)
            self.assertIn('external_rollback_resistance',store.summary()['not_checked'])

    def test_generation_gap_and_extra_objects_rejected(self):
        self.create();raw,source,_=self.event();self.add(raw,source)
        path=self.root/'generations/00000001.json';path.rename(path.with_name('00000002.json'))
        with self.assertRaises(Blocked):
            with self.open():pass
        path.with_name('00000002.json').rename(path)
        extra=self.root/'objects'/('0'*64);extra.write_bytes(b'extra');extra.chmod(0o600)
        with self.assertRaises(Blocked):
            with self.open():pass

    def test_actual_cas_byte_corruption_and_missing(self):
        self.create();context=self.root/'objects'/self.receipt['context']['sha256'];raw=context.read_bytes()
        context.write_bytes(raw[:-1]+b'x')
        with self.assertRaises(Blocked):
            with self.open():pass
        context.unlink()
        with self.assertRaises(Blocked):
            with self.open():pass

    def test_file_symlink_hardlink_fifo_metadata(self):
        self.create();context=self.root/'objects'/self.receipt['context']['sha256'];raw=context.read_bytes()
        outside=self.base/'outside';outside.write_bytes(raw);outside.chmod(0o600);context.unlink();context.symlink_to(outside)
        with self.assertRaises(Blocked):
            with self.open():pass
        context.unlink();os.link(outside,context)
        with self.assertRaises(Blocked):
            with self.open():pass
        context.unlink();os.mkfifo(context,0o600)
        with self.assertRaises(Blocked):
            with self.open():pass

    def test_unsafe_local_dir_not_repaired(self):
        local=self.base/'local';local.mkdir();local.chmod(0o777)
        with self.assertRaises(Blocked):self.create()
        self.assertEqual(stat.S_IMODE(local.stat().st_mode),0o777)

    def test_namespace_and_lock_rebinding_rejected(self):
        self.create()
        with self.open() as store:
            lock=self.root/'lock';lock.rename(self.root/'old-lock');lock.write_bytes(M['LOCK']);lock.chmod(0o600)
            with self.assertRaises(Blocked):store.summary()

    def test_store_directory_rebound_before_write(self):
        self.create();raw,source,_=self.event()
        with self.open() as store:
            moved=self.root.with_name(uid());self.root.rename(moved);self.root.mkdir(mode=0o700)
            with self.assertRaises(Blocked):store.import_assent(raw,ref(raw),source,ref(source),self.subject,ref(self.subject),attest_exact_owner_assent=True)
            self.assertFalse(any((self.root).iterdir()))

    def test_reduced_budget_and_generation_limits(self):
        self.create();raw,source,_=self.event();before=self.files()
        with self.open() as store,patch.dict(G,TOTAL=1),self.assertRaises(Blocked):
            store.import_assent(raw,ref(raw),source,ref(source),self.subject,ref(self.subject),attest_exact_owner_assent=True)
        self.assertEqual(before,self.files())
        with self.open() as store,patch.dict(G,GENERATIONS=1),self.assertRaises(Blocked):
            store.import_assent(raw,ref(raw),source,ref(source),self.subject,ref(self.subject),attest_exact_owner_assent=True)
        self.assertEqual(before,self.files())

    def test_zero_write_failure_no_receipt_or_auto_cleanup(self):
        self.create();raw,source,_=self.event()
        with self.open() as store:
            with patch('os.write',return_value=0),self.assertRaises(Blocked):
                store.import_assent(raw,ref(raw),source,ref(source),self.subject,ref(self.subject),attest_exact_owner_assent=True)
            with self.assertRaises(Blocked):store.summary()
        self.assertEqual(len(list((self.root/'generations').iterdir())),1)
        self.assertGreater(len(list((self.root/'objects').iterdir())),1)
        with self.assertRaises(Blocked):
            with self.open():pass

    def test_fsync_failure_not_success_retains_partial(self):
        self.create();raw,source,_=self.event()
        with self.open() as store,patch('os.fsync',side_effect=OSError('synthetic fsync')),self.assertRaises(Blocked):
            store.import_assent(raw,ref(raw),source,ref(source),self.subject,ref(self.subject),attest_exact_owner_assent=True)
        self.assertEqual(len(list((self.root/'generations').iterdir())),1)
        self.assertGreater(len(list((self.root/'objects').iterdir())),1)

    def test_partial_write_loop_success(self):
        self.create();raw,source,event=self.event();original=os.write
        def short(fd,data):return original(fd,data[:17])
        with patch('os.write',side_effect=short):self.add(raw,source)
        self.assertEqual(self.check(event)['check_result']['status'],'permission_granted_in_declared_context')

    def test_unknown_event_and_duplicate_source_json_no_persistence(self):
        self.create();raw,source,_=self.event();before=self.files()
        value=json.loads(raw);value['decision']='new_type';raw=enc(value)
        with self.assertRaises(Blocked):self.add(raw,source)
        raw,source,_=self.event();source=b'{"x":1,"x":2}\n'
        with self.assertRaises(Blocked):self.add(raw,source)
        self.assertEqual(before,self.files())

    def test_platform_and_installed_pin_gate_before_namespace(self):
        with patch('platform.system',return_value='Other'),self.assertRaises(Blocked):self.create()
        self.assertFalse((self.base/'local').exists())
        pins=copy.deepcopy(M['PINS']);next(iter(pins.values()))['sha256']='0'*64
        with patch.dict(G,PINS=pins),self.assertRaises(Blocked):self.create()
        self.assertFalse((self.base/'local').exists())

    def test_empty_lab_creates_no_owner_decisions(self):
        value=M['run_empty_lab'](trust_owner_controlled_namespace=True)
        self.assertEqual(value['check_result']['diagnostics'],['GRANT_REFERENCE'])
        self.assertEqual(value['reopened']['events_count'],0);self.assertEqual(value['reopened']['checks_count'],1)
        self.assertFalse(value['action_claim_created'])


    def test_unsafe_base_and_late_private_modes(self):
        self.base.chmod(0o777)
        with self.assertRaises(Blocked):self.create()
        self.assertFalse((self.base/'local').exists());self.base.chmod(0o700);self.create()
        with self.open() as store:
            self.root.chmod(0o755)
            with self.assertRaises(Blocked):store.summary()
            self.root.chmod(0o700)
            with self.assertRaises(Blocked):store.context_packet()

    def test_recorded_check_result_not_just_cas_hashes(self):
        self.create();raw,source,event=self.event();self.add(raw,source);self.check(event)
        head_path=self.root/'generations/00000002.json';head=json.loads(head_path.read_bytes())
        row=head['checks'][0];old=json.loads((self.root/'objects'/row['result']['sha256']).read_bytes())
        old['release_allowed']=True;raw=enc(old);obj=self.root/'objects'/ref(raw)['sha256'];obj.write_bytes(raw);obj.chmod(0o600)
        row['result']=ref(raw);newhead=enc(head);head_path.write_bytes(newhead)
        receipt=dict(self.receipt,head=ref(newhead))
        with self.assertRaises(Blocked) as err:
            with self.open(receipt):pass
        self.assertEqual(err.exception.code,'CHECK_RESULT_BINDING')

    def test_recorded_parent_link_native_generation_and_inventory(self):
        self.create();raw,source,_=self.event();self.add(raw,source)
        path=self.root/'generations/00000001.json';old=path.read_bytes()
        for field,value in [('parent',ref(b'wrong')),('generation',1.0)]:
            head=json.loads(old);head[field]=value;new=enc(head);path.write_bytes(new)
            receipt=dict(self.receipt,head=ref(new))
            with self.assertRaises(Blocked):
                with self.open(receipt):pass
        path.write_bytes(old)
        extra=self.root/'extra.txt';extra.write_bytes(b'extra');extra.chmod(0o600)
        with self.assertRaises(Blocked):
            with self.open():pass


    def test_cross_process_lock_not_just_python_object(self):
        self.create()
        code="""import json,runpy,sys
from pathlib import Path
m=runpy.run_path(sys.argv[1]);m['create_store'].__globals__['LOCAL_BASE']=Path(sys.argv[2]);r=json.loads(sys.argv[3])
try:
    with m['AuthorityStore'](r['store_id'],r['head'],trust_owner_controlled_namespace=True):pass
except m['StateBlocked'] as e:
    raise SystemExit(0 if e.code=='AUTHORITY_STATE_BUSY' else 2)
raise SystemExit(3)
"""
        with self.open():
            result=subprocess.run([sys.executable,'-c',code,str(HERE/'state.py'),str(self.base),json.dumps(self.receipt)],capture_output=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr.decode())

    def test_known_negative_cannot_be_removed_from_new_generation(self):
        self.create();raw,source,event=self.event();self.add(raw,source)
        r,s,deny=self.event('deny_permission');self.add(r,s);self.check(event)
        path=self.root/'generations/00000003.json';head=json.loads(path.read_bytes())
        head['sources']=[row for row in head['sources'] if row['event']['event_id']!=deny['event_id']]
        context=enc(M['_context'](head));obj=self.root/'objects'/ref(context)['sha256'];obj.write_bytes(context);obj.chmod(0o600)
        head['context']=ref(context);new=enc(head);path.write_bytes(new)
        with self.assertRaises(Blocked) as err:
            with self.open(dict(self.receipt,head=ref(new))):pass
        self.assertEqual(err.exception.code,'HISTORY_REMOVED_OR_CHANGED')

    def test_physical_corruption_after_write_readback_stops_commit(self):
        self.create();raw,source,_=self.event()
        with self.open() as store:
            original=store.s['_write_file']
            def corrupt(directory,name,data):
                original(directory,name,data)
                fd=os.open(name,os.O_WRONLY|os.O_NOFOLLOW,dir_fd=directory)
                try:os.pwrite(fd,b'?',0)
                finally:os.close(fd)
            with patch.dict(store.s,_write_file=corrupt),self.assertRaises(Blocked):
                store.import_assent(raw,ref(raw),source,ref(source),self.subject,ref(self.subject),attest_exact_owner_assent=True)
        self.assertEqual(len(list((self.root/'generations').iterdir())),1)
        with self.assertRaises(Blocked):
            with self.open():pass


    def test_assent_basis_identity_cannot_be_reused_for_other_event(self):
        self.create();raw,source,_=self.event();self.add(raw,source);before=self.files()
        raw2,source2,_=self.event();value=json.loads(source2);value['basis_id']=json.loads(source)['basis_id'];source2=enc(value)
        with self.assertRaises(Blocked):self.add(raw2,source2)
        self.assertEqual(before,self.files())

    def test_fresh_check_id_does_not_mean_export_grant_was_consumed(self):
        self.create();raw,source,event=self.event();self.add(raw,source)
        first=self.check(event);second=self.check(event)
        self.assertNotEqual(first['check_result']['request'],second['check_result']['request'])
        self.assertEqual(second['check_result']['status'],'permission_granted_in_declared_context')
        self.assertEqual(second['receipt']['checks_count'],2)
        self.assertFalse(second['action_claim_created']);self.flags(second['check_result'])


if __name__=='__main__':unittest.main(verbosity=2)
