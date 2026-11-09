#!/usr/bin/env python3
"""61: anchor corrections for A-01..A-05, S-01 accepted as residual risk.

The rule statements must stay byte-identical; only the evidence grows.
"""
import hashlib
import json
import os
import re
from pathlib import Path
import unittest

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

CORR = 'research/61-agent-system-anchor-corrections.json'
CORR_SHA = 'fa7f11e1e107df1de27f27dc799ba6af34eb0368617fb4fc38da19345480c88e'
REPORT = 'research/61-agent-system-anchor-corrections.md'
RULES = 'research/53-agent-system-condition-rules.json'
RULES_SHA = 'bc5dc93e58fdc9df7e49e24e870e7e8b00193f19fc2d057a54593ad6961f2c29'
ACCEPT = 'research/54-agent-system-owner-acceptance.json'
ACCEPT_SHA = '525dc3b2c415927b308debf3d665770dad99f7a13b72eac85f70124feee673e6'
V2 = 'research/57-agent-system-portable-rules-text-v2.md'
V2_SHA = '15338d93103875dff2dad53218a827d9c2f26f8aa6ac8bd7af338529ac99cd85'
REGISTRY = 'agent_system/catalog/registry.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return (ROOT / path).read_bytes()


def norm(text):
    return re.sub(r'\s+', ' ', text).strip()


class AnchorCorrectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sha(read(CORR)) != CORR_SHA:
            raise ValueError('CORR_PIN')
        cls.doc = json.loads(read(CORR))
        cls.rules = {r['id']: r for r in json.loads(read(RULES))['rules']}
        cls.corr = {c['rule']: c for c in cls.doc['corrections']}
        cls.report = read(REPORT).decode('utf-8')

    def test_statements_are_untouched(self):
        self.assertEqual(self.doc['unchanged']['statement_count'], 23)
        self.assertTrue(self.doc['unchanged']['statements'])
        for c in self.corr.values():
            statement = self.rules[c['rule']]['statement']
            self.assertEqual(c['statement'], statement)
            self.assertEqual(c['statement_sha256'],
                             sha(statement.encode('utf-8')))
            self.assertEqual(c['original_evidence'],
                             self.rules[c['rule']]['evidence'])
        self.assertEqual(sha(read(RULES)), RULES_SHA)
        self.assertEqual(sha(read(ACCEPT)), ACCEPT_SHA)
        self.assertEqual(sha(read(V2)), V2_SHA)

    def test_every_added_anchor_is_verbatim(self):
        total = 0
        for c in self.corr.values():
            self.assertTrue(c['added'], c['rule'])
            for a in c['added']:
                total += 1
                text = (ROOT / a['path']).read_text(encoding='utf-8')
                self.assertIn(norm(a['quote']), norm(text), (a['path'], a['quote']))
                self.assertEqual(a['file_sha256'], sha(read(a['path'])), a['path'])
                self.assertEqual(a['file_size_bytes'],
                                 (ROOT / a['path']).stat().st_size)
                self.assertGreaterEqual(a['line'], 1)
                self.assertTrue(a['supports'])
        self.assertEqual(total, 9)

    def test_defects_a01_to_a05_are_closed_once_each(self):
        self.assertEqual(sorted(self.corr), ['F03', 'F04', 'F12', 'F16', 'F17'])
        self.assertEqual([c['defect'] for c in self.doc['corrections']],
                         ['A-01', 'A-02', 'A-03', 'A-04', 'A-05'])
        closed = self.doc['status_after']['defects_closed']
        for defect in ('A-01', 'A-02', 'A-03', 'A-04', 'A-05'):
            self.assertEqual(closed[defect], 'fixed')
        self.assertEqual(closed['A-07'],
                         'fixed_as_side_effect_of_A-04_and_A-05')

    def test_s01_is_recorded_as_accepted_residual_risk(self):
        decision = {d['id']: d for d in self.doc['owner_decisions']}['S-01']
        self.assertEqual(decision['decision'], 'accept_single_anchor')
        self.assertEqual(decision['wording'], 'жить с одиночной цитатой у 13 правил')
        covered = decision['rules_covered_after_corrections']
        self.assertEqual(covered,
                         ['F02', 'F05', 'F09', 'F10', 'F11', 'F15', 'F22', 'F23'])
        self.assertEqual(len(covered), 8)
        self.assertEqual(decision['not_covered_by_this_decision'],
                         ['A-06 (подчинённая оговорка F10)',
                          'A-08 (обрыв цитаты F22)'])

    def test_coverage_arithmetic_matches_the_rules(self):
        quoted = [rid for rid in self.rules
                  if self.rules[rid]['evidence']['kind'] == 'rule']
        self.assertEqual(len(quoted), 17)
        cov = self.doc['status_after']['anchor_coverage']
        self.assertEqual(cov['before'], {'full': 4, 'partial': 10, 'none': 3})
        self.assertEqual(cov['after'], {'full': 9, 'partial': 8, 'none': 0})
        fixed = set(self.corr)
        FULL = {'F13', 'F18', 'F19', 'F20'}  # один якорь покрывал утверждение и до правки
        self.assertTrue(fixed <= set(quoted))
        residual = [rid for rid in quoted if rid not in fixed and rid not in FULL]
        self.assertEqual(residual,
                         ['F02', 'F05', 'F09', 'F10', 'F11', 'F15', 'F22', 'F23'])
        self.assertEqual(set(residual), set(
            {d['id']: d for d in self.doc['owner_decisions']}['S-01']
            ['rules_covered_after_corrections']))

    def test_open_items_are_named(self):
        still = {i['id']: i for i in self.doc['status_after']['still_open']}
        self.assertEqual(sorted(still), ['A-06', 'A-08'])
        self.assertEqual(still['A-06']['rule'], 'F10')
        self.assertEqual(still['A-08']['rule'], 'F22')
        self.assertIn('не запрошено', still['A-06']['note'])

    def test_acceptance_consequence_is_explicit(self):
        consequence = self.doc['acceptance_consequence']
        self.assertEqual(consequence['status'], 'pending_owner_confirmation')
        self.assertIn('54', consequence['finding'])

    def test_no_authority_and_no_round2(self):
        flags = self.doc['flags']
        for key in ('release_allowed', 'export_allowed', 'activation_allowed',
                    'compatible_release_allowed', 'environment_created',
                    'kit_materialized', 'registry_changed', 'text_changed',
                    'statements_changed', 'b4_closed', 'round2_started'):
            self.assertFalse(flags[key], key)
        self.assertEqual(self.doc['b4_status'], 'open')
        registry = json.loads(read(REGISTRY))
        self.assertEqual(len(registry['entities']), 19)
        self.assertEqual(sum(len(e['revisions']) for e in registry['entities']), 31)

    def test_round2_options_have_balanced_tradeoffs(self):
        options = {o['id']: o for o in self.doc['round2_options']}
        self.assertEqual(sorted(options), ['R2-A', 'R2-B', 'R2-C', 'R2-D'])
        for o in options.values():
            self.assertGreaterEqual(len(o['pros']), 3)
            self.assertGreaterEqual(len(o['cons']), 3)
            for key in ('cost', 'independence', 'closes_b4', 'risk', 'what'):
                self.assertTrue(o[key], (o['id'], key))
        self.assertEqual(options['R2-A']['closes_b4'],
                         'да, при отсутствии открытых S1/S2')
        self.assertEqual(options['R2-C']['independence'], 'нет')
        self.assertEqual(self.doc['recommendation']['option'], 'R2-A')
        self.assertEqual(self.doc['recommendation']['decision_status'],
                         'pending_owner_choice')

    def test_report_matches_the_ledger(self):
        for marker in ('9 из 17', 'A-06', 'A-08', 'R2-A', 'R2-B', 'R2-C', 'R2-D',
                       'pending_owner_confirmation', '**8 правил**'):
            self.assertIn(marker, self.report, marker)
        self.assertNotIn('B4 закрыт', self.report)


if __name__ == '__main__':
    unittest.main()
