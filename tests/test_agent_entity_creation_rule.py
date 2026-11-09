#!/usr/bin/env python3
"""62: assessment of a universal entity-creation rule.

Pins the measurement, not the opinion: the corpus coverage, the retrospective
counts, and the dry run that shows embedding 61 into 53 voids acceptance 54.
"""
import hashlib
import json
import os
import re
from pathlib import Path
import unittest

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

DOC = 'research/62-agent-system-entity-creation-rule-assessment.json'
DOC_SHA = '6ac088ed82e1aaa9aec14366bb885075d86d7a3d93fcd7617689d2834f6f5d95'
REPORT = 'research/62-agent-system-entity-creation-rule-assessment.md'
RULES = 'research/53-agent-system-condition-rules.json'
RULES_SHA = 'bc5dc93e58fdc9df7e49e24e870e7e8b00193f19fc2d057a54593ad6961f2c29'
ACCEPT = 'research/54-agent-system-owner-acceptance.json'
ACCEPT_SHA = '525dc3b2c415927b308debf3d665770dad99f7a13b72eac85f70124feee673e6'
V2 = 'research/57-agent-system-portable-rules-text-v2.md'
V2_SHA = '15338d93103875dff2dad53218a827d9c2f26f8aa6ac8bd7af338529ac99cd85'
A61 = 'research/61-agent-system-anchor-corrections.json'
A61_SHA = 'fa7f11e1e107df1de27f27dc799ba6af34eb0368617fb4fc38da19345480c88e'
REGISTRY = 'agent_system/catalog/registry.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return (ROOT / path).read_bytes()


def norm(text):
    return re.sub(r'\s+', ' ', text).strip()


class EntityCreationRuleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sha(read(DOC)) != DOC_SHA:
            raise ValueError('DOC_PIN')
        cls.doc = json.loads(read(DOC))
        cls.report = read(REPORT).decode('utf-8')
        cls.clauses = {c['id']: c for c in cls.doc['theory']['clauses']}

    def test_coverage_is_measured_not_claimed(self):
        stats = self.doc['theory']['stats']
        self.assertEqual(stats, {'covered': 2, 'partial': 4, 'absent': 2})
        counted = {}
        for c in self.clauses.values():
            counted[c['status']] = counted.get(c['status'], 0) + 1
        self.assertEqual(counted, stats)
        self.assertEqual([c['id'] for c in self.doc['theory']['clauses']],
                         ['C%d' % n for n in range(1, 9)])

    def test_every_anchor_is_verbatim(self):
        total = 0
        for c in self.clauses.values():
            for a in c['anchors']:
                total += 1
                text = (ROOT / a['path']).read_text(encoding='utf-8')
                self.assertIn(norm(a['quote']), norm(text), (a['path'], a['quote'][:50]))
                self.assertEqual(a['file_sha256'], sha(read(a['path'])))
                self.assertGreaterEqual(a['line'], 1)
        self.assertEqual(total, 8)
        self.assertEqual(self.clauses['C3']['anchors'], [])
        self.assertEqual(self.clauses['C5']['anchors'], [])

    def test_retrospective_counts_match_the_files(self):
        retro = self.doc['theory']['retrospective']
        total = retro['total']
        self.assertEqual((total['artifacts'], total['files']), (35, 63))
        groups = retro['groups']
        self.assertEqual(sum(g['files'] for g in groups.values()), 63)
        self.assertEqual(sum(g['artifacts'] for g in groups.values()), 35)
        self.assertEqual(groups['A_standalone']['artifacts'], 21)
        self.assertEqual(groups['C_analysis']['artifacts'], 8)
        self.assertTrue(retro['counter_risk'])

    def test_dry_run_numbers_are_reproducible(self):
        dry = self.doc['practice']['dry_run']
        self.assertEqual(dry['delta_bytes'], 2315)
        self.assertEqual(dry['anchor_quote_chars'], 741)
        self.assertFalse(dry['render_shows_anchors'])
        self.assertIn('любое изменение текста аннулирует',
                      dry['acceptance_condition_verbatim'])
        # реальный пересчёт: тот же sha, что в документе
        rules = json.loads(read(RULES))
        corr = json.loads(read(A61))
        by = {r['id']: r for r in rules['rules']}
        for c in corr['corrections']:
            by[c['rule']]['additional_anchors'] = [
                {'path': a['path'], 'line': a['line'], 'quote': a['quote'],
                 'supports': a['supports']} for a in c['added']]
        raw = (json.dumps(rules, ensure_ascii=False, indent=1) + '\n').encode()
        self.assertEqual(sha(raw), dry['new_sha256'])
        self.assertEqual(len(raw) - len(read(RULES)), dry['delta_bytes'])

    def test_acceptance_would_be_voided(self):
        condition = json.loads(read(ACCEPT))['conditions']
        self.assertTrue(any('любое изменение текста аннулирует' in c for c in condition))
        refs = self.doc['practice']['references']
        self.assertEqual(refs['files_pinning_rules_sha'], 14)
        self.assertEqual(refs['tests_pinning_rules_sha'], 3)
        self.assertIn('O1', [o['id'] for o in self.doc['options_for_61']])
        self.assertEqual(self.doc['practice']['recommendation'][0], 'O1 сейчас')

    def test_options_and_recommendation(self):
        options = {o['id']: o for o in self.doc['options_for_61']}
        self.assertEqual(sorted(options), ['O1', 'O2', 'O3'])
        self.assertEqual(options['O2']['cost']['acceptance_voided'], 1)
        self.assertEqual(options['O1']['cost']['changed_files'], 1)
        self.assertEqual(options['O3']['cost']['repins'], 0)
        self.assertTrue(any('аннулируется' in c for c in options['O2']['cons']))

    def test_rule_is_not_registered_or_added(self):
        verdict = self.doc['verdict']
        self.assertTrue(verdict['adopt_substance'])
        self.assertFalse(verdict['as_new_entity'])
        self.assertFalse(verdict['as_normative_rule_now'])
        self.assertEqual(self.doc['improved_rule']['f24_candidate']['status'],
                         'candidate_not_in_rule_set')
        for key, value in self.doc['flags'].items():
            self.assertFalse(value, key)
        registry = json.loads(read(REGISTRY))
        self.assertEqual(len(registry['entities']), 19)
        self.assertEqual(sum(len(e['revisions']) for e in registry['entities']), 31)

    def test_subject_bytes_are_untouched(self):
        self.assertEqual(sha(read(RULES)), RULES_SHA)
        self.assertEqual(sha(read(ACCEPT)), ACCEPT_SHA)
        self.assertEqual(sha(read(V2)), V2_SHA)
        self.assertEqual(sha(read(A61)), A61_SHA)
        subject = self.doc['subject_bytes']
        self.assertEqual(subject['rules']['sha256'], RULES_SHA)
        self.assertEqual(subject['acceptance']['sha256'], ACCEPT_SHA)

    def test_report_states_both_checks_and_the_verdict(self):
        for marker in ('Теоретическая проверка', 'Практическая проверка',
                       'Критический анализ', 'Вердикт', 'Улучшенные формулировки',
                       'ничего не переоформлять', 'недостижима', 'K9'):
            self.assertIn(marker, self.report, marker)
        self.assertEqual(len(self.doc['critique']), 9)
        self.assertEqual(len(self.doc['improvements']), 9)
        self.assertEqual([k['id'] for k in self.doc['critique']],
                         ['K%d' % n for n in range(1, 10)])
        self.assertEqual([u['id'] for u in self.doc['improvements']],
                         ['U%d' % n for n in range(1, 10)])
        w04 = self.doc['improved_rule']['w04_addition']
        self.assertIn('Встраивание прежде создания сущности', w04)
        self.assertIn('решение владельца', w04)
        self.assertIn('аннулирует', w04)
        self.assertNotIn('F24 зарегистрирован', self.report)


if __name__ == '__main__':
    unittest.main()
