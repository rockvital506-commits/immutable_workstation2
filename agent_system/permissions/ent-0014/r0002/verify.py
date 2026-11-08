"""Synthetic local-owner contexts test semantics, NOT real grants/readiness/actuation."""
import copy
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch
import uuid

HERE=Path(__file__).resolve().parent
A=runpy.run_path(str(HERE/'authority.py'));ref=A['reference'];enc=A['encode']
OLD=runpy.run_path(str(HERE.parent/'r0001/verify.py'))


def uid():return str(uuid.uuid4())
def er(event):return dict(event_id=event['event_id'],**ref(enc(event)))


class AuthorityTests(unittest.TestCase):
    def setUp(self):
        self.subject=dict(schema_version='1',kind='release_subject',candidate=ref(b'candidate\n'),
                          registry=ref(b'registry\n'),entity_decisions=[],artifacts=[dict(path='payload/a.md',**ref(b'a\n'))],
                          coverage_description=ref(b'coverage\n'),procedure=ref(b'procedure\n'),prompt=ref(b'prompt\n'))
        self.events=[];self.grant=self.event('authorize_release');self.action='release';self.export_data=None
        self.current=None;self.generation=1

    def event(self,kind,action='release',target=None):
        value=dict(schema_version='1',kind='permission_event',event_id=uid(),decision=kind,action=action,
                   subject=ref(enc(self.subject)),parent=None,export=None,target=er(target) if target else None)
        self.events.append(value);return value

    def export(self):
        parent=self.grant;self.grant=self.event('authorize_export','export')
        self.export_data=dict(export_id=uid(),paths=[a['path'] for a in self.subject['artifacts']],
                              destination=ref(b'destination\n'),procedure=self.subject['procedure'],prompt=self.subject['prompt'])
        self.grant.update(parent=er(parent),export=copy.deepcopy(self.export_data));self.action='export'

    def packet(self):
        self.maps={'permission-events/'+v['event_id']+'.json':enc(v) for v in self.events}
        context=dict(schema_version='1',kind='local_owner_context',profile='owner-controlled-local-r0001',
                     context_id=uid(),generation=self.generation,
                     known_events=[dict(path=p,**ref(b)) for p,b in sorted(self.maps.items())],
                     approved_events=sorted([er(v) for v in self.events],key=lambda v:v['event_id']))
        self.ctx=enc(context);self.authority=A['establish_local_authority'](self.ctx,ref(self.ctx),trust_owner_controlled_context=True)
        request=dict(schema_version='1',kind='permission_check',request_id=uid(),action=self.action,context=ref(self.ctx),
                     generation=self.generation,subject=ref(enc(self.subject)),grant=er(self.grant),export=self.export_data)
        self.req=enc(request);return request

    def check(self,prepare=True):
        if prepare:self.packet()
        r=A['evaluate_permission'](self.req,ref(self.req),enc(self.subject),ref(enc(self.subject)),self.maps,
                                  authority=self.authority,expected_current_context=self.current or ref(self.ctx))
        for flag in ['performed','transition_allowed','release_allowed','export_allowed','activation_allowed']:
            self.assertIs(r[flag],False)
        self.assertEqual(r['overall_admission'],'not_evaluated')
        return r

    def failed(self,code=None,prepare=True):
        r=self.check(prepare);self.assertEqual(r['status'],'failed',r)
        if code:self.assertEqual(r['diagnostics'],[code])
        return r

    def test_positive_release_recognition_not_readiness(self):
        r=self.check();self.assertEqual(r['status'],'permission_granted_in_declared_context');self.assertTrue(r['authority_valid'])
        self.assertTrue(r['release_permission_recognized']);self.assertFalse(r['export_permission_recognized'])
        self.assertEqual(r['readiness'],'not_checked')

    def test_positive_export_with_exact_release_parent(self):
        self.export();r=self.check();self.assertEqual(r['status'],'permission_granted_in_declared_context')
        self.assertTrue(r['export_permission_recognized'])

    def test_context_ack_required_not_boolean_coercion(self):
        self.packet()
        for ack in [False,1,'true',None]:
            with self.subTest(ack=ack),self.assertRaises(A['PermissionBlocked']):
                A['establish_local_authority'](self.ctx,ref(self.ctx),trust_owner_controlled_context=ack)

    def test_context_pin_required(self):
        self.packet()
        with self.assertRaises(A['PermissionBlocked']):A['establish_local_authority'](self.ctx,ref(b'other\n'),trust_owner_controlled_context=True)

    def test_no_authority_from_role_or_raw_context(self):
        self.packet();self.authority=json.loads(self.ctx);self.failed('OWNER_AUTHORITY_NOT_ESTABLISHED',False)

    def test_input_actor_role_not_an_authority_field(self):
        self.grant['actor_role']='owner';self.failed('DOCUMENT_SCHEMA')

    def test_proposal_or_approve_not_permission_event(self):
        for kind in ['approve_revision','permission_proposal','authorize_activation']:
            with self.subTest(kind=kind):self.grant['decision']=kind;self.failed('DOCUMENT_SCHEMA')

    def test_external_request_and_subject_pins(self):
        self.packet()
        for which in ['request','subject']:
            args=[self.req,ref(self.req),enc(self.subject),ref(enc(self.subject)),self.maps]
            args[1 if which=='request' else 3]=ref(b'wrong\n')
            self.assertEqual(A['evaluate_permission'](*args,authority=self.authority,expected_current_context=ref(self.ctx))['diagnostics'],['REFERENCE_MISMATCH'])

    def test_known_event_mutation_missing_extra(self):
        self.packet();old=dict(self.maps)
        for maps in [{},dict(old,**{'permission-events/'+uid()+'.json':b'{}\n'}),{p:b+b' ' for p,b in old.items()}]:
            self.maps=maps;self.failed('KNOWN_STREAM_BINDING',False)

    def test_unapproved_known_event(self):
        self.packet();ctx=json.loads(self.ctx);ctx['approved_events']=[];self.ctx=enc(ctx)
        self.authority=A['establish_local_authority'](self.ctx,ref(self.ctx),trust_owner_controlled_context=True)
        req=json.loads(self.req);req['context']=ref(self.ctx);self.req=enc(req);self.failed('EVENT_NOT_OWNER_APPROVED',False)

    def test_export_parent_wrong_subject(self):
        self.export();self.events[0]['subject']=ref(b'other\n');self.grant['parent']=er(self.events[0]);self.failed('RELEASE_PARENT_SUBJECT')

    def test_export_parent_must_be_release(self):
        self.export();self.grant['parent']=er(self.grant);self.failed('RELEASE_PARENT_REFERENCE')

    def test_export_without_release_parent(self):
        self.export();self.grant['parent']=None;self.failed('RELEASE_PARENT_REFERENCE')

    def test_no_implicit_export_from_release(self):
        self.action='export';self.export_data=dict(export_id=uid(),paths=['payload/a.md'],destination=ref(b'd\n'),procedure=self.subject['procedure'],prompt=self.subject['prompt'])
        self.failed('GRANT_SCOPE')

    def test_export_request_destination_procedure_prompt_and_id_binding(self):
        self.export();old=copy.deepcopy(self.export_data)
        for field in ['destination','procedure','prompt','export_id']:
            with self.subTest(field=field):
                self.export_data=copy.deepcopy(old);self.export_data[field]=uid() if field=='export_id' else ref(b'changed\n')
                self.failed('EXPORT_REQUEST_BINDING' if field in ['destination','export_id'] else 'EXPORT_PROCEDURE')

    def test_export_allowlist_no_subset_extra_reorder(self):
        self.subject['artifacts'].append(dict(path='payload/b.md',**ref(b'b\n')));self.grant['subject']=ref(enc(self.subject));self.export()
        for paths in [['payload/a.md'],['payload/a.md','payload/b.md','payload/c.md'],['payload/b.md','payload/a.md']]:
            with self.subTest(paths=paths):self.export_data['paths']=paths;self.failed('EXPORT_ALLOWLIST')

    def test_deny_release_blocks_export(self):
        self.export();self.event('deny_permission');r=self.check()
        self.assertEqual(r['status'],'blocked_known_permission');self.assertFalse(r['export_permission_recognized'])

    def test_export_deny_does_not_deny_release(self):
        self.event('deny_permission','export');self.assertEqual(self.check()['status'],'permission_granted_in_declared_context')

    def test_two_denies_not_overridden_by_later_grant(self):
        self.event('deny_permission');self.event('deny_permission');self.grant=self.event('authorize_release')
        self.assertEqual(self.check()['status'],'blocked_known_permission')
        self.events.pop(1);self.assertEqual(self.check()['status'],'blocked_known_permission')

    def test_revoke_exact_grant_not_latest(self):
        first=self.grant;self.event('revoke_permission',target=first);second=self.event('authorize_release')
        self.assertEqual(self.check()['status'],'blocked_known_permission')
        self.grant=second;self.assertEqual(self.check()['status'],'permission_granted_in_declared_context')

    def test_revoked_release_blocks_child_export(self):
        parent=self.grant;self.export();self.event('revoke_permission',target=parent)
        self.assertEqual(self.check()['status'],'blocked_known_permission')

    def test_revoked_export_not_release(self):
        self.export();self.event('revoke_permission','export',target=self.grant);r=self.check()
        self.assertEqual(r['status'],'blocked_known_permission');self.assertTrue(r['release_permission_recognized'])

    def test_dangling_revoke_even_unrequested_event(self):
        target=copy.deepcopy(self.grant);target['event_id']=uid();self.event('revoke_permission',target=target)
        self.failed('REVOKE_TARGET_REFERENCE')

    def test_revoke_wrong_scope(self):
        self.event('revoke_permission','export',target=self.grant);self.failed('REVOKE_TARGET_SCOPE')

    def test_unrelated_subject_deny_does_not_block(self):
        value=self.event('deny_permission');value['subject']=ref(b'other\n')
        self.assertEqual(self.check()['status'],'permission_granted_in_declared_context')

    def test_unknown_unrelated_event_not_filtered(self):
        value=self.event('deny_permission');value['subject']=ref(b'other\n');value['decision']='future_kind';self.failed('DOCUMENT_SCHEMA')

    def test_duplicate_event_id_or_wrong_path(self):
        self.packet();raw=next(iter(self.maps.values()));self.maps['permission-events/'+uid()+'.json']=raw
        ctx=json.loads(self.ctx);ctx['known_events']=[dict(path=p,**ref(b)) for p,b in sorted(self.maps.items())]
        self.ctx=enc(ctx);self.authority=A['establish_local_authority'](self.ctx,ref(self.ctx),trust_owner_controlled_context=True)
        req=json.loads(self.req);req['context']=ref(self.ctx);self.req=enc(req)
        self.assertEqual(self.check(False)['status'],'failed')

    def test_old_context_rejected_by_external_current_pin(self):
        self.current=ref(b'new protected context\n');self.failed('REFERENCE_MISMATCH')

    def test_same_old_context_is_not_freshness_or_claim(self):
        self.export();self.packet();a=self.check(False);b=self.check(False)
        self.assertEqual(a,b);self.assertIn('freshness',a['not_checked']);self.assertIn('single_use_claim',a['not_checked'])

    def test_generation_native_and_exact(self):
        for generation in [True,1.0]:
            self.generation=generation
            with self.assertRaises(A['PermissionBlocked']):self.packet()
        self.generation=1;req=self.packet();req['generation']=2;self.req=enc(req);self.failed('CONTEXT_BINDING',False)

    def test_duplicate_keys_constants_bom_crlf_and_trailing_lf(self):
        self.packet();raw=self.req
        for value in [b'\xef\xbb\xbf'+raw,raw.replace(b'\n',b'\r\n'),raw+b'\n',b'{"x":1,"x":2}\n',b'{"x":NaN}\n']:
            self.req=value;self.assertEqual(self.check(False)['status'],'failed')

    def test_reference_float_and_bool_rejected(self):
        for value in [True,2.0]:
            req=self.packet();req['subject']['size_bytes']=value;self.req=enc(req);self.failed('NATIVE_INTEGER_REQUIRED',False)

    def test_unsafe_and_duplicate_subject_paths(self):
        old=copy.deepcopy(self.subject['artifacts'])
        for paths in [['../a'],['/a'],['a\\b'],['a:a'],['a','a']]:
            self.subject['artifacts']=[dict(path=p,**ref(b'a\n')) for p in paths]
            self.grant['subject']=ref(enc(self.subject));self.assertEqual(self.check()['status'],'failed')
        self.subject['artifacts']=old

    def test_inputs_not_mutated_no_output_writes(self):
        self.packet();before=copy.deepcopy((self.events,self.subject,self.maps))
        with patch('pathlib.Path.write_bytes',side_effect=AssertionError('write')),patch('os.mkdir',side_effect=AssertionError('mkdir')):
            self.assertEqual(self.check(False)['status'],'permission_granted_in_declared_context')
        self.assertEqual(before,(self.events,self.subject,self.maps))

    def test_installed_pin_change_stops(self):
        self.packet();pins=copy.deepcopy(A['PINS']);next(iter(pins.values()))['sha256']='0'*64
        with patch.dict(A['evaluate_permission'].__globals__,PINS=pins):self.failed('REFERENCE_MISMATCH',False)

    def test_limits_before_parsing(self):
        self.packet()
        with patch.dict(A['evaluate_permission'].__globals__,TOTAL=1):self.failed('TOTAL_LIMIT',False)
        with patch.dict(A['evaluate_permission'].__globals__,COUNT=0):self.failed('EVENT_SET_LIMIT',False)
        self.req=b'x'*(A['LIMIT']+1);self.failed('REFERENCE_MISMATCH',False)


    def test_safe_result_refs_and_context_repr(self):
        self.packet();r=self.check(False)
        self.assertEqual(r['request'],ref(self.req));self.assertEqual(r['subject'],ref(enc(self.subject)))
        self.assertNotIn('local_owner_context',repr(self.authority))
        self.assertNotIn('payload/a.md',json.dumps(r))



