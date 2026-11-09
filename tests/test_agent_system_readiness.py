#!/usr/bin/env python3
"""63: five delegated decisions and the readiness report.

Pins the numbers the report rests on and the honesty constraints: the report
must not claim release or activation readiness, and must not turn delegated
decision authority into verification.
"""
import hashlib
import json
import os
import re
from pathlib import Path
import unittest

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

DOC = 'research/63-agent-system-decisions-and-readiness.json'
DOC_SHA = '0537f913b7f4e18531a8ccf722d0245f64da1b37c5424a18470d46c01c757dab'
REPORT = 'research/63-agent-system-decisions-and-readiness.md'
REGISTRY = 'agent_system/catalog/registry.json'
R58 = 'research/58-agent-system-r6-readiness-qualification.json'
RULES = 'research/53-agent-system-condition-rules.json'
RULES_SHA = 'bc5dc93e58fdc9df7e49e24e870e7e8b00193f19fc2d057a54593ad6961f2c29'
V2 = 'research/57-agent-system-portable-rules-text-v2.md'
V2_SHA = '15338d93103875dff2dad53218a827d9c2f26f8aa6ac8bd7af338529ac99cd85'
ACC = 'research/54-agent-system-owner-acceptance.json'
ACC_SHA = '525dc3b2c415927b308debf3d665770dad99f7a13b72eac85f70124feee673e6'
R61 = 'research/61-agent-system-anchor-corrections.json'
R61_SHA = 'fa7f11e1e107df1de27f27dc799ba6af34eb0368617fb4fc38da19345480c88e'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return (ROOT / path).read_bytes()


class ReadinessReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sha(read(DOC)) != DOC_SHA:
            raise ValueError('DOC_PIN')
        cls.doc = json.loads(read(DOC))
        cls.report = read(REPORT).decode('utf-8')

    def test_five_decisions_are_recorded_with_grounds(self):
        decisions = self.doc['decisions']
        self.assertEqual([d['id'] for d in decisions], ['D1', 'D2', 'D3', 'D4', 'D5'])
        for d in decisions:
            self.assertTrue(d['decision'] and d['why'] and d['effect'], d['id'])
        by_id = {d['id']: d for d in decisions}
        self.assertIn('O1', by_id['D1']['decision'])
        self.assertIn('O3', by_id['D2']['decision'])
        self.assertEqual(by_id['D3']['trigger'],
                         'следующая плановая ревизия корпуса вместе с A-06/A-08 и F24')
        self.assertIn('R2-D', by_id['D4']['decision'])
        self.assertIn('53 r2', by_id['D5']['decision'])

    def test_authority_is_quoted_and_bounded(self):
        auth = self.doc['decision_authority']
        self.assertIn('прими решение сам с учетом оптимальности',
                      auth['owner_statement_verbatim'])
        self.assertEqual(auth['language'], 'ru')
        for item in ('выпуск', 'экспорт', 'активация',
                     'регистрация нормативной ревизии'):
            self.assertIn(item, auth['not_delegated'])
        self.assertIn('не хватает проверок', self.doc['overall']['statement'])

    def test_registry_numbers_match_the_file(self):
        registry = json.loads(read(REGISTRY))
        system = self.doc['system']['registry']
        self.assertEqual(system['entities'], len(registry['entities']))
        self.assertEqual(system['revisions'],
                         sum(len(e['revisions']) for e in registry['entities']))
        self.assertEqual(system['artifacts'],
                         sum(len(rv['artifacts'])
                             for e in registry['entities'] for rv in e['revisions']))
        self.assertEqual((system['entities'], system['revisions'], system['artifacts']),
                         (19, 31, 111))
        self.assertEqual(system['kinds'],
                         {'protocol': 16, 'check': 8, 'contract': 3,
                          'schema': 2, 'adapter': 2})
        for rev in (rv for e in registry['entities'] for rv in e['revisions']):
            self.assertEqual(rev['approval']['status'], 'approved')

    def test_r6_numbers_match_the_qualification(self):
        r58 = json.loads(read(R58))['summary']
        r6 = self.doc['system']['r6']
        self.assertEqual(r6['rows'], r58['rows_total'])
        self.assertEqual(r6['text_covered'], r58['text_status']['covered'])
        self.assertEqual(r6['text_partial'], r58['text_status']['partial'])
        self.assertEqual(r6['meeting_level'], r58['rows_meeting_required_level'])
        self.assertEqual(r6['behaviour_rows'], r58['rows_with_behaviour_evidence'])
        self.assertEqual((r6['rows'], r6['meeting_level'], r6['behaviour_rows']),
                         (25, 3, 0))
        self.assertEqual(r6['implementation'],
                         {'absent': 11, 'present_unverified': 11, 'verified_structural': 3})

    def test_readiness_is_split_and_not_overstated(self):
        table = {v['notion']: v['ready'] for v in self.doc['readiness']}
        self.assertTrue(table['Рабочий контур (лаборатория)'])
        self.assertTrue(table['Кандидатный текст правил'])
        self.assertFalse(table['Совместимый выпуск'])
        self.assertFalse(table['Активная связка в новой среде'])
        overall = self.doc['overall']
        self.assertTrue(overall['ready_for_use'])
        self.assertFalse(overall['release_ready'])
        self.assertFalse(overall['activation_ready'])
        self.assertFalse(overall['b4_closed'])
        for key, value in self.doc['flags'].items():
            self.assertFalse(value, key)

    def test_every_capability_and_limit_has_a_boundary(self):
        self.assertEqual(len(self.doc['capabilities']), 11)
        for cap in self.doc['capabilities']:
            self.assertTrue(cap['limits'], cap['name'])
            self.assertTrue(cap['use'], cap['name'])
        self.assertEqual(len(self.doc['limits']), 10)
        kinds = {l['kind'] for l in self.doc['limits']}
        self.assertEqual(kinds, {'платформа', 'зависимости', 'объём', 'полномочия',
                                 'доказательность', 'смысл правил', 'доверие',
                                 'безопасность', 'секреты', 'параллельность'})
        self.assertEqual(len(self.doc['blocks']), 8)
        self.assertEqual(len(self.doc['bottlenecks']), 7)
        self.assertEqual(len(self.doc['nuances']), 10)

    def test_open_items_have_triggers(self):
        items = {o['id']: o for o in self.doc['open_items']}
        self.assertIn('B4', items)
        self.assertIn('53r2', items)
        for o in items.values():
            self.assertTrue(o['trigger'], o['id'])

    def test_subject_bytes_are_untouched(self):
        self.assertEqual(sha(read(RULES)), RULES_SHA)
        self.assertEqual(sha(read(V2)), V2_SHA)
        self.assertEqual(sha(read(ACC)), ACC_SHA)
        self.assertEqual(sha(read(R61)), R61_SHA)
        self.assertEqual(self.doc['system']['rule_set']['sha256'], RULES_SHA)
        self.assertEqual(self.doc['system']['anchor_corrections']['status'],
                         'non_normative_evidence')

    def test_report_carries_the_same_verdict(self):
        for marker in ('не готова как совместимый выпуск',
                       'не готова к активации в новой среде',
                       'D1', 'D4', 'D5', 'R2-D',
                       'Узкие места', 'Нюансы использования',
                       'Чего делать нельзя'):
            self.assertIn(marker, self.report, marker)
        self.assertNotIn('система полностью готова', self.report.lower())
        self.assertIn('B4 остаётся открытым', self.report)
        self.assertEqual(self.report.count('\n## '), 12)


if __name__ == '__main__':
    unittest.main()
