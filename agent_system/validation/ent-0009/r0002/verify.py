#!/usr/bin/env python3
"""Plan execution regressions; synthetic source, no actual permission or activation."""
import copy
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[2]
MODULE = runpy.run_path(str(HERE / 'execute.py'))
execute = MODULE['execute_plan']
G = execute.__globals__
Blocked = MODULE['PlanBlocked']
ref = MODULE['reference']
encode = MODULE['_encode']
FIXTURES = runpy.run_path(str(BASE / 'validation/ent-0006/r0003/verify.py'))


class PlanExecutionTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.fixture = FIXTURES['BindingGraphTests']()
        self.fixture.make_fixture(1)
        self.sync()

    def sync(self):
        blobs = dict(self.fixture.artifacts, **self.fixture.witnesses)
        blobs['catalog/registry.json'] = encode(self.fixture.registry)
        for name, data in blobs.items():
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        self.plan = dict(schema_version='1', kind='validation_plan',
                         plan_id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
                         catalog_id=self.fixture.registry['catalog_id'],
                         execution_profile=MODULE['PROFILE'],
                         expectation_authority='caller_supplied_not_authenticated',
                         context=dict(operation='export', area='local'), selection=self.fixture.selection,
                         registry=dict(path='catalog/registry.json', **ref(blobs['catalog/registry.json'])),
                         artifacts=[dict(path=p, **ref(b)) for p,b in self.fixture.artifacts.items()],
                         decisions=[dict(path=p, **ref(b)) for p,b in self.fixture.witnesses.items()])

    def run_plan(self):
        raw = encode(self.plan)
        result = execute(self.root, raw, ref(raw))
        self.result = result
        report = json.loads(result['report_bytes'])
        self.assertFalse(report['transition_allowed'])
        return report

    def child(self, report, stage):
        return json.loads(self.result['documents'][report['stages'][stage]['evidence']['sha256']])

    def preflight(self, code):
        tools = G['_load']()
        read = tools[2]['read_set']
        with patch.dict(tools[2], read_set=lambda *a, **k: self.fail('source read during preflight')):
            with patch.dict(G, _load=lambda: tools):
                with self.assertRaises(Blocked) as context:
                    self.run_plan()
        tools[2]['read_set'] = read
        self.assertEqual(context.exception.code, code)
        self.assertNotIn(str(self.root), str(context.exception))

    def changed_child(self, change):
        tools = list(G['_load']())
        checker = tools[3]
        def wrong(*args, **kwargs):
            value = checker(*args, **kwargs)
            change(value)
            return value
        tools[3] = wrong
        with patch.dict(G, _load=lambda: tools):
            return self.run_plan()

    def test_positive_exact_documents(self):
        report = self.run_plan()
        self.assertEqual(report['status'], 'passed_known_inputs')
        for pointer in [report['plan'], *[s['evidence'] for s in report['stages'].values()]]:
            self.assertEqual(ref(self.result['documents'][pointer['sha256']]), pointer)
        self.assertEqual(report['plan_id'], self.plan['plan_id'])

    def test_context_byte_substitution_blocked(self):
        raw = encode(self.plan)
        self.plan['context']['operation'] = 'activate'
        with self.assertRaises(Blocked) as context:
            execute(self.root, encode(self.plan), ref(raw))
        self.assertEqual(context.exception.code, 'PLAN_REFERENCE_MISMATCH')

    def test_selection_byte_substitution_blocked(self):
        raw = encode(self.plan)
        self.plan['selection'][0]['revision'] = 'r0002'
        with self.assertRaises(Blocked):
            execute(self.root, encode(self.plan), ref(raw))

    def test_duplicate_path_preflight(self):
        self.plan['artifacts'].append(dict(self.plan['artifacts'][0], sha256='b'*64))
        self.preflight('PLAN_DUPLICATE_PATH')

    def test_registry_duplicate_preflight(self):
        self.plan['artifacts'].append(copy.deepcopy(self.plan['registry']))
        self.preflight('PLAN_DUPLICATE_PATH')

    def test_wrong_selection_catalog_preflight(self):
        self.plan['selection'][0]['catalog_id'] = self.plan['plan_id']
        self.preflight('PLAN_CATALOG_MISMATCH')

    def test_aggregate_limit_preflight(self):
        self.plan['artifacts'] = [dict(path=f'fixtures/{i}',sha256='a'*64,size_bytes=16*1024*1024) for i in range(5)]
        self.preflight('PLAN_SET_LIMIT')

    def test_non_native_integer_preflight(self):
        self.plan['registry']['size_bytes'] = float(self.plan['registry']['size_bytes'])
        self.preflight('PLAN_SIZE_TYPE')

    def test_unknown_profile_no_fallback(self):
        self.plan['execution_profile'] = 'latest'
        self.preflight('PLAN_SCHEMA')

    def test_ambiguous_json_no_source(self):
        raw = b'{"x":1,"x":2}\n'
        with self.assertRaises(Blocked) as context:
            execute(self.root,raw,ref(raw))
        self.assertEqual(context.exception.code,'PLAN_PARSE_OR_SCHEMA')

    def test_large_plan_rejected(self):
        with self.assertRaises(Blocked) as context:
            execute(self.root,b' '*(MODULE['LIMIT']+1),{})
        self.assertEqual(context.exception.code,'INVALID_PLAN_BYTES_OR_LIMIT')

    def test_missing_final_lf(self):
        raw = encode(self.plan).rstrip(b'\n')
        with self.assertRaises(Blocked) as context:
            execute(self.root,raw,ref(raw))
        self.assertEqual(context.exception.code,'PLAN_SERIALIZATION')

    def test_extra_decision_blocks_before_binding(self):
        (self.root/'catalog/approvals/.hidden').write_bytes(b'unknown')
        report = self.run_plan()
        self.assertEqual(report['status'],'failed')
        self.assertEqual(report['stages']['binding']['status'],'not_run')
        self.assertNotIn('evidence',report['stages']['acquisition'])

    def test_mismatched_bytes_blocks_before_binding(self):
        (self.root/self.plan['artifacts'][0]['path']).write_bytes(b'changed')
        report = self.run_plan()
        self.assertEqual(report['status'],'failed')
        self.assertEqual(report['stages']['binding']['status'],'not_run')

    def test_known_scope_block_not_permission(self):
        self.fixture.add_restriction()
        self.sync()
        report = self.run_plan()
        self.assertEqual(report['status'],'blocked_known_scope')
        self.assertEqual(report['stages']['binding']['diagnostics'],[dict(code='KNOWN_SCOPE_BLOCK')])
        self.assertEqual(self.child(report,'binding')['diagnostics'],[])

    def test_source_catalog_mismatch_is_binding_failure(self):
        self.plan['catalog_id'] = self.plan['plan_id']
        self.plan['selection'][0]['catalog_id'] = self.plan['plan_id']
        report = self.run_plan()
        self.assertEqual(report['stages']['acquisition']['status'],'passed_known_inputs')
        self.assertEqual(report['stages']['binding']['diagnostics'],[dict(code='SOURCE_CATALOG_MISMATCH')])

    def test_child_context_substitution(self):
        report=self.changed_child(lambda c:c['restriction_evaluation']['context'].update(operation='activate'))
        self.assertEqual(report['stages']['binding']['diagnostics'],[dict(code='CHILD_RESULT_MISMATCH')])

    def test_child_selection_substitution(self):
        report=self.changed_child(lambda c:c.update(selected_closure=[]))
        self.assertEqual(report['status'],'failed')

    def test_child_input_substitution(self):
        report=self.changed_child(lambda c:c['inputs'][0].update(sha256='0'*64))
        self.assertEqual(report['status'],'failed')

    def test_child_cannot_grant_admission(self):
        report=self.changed_child(lambda c:c.update(transition_allowed=True))
        self.assertEqual(report['status'],'failed')

    def test_acquisition_payload_substitution(self):
        tools=list(G['_load']());reader=tools[2];original=reader['read_set']
        def wrong(*args,**kwargs):
            value=original(*args,**kwargs);value['artifacts'][self.plan['artifacts'][0]['path']]=b'forged';return value
        with patch.dict(reader,read_set=wrong),patch.dict(G,_load=lambda:tools):
            report=self.run_plan()
        self.assertEqual(report['stages']['binding']['status'],'not_run')
        self.assertEqual(report['status'],'failed')

    def test_event_input_substitution(self):
        report=self.changed_child(lambda c:c['restriction_evaluation']['inputs'][0].update(sha256='0'*64))
        self.assertEqual(report['status'],'failed')

    def test_acquisition_inventory_substitution(self):
        tools=list(G['_load']());reader=tools[2];original=reader['read_set']
        def wrong(*args,**kwargs):
            value=original(*args,**kwargs);value['evidence']['directory_after']['entries']=[];return value
        with patch.dict(reader,read_set=wrong),patch.dict(G,_load=lambda:tools):report=self.run_plan()
        self.assertEqual(report['stages']['binding']['status'],'not_run')
        self.assertEqual(report['status'],'failed')

    def test_interruption_does_not_invent_report(self):
        tools=list(G['_load']())
        def interrupted(*a,**k):raise KeyboardInterrupt()
        tools[3]=interrupted
        with patch.dict(G,_load=lambda:tools):
            with self.assertRaises(KeyboardInterrupt):self.run_plan()

    def test_missing_engine_is_unsupported(self):
        from importlib import metadata
        with patch.object(metadata,'version',side_effect=metadata.PackageNotFoundError('jsonschema')):
            with self.assertRaises(Blocked) as context:self.run_plan()
        self.assertEqual(context.exception.code,'INSTALLED_PROFILE_UNAVAILABLE')
        self.assertTrue(context.exception.unsupported)

    def test_installed_pin_change_no_fallback(self):
        path=next(iter(MODULE['PINS']))
        pins={path:dict(MODULE['PINS'][path],sha256='0'*64)}
        with patch.dict(G,PINS=pins):
            with self.assertRaises(Blocked) as context:self.run_plan()
        self.assertEqual(context.exception.code,'INSTALLED_PROFILE_CHANGED')
        self.assertTrue(context.exception.unsupported)

    def test_unexpected_stage_failure_no_old_result(self):
        tools=list(G['_load']())
        def fail(*a,**k):raise OSError('private details')
        tools[3]=fail
        with patch.dict(G,_load=lambda:tools):report=self.run_plan()
        self.assertEqual(report['stages']['binding']['diagnostics'],[dict(code='STAGE_UNAVAILABLE')])
        self.assertNotIn('private details',self.result['report_bytes'].decode())

    def test_document_limit_no_silent_truncation(self):
        with self.assertRaises(Blocked):encode({'x':'x'*MODULE['LIMIT']})

    def test_repeated_runs_keep_plan_new_run_id(self):
        first=self.run_plan();second=self.run_plan()
        self.assertEqual(first['plan'],second['plan'])
        self.assertNotEqual(first['run_id'],second['run_id'])

    def test_no_source_writes(self):
        before={p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.run_plan()
        after={p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before,after)


class CaptureContractTests(PlanExecutionTests):
    """Mirror the 30 legacy scenarios through the full capture surface."""
    def setUp(self):
        super().setUp()
        def captured(*args, **kwargs):
            result = MODULE['capture_plan'](*args, **kwargs)
            self.assertEqual(set(result), {'report_bytes', 'documents', 'capture'})
            if json.loads(result['report_bytes'])['status'] == 'passed_known_inputs':
                value = result['capture']
                self.assertEqual(set(value), {'registry', 'artifacts', 'decisions'})
                self.assertEqual(value['registry'], (self.root/'catalog/registry.json').read_bytes())
                self.assertEqual(value['artifacts'], self.fixture.artifacts)
                self.assertEqual(value['decisions'], self.fixture.witnesses)
            else:
                self.assertIsNone(result['capture'])
            return result
        replacement = patch.dict(PlanExecutionTests.run_plan.__globals__, execute=captured)
        replacement.start()
        self.addCleanup(replacement.stop)


class HandoffTests(unittest.TestCase):
    setUp = PlanExecutionTests.setUp
    sync = PlanExecutionTests.sync
    run_plan = PlanExecutionTests.run_plan
    def capture(self):
        raw = encode(self.plan)
        return MODULE['capture_plan'](self.root, raw, ref(raw))

    def test_r1_metadata_semantics_unchanged(self):
        legacy = runpy.run_path(str(HERE.parent/'r0001/execute.py'))['execute_plan']
        raw = encode(self.plan)
        old = legacy(self.root, raw, ref(raw))
        new = execute(self.root, raw, ref(raw))
        first, second = json.loads(old['report_bytes']), json.loads(new['report_bytes'])
        first.pop('run_id'); second.pop('run_id')
        self.assertEqual(first, second)
        self.assertEqual(old['documents'], new['documents'])

    def test_success_capture_supports_offline_semantic_replay(self):
        value = self.capture()
        captured = value['capture']
        payloads = dict(captured['artifacts'], **captured['decisions'])
        payloads['catalog/registry.json'] = captured['registry']
        verify = runpy.run_path(str(BASE/'validation/ent-0010/r0001/bundle.py'))['verify_bundle']
        report = json.loads(value['report_bytes'])
        result = verify(value['report_bytes'], ref(value['report_bytes']), report['plan'],
                        value['documents'], payloads)
        self.assertEqual(result['status'], 'consistent_recorded_bundle')
        self.assertFalse(result['transition_allowed'])

    def test_one_acquisition_per_surface(self):
        for call in (execute, MODULE['capture_plan']):
            with self.subTest(surface=call.__name__):
                tools = list(G['_load']())
                with patch.dict(tools[2], read_set=Mock(wraps=tools[2]['read_set'])):
                    spy = tools[2]['read_set']
                    with patch.dict(G, _load=lambda: tools):
                        raw = encode(self.plan)
                        call(self.root, raw, ref(raw))
                    self.assertEqual(spy.call_count, 1)

    def test_metadata_projection_shape(self):
        self.run_plan()
        self.assertEqual(set(self.result), {'report_bytes', 'documents'})

    def test_no_source_reread_after_binding(self):
        tools = list(G['_load']()); checker = tools[3]
        expected = dict(self.fixture.artifacts)
        def change_source(*a, **k):
            value = checker(*a, **k)
            for path in self.plan['artifacts']:
                (self.root/path['path']).write_bytes(b'changed after acquisition')
            return value
        tools[3] = change_source
        with patch.dict(G, _load=lambda: tools):
            result = self.capture()
        self.assertEqual(result['capture']['artifacts'], expected)
        self.assertTrue(all(type(b) is bytes for b in result['capture']['artifacts'].values()))

    def test_capture_owned_maps(self):
        tools = list(G['_load']()); read = tools[2]['read_set']; observed = []
        def remember(*a, **k):
            value = read(*a, **k); observed.append(value); return value
        with patch.dict(tools[2], read_set=remember), patch.dict(G, _load=lambda: tools):
            result = self.capture()
        value = result['capture']
        self.assertIsNot(value['artifacts'], observed[0]['artifacts'])
        self.assertIsNot(value['decisions'], observed[0]['decisions'])
        observed[0]['artifacts'].clear(); observed[0]['decisions'].clear()
        self.assertEqual(value['artifacts'], self.fixture.artifacts)
        self.assertEqual(value['decisions'], self.fixture.witnesses)
        self.assertNotIn('catalog/registry.json', value['artifacts'])

    def test_final_schema_failure_returns_nothing(self):
        tools = list(G['_load']()); validators = list(tools[1])
        validators[1] = Mock(is_valid=lambda value: False)
        tools[1] = validators
        with patch.dict(G, _load=lambda: tools):
            with self.assertRaises(Blocked) as error:
                self.capture()
        self.assertEqual(error.exception.code, 'RUN_ENVELOPE_INVALID')

    def test_final_serialization_failure_returns_nothing(self):
        original = G['_encode']
        def final_error(value):
            if value.get('kind') == 'validation_run_report':
                raise Blocked('DOCUMENT_LIMIT')
            return original(value)
        with patch.dict(G, _encode=final_error):
            with self.assertRaises(Blocked) as error:
                self.capture()
        self.assertEqual(error.exception.code, 'DOCUMENT_LIMIT')

    def test_failure_after_success_cannot_reuse_maps(self):
        first = self.capture()
        self.assertIsNotNone(first['capture'])
        (self.root/self.plan['artifacts'][0]['path']).write_bytes(b'bad')
        second = self.capture()
        self.assertIsNone(second['capture'])
        self.assertEqual(json.loads(second['report_bytes'])['status'], 'failed')
        self.assertEqual(first['capture']['artifacts'], self.fixture.artifacts)

    def test_successful_repeated_captures_are_independent(self):
        first = self.capture(); second = self.capture()
        self.assertIsNot(first['capture'], second['capture'])
        self.assertIsNot(first['capture']['artifacts'], second['capture']['artifacts'])
        first['capture']['artifacts'].clear()
        self.assertEqual(second['capture']['artifacts'], self.fixture.artifacts)

    def test_no_capture_after_late_child_mismatch(self):
        tools = list(G['_load']()); checker = tools[3]
        def wrong(*a, **k):
            value = checker(*a, **k)
            value['transition_allowed'] = True
            return value
        tools[3] = wrong
        with patch.dict(G, _load=lambda: tools):
            result = self.capture()
        self.assertIsNone(result['capture'])
        self.assertEqual(json.loads(result['report_bytes'])['status'], 'failed')

    def test_no_capture_for_unsupported_reader(self):
        tools = list(G['_load']())
        def unsupported(*a, **k):
            raise tools[2]['ReadBlocked']('UNSUPPORTED_PLATFORM')
        with patch.dict(tools[2], read_set=unsupported), patch.dict(G, _load=lambda: tools):
            result = self.capture()
        self.assertIsNone(result['capture'])
        self.assertEqual(json.loads(result['report_bytes'])['status'], 'unsupported')

    def test_no_capture_for_failed_binding(self):
        tools = list(G['_load']())
        def fail(*a, **k):
            raise OSError('private details')
        tools[3] = fail
        with patch.dict(G, _load=lambda: tools):
            result = self.capture()
        self.assertIsNone(result['capture'])
        self.assertNotIn(b'private details', result['report_bytes'])

    def test_capture_does_not_write_source(self):
        before = {p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.capture()
        self.assertEqual(before, {p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main(verbosity=2)
