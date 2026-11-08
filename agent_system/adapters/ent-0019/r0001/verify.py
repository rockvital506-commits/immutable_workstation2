"""Synthetic declarations + physical private lineage; never actual environment grants."""
import copy
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch
import uuid

HERE=Path(__file__).resolve().parent;BASE=HERE.parents[2]
M=runpy.run_path(str(HERE/'binding.py'));G=M['assess_binding'].__globals__
enc=M['encode'];ref=M['reference'];Blocked=M['BindingBlocked']


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.tools=M['_load']();e=self.tools[-1];stage,reader=e['_tools']();self.stage=stage
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        p=patch.dict(e['EvidenceStore'].__enter__.__globals__,BASE=self.root,_tools=lambda:(stage,reader));p.start();self.addCleanup(p.stop)
        p=patch.dict(G,_load=lambda:self.tools);p.start();self.addCleanup(p.stop)
        arts=[dict(path=M['PREFIX']+n,**ref((HERE/n).read_bytes()),role='normative') for n in M['OWN']]
        # SYNTHETIC metadata fixture, NOT an actual approved R5 descriptor.
        self.comp=dict(kind='inactive_transfer_composition',status='prepared_inactive',composition_coverage='not_evaluated',
                       components=[dict(subject=dict(entity_id='ENT-0019',revision='r0001'),record=dict(artifacts=arts))],
                       observed_artifacts=[{k:a[k] for k in ['path','sha256','size_bytes']} for a in arts],
                       **{k:v for k,v in M['_flags']().items() if k!='binding_state'})
        self.observation=b'SYNTHETIC declared evidence, not a real observation.\n';self.context=ref(b'SYNTHETIC existing context\n')
        self.env=dict(kind='environment_snapshot',environment_id=str(uuid.uuid4()),revision=1,observation_level='declared_demo',
                      capabilities=[dict(id='host.io',state='available',evidence=ref(self.observation))],constraints=[])
        self.adapter=dict(kind='adapter_declaration',adapter_id=str(uuid.uuid4()),revision=1,verification_level='declaration_only',
                          rule=self.comp['observed_artifacts'][0],requires=['host.io'],provides=['binding.evidence'],conflicts=[])
        self.requirements=[dict(capability='binding.evidence',mandatory=True),dict(capability='host.optional',mandatory=False)]
        self.adapters=[self.adapter]

    def packet(self):
        env=enc(self.env);comp=enc(self.comp);adapters=[enc(a) for a in self.adapters]
        docs={ref(b)['sha256']:b for b in [env,comp,*adapters]}
        if any(row['evidence'] is not None for row in self.env['capabilities']):docs[ref(self.observation)['sha256']]=self.observation
        req=dict(kind='inactive_binding_request',request_id=str(uuid.uuid4()),environment=ref(env),composition=ref(comp),scope='synthetic.scope',
                 existing_context=self.context,requirements=self.requirements,adapters=[ref(a) for a in adapters])
        return req,docs

    def assess(self):
        req,docs=self.packet();self.result=M['assess_binding'](enc(req),ref(enc(req)),docs,self.context,acknowledge_inactive_only=True)
        return json.loads(self.result['assessment_bytes'])

    def save(self,parent=None):
        self.assess();return M['save_binding'](self.result,predecessor=parent,trust_private_namespace=True)

    def flags(self,r):
        for k,v in M['_flags']().items():self.assertEqual(type(r[k]),type(v));self.assertEqual(r[k],v)

    def test_positive_declared_resolution_is_inactive_not_ready(self):
        a=self.assess();self.assertEqual(a['status'],'declared_conditions_satisfied');self.flags(a)
        self.assertEqual(a['optional_limitations'],['host.optional']);self.assertEqual(a['verification_level'],'declaration_resolution_only')

    def test_unknown_unavailable_mandatory_host_not_available(self):
        for state in ['unknown','unavailable']:
            self.env['capabilities'][0]['state']=state
            a=self.assess();self.assertEqual(a['status'],'blocked_declared_requirements');self.assertEqual(a['mandatory_blockers'],['binding.evidence'])

    def test_false_ack_before_loader_and_wrong_pin(self):
        req,docs=self.packet()
        for ack in [False,1,'true',None]:
            with patch.dict(G,_load=lambda:self.fail('loader called')),self.assertRaises(Blocked):M['assess_binding'](enc(req),ref(enc(req)),docs,self.context,acknowledge_inactive_only=ack)
        with self.assertRaises(Blocked):M['assess_binding'](enc(req),ref(b'wrong'),docs,self.context,acknowledge_inactive_only=True)

    def test_unknown_fields_commands_and_verified_claim_rejected(self):
        original=copy.deepcopy(self.adapter)
        for change in [dict(command='DO NOT EXECUTE'),dict(verification_level='verified'),dict(activation_allowed=True)]:
            self.adapter.update(change)
            with self.assertRaises(Blocked):self.assess()
            self.adapter.clear();self.adapter.update(original)

    def test_native_float_revisions_and_ref_sizes_rejected(self):
        self.env['revision']=1.0
        with self.assertRaises(Blocked):self.assess()
        self.env['revision']=1;self.adapter['rule']['size_bytes']=float(self.adapter['rule']['size_bytes'])
        with self.assertRaises(Blocked):self.assess()

    def test_extra_missing_and_changed_evidence_not_ignored(self):
        req,docs=self.packet()
        for changed in [dict(docs,**{ref(b'extra')['sha256']:b'extra'}),{k:v for k,v in docs.items() if k!=ref(self.observation)['sha256']},dict(docs,**{ref(self.observation)['sha256']:b'changed'})]:
            with self.assertRaises(Blocked):M['assess_binding'](enc(req),ref(enc(req)),changed,self.context,acknowledge_inactive_only=True)

    def test_available_requires_pinned_observation(self):
        self.env['capabilities'][0]['evidence']=None
        with self.assertRaises(Blocked):self.assess()

    def test_conflict_blocks_even_unneeded_adapter(self):
        self.env['constraints']=['no-demo'];self.adapter['conflicts']=['no-demo'];self.requirements=[]
        a=self.assess();self.assertEqual(a['status'],'blocked_declared_requirements');self.assertEqual(a['unresolved_adapters'][0]['reason'],'declared_conflict')

    def test_cycles_and_self_providers_do_not_bootstrap(self):
        self.adapter['requires']=['binding.evidence']
        self.assertEqual(self.assess()['status'],'blocked_declared_requirements')
        other=copy.deepcopy(self.adapter);other.update(adapter_id=str(uuid.uuid4()),requires=['binding.evidence'],provides=['binding.second'])
        self.adapter['requires']=['binding.second'];self.adapters.append(other)
        self.assertEqual(len(self.assess()['unresolved_adapters']),2)

    def test_fixed_point_order_independent(self):
        other=copy.deepcopy(self.adapter);other.update(adapter_id=str(uuid.uuid4()),requires=['binding.evidence'],provides=['binding.second'])
        self.adapters=[other,self.adapter];self.requirements=[dict(capability='binding.second',mandatory=True)]
        self.assertEqual(self.assess()['status'],'declared_conditions_satisfied')

    def test_duplicate_provider_adapter_host_requirement_rejected(self):
        other=copy.deepcopy(self.adapter);other['adapter_id']=str(uuid.uuid4());self.adapters.append(other)
        with self.assertRaises(Blocked):self.assess()
        self.adapters=[self.adapter];self.env['capabilities'].append(self.env['capabilities'][0])
        with self.assertRaises(Blocked):self.assess()
        self.env['capabilities'].pop();self.requirements.append(self.requirements[0])
        with self.assertRaises(Blocked):self.assess()

    def test_adapter_cannot_provide_host_or_reference_noncomposition_rule(self):
        self.adapter['provides']=['host.io']
        with self.assertRaises(Blocked):self.assess()
        self.adapter['provides']=['binding.evidence'];self.adapter['rule']['path']='private/file'
        with self.assertRaises(Blocked):self.assess()

    def test_missing_component_and_action_claims_in_composition_block(self):
        self.comp['activation_allowed']=True
        with self.assertRaises(Blocked):self.assess()
        self.comp['activation_allowed']=False;self.comp['components']=[]
        with self.assertRaises(Blocked):self.assess()

    def test_expected_context_is_separate(self):
        req,docs=self.packet()
        with self.assertRaises(Blocked):M['assess_binding'](enc(req),ref(enc(req)),docs,ref(b'new context'),acknowledge_inactive_only=True)

    def test_physical_private_history_and_immutable_parent(self):
        parent=self.save();before={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.env['revision']=2;self.env['capabilities'][0].update(state='unknown',evidence=None)
        child=self.save(parent);summary=M['inspect_history'](child);self.flags(summary);self.assertEqual(summary['nodes_count'],2)
        for p,b in before.items():self.assertEqual(p.read_bytes(),b)
        for p in self.root.rglob('*'):self.assertEqual(p.stat().st_mode&0o777,0o700 if p.is_dir() else 0o600)

    def test_forks_are_inactive_not_current(self):
        parent=self.save();one=self.save(parent);two=self.save(parent)
        self.assertNotEqual(one['run_id'],two['run_id'])
        for r in [one,two]:self.assertTrue(M['inspect_history'](r)['draft_forks_not_current_selection'])

    def test_changed_environment_requires_revision_advance(self):
        parent=self.save();self.env['constraints']=['changed']
        with self.assertRaises(Blocked):self.save(parent)
        self.env['revision']=2;self.save(parent)

    def test_wrong_family_or_scope_predecessor_rejected(self):
        parent=self.save();self.env['environment_id']=str(uuid.uuid4())
        with self.assertRaises(Blocked):self.save(parent)

    def test_missing_corrupt_predecessor_stops_before_writes(self):
        parent=self.save();path=self.root/'local/operator-runs'/parent['run_id']/'index.json';raw=path.read_bytes();path.write_bytes(raw+b'x')
        before=set((self.root/'local/operator-runs').iterdir())
        with self.assertRaises(Blocked):self.save(parent)
        self.assertEqual(before,set((self.root/'local/operator-runs').iterdir()))

    def test_lineage_cap_before_new_node(self):
        parent=self.save()
        with patch.dict(G,MAX_LINEAGE=1),self.assertRaises(Blocked):self.save(parent)
        self.assertEqual(len(list((self.root/'local/operator-runs').iterdir())),1)

    def test_assessment_tamper_and_save_ack_block(self):
        self.assess()
        with self.assertRaises(Blocked):M['save_binding'](self.result)
        a=json.loads(self.result['assessment_bytes']);a['activation_allowed']=True;self.result['assessment_bytes']=enc(a)
        with self.assertRaises(Blocked):M['save_binding'](self.result,trust_private_namespace=True)
        self.assertFalse((self.root/'local').exists())

    def test_activation_proposal_never_grant_or_action(self):
        parent=self.save();p=M['activation_proposal'](parent,self.context);self.flags(p)
        self.assertEqual(p['status'],'activation_not_authorized');self.assertEqual(len(p['required_gates']),5)
        with self.assertRaises(Blocked):M['activation_proposal'](parent,ref(b'wrong'))

    def test_write_failure_retains_partial_no_receipt(self):
        self.assess();stage=self.stage
        def bad(*a,**k):raise OSError('SYNTHETIC failure')
        with patch.dict(stage,_write_file=bad),self.assertRaises(Blocked):M['save_binding'](self.result,trust_private_namespace=True)
        self.assertEqual(len(list((self.root/'local/operator-runs').iterdir())),1)

    def test_limits_and_demo_ack(self):
        with self.assertRaises(Blocked):M['run_declared_demo']()
        req,docs=self.packet()
        with patch.dict(G,TOTAL=1),self.assertRaises(Blocked):M['assess_binding'](enc(req),ref(enc(req)),docs,self.context,acknowledge_inactive_only=True)


    def test_wrong_scope_successor_rejected(self):
        parent=self.save();req,docs=self.packet();req['scope']='other.scope';raw=enc(req)
        result=M['assess_binding'](raw,ref(raw),docs,self.context,acknowledge_inactive_only=True)
        with self.assertRaises(Blocked):M['save_binding'](result,predecessor=parent,trust_private_namespace=True)

    def test_coherently_forged_assessment_recomputed_on_inspection(self):
        parent=self.save();run=self.root/'local/operator-runs'/parent['run_id'];objects=run/'objects'
        index=json.loads((run/'index.json').read_bytes());old_record=index['metadata']['record'];node=json.loads((objects/old_record['sha256']).read_bytes())
        old_assessment=node['assessment'];a=json.loads((objects/old_assessment['sha256']).read_bytes());a['status']='blocked_declared_requirements'
        raw_a=enc(a);node['assessment']=ref(raw_a);raw_node=enc(node)
        index['metadata']['record']=ref(raw_node)
        index['objects']=[r for r in index['objects'] if r['sha256'] not in [old_record['sha256'],old_assessment['sha256']]]+[ref(raw_a),ref(raw_node)]
        index['objects'].sort(key=lambda r:r['sha256'])
        # Adversarial rewrites/deletes only in this disposable synthetic fixture.
        for r in [old_record,old_assessment]:(objects/r['sha256']).unlink()
        for raw in [raw_a,raw_node]:
            p=objects/ref(raw)['sha256'];p.write_bytes(raw);p.chmod(0o600)
        raw=enc(index);(run/'index.json').write_bytes(raw);forged=dict(run_id=parent['run_id'],index=ref(raw))
        with self.assertRaises(Blocked) as caught:M['inspect_history'](forged)
        self.assertEqual(caught.exception.code,'HISTORY_ASSESSMENT_REPLAY')


if __name__=='__main__':unittest.main(verbosity=2)
