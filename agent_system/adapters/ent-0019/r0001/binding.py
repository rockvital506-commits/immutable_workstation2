"""Inactive declared binding assessment/history. No host survey/activation actuator."""
import copy
import hashlib
import json
from pathlib import Path
import runpy
import uuid

BASE=Path(__file__).resolve().parents[3]
PREFIX='adapters/ent-0019/r0001/'
OWN=['binding.py','binding.schema.json','procedure.md','prompt.md','usage.md','verify.py']
LIMIT=16*1024*1024
TOTAL=64*1024*1024
MAX_LINEAGE=32
PINS={'transfer/ent-0012/r0002/prepare.py': {'sha256': 'fc0db8b9063b35d926b0240984fcde9d6bb90dbde470a25864727294d8d4c344', 'size_bytes': 19657}, 'transfer/ent-0012/r0002/preparation.schema.json': {'sha256': '4bb5139908226a3ae7894df60dc5092a7f35c5dad3bb0c6623ea1bd90017ea4f', 'size_bytes': 1289}, 'transfer/ent-0012/r0002/procedure.md': {'sha256': '566c5ba67ce471e881d131d5273718c49c9a1e35ba9c8bf122c565b4b3ed0f7b', 'size_bytes': 3879}, 'transfer/ent-0012/r0002/prompt.md': {'sha256': '1c5e7a9300e964812c755ecbd187984db0faa818371b19cd93ea67777dfc4917', 'size_bytes': 2706}, 'transfer/ent-0012/r0002/usage.md': {'sha256': '4773ba46e35c51559ace42590eff5de988c9abab67fe4421d4f4df134b6cca41', 'size_bytes': 4762}, 'transfer/ent-0012/r0002/verify.py': {'sha256': 'f1b4bcf30a52818cbc5eb59699981d5f94b60ee84abeea3681891d5f759e8169', 'size_bytes': 14322}, 'operator/ent-0018/r0001/acceptance_verify.py': {'sha256': '479dcc4a54d3ca5d2f7cf5a8a844d987ce6b90050955a66abfcea4b66c94aae9', 'size_bytes': 11722}, 'operator/ent-0018/r0001/evidence.py': {'sha256': '255bffc084d40ce598248ddda687249dcf548992ab4bc386a12cdaeb997f972f', 'size_bytes': 9453}, 'operator/ent-0018/r0001/lab.py': {'sha256': 'b14bebf61d26e2e2f6291db9c4d7d2a982b907488682c06a4acb7675cb98cc0f', 'size_bytes': 4182}, 'operator/ent-0018/r0001/procedure.md': {'sha256': '54f41439a8399f89e6d11dd7fd8ac95569e0bfce96667df5c3bb7bb4e2d0ccbd', 'size_bytes': 7077}, 'operator/ent-0018/r0001/prompt.md': {'sha256': '87f5ca9e72f58442981602d7910178c13b49f80ab931333d373f4f20c58be378', 'size_bytes': 2307}, 'operator/ent-0018/r0001/replay.py': {'sha256': '95ce2ad08944b1a8fe6d74b27a30f97f087b12b6ff159397b8b1876144fe5e37', 'size_bytes': 12615}, 'operator/ent-0018/r0001/replay_verify.py': {'sha256': 'b2ecd0a50dfb99452ffc910f89954f17a0e4700f61c198895a3dffcb5051a864', 'size_bytes': 8421}, 'operator/ent-0018/r0001/run.py': {'sha256': '68d3251e7b212b673b6705b32855f554829d76147467a18262e208635b4b1c00', 'size_bytes': 23614}, 'operator/ent-0018/r0001/runner_verify.py': {'sha256': 'd7451bdf77d030f11811472f83ccc3d43e1fb05004832b181a6029a05fa2df6e', 'size_bytes': 17076}, 'operator/ent-0018/r0001/session.py': {'sha256': '789a60c5b09744f804bfb3e9685eb63796fbfdeb561376aace5fc2bca8e82aad', 'size_bytes': 12464}, 'operator/ent-0018/r0001/session.schema.json': {'sha256': '76a3030a1f107a92e24cc80af978b0b1c9a0c5c0f16718829b8907a51a66e76f', 'size_bytes': 2856}, 'operator/ent-0018/r0001/usage.md': {'sha256': '13eeeab847fa30e15e6cce444a1b2cdd9982cf5147035aed8dfa25aadac12679', 'size_bytes': 12012}, 'operator/ent-0018/r0001/verify.py': {'sha256': '444b7ea06dd237a1720573ff0cb9e88d12a3b97cd30e7987372c7d931a71ee3a', 'size_bytes': 13735}, 'adapters/ent-0019/r0001/binding.schema.json': {'sha256': '8574b6e627b213c2931553bf1cb28ad7b9935c3f62193deedd3e3f20e1f24560', 'size_bytes': 5899}, 'adapters/ent-0019/r0001/procedure.md': {'sha256': '535af257111ab3e558adddd8da0f96d44592aaeb2cf19482c5ec18a2b38d60fe', 'size_bytes': 4219}, 'adapters/ent-0019/r0001/prompt.md': {'sha256': '14bc47aaedce77955facdf4d611b1dba5bbc4c61025170e8c6870a5b525a588b', 'size_bytes': 2065}}


