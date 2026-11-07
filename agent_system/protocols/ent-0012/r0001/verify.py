#!/usr/bin/env python3
"""Preparation tests and procedural traceability, NOT exporter or activation tests."""
import copy
import inspect
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[3]
MODULE = runpy.run_path(str(BASE/'transfer/ent-0012/r0001/prepare.py'))
prepare = MODULE['prepare_run']
G = prepare.__globals__
Blocked = MODULE['PreparationBlocked']
ref = MODULE['_ref']
CID = '83bd5866-5e17-477f-9671-4e6a91481221'
ID = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'


def encode(value):
    return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()


class GovernancePreparationTests(unittest.TestCase):
    def setUp(self):
        self.plan = dict(schema_version='1',kind='validation_plan',plan_id=ID,catalog_id=CID,
                         execution_profile='linux-observed-set-5r3-6r3',
                         expectation_authority='caller_supplied_not_authenticated',
                         context=dict(operation='export',area='agent_system.transfer'),
                         selection=[dict(catalog_id=CID,entity_id='ENT-0012',revision='r0001')],
                         registry=dict(path='catalog/registry.json',sha256='0'*64,size_bytes=1),
                         artifacts=[dict(path=path,**ref((BASE/path).read_bytes()))
                                    for path in MODULE['COMPONENT']],decisions=[])

    def receipt(self):
        raw=encode(self.plan)
        output=prepare(raw,ref(raw))
        self.assertIs(type(output),bytes)
        self.assertTrue(output.endswith(b'\n'))
        result=json.loads(output)
        self.assertEqual(result['status'],'prepared_only')
        self.assertEqual(result['overall_admission'],'not_evaluated')
        for name in ['transition_allowed','release_allowed','export_allowed','activation_allowed',
                     'export_performed','activation_performed','current_binding_changed']:
            self.assertIs(result[name],False)
        return result

    def blocked(self,code):
        raw=encode(self.plan)
        with self.assertRaises(Blocked) as context:prepare(raw,ref(raw))
        self.assertEqual(context.exception.code,code)

    def test_positive_freezes_exact_refs(self):
        receipt=self.receipt()
        self.assertEqual(receipt['plan'],ref(encode(self.plan)))
        self.assertEqual(receipt['plan_id'],self.plan['plan_id'])
        self.assertEqual(receipt['context'],self.plan['context'])
        for name,path in [('procedure',MODULE['PROCEDURE']),('prompt',MODULE['PROMPT'])]:
            self.assertEqual(receipt[name],dict(path=path,**MODULE['PINS'][path]))

    def test_no_source_argument_or_execution(self):
        self.assertEqual(list(inspect.signature(prepare).parameters),['plan_bytes','expected_plan'])
        self.plan['artifacts'].append(dict(path='does-not-exist/file.md',sha256='b'*64,size_bytes=12))
        receipt=self.receipt()
        self.assertIn('source_integrity',receipt['not_checked'])
        self.assertIn('dependency_closure',receipt['not_checked'])

    def test_claimed_allowlist_count_not_approval(self):
        receipt=self.receipt()
        self.assertEqual(receipt['declared_file_count'],5)
        self.assertEqual(receipt['declared_bytes'],sum(a['size_bytes'] for a in [self.plan['registry'],*self.plan['artifacts']]))
        self.assertIn('known_restrictions',receipt['not_checked'])
        self.assertIn('mandatory_core_coverage',receipt['not_checked'])

    def test_new_run_id_old_plan_unmodified(self):
        before=copy.deepcopy(self.plan)
        first,second=self.receipt(),self.receipt()
        self.assertNotEqual(first['run_id'],second['run_id'])
        self.assertEqual(first['plan'],second['plan'])
        self.assertEqual(self.plan,before)

    def test_plan_byte_change_requires_new_pin(self):
        raw=encode(self.plan);self.plan['plan_id']=CID
        with self.assertRaises(Blocked) as context:prepare(encode(self.plan),ref(raw))
        self.assertEqual(context.exception.code,'PLAN_REFERENCE_MISMATCH')

    def test_prompt_change_no_silent_rebind(self):
        self.plan['artifacts'][1]['sha256']='0'*64
        self.blocked('PREPARATION_INPUT_MISMATCH')

    def test_procedure_change_no_silent_rebind(self):
        self.plan['artifacts'][0]['size_bytes']+=1
        self.blocked('PREPARATION_INPUT_MISMATCH')

    def test_missing_prompt_blocks(self):
        self.plan['artifacts'].pop(1)
        self.blocked('PREPARATION_INPUT_MISMATCH')

    def test_missing_procedure_blocks(self):
        self.plan['artifacts'].pop(0)
        self.blocked('PREPARATION_INPUT_MISMATCH')

    def test_preparer_bytes_fixed_in_receipt(self):
        receipt=self.receipt()
        expected=[dict(path=path,**ref((BASE/path).read_bytes())) for path in MODULE['COMPONENT']]
        self.assertEqual(receipt['preparation_component']['artifacts'],expected)
        self.assertEqual(receipt['preparation_component']['subject'],self.plan['selection'][0])
        self.assertEqual(receipt['execution_profile'],self.plan['execution_profile'])

    def test_preparer_metadata_change_blocks(self):
        self.plan['artifacts'][2]['sha256']='0'*64
        self.blocked('PREPARATION_INPUT_MISMATCH')

    def test_wrong_selection(self):
        self.plan['selection'][0]['revision']='r0002'
        self.blocked('PREPARATION_SELECTION_MISSING')

    def test_wrong_context_operation(self):
        self.plan['context']['operation']='activate'
        self.blocked('PREPARATION_CONTEXT_MISMATCH')

    def test_wrong_context_area(self):
        self.plan['context']['area']='local'
        self.blocked('PREPARATION_CONTEXT_MISMATCH')

    def test_unknown_profile(self):
        self.plan['execution_profile']='latest'
        self.blocked('PLAN_SCHEMA')

    def test_duplicate_paths(self):
        self.plan['artifacts'].append(dict(self.plan['artifacts'][0],sha256='c'*64))
        self.blocked('PLAN_DUPLICATE_PATH')

    def test_preflight_limits(self):
        self.plan['artifacts'] += [dict(path=f'fixtures/{i}',sha256='a'*64,size_bytes=16*1024*1024) for i in range(5)]
        self.blocked('PLAN_SET_LIMIT')

    def test_missing_final_lf(self):
        raw=encode(self.plan).rstrip(b'\n')
        with self.assertRaises(Blocked) as context:prepare(raw,ref(raw))
        self.assertEqual(context.exception.code,'PLAN_SERIALIZATION')

    def test_ambiguous_json(self):
        raw=b'{"x":1,"x":2}\n'
        with self.assertRaises(Blocked) as context:prepare(raw,ref(raw))
        self.assertEqual(context.exception.code,'PLAN_PARSE_OR_SCHEMA')

    def test_installed_prompt_change_blocks(self):
        pins=copy.deepcopy(MODULE['PINS']);pins[MODULE['PROMPT']]['sha256']='0'*64
        with patch.dict(G,PINS=pins):
            raw=encode(self.plan)
            with self.assertRaises(Blocked) as context:prepare(raw,ref(raw))
        self.assertEqual(context.exception.code,'INSTALLED_PREPARATION_CHANGED')
        self.assertTrue(context.exception.unsupported)

    def test_missing_engine_blocks(self):
        from importlib import metadata
        with patch.object(metadata,'version',side_effect=metadata.PackageNotFoundError('jsonschema')):
            raw=encode(self.plan)
            with self.assertRaises(Blocked) as context:prepare(raw,ref(raw))
        self.assertTrue(context.exception.unsupported)

    def test_symlink_metadata_stays_in_pinned_plan(self):
        artifact=self.plan['artifacts'][1]
        artifact.update(links=[dict(path=artifact['path'],link_type='symbolic_link',target='prompt-target.md')],
                        resolved_path='transfer/ent-0012/r0001/prompt-target.md')
        receipt=self.receipt()
        self.assertEqual(receipt['plan'],ref(encode(self.plan)))
        self.assertFalse(receipt['export_allowed'])

    def test_empty_ledger_does_not_assert_permission(self):
        receipt=self.receipt()
        self.assertIn('release_permission',receipt['not_checked'])
        self.assertIn('export_permission',receipt['not_checked'])
        self.assertIn('activation_permission',receipt['not_checked'])

    def test_procedure_has_both_lifecycles_and_history(self):
        text=(BASE/MODULE['PROCEDURE']).read_text()
        for section in ['G00','G01','G02','G03','G04','G05','G06','G07','G08','G09']:
            self.assertEqual(text.count('## '+section+'.'),1)
        for phase in ['A1','A2','A3','A4','A5','A6','B1','B2','B3','B4','B5']:
            self.assertIn(phase+' —',text)
        self.assertIn('Неактивные/исторические связки',text)

    def test_prompt_is_versioned_preparation_not_activation(self):
        text=(BASE/MODULE['PROMPT']).read_text()
        self.assertIn('ENT-0012 r0001',text)
        self.assertIn('не копируй/публикуй/активируй',text)
        self.assertIn('prepared_only',text)


if __name__=='__main__':
    unittest.main(verbosity=2)
