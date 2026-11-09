#!/usr/bin/env python3
"""B4 harness: blind package really blind, checklist verbatim, discrepancies separated."""
import hashlib
import json
import os
import re
from pathlib import Path
import unittest

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

PRECHECK = 'research/59-agent-system-b4-precheck.json'
PRECHECK_SHA = 'a495955b49344612aaed350b51a696e3b480278e86b88b573848b6a0ccd3fa26'
PROTOCOL = 'research/59-agent-system-b4-review-protocol.md'
PROTOCOL_SHA = 'fc86ae8da62fdd64907f06fcd02db5957bda56b90497d67762b44117e212a26f'
WORKSHEET = 'research/59-agent-system-b4-worksheet.json'
WORKSHEET_SHA = '0e872af7cc02b9c08cff89b8ca586d49618f3003305e0517df866bf66bd8e687'
PROMPT = 'research/59-b4-reviewer-prompt.md'
PROMPT_SHA = '3be1787cbe71c7c1a5e6d419bd22a7d04d252c57107e6ae3f44ddd70a35bc3c6'
RULES_MD = 'research/53-agent-system-condition-rules.md'
RULES_JSON = 'research/53-agent-system-condition-rules.json'
CHECKLIST = [
    'Confirm each rule stays inside its cited source.',
    'Confirm no rule silently weakens or strengthens its source.',
    'Confirm the forbidden-conclusion lines match the intended limits.',
    'Name any missing condition not covered by F01-F23.',
]
CHECKLIST_RU = [
    'правило остаётся внутри области цитируемого основания',
    'правило не ослабляет и не усиливает основание молча',
    'строки «запрещено выводить» соответствуют намеренным пределам',
    'названо отсутствующее условие, не покрытое F01–F23',
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return (ROOT / path).read_bytes()


def words(text):
    return re.findall(r'[а-яёa-z0-9]+', text.lower())


def longest_run(a, b):
    best = 0
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                best = max(best, cur[j])
        prev = cur
    return best


def load():
    for path, pin in ((PRECHECK, PRECHECK_SHA), (PROTOCOL, PROTOCOL_SHA),
                      (WORKSHEET, WORKSHEET_SHA), (PROMPT, PROMPT_SHA)):
        if sha(read(path)) != pin:
            raise ValueError('PIN ' + path)
    ledger = json.loads(read(PRECHECK))
    return (ledger, json.loads(read(WORKSHEET)), read(PROMPT).decode('utf-8'),
            read(PROTOCOL).decode('utf-8'),
            [r['statement'] for r in json.loads(read(RULES_JSON))['rules']])


class B4ReviewHarnessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (cls.ledger, cls.worksheet, cls.prompt, cls.protocol,
         cls.statements) = load()

    def test_status_is_open_and_nothing_claims_independence(self):
        self.assertEqual(self.ledger['b4_status'], 'open')
        self.assertFalse(self.ledger['flags']['independent_review_performed'])
        self.assertTrue(self.ledger['status_statement'].startswith('Независимый проход не выполнялся'))
        self.assertIn('B4 остаётся ОТКРЫТЫМ', self.protocol)
        for candidate in self.ledger['discrepancy_candidates']:
            self.assertEqual(candidate['found_by'], 'author_precheck', candidate['id'])
            self.assertEqual(candidate['status'], 'open')
        self.assertEqual(self.ledger['candidate_stats']['by_found_by'],
                         {'author_precheck': 5, 'independent_reviewer': 0})
        self.assertIn('любой документ, называющий\nсвод «независимо проверенным», будет неверным', self.protocol)

    def test_checklist_is_verbatim_from_53(self):
        source = read(RULES_MD).decode('utf-8')
        for verbatim, ru in zip(CHECKLIST, CHECKLIST_RU):
            self.assertIn(verbatim, source, verbatim)
            self.assertIn(verbatim, self.protocol, verbatim)
            self.assertIn(ru, self.protocol, ru)
        ids = [c['id'] for c in self.worksheet['checklist']]
        self.assertEqual(ids, ['Q1', 'Q2', 'Q3', 'Q4'])
        for item, verbatim, ru in zip(self.worksheet['checklist'], CHECKLIST, CHECKLIST_RU):
            self.assertEqual(item['verbatim'], verbatim)
            self.assertEqual(item['ru'], ru)
            self.assertIn(item['accept'][0], self.protocol)

    def test_blind_package_has_no_rule_statements(self):
        package = json.dumps(self.worksheet, ensure_ascii=False) + self.prompt
        for statement in self.statements:
            self.assertNotIn(statement, package, statement[:40])
        pw = words(self.prompt)
        worst = max(longest_run(words(s), pw) for s in self.statements)
        self.assertLessEqual(worst, 8)
        self.assertEqual(self.ledger['leakage']['max_shared_word_run'], worst)
        for forbidden in self.worksheet['must_not_be_given_to_reviewer']:
            self.assertNotIn('```', forbidden)

    def test_every_rule_has_material(self):
        items = self.worksheet['items']
        self.assertEqual(len(items), 23)
        self.assertEqual(len({i['id'] for i in items}), 23)
        self.assertEqual([i['id'] for i in items], ['F%02d' % n for n in range(1, 24)])
        for item in items:
            self.assertGreater(len(item['text']), 120, item['id'])
            self.assertIn(item['track'], {'A_quote_rederivation', 'B_conditional_note_scope'})
        tracks = {}
        for item in items:
            tracks[item['track']] = tracks.get(item['track'], 0) + 1
        self.assertEqual(tracks, {'A_quote_rederivation': 17, 'B_conditional_note_scope': 6})
        self.assertEqual(self.ledger['harness']['tracks'],
                         {'A_quote_rederivation': 17, 'B_conditional_note_scope': 6})
        # у правил с цитатой выдан именно первоисточник, включая два производных случая
        derived = [i for i in items if i['id'] in {'F04', 'F16'}]
        for item in derived:
            self.assertEqual(item['material_kind'], 'original_block_from_derived_part')
            self.assertTrue(item['source_path'].startswith('agent_system/'))

    def test_precheck_findings_are_real_and_typed(self):
        candidates = {c['id']: c for c in self.ledger['discrepancy_candidates']}
        self.assertEqual(set(candidates), {'D-01', 'D-02', 'D-03', 'D-04', 'D-05'})
        self.assertEqual(self.ledger['candidate_stats']['by_severity'],
                         {'S1': 0, 'S2': 2, 'S3': 3, 'S4': 0})
        self.assertEqual({c['rule'] for c in candidates.values()},
                         {'F03', 'F04', 'F16', 'F22'})
        for candidate in candidates.values():
            for field in ('rule', 'kind', 'severity', 'what', 'evidence', 'proposed_resolution'):
                self.assertTrue(candidate[field], (candidate['id'], field))
        # D-03 и D-04 подтверждены прямым чтением источника
        governance = read('agent_system/protocols/ent-0012/r0001/governance.md').decode('utf-8')
        self.assertIn('approval или revision не снимают их', governance)
        work = read('agent_system/protocols/ent-0011/r0002/work.md').decode('utf-8')
        paragraph = work[work.index('Выпуск, согласование состава и активация') - 420:
                         work.index('Выпуск, согласование состава и активация') + 320]
        self.assertNotIn('экспорт', paragraph.lower())
        items = {i['id']: i for i in self.ledger['items']}
        self.assertIn('P8_quote_ends_mid_sentence', items['F22']['flags'])
        self.assertEqual(items['F04']['source_tier'], 'derived_research_47')

    def test_tier_and_modal_results(self):
        self.assertEqual(self.ledger['tiers'],
                         {'primary_contract': 15, 'derived_research_47': 2,
                          'conditional_note': 6})
        self.assertEqual(self.ledger['flag_counts'],
                         {'P2_source_is_derived_artifact': 2,
                          'P4_negation_absent_in_source': 3,
                          'P8_quote_ends_mid_sentence': 1})
        for item in self.ledger['items']:
            self.assertEqual(item['extra_strong_modals'], [], item['id'])
        self.assertEqual([c['id'] for c in self.ledger['checks']
                          if c['result'] != 'PASS'], [])

    def test_protocol_defines_severity_and_close_criteria(self):
        for code, name in (('S1', 'смысловое'), ('S2', 'сужение'), ('S3', 'прослеживаемость'),
                           ('S4', 'формулировка')):
            self.assertIn('| %s |' % code, self.protocol)
            self.assertIn(name, self.protocol.lower())
        self.assertEqual(len(self.ledger['close_criteria']), 5)
        for marker in ('accepted', 'rejected', 'D-NN', 'author_precheck'):
            self.assertIn(marker, self.protocol)
        self.assertIn('не закрывает расхождения сам'.replace('не ', ''), self.protocol)


if __name__ == '__main__':
    unittest.main()
