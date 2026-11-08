#!/usr/bin/env python3
"""Two-view synthetic byte comparisons, not source discovery or owner permission."""
import copy
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch
import uuid

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[2]
M=runpy.run_path(str(HERE/'compare.py'))
compare=M['compare_views'];ref=M['reference'];encode=M['encode']
FIX={'class':runpy.run_path(str(BASE/'candidates/ent-0013/r0001/verify.py'))['CandidateCoverageTests']}


class KnownViewComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):FIX['class'].setUpClass()

    def setUp(self):
        f=FIX['class'];self.candidate=f.candidate_bytes;self.payloads=dict(f.declared_payloads)
        self.archive_registry=f.registry_bytes;self.archive_decisions=dict(f.witnesses)
        self.current_registry=f.registry_bytes;self.current_decisions=dict(f.witnesses)
        self.context=dict(operation='export',area='agent_system.transfer')
        self.objects={};self.refresh_archive()

    def refresh_archive(self):
        self.objects={}
        def put(raw):
            r=ref(raw);self.objects[r['sha256']]=raw;return r
        self.manifest=dict(schema_version='1',profile='ent-0015-r0001-linux-x86_64-object-store',kind='incomplete_trial_snapshot',
                           run_id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',candidate=put(self.candidate),registry=put(self.archive_registry),
                           payloads=[dict(path=p,**put(b)) for p,b in sorted(self.payloads.items())],
                           decisions=[dict(path=p,**put(b)) for p,b in sorted(self.archive_decisions.items())],
                           readiness='incomplete_candidate',release_allowed=False,export_allowed=False,activation_allowed=False,
                           transition_allowed=False,overall_admission='not_evaluated')

    def plan(self):
        return dict(schema_version='1',kind='known_view_comparison_plan',plan_id='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
                    archive_manifest=ref(encode(self.manifest)),current_registry=ref(self.current_registry),
                    current_decisions=[dict(path=p,**ref(b)) for p,b in sorted(self.current_decisions.items())],context=dict(self.context))

    def check(self,plan=None):
        raw=encode(plan or self.plan());result=compare(raw,ref(raw),encode(self.manifest),self.objects,self.current_registry,self.current_decisions)
        for flag in ['transition_allowed','release_allowed','export_allowed','activation_allowed','performed']:self.assertIs(result[flag],False)
        self.assertEqual(result['current_permissions'],'not_evaluated');return result

    def failure(self,code=None,plan=None):
        r=self.check(plan);self.assertEqual(r['status'],'failed',r)
        if code:self.assertEqual(r['diagnostics'],[dict(code=code)])

    def event(self,kind='revoke_use',target=None,scope=None):
        c=json.loads(self.candidate)['components'][-1]
        event=json.loads(self.archive_decisions[c['record']['approval']['reference']['path']])
        event.update(decision_id=str(uuid.uuid4()),decision_type=kind,reason='Synthetic only',scope=scope or dict(operations=['export'],areas=['agent_system.transfer']))
        if target:
            path,raw=target;event['target']=dict(decision_id=json.loads(raw)['decision_id'],sha256=ref(raw)['sha256'])
        return 'catalog/approvals/'+event['decision_id']+'.json',encode(event)

    def test_same_declared_view_no_admission(self):
        r=self.check();self.assertEqual(r['status'],'compared_known_views_no_admission',r)
        self.assertEqual(r['added_decisions'],0);self.assertEqual(r['archive_query'],'passed_known_inputs')

    def test_added_known_revoke_blocks_requested_scope(self):
        p,b=self.event();self.current_decisions[p]=b;r=self.check()
        self.assertEqual(r['status'],'blocked_known_scope');self.assertEqual(r['archive_query'],'passed_known_inputs')
        self.assertEqual(r['declared_query'],'blocked_known_scope')

    def test_archived_revoke_cannot_be_omitted(self):
        p,b=self.event();self.archive_decisions[p]=b;self.refresh_archive()
        self.failure('ARCHIVED_DECISION_NOT_RETAINED')

    def test_archived_negative_bytes_cannot_change(self):
        p,b=self.event();self.archive_decisions[p]=b;self.current_decisions[p]=b+b' ';self.refresh_archive()
        self.failure('ARCHIVED_DECISION_NOT_RETAINED')

    def test_explicit_lift_retains_old_block_and_only_changes_known_scope(self):
        p,b=self.event();self.archive_decisions[p]=b;self.current_decisions[p]=b;self.refresh_archive()
        q,c=self.event('lift_restriction',target=(p,b));self.current_decisions[q]=c
        r=self.check();self.assertEqual(r['status'],'compared_known_views_no_admission',r)
        self.assertEqual(r['archive_query'],'blocked_known_scope');self.assertEqual(r['declared_query'],'passed_known_inputs')

    def test_lift_one_of_two_does_not_unblock_other(self):
        p,b=self.event();q,c=self.event();self.current_decisions.update({p:b,q:c})
        a,d=self.event('lift_restriction',target=(p,b));self.current_decisions[a]=d
        self.assertEqual(self.check()['status'],'blocked_known_scope')

    def test_other_operation_does_not_mean_prefix_permission(self):
        p,b=self.event(scope=dict(operations=['activate'],areas=['agent_system.transfer']));self.current_decisions[p]=b
        self.assertEqual(self.check()['status'],'compared_known_views_no_admission')

    def test_wildcard_restriction_is_preserved(self):
        p,b=self.event(scope=dict(operations=['*'],areas=['*']));self.current_decisions[p]=b
        self.assertEqual(self.check()['status'],'blocked_known_scope')

    def test_old_view_as_current_is_not_proof_of_freshness(self):
        r=self.check();self.assertEqual(r['status'],'compared_known_views_no_admission')
        self.assertIn('view_freshness',r['not_checked']);self.assertIn('global_event_completeness',r['not_checked'])

    def test_wrong_external_plan_pin(self):
        raw=encode(self.plan());r=compare(raw,dict(ref(raw),sha256='0'*64),encode(self.manifest),self.objects,self.current_registry,self.current_decisions)
        self.assertEqual(r['diagnostics'],[dict(code='PLAN_REFERENCE_MISMATCH')])

    def test_current_registry_pin(self):
        p=self.plan();p['current_registry']['sha256']='0'*64;self.failure('CURRENT_REGISTRY_REFERENCE',p)

    def test_archive_manifest_pin(self):
        p=self.plan();p['archive_manifest']['sha256']='0'*64;self.failure('ARCHIVE_MANIFEST_REFERENCE',p)

    def test_missing_declared_reference(self):
        p=self.plan();p['current_decisions'].pop();self.failure('CURRENT_DECISION_REFERENCES',p)

    def test_duplicate_current_reference(self):
        p=self.plan();p['current_decisions'].append(copy.deepcopy(p['current_decisions'][0]));self.failure(plan=p)

    def test_no_wildcard_query(self):
        self.context['operation']='*';self.failure('QUERY_CONTEXT')

    def test_unknown_plan_field(self):
        p=self.plan();p['export_allowed']=True;self.failure('COMPARISON_SHAPE',p)

    def test_native_sizes_in_plan(self):
        p=self.plan();p['current_decisions'][0]['size_bytes']=float(p['current_decisions'][0]['size_bytes']);self.failure(plan=p)

    def test_corrupt_archive_object(self):
        self.objects[next(iter(self.objects))]=b'changed';self.failure('ARCHIVE_OBJECT_BYTES')

    def test_extra_archive_object(self):
        self.objects['0'*64]=b'extra';self.failure('ARCHIVE_OBJECT_SET')

    def test_missing_archive_object(self):
        self.objects.pop(next(iter(self.objects)));self.failure('ARCHIVE_OBJECT_SET')

    def test_archive_permission_claim(self):
        self.manifest['activation_allowed']=True;self.failure('ARCHIVE_PERMISSION_CLAIM')

    def test_changed_selected_record(self):
        r=json.loads(self.current_registry);r['entities'][0]['revisions'][0]['title']+=' changed';self.current_registry=encode(r)
        self.failure('ARCHIVED_RECORD_NOT_RETAINED')

    def test_changed_unselected_historical_record(self):
        r=json.loads(self.current_registry);entity=next(e for e in r['entities'] if e['entity_id']=='ENT-0002')
        entity['revisions'][0]['title']+=' changed';self.current_registry=encode(r);self.failure('ARCHIVED_RECORD_NOT_RETAINED')

    def test_removed_historical_record(self):
        r=json.loads(self.current_registry);r['entities'][1]['revisions'].pop(0);self.current_registry=encode(r)
        self.failure('ARCHIVED_RECORD_NOT_RETAINED')

    def test_object_key_order_not_record_change(self):
        r=json.loads(self.current_registry)
        for e in r['entities']:
            e['revisions']=[dict(reversed(list(v.items()))) for v in e['revisions']]
        self.current_registry=encode(r);self.assertEqual(self.check()['status'],'compared_known_views_no_admission')

    def test_changed_catalog(self):
        r=json.loads(self.current_registry);r['catalog_id']=str(uuid.uuid4());self.current_registry=encode(r);self.failure('CATALOG_ID_CHANGED')

    def test_unknown_new_event_not_filtered(self):
        p,b=self.event();event=json.loads(b);event['decision_type']='authorize_release';self.current_decisions[p]=encode(event)
        self.assertEqual(self.check()['status'],'unsupported')

    def test_no_output_writes(self):
        with patch('pathlib.Path.write_bytes',side_effect=AssertionError('write')),patch('os.mkdir',side_effect=AssertionError('mkdir')):
            self.assertEqual(self.check()['status'],'compared_known_views_no_admission')

    def test_modified_python_object_not_executed(self):
        row=next(r for r in self.manifest['payloads'] if r['path'].endswith('.py'))
        old=row['sha256'];raw=b'raise AssertionError("Input code executed")\n'
        row.update(ref(raw));self.objects.pop(old);self.objects[row['sha256']]=raw
        self.failure()

    def test_input_mappings_unchanged(self):
        before=copy.deepcopy((self.objects,self.current_decisions,self.manifest));self.check()
        self.assertEqual(before,(self.objects,self.current_decisions,self.manifest))

    def test_installed_pin_change(self):
        pins=copy.deepcopy(M['PINS']);next(iter(pins.values()))['sha256']='0'*64
        with patch.dict(compare.__globals__,PINS=pins):self.assertEqual(self.check()['status'],'unsupported')

    def test_plan_limit_before_loader(self):
        with patch.dict(compare.__globals__,_load=lambda:self.fail('loaded')):
            self.assertEqual(compare(b'x'*(M['LIMIT']+1),{},b'',{},b'',{})['status'],'failed')


if __name__=='__main__':unittest.main(verbosity=2)
