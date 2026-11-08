"""Pinned offline successful-journal replay, never current permissions or execution proof."""
from pathlib import Path
import re
import runpy
import uuid

HERE=Path(__file__).resolve().parent


class ReplayBlocked(Exception):
    def __init__(self,code):self.code=code;super().__init__(code)


def _load():
    runner=runpy.run_path(str(HERE/'run.py'))
    try:return runner,runner['_load']()
    except runner['OperatorBlocked']:raise ReplayBlocked('REPLAY_INSTALLATION_UNAVAILABLE') from None


def _keys(value,names):
    if type(value) is not dict or set(value)!=set(names.split()):raise ReplayBlocked('REPLAY_SHAPE')


def _uuid(value):
    if type(value) is not str or str(uuid.UUID(value))!=value:raise ReplayBlocked('REPLAY_UUID')


def replay_operator_run(run_id,expected_index):
    """No source/trial/live-ledger reads. Failed journals are explicitly partial.

    External index pin/immutable trusted installation required. Consistent claims
    can be fabricated; this API authenticates neither execution nor the caller.
    """
    try:
        r,t=_load();s=t['s'];ref=s['reference'];canon=r['_canonical'];parse=t['parse']
        index,objects=t['e']['_read_evidence'](run_id,expected_index,with_capture=True)
        used=set()
        def raw(pointer):
            t['e']['_pin'](pointer)
            value=objects[pointer['sha256']];s['_pin'](value,pointer);used.add(pointer['sha256']);return value
        def document(pointer):
            value=raw(pointer)
            if not value.endswith(b'\n') or value.endswith(b'\n\n') or b'\r' in value:raise ReplayBlocked('REPLAY_SERIALIZATION')
            return parse(value)
        metadata=index['metadata'];_keys(metadata,'kind journal')
        if metadata['kind']!='operator_run_index':raise ReplayBlocked('NOT_OPERATOR_EVIDENCE')
        journal=document(metadata['journal']);_keys(journal,'kind session profile human_report run_id terminal_claim seal_confirmation')
        if (journal['kind']!='operator_run_journal' or journal['run_id']!=run_id
                or journal['seal_confirmation']!='external_receipt_required'):raise ReplayBlocked('JOURNAL_BINDING')
        snapshot=document(journal['profile']);_keys(snapshot,'kind profile records procedure prompt')
        if snapshot['kind']!='operator_profile_snapshot':raise ReplayBlocked('PROFILE_SNAPSHOT')
        profile=snapshot['profile'];_keys(profile,'catalog_id selection artifacts candidate');cid=profile['catalog_id'];_uuid(cid)
        own_prefix='operator/ent-0018/r0001/'
        expected=dict(s['PINS'])
        for name in r['OWN']:expected[own_prefix+name]=ref(r['_installed'](own_prefix+name))
        expected_rows=[dict(path=p,**v) for p,v in sorted(expected.items())]
        if (canon(profile['artifacts'])!=canon(expected_rows) or profile['selection']!=[dict(catalog_id=cid,entity_id='ENT-0018',revision='r0001')]
                or canon(profile['candidate'])!=canon(s['PINS']['candidates/ent-0013/r0001/candidate.json'])):
            raise ReplayBlocked('REPLAY_PROFILE_MISMATCH')
        records={}
        if type(snapshot['records']) is not list:raise ReplayBlocked('PROFILE_RECORDS')
        for row in snapshot['records']:
            _keys(row,'subject record');subject=row['subject'];_keys(subject,'catalog_id entity_id revision')
            key=(subject['entity_id'],subject['revision'])
            if subject['catalog_id']!=cid or key in records:raise ReplayBlocked('PROFILE_RECORDS')
            records[key]=row['record']
        identities={('ENT-'+m[0],m[1]) for path in s['PINS'] for m in re.findall(r'ent-(\d{4})/(r\d{4})(?:/|\.md$)',path)}|{('ENT-0018','r0001')}
        if set(records)!=identities:raise ReplayBlocked('PROFILE_RECORDS')
        own=records[('ENT-0018','r0001')]
        if (own['kind']!='protocol' or own['scopes']!=['agent_system.operator_trial'] or own['approval']['status']!='approved'
                or len(own['relations'])!=len(r['DEPENDENCIES'])
                or any(x['type']!='depends_on' or x['target']['catalog_id']!=cid for x in own['relations'])
                or {(x['target']['entity_id'],x['target']['revision']) for x in own['relations']}!=r['DEPENDENCIES']):
            raise ReplayBlocked('REPLAY_PROFILE_MISMATCH')
        composition={}
        for key,record in records.items():
            if record['revision']!=key[1]:raise ReplayBlocked('PROFILE_RECORDS')
            for artifact in record['artifacts']:
                if artifact['path'] in composition or artifact['role']!='normative':raise ReplayBlocked('PROFILE_COMPOSITION')
                composition[artifact['path']]={k:artifact[k] for k in ['sha256','size_bytes']}
        if canon(composition)!=canon(expected):raise ReplayBlocked('PROFILE_COMPOSITION')
        for name in ['procedure','prompt']:
            pointer={k:v for k,v in expected[own_prefix+name+'.md'].items()}
            if canon(snapshot[name])!=canon(pointer):raise ReplayBlocked('PROTOCOL_REFERENCE')
            raw(snapshot[name])
        session_raw=raw(journal['session']);session=parse(session_raw)
        plans={p['sha256']:raw(p) for p in [session['plan_a']]+([session['plan_b']] if session['plan_b'] is not None else [])}
        prepared=s['validate_session'](session_raw,journal['session'],plans,profile,has_source_b=session['plan_b'] is not None)
        claim=journal['terminal_claim']
        _keys(claim,'profile operator_run_id status task_id purpose overall_admission current_permissions transition_allowed release_allowed export_allowed activation_allowed steps query capture_invocations completed_source_reports validated_captures source_acquisition_calls evidence_sealed not_checked diagnostics')
        if (claim['operator_run_id']!=run_id or claim['task_id']!=session['task_id'] or claim['evidence_sealed'] is not False):raise ReplayBlocked('TERMINAL_BINDING')
        if raw(journal['human_report'])!=r['format_operator_result'](claim).encode():raise ReplayBlocked('HUMAN_REPORT_BINDING')
        out=dict(overall_admission='not_evaluated',current_permissions='not_evaluated',**{f:False for f in r['FLAGS']},
                 not_checked=list(r['NOT_CHECKED']),run_id=run_id)
        success=['trial_checked_no_query','trial_checked_with_known_query_no_admission']
        if claim['status'] not in success:
            return dict(out,status='recorded_partial_run_no_full_replay',full_replay=False,
                        recorded_status=claim['status'],not_replayed=['failed_or_blocked_child_semantics','missing_raw_failed_capture'])
        b=session['plan_b'] is not None;count=2 if b else 1
        if (claim['status']!=success[1 if b else 0] or claim['diagnostics']!=[]
                or any(type(claim[k]) is not int or claim[k]!=count for k in ['capture_invocations','completed_source_reports','validated_captures','source_acquisition_calls'])):
            raise ReplayBlocked('TERMINAL_COUNTERS_OR_STATUS')
        steps=claim['steps'];_keys(steps,'source_a candidate stage reader handoff source_b comparison')
        def step(name,status,source=False):
            entry=steps[name];_keys(entry,'status document child_run_id' if source else 'status document')
            if entry['status']!=status:raise ReplayBlocked('STEP_STATUS')
            return document(entry['document'])
        child_ids=[]
        def source(name,which):
            bundle=step(name,'passed_known_inputs',True);_keys(bundle,'kind plan report documents inputs')
            if bundle['kind']!='operator_source_bundle' or type(bundle['documents']) is not list or type(bundle['inputs']) is not list:raise ReplayBlocked('SOURCE_BUNDLE')
            if canon(bundle['plan'])!=canon(session['plan_a' if which==0 else 'plan_b']):raise ReplayBlocked('SOURCE_PLAN_BINDING')
            docmap={p['sha256']:raw(p) for p in bundle['documents']}
            if len(docmap)!=len(bundle['documents']):raise ReplayBlocked('SOURCE_DOCUMENT_SET')
            inputs={}
            for row in bundle['inputs']:
                _keys(row,'path sha256 size_bytes')
                if row['path'] in inputs:raise ReplayBlocked('SOURCE_INPUT_SET')
                inputs[row['path']]=raw({k:row[k] for k in ['sha256','size_bytes']})
            plan=prepared['plans'][which]
            cap=dict(registry=inputs['catalog/registry.json'],artifacts={x['path']:inputs[x['path']] for x in plan['artifacts']},
                     decisions={x['path']:inputs[x['path']] for x in plan['decisions']})
            if set(inputs)!={'catalog/registry.json',*cap['artifacts'],*cap['decisions']}:raise ReplayBlocked('SOURCE_INPUT_SET')
            packet=dict(report_bytes=raw(bundle['report']),documents=docmap,capture=cap)
            report,captured,_=r['_source_packet'](t,packet,plans[bundle['plan']['sha256']],plan,records)
            r['_passed'](report,'passed_known_inputs')
            bound=t['parse'](docmap[report['stages']['binding']['evidence']['sha256']])
            expected_closure={(x['entity_id'],x['revision']) for x in bound['selected_closure']}
            if expected_closure!=set(records):raise ReplayBlocked('SOURCE_CLOSURE')
            if steps[name]['child_run_id']!=report['run_id'] or report['run_id'] in child_ids:raise ReplayBlocked('CHILD_RUN_BINDING')
            child_ids.append(report['run_id'])
            return captured
        a=source('source_a',0);candidate=a['artifacts']['candidates/ent-0013/r0001/candidate.json'];descriptor=parse(candidate)
        payloads={x['path']:a['artifacts'][x['path']] for c in descriptor['components'] for x in c['record']['artifacts']}
        actual=t['candidate']['check_candidate'](candidate,session['candidate'],a['registry'],a['decisions'],payloads)
        r['_passed'](actual,'consistent_incomplete_candidate')
        if canon(step('candidate','consistent_incomplete_candidate'))!=canon(actual):raise ReplayBlocked('CANDIDATE_REPLAY')
        r['_scope'](t,a,profile['selection'],'stage_trial','agent_system.trial')
        receipt=step('stage','staged_trial_only');reader=step('reader','consistent_archived_trial')
        r['_scope'](t,a,profile['selection'],'read_trial','agent_system.trial')
        handoff=step('handoff','passed');_keys(handoff,'manifest objects')
        if type(handoff['objects']) is not list:raise ReplayBlocked('HANDOFF_OBJECT_SET')
        archive=dict(manifest_bytes=raw(handoff['manifest']),objects={p['sha256']:raw(p) for p in handoff['objects']})
        if len(archive['objects'])!=len(handoff['objects']):raise ReplayBlocked('HANDOFF_OBJECT_SET')
        archive=r['_handoff'](t,receipt,dict(result=reader,capture=archive),candidate,a,payloads)
        if b:
            current=source('source_b',1);r['_scope'](t,current,profile['selection'],**session['query'])
            comparison=step('comparison','compared_known_views_no_admission');_keys(comparison,'plan result')
            plan_raw=raw(comparison['plan']);plan=parse(plan_raw);_uuid(plan['plan_id'])
            expected=dict(schema_version='1',kind='known_view_comparison_plan',plan_id=plan['plan_id'],archive_manifest=handoff['manifest'],
                          current_registry=ref(current['registry']),current_decisions=[dict(path=p,**ref(v)) for p,v in sorted(current['decisions'].items())],context=session['query'])
            if canon(plan)!=canon(expected):raise ReplayBlocked('DERIVED_PLAN_BINDING')
            actual=t['compare']['compare_views'](plan_raw,comparison['plan'],archive['manifest_bytes'],archive['objects'],current['registry'],current['decisions'])
            r['_passed'](actual,'compared_known_views_no_admission')
            if canon(actual)!=canon(comparison['result']) or claim['query']!=actual['status']:raise ReplayBlocked('COMPARISON_REPLAY')
        elif steps['source_b']!={'status':'not_run'} or steps['comparison']!={'status':'not_run'} or claim['query']!='not_requested':
            raise ReplayBlocked('UNREQUESTED_QUERY')
        if used!=set(objects):raise ReplayBlocked('UNREFERENCED_EVIDENCE_OBJECT')
        return dict(out,status='consistent_recorded_operator_run_no_admission',full_replay=True,
                    recorded_status=claim['status'],source_bundles=count,objects_count=len(objects))
    except ReplayBlocked:raise
    except (OSError,ValueError,TypeError,KeyError,RuntimeError,ImportError,RecursionError,AttributeError):
        raise ReplayBlocked('REPLAY_INVALID') from None
    except Exception as error:
        if 't' not in locals() or not isinstance(error,(t['e']['EvidenceBlocked'],t['s']['SessionBlocked'],r['OperatorBlocked'],t['n']['PlanBlocked'])):raise
        raise ReplayBlocked('REPLAY_BINDING_FAILED') from None