class NativeGuardTests(unittest.TestCase):
    setUp=AuthorityTests.setUp
    event=AuthorityTests.event
    export=AuthorityTests.export
    packet=AuthorityTests.packet

    def fixture(self,export=False):
        cls=OLD['PermissionProposalTests'];cls.setUpClass();self.f=cls('test_release_proposal_consistent_but_blocked');self.f.setUp()
        if export:self.f.export()
        f=self.f
        self.subject.update(candidate=ref(f.candidate),registry=ref(f.registry),coverage_description=ref(f.candidate),
                            artifacts=[dict(path=p,**ref(b)) for p,b in sorted(f.payloads.items())],
                            entity_decisions=[dict(path=p,**ref(b)) for p,b in sorted(f.decisions.items())],
                            procedure=ref(f.payloads['protocols/ent-0012/r0001/governance.md']),
                            prompt=ref(f.payloads['transfer/ent-0012/r0001/prompt.md']))
        self.grant['subject']=ref(enc(self.subject))
        if export:self.export()
        self.packet()

    def check_native(self):
        f=self.f;raw=enc(f.request)
        return A['check_current_candidate'](self.req,ref(self.req),enc(self.subject),ref(enc(self.subject)),self.maps,
                 authority=self.authority,expected_current_context=ref(self.ctx),proposal_bytes=raw,expected_proposal=ref(raw),
                 candidate_bytes=f.candidate,expected_candidate=ref(f.candidate),registry_blob=f.registry,
                 entity_decisions=f.decisions,payloads=f.payloads,release_request_bytes=f.parent)

    def test_native_release_authority_but_incomplete_no_injection(self):
        self.fixture();r=self.check_native();self.assertEqual(r['status'],'blocked_incomplete_candidate',r)
        self.assertTrue(r['authority_valid']);self.assertEqual(r['readiness'],'incomplete_candidate')
        self.assertFalse(r['release_allowed'])

    def test_native_export_authority_but_incomplete_no_injection(self):
        self.fixture(True);r=self.check_native();self.assertEqual(r['status'],'blocked_incomplete_candidate',r)
        self.assertTrue(r['export_permission_recognized']);self.assertFalse(r['performed'])

    def test_ready_boolean_not_supported(self):
        self.fixture();c=json.loads(self.f.candidate);c['readiness']='ready';self.f.candidate=enc(c)
        self.subject.update(candidate=ref(self.f.candidate),coverage_description=ref(self.f.candidate))
        self.f.request['candidate']=ref(self.f.candidate)
        self.grant['subject']=ref(enc(self.subject));self.packet()
        r=self.check_native();self.assertEqual(r['status'],'failed',r)
        self.assertIn('native_legacy_candidate_and_scope_guard',r['checks'])

    def test_candidate_mutation_even_with_reapproved_synthetic_context(self):
        self.fixture();self.f.payloads[next(iter(self.f.payloads))]+=b'changed'
        self.assertEqual(self.check_native()['diagnostics'],['CURRENT_ARTIFACT_BINDING'])

    def test_real_profile_wrong_pinned_procedure(self):
        self.fixture();self.subject['procedure']=ref(b'wrong\n');self.grant['subject']=ref(enc(self.subject));self.packet()
        self.assertEqual(self.check_native()['diagnostics'],['CURRENT_PROCEDURE_BINDING'])

    def test_native_input_limit_before_hashing(self):
        self.fixture()
        with patch.dict(A['check_current_candidate'].__globals__,COUNT=10):
            self.assertEqual(self.check_native()['diagnostics'],['CURRENT_INPUT_LIMIT'])


    def test_actual_entity_scope_block_not_bypassed_by_positive_authority(self):
        for export in [False,True]:
            with self.subTest(export=export):
                self.setUp();self.fixture(export)
                component=json.loads(self.f.candidate)['components'][-1]
                event=json.loads(self.f.decisions[component['record']['approval']['reference']['path']])
                event.update(decision_id=uid(),decision_type='revoke_use',reason='Synthetic only',
                             scope=dict(operations=['export' if export else 'release'],
                                        areas=['agent_system.transfer' if export else 'agent_system.release']))
                self.f.decisions['catalog/approvals/'+event['decision_id']+'.json']=enc(event)
                rows=[dict(path=p,**ref(b)) for p,b in sorted(self.f.decisions.items())]
                self.f.request['decisions']=rows
                if export:
                    parent=json.loads(self.f.parent);parent['decisions']=rows
                    self.f.parent=enc(parent);self.f.request['release_request']=ref(self.f.parent)
                self.subject['entity_decisions']=rows
                for e in self.events:e['subject']=ref(enc(self.subject))
                if export:self.grant['parent']=er(self.events[0])
                self.packet();r=self.check_native()
                self.assertEqual(r['status'],'blocked_known_scope',r)
                self.assertTrue(r['authority_valid']);self.assertFalse(r['release_allowed']);self.assertFalse(r['export_allowed'])



if __name__=='__main__':unittest.main(verbosity=2)
