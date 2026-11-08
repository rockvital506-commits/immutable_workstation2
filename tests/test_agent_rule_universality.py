#!/usr/bin/env python3
"""Bounded trace/packet regression oracle, NOT a natural-language classifier.

Trusted, owner-visible research fixture is pinned independently of candidate output.
Exact comparison is intentionally conservative. Passing establishes consistency with
this manually authored selection only, not semantic equivalence or owner review.
No export, activation, automatic classification or generic input-path reader exists.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
FIXTURE = 'research/44-agent-system-universality-trace.json'
FIXTURE_SHA256 = '9ddbd974dc1cb691289d28ae2d48bc5a0bb4e4f9a8acda0807dcf4ee8e33dc82'


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(',', ':'))


def load_basis(root=ROOT):
    # Local trusted test roots only; not a production hostile-tree reader.
    data = (root / FIXTURE).read_bytes()
    if hashlib.sha256(data).hexdigest() != FIXTURE_SHA256:
        raise ValueError('FIXTURE_PIN')
    basis = json.loads(data)
    for unit in basis['units']:
        source = unit['source']
        raw = (root / source['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != source['sha256']:
            raise ValueError('SOURCE_PIN')
        text = raw.decode('utf-8')
        quote = text[source['start_offset']:source['end_offset']]
        if text[:source['start_offset']].count('\n')+1 != source['start_line']:
            raise ValueError('SOURCE_LOCATOR')
        if source['start_line']+quote.count('\n') != source['end_line']:
            raise ValueError('SOURCE_LOCATOR')
        if quote != source['quote'] or text.count(quote) != 1:
            raise ValueError('SOURCE_LOCATOR')
    return basis


def expected_packet(basis):
    # Only a draft, including held/excluded trace entries with NO rule payload.
    return dict(
        version=1, status='draft_not_exportable', selection_complete=False,
        review='agent_self_review_not_independent',
        unresolved=[u['id'] for u in basis['units'] if u['route'] == 'hold'],
        release_allowed=False, export_allowed=False, activation_allowed=False,
        compatible_release_allowed=False,
        units=[dict(id=u['id'], source={k:v for k,v in u['source'].items() if k!='quote'},
                    universality=u['universality'], route=u['route'],
                    contexts=u['contexts'], meaning_dependencies=u['meaning_dependencies'],
                    text=u['output']) for u in basis['units']])


def assess(packet, root=ROOT):
    # Never obtain the expected basis from packet hashes/self-report.
    basis = load_basis(root)
    matches = canonical(packet) == canonical(expected_packet(basis))
    return dict(fixture_consistent=matches,
                semantic_equivalence='not_established',
                selection_coverage='selected_units_only',
                review='agent_self_review_not_independent',
                classification_automated=False,
                unresolved=[u['id'] for u in basis['units'] if u['route']=='hold'],
                release_allowed=False, export_allowed=False, activation_allowed=False,
                compatible_release_allowed=False)


class UniversalityTraceTests(unittest.TestCase):
    def setUp(self):
        self.basis = load_basis()
        self.packet = expected_packet(self.basis)

    def unit(self, uid):
        return next(u for u in self.packet['units'] if u['id']==uid)

    def blocked(self):
        result = assess(self.packet)
        self.assertFalse(result['fixture_consistent'])
        self.assertFalse(result['release_allowed'])
        self.assertFalse(result['activation_allowed'])

    def test_source_pins_and_line_locators(self):
        self.assertEqual(17,len(self.basis['units']))
        self.assertEqual(17,len({u['id'] for u in self.basis['units']}))

    def test_reviewed_selection_shape(self):
        routes = [u['route'] for u in self.basis['units']]
        self.assertEqual([13,1,2,1],[routes.count(r) for r in ('preserve','generalize','exclude','hold')])
        for unit in self.basis['units']:
            self.assertTrue(unit['rationale'])
            self.assertTrue(unit['meaning_dependencies'])
            if unit['route']=='preserve':
                self.assertEqual(unit['source']['quote'],unit['output'])
                self.assertTrue(unit['contexts'])
            if unit['route'] in ('exclude','hold'):
                self.assertIsNone(unit['output'])

    def test_positive_draft_consistency_not_admission(self):
        result=assess(self.packet)
        self.assertTrue(result['fixture_consistent'])
        self.assertEqual('not_established',result['semantic_equivalence'])
        self.assertEqual(['U01'],result['unresolved'])
        for name in ('release_allowed','export_allowed','activation_allowed','compatible_release_allowed'):
            self.assertIs(False,result[name])

    def test_excluded_source_quotes_not_embedded_in_draft(self):
        serialized=canonical(self.packet)
        rules='\n'.join(u['text'] for u in self.packet['units'] if u['text'] is not None)
        for unit in self.basis['units']:
            if unit['route'] in ('exclude','hold'):
                self.assertNotIn(unit['source']['quote'],serialized)
                self.assertNotIn(unit['source']['quote'],rules)
        self.assertNotIn('openat2',rules)
        self.assertNotIn('/proc/self/fd',rules)

    def test_missing_high_unit(self):
        self.packet['units'].pop(0);self.blocked()

    def test_weakening_permission_requirement(self):
        self.unit('C09')['text']='Разрешения можно считать общими.';self.blocked()

    def test_strengthening_preparatory_test_prohibition(self):
        self.unit('C06')['text']='Любые испытания кандидата запрещены.';self.blocked()

    def test_lost_exception_and_conditions(self):
        self.unit('C06')['text']=self.unit('C06')['text'].split('Подготовительные испытания')[0]
        self.blocked()

    def test_lost_scope(self):
        self.unit('C01')['contexts']=[];self.blocked()

    def test_lost_dependency(self):
        self.unit('W00')['meaning_dependencies']=[];self.blocked()

    def test_unknown_as_approved(self):
        self.unit('U01')['route']='preserve'
        self.unit('U01')['text']=next(u['source']['quote'] for u in self.basis['units'] if u['id']=='U01')
        self.packet['unresolved']=[];self.blocked()

    def test_silent_unknown_exclusion(self):
        self.packet['units']=[u for u in self.packet['units'] if u['id']!='U01']
        self.packet['unresolved']=[];self.blocked()

    def test_nonuniversal_promoted_to_rule(self):
        self.unit('X02')['route']='preserve'
        self.unit('X02')['text']=next(u['source']['quote'] for u in self.basis['units'] if u['id']=='X02');self.blocked()

    def test_generalization_overreach(self):
        self.unit('G01')['text']='Каждый агент обязан всегда применять Linux openat2.'
        self.blocked()

    def test_generalization_weakening(self):
        self.unit('G01')['text']='Можно открыть файл после resolve при недоступной защите.'
        self.blocked()

    def test_leakage_via_extra_metadata(self):
        self.unit('G01')['private_path']='/private/example';self.blocked()

    def test_leakage_via_context(self):
        self.unit('G01')['contexts'].append('Всегда применять /private/example')
        self.blocked()

    def test_unapproved_extra_rule(self):
        extra=copy.deepcopy(self.unit('G01'));extra['id']='INVENTED'
        self.packet['units'].append(extra);self.blocked()

    def test_coherently_repinned_false_output(self):
        unit=self.unit('C09');unit['text']='Автоактивация разрешена.'
        unit['source']['sha256']=hashlib.sha256(unit['text'].encode()).hexdigest()
        self.blocked()

    def test_wrong_source_revision(self):
        self.unit('C01')['source']['path']=self.unit('C01')['source']['path'].replace('r0001','r0002')
        self.blocked()

    def test_self_attested_qualified_review(self):
        self.packet['review']='independent_owner_approved';self.blocked()

    def test_fabricated_complete_coverage(self):
        self.packet['selection_complete']=True;self.blocked()

    def test_each_action_flag_blocked(self):
        for name in ('release_allowed','export_allowed','activation_allowed','compatible_release_allowed'):
            with self.subTest(name=name):
                self.packet=expected_packet(self.basis);self.packet[name]=True;self.blocked()

    def test_bool_integer_not_equivalent(self):
        self.packet['release_allowed']=0;self.blocked()

    def test_changed_source_and_fixture_rejected_independently(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for path in [FIXTURE]+list({u['source']['path'] for u in self.basis['units']}):
                target=root/path;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((ROOT/path).read_bytes())
            src=root/self.basis['units'][0]['source']['path']
            src.write_bytes(src.read_bytes()+b'\n')
            with self.assertRaisesRegex(ValueError,'SOURCE_PIN'):load_basis(root)
            target=root/FIXTURE;target.write_bytes(target.read_bytes()+b'\n')
            with self.assertRaisesRegex(ValueError,'FIXTURE_PIN'):load_basis(root)

    def test_no_generic_paraphrase_equivalence_claim(self):
        # Safe rephrasing may be equivalent; this oracle cannot establish that.
        self.unit('C09')['text']='Для выпуска и активации требуются отдельные разрешения.'
        self.blocked()


if __name__=='__main__':
    unittest.main(verbosity=2)