class BindingBlocked(Exception):
    def __init__(self,code):self.code=code;super().__init__(code)


def _stop(code):raise BindingBlocked(code)
def reference(raw):return dict(sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))
def encode(value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    if len(raw)>LIMIT:_stop('DOCUMENT_LIMIT')
    return raw


def _ref(r):
    if (type(r) is not dict or set(r)!={'sha256','size_bytes'} or type(r['size_bytes']) is not int
            or not 0<=r['size_bytes']<=LIMIT or type(r['sha256']) is not str or len(r['sha256'])!=64
            or any(c not in '0123456789abcdef' for c in r['sha256'])):_stop('INVALID_REFERENCE')


def _pin(raw,r):
    _ref(r)
    if type(raw) is not bytes or len(raw)>LIMIT or reference(raw)!=r:_stop('REFERENCE_MISMATCH')


def _flags():return dict(overall_admission='not_evaluated',binding_state='inactive',performed=False,transition_allowed=False,compatible_release_allowed=False,release_allowed=False,export_allowed=False,activation_allowed=False,current_binding_changed=False)


def _load():
    try:
        for p,r in PINS.items():
            with (BASE/p).open('rb') as f:raw=f.read(r['size_bytes']+1)
            _pin(raw,r)
        prep=runpy.run_path(str(BASE/'transfer/ent-0012/r0002/prepare.py'))
        t=prep['_tools']();parse=t[1];validator=t[2]
        schema=parse((BASE/(PREFIX+'binding.schema.json')).read_bytes())
        type(validator).check_schema(schema)
        from referencing import Registry
        def deny(_):raise ValueError('External schema forbidden')
        def doc(raw,r,kind):
            _pin(raw,r)
            if not raw.endswith(b'\n') or raw.endswith(b'\n\n') or b'\r' in raw:_stop('DOCUMENT_SERIALIZATION')
            value=parse(raw)
            def native(x):
                if type(x) is dict:
                    for k,v in x.items():
                        if (k=='size_bytes' or (k=='revision' and kind in ['environment','adapter'])) and type(v) is not int:_stop('NATIVE_INTEGER_REQUIRED')
                        native(v)
                elif type(x) is list:
                    for v in x:native(v)
            native(value)
            if kind and not type(validator)({**schema,'$ref':'#/$defs/'+kind},format_checker=validator.format_checker,registry=Registry(retrieve=deny)).is_valid(value):_stop('DOCUMENT_SCHEMA')
            return value
        return prep,doc,t[-1]
    except BindingBlocked:raise
    except Exception:_stop('INSTALLED_PROFILE_UNAVAILABLE')


def _component(comp):
    if comp.get('kind')!='inactive_transfer_composition' or comp.get('status')!='prepared_inactive' or comp.get('composition_coverage')!='not_evaluated':_stop('COMPOSITION_PROFILE')
    for k,v in _flags().items():
        if k=='binding_state':continue
        if type(comp[k]) is not type(v) or comp[k]!=v:_stop('COMPOSITION_ACTION_CLAIM')
    own=[c for c in comp['components'] if c['subject']['entity_id']=='ENT-0019' and c['subject']['revision']=='r0001']
    if len(own)!=1:_stop('BINDING_COMPONENT_MISSING')
    arts=own[0]['record']['artifacts']
    if {a['path'] for a in arts}!={PREFIX+n for n in OWN} or len(arts)!=len(OWN):_stop('BINDING_COMPONENT_SET')
    for a in arts:
        with (BASE/a['path']).open('rb') as f:raw=f.read(LIMIT+1)
        if a['role']!='normative':_stop('BINDING_COMPONENT_ROLE')
        _pin(raw,{k:a[k] for k in ['sha256','size_bytes']})
    observed={(a['path'],a['sha256'],a['size_bytes']) for a in comp['observed_artifacts']}
    if not {(a['path'],a['sha256'],a['size_bytes']) for a in arts}<=observed:_stop('COMPONENT_OBSERVATION_BINDING')
    return observed


def assess_binding(request_bytes,expected_request,documents,expected_existing_context,*,acknowledge_inactive_only=False):
    """Declared input resolution, NOT observation truth/semantics/permission."""
    if acknowledge_inactive_only is not True:_stop('EXPLICIT_INACTIVE_ACK_REQUIRED')
    try:
        _pin(request_bytes,expected_request);_ref(expected_existing_context)
        if type(documents) is not dict or len(documents)>1000:_stop('DOCUMENT_SET_LIMIT')
        docs=dict(documents)
        if any(type(b) is not bytes or len(b)>LIMIT for b in docs.values()) or sum(map(len,docs.values()))+len(request_bytes)>TOTAL:_stop('INPUT_LIMIT')
        for sha,raw in docs.items():
            if reference(raw)['sha256']!=sha:_stop('DOCUMENT_HASH')
        prep,doc,evidence=_load();req=doc(request_bytes,expected_request,'request')
        if req['existing_context']!=expected_existing_context:_stop('CURRENT_CONTEXT_MISMATCH')
        env=doc(docs[req['environment']['sha256']],req['environment'],'environment')
        comp=doc(docs[req['composition']['sha256']],req['composition'],None);rules=_component(comp)
        adapters=[doc(docs[r['sha256']],r,'adapter') for r in req['adapters']]
        refs=[req['environment'],req['composition'],*req['adapters']]
        caps={};available=set();constraints=set(env['constraints'])
        for row in env['capabilities']:
            if row['id'] in caps:_stop('DUPLICATE_HOST_CAPABILITY')
            caps[row['id']]=row['state']
            if row['state']!='unknown' and row['evidence'] is None:_stop('OBSERVATION_EVIDENCE_MISSING')
            if row['evidence'] is not None:
                r=row['evidence'];_pin(docs[r['sha256']],r);refs.append(r)
            if row['state']=='available':available.add(row['id'])
        if set(docs)!={r['sha256'] for r in refs}:_stop('EXACT_DOCUMENT_SET')
        if len({r['capability'] for r in req['requirements']})!=len(req['requirements']):_stop('DUPLICATE_REQUIREMENT')
        ids=set();providers=set()
        for a in adapters:
            if a['adapter_id'] in ids:_stop('DUPLICATE_ADAPTER_ID')
            ids.add(a['adapter_id'])
            if tuple(a['rule'][k] for k in ['path','sha256','size_bytes']) not in rules:_stop('ADAPTER_RULE_OUTSIDE_COMPOSITION')
            if len(set(a['provides']))!=len(a['provides']) or providers.intersection(a['provides']):_stop('DUPLICATE_PROVIDER')
            providers.update(a['provides'])
        pending=list(adapters);resolved=[]
        while pending:
            ready=[a for a in pending if not constraints.intersection(a['conflicts']) and set(a['requires'])<=available]
            if not ready:break
            for a in ready:
                pending.remove(a);available.update(a['provides']);resolved.append(a['adapter_id'])
        rows=[dict(capability=r['capability'],mandatory=r['mandatory'],declared_satisfied=r['capability'] in available) for r in req['requirements']]
        missing=[r['capability'] for r in rows if r['mandatory'] and not r['declared_satisfied']]
        # Even unused unresolved declarations remain visible and block a fully resolved draft.
        blocked=[dict(adapter_id=a['adapter_id'],reason='declared_conflict' if constraints.intersection(a['conflicts']) else 'unresolved_prerequisite') for a in pending]
        assessment=dict(kind='inactive_binding_assessment',assessment_id=str(uuid.uuid4()),status='blocked_declared_requirements' if missing or blocked else 'declared_conditions_satisfied',
                        request=expected_request,environment=req['environment'],environment_id=env['environment_id'],environment_revision=env['revision'],
                        composition=req['composition'],scope=req['scope'],existing_context=req['existing_context'],verification_level='declaration_resolution_only',
                        requirements=rows,mandatory_blockers=missing,optional_limitations=[r['capability'] for r in rows if not r['mandatory'] and not r['declared_satisfied']],
                        resolved_adapters=resolved,unresolved_adapters=blocked,not_checked=['environment_observation_truth','adapter_semantics_preservation','composition_origin_authentication',
                        'core_coverage','current_context_freshness','activation_authority','actuator_result','agent_behavior'],**_flags())
        return dict(assessment_bytes=encode(assessment),request_bytes=request_bytes,documents=docs)
    except BindingBlocked:raise
    except (OSError,ValueError,TypeError,KeyError,RuntimeError,ImportError,RecursionError,AttributeError):_stop('INPUT_OR_PROFILE_INVALID')


def _history(receipt,evidence):
    seen=set();nodes=[];total=0;current=receipt
    while current is not None:
        if type(current) is not dict or set(current)!={'run_id','index'}:_stop('PREDECESSOR_REFERENCE')
        if current['run_id'] in seen or len(nodes)>=MAX_LINEAGE:_stop('LINEAGE_LIMIT_OR_CYCLE')
        seen.add(current['run_id'])
        index,objects=evidence['_read_evidence'](current['run_id'],current['index'],with_capture=True)
        total+=sum(len(b) for b in objects.values())+current['index']['size_bytes']
        if total>128*1024*1024:_stop('LINEAGE_BYTE_LIMIT')
        meta=index['metadata']
        if set(meta)!={'kind','record'} or meta['kind']!='inactive_binding_history':_stop('HISTORY_KIND')
        _pin(objects[meta['record']['sha256']],meta['record']);node=json.loads(objects[meta['record']['sha256']])
        if set(node)!={'kind','binding_id','assessment','inputs','predecessor'} or node['kind']!='inactive_binding_node' or node['binding_id']!=current['run_id']:_stop('NODE_SHAPE')
        _pin(objects[node['assessment']['sha256']],node['assessment']);assessment=json.loads(objects[node['assessment']['sha256']])
        for k,v in _flags().items():
            if type(assessment[k]) is not type(v) or assessment[k]!=v:_stop('HISTORY_ACTION_CLAIM')
        for r in node['inputs']:_pin(objects[r['sha256']],r)
        if set(objects)!={r['sha256'] for r in [meta['record'],node['assessment'],*node['inputs']]}:_stop('HISTORY_OBJECT_SET')
        req=assessment['request'];input_shas={r['sha256'] for r in node['inputs']}
        if req['sha256'] not in input_shas:_stop('HISTORY_REQUEST_MISSING')
        replay=assess_binding(objects[req['sha256']],req,{sha:objects[sha] for sha in input_shas if sha!=req['sha256']},assessment['existing_context'],acknowledge_inactive_only=True)
        replayed=json.loads(replay['assessment_bytes']);replayed['assessment_id']=assessment['assessment_id']
        if encode(replayed)!=encode(assessment):_stop('HISTORY_ASSESSMENT_REPLAY')
        nodes.append(dict(binding_id=node['binding_id'],assessment=assessment,predecessor=node['predecessor']))
        current=node['predecessor']
    for child,parent in zip(nodes,nodes[1:]):_successor(child['assessment'],parent['assessment'])
    return nodes


def _successor(new,old):
    if new['environment_id']!=old['environment_id'] or new['scope']!=old['scope']:_stop('PREDECESSOR_ENVIRONMENT_OR_SCOPE')
    if new['environment']!=old['environment'] and new['environment_revision']<=old['environment_revision']:_stop('ENVIRONMENT_REVISION_NOT_ADVANCED')


def save_binding(result,*,predecessor=None,trust_private_namespace=False):
    """Immutable draft node; forks are drafts, never current/active selection."""
    if trust_private_namespace is not True:_stop('EXPLICIT_PRIVATE_NAMESPACE_REQUIRED')
    try:
        prep,doc,evidence=_load();assessment=json.loads(result['assessment_bytes'])
        req=doc(result['request_bytes'],assessment['request'],'request')
        # Recompute through protected code from the retained inputs, no caller result injection.
        actual=assess_binding(result['request_bytes'],assessment['request'],result['documents'],req['existing_context'],acknowledge_inactive_only=True)
        new=json.loads(actual['assessment_bytes']);new['assessment_id']=assessment['assessment_id']
        if encode(new)!=result['assessment_bytes']:_stop('ASSESSMENT_REPLAY_MISMATCH')
        parents=_history(copy.deepcopy(predecessor),evidence) if predecessor is not None else []
        if len(parents)+1>MAX_LINEAGE:_stop('LINEAGE_LIMIT_OR_CYCLE')
        if parents:_successor(assessment,parents[0]['assessment'])
        with evidence['EvidenceStore']() as store:
            inputs=[store.put(raw) for raw in [result['request_bytes'],*result['documents'].values()]]
            assessed=store.put(result['assessment_bytes'])
            node=dict(kind='inactive_binding_node',binding_id=store.run_id,assessment=assessed,inputs=inputs,predecessor=copy.deepcopy(predecessor))
            record=store.put(encode(node));receipt=store.seal(dict(kind='inactive_binding_history',record=record))
        _history(receipt,evidence)
        return receipt
    except BindingBlocked:raise
    except Exception:_stop('HISTORY_UNAVAILABLE_OR_PARTIAL')


def inspect_history(receipt):
    try:
        *_,evidence=_load();nodes=_history(copy.deepcopy(receipt),evidence)
        return dict(status='consistent_inactive_lineage',binding_id=nodes[0]['binding_id'],nodes_count=len(nodes),draft_forks_not_current_selection=True,**_flags())
    except BindingBlocked:raise
    except Exception:_stop('HISTORY_INVALID')


def activation_proposal(receipt,expected_existing_context):
    try:
        *_,evidence=_load();node=_history(copy.deepcopy(receipt),evidence)[0];_ref(expected_existing_context)
        if node['assessment']['existing_context']!=expected_existing_context:_stop('CURRENT_CONTEXT_MISMATCH')
        return dict(status='activation_not_authorized',binding_id=node['binding_id'],required_gates=['qualified_composition_and_binding_checks','explicit_exact_owner_activation_decision',
                    'protected_current_context_and_negative_decisions','implemented_actuator','observed_result_verification'],**_flags())
    except BindingBlocked:raise
    except Exception:_stop('ACTIVATION_PROPOSAL_INVALID')


def run_declared_demo(*,acknowledge_demo_only=False):
    """Native installed composition + declared fixture, NOT a survey of this host."""
    if acknowledge_demo_only is not True:_stop('EXPLICIT_DEMO_ACK_REQUIRED')
    prep,doc,evidence=_load()
    raw_request,raw_plan=prep['installed_packet'](trust_installed_namespace=True)
    plan=json.loads(raw_plan);request=json.loads(raw_request)
    registry=json.loads((BASE/'catalog/registry.json').read_bytes())
    own=next(v for e in registry['entities'] if e['entity_id']=='ENT-0019' for v in e['revisions'] if v['revision']=='r0001')
    plan['selection'].append(dict(catalog_id=registry['catalog_id'],entity_id='ENT-0019',revision='r0001'))
    plan['artifacts'].extend({k:a[k] for k in ['path','sha256','size_bytes']} for a in own['artifacts'])
    raw_plan=encode(plan);request['plan']=reference(raw_plan);raw_request=encode(request)
    prepared=prep['prepare_inactive'](BASE,raw_request,reference(raw_request),raw_plan,reference(raw_plan),acknowledge_inactive_only=True)
    if prepared['status']!='prepared_inactive':_stop('DEMO_COMPOSITION_PREPARATION_FAILED')
    source_receipt=prep['persist_preparation'](prepared,trust_private_namespace=True)
    comp=prepared['manifest_bytes'];value=json.loads(comp)
    rule=next(a for a in value['observed_artifacts'] if a['path']==PREFIX+'procedure.md')
    evidence_raw=b'DECLARED DEMO ONLY; no host capability was observed.\n'
    context=reference(b'DECLARED DEMO CONTEXT, not actual active platform context.\n')
    env=dict(kind='environment_snapshot',environment_id=str(uuid.uuid4()),revision=1,observation_level='declared_demo',
             capabilities=[dict(id='host.demo_signal',state='available',evidence=reference(evidence_raw))],constraints=[])
    adapter=encode(dict(kind='adapter_declaration',adapter_id=str(uuid.uuid4()),revision=1,verification_level='declaration_only',
                       rule=rule,requires=['host.demo_signal'],provides=['binding.inactive_history'],conflicts=[]))
    req=dict(kind='inactive_binding_request',request_id=str(uuid.uuid4()),environment=reference(encode(env)),composition=reference(comp),
             scope='declared-controller-demo',existing_context=context,
             requirements=[dict(capability='binding.inactive_history',mandatory=True),dict(capability='host.unexamined',mandatory=False)],adapters=[reference(adapter)])
    docs={reference(b)['sha256']:b for b in [encode(env),comp,adapter,evidence_raw]}
    result=assess_binding(encode(req),reference(encode(req)),docs,context,acknowledge_inactive_only=True)
    parent=save_binding(result,trust_private_namespace=True)
    env['revision']=2;env['capabilities'][0].update(state='unknown',evidence=None);raw_env=encode(env);req['environment']=reference(raw_env)
    docs={reference(b)['sha256']:b for b in [raw_env,comp,adapter]}
    changed=assess_binding(encode(req),reference(encode(req)),docs,context,acknowledge_inactive_only=True)
    child=save_binding(changed,predecessor=parent,trust_private_namespace=True)
    return dict(source_preparation=source_receipt,binding=child,history=inspect_history(child),
                activation_proposal=activation_proposal(child,context),observation_level='declared_demo',
                parent_assessment=json.loads(result['assessment_bytes'])['status'],child_assessment=json.loads(changed['assessment_bytes'])['status'],**_flags())


if __name__=='__main__':
    import argparse
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--demo-inactive',action='store_true');args=cli.parse_args()
    try:print(json.dumps(run_declared_demo(acknowledge_demo_only=args.demo_inactive)))
    except BindingBlocked as error:print(error.code);raise SystemExit(2)
