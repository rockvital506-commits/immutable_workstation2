#!/usr/bin/env python3
"""B4 round 1: reviewer output preserved, every finding answered, B4 still open."""
import hashlib
import json
import os
import re
from pathlib import Path
import unittest

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

RESULT = 'research/60-agent-system-b4-round1.json'
RESULT_SHA = '03e01362726650fb86a0530a81a6b26a6875963574db6bee46681dd38ea4dd20'
RESPONSE = 'research/60-agent-system-b4-round1-reviewer-response.json'
RESPONSE_SHA = '1c6a09f398df7b5ee46efbd34d0556d9702048f55a78442a2d08807fb9b8b2e1'
REPORT = 'research/60-agent-system-b4-round1.md'
WORKSHEET = 'research/59-agent-system-b4-worksheet.json'
RULES = 'research/53-agent-system-condition-rules.json'
RULES_MD = 'research/53-agent-system-condition-rules.md'
V2 = 'research/57-agent-system-portable-rules-text-v2.md'
REGISTRY = 'agent_system/catalog/registry.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return (ROOT / path).read_bytes()


def tokens(text):
    return re.findall(r'[а-яёa-z0-9]+', text.lower())


def jaccard(a, b):
    A, B = set(tokens(a)), set(tokens(b))
    return len(A & B) / max(1, len(A | B))


def containment(a, b):
    A, B = set(tokens(a)), set(tokens(b))
    return len(A & B) / max(1, len(A))


def load():
    raw = read(RESULT)
    if sha(raw) != RESULT_SHA:
        raise ValueError('RESULT_PIN')
    if sha(read(RESPONSE)) != RESPONSE_SHA:
        raise ValueError('RESPONSE_PIN')
    return (json.loads(raw), json.loads(read(RESPONSE)),
            json.loads(read(WORKSHEET)), json.loads(read(RULES)))


class B4Round1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result, cls.response, cls.worksheet, cls.rules = load()
        cls.journal = {j['id']: j for j in cls.result['journal']}
        cls.report = read(REPORT).decode('utf-8')
        cls.items = {i['id']: i for i in cls.worksheet['items']}

    def test_response_is_preserved_whole(self):
        self.assertEqual(len(self.response['items']), 23)
        self.assertEqual([i['id'] for i in self.response['items']],
                         ['F%02d' % n for n in range(1, 24)])
        self.assertEqual(len(self.response['discrepancies']), 5)
        self.assertEqual(self.response['reviewer']['kind'], 'model')
        self.assertIn('не участвовал в составлении', self.response['attestation'])
        record = self.result['review_record']
        self.assertEqual(record['response']['sha256'], sha(read(RESPONSE)))
        self.assertFalse(record['authenticity']['verified'])
        self.assertEqual(record['independence'], 'claimed_not_verified')

    def test_every_reviewer_finding_is_answered(self):
        reviewer = {d['id'] for d in self.response['discrepancies']}
        self.assertEqual(reviewer, {'D-01', 'D-02', 'D-03', 'D-04', 'D-05'})
        for rid in reviewer:
            entry = self.journal[rid]
            self.assertEqual(entry['found_by'], 'independent_reviewer')
            self.assertNotEqual(entry['status'], 'open', rid)
            self.assertTrue(entry['evidence'] and entry['resolution'], rid)
        self.assertEqual(self.result['journal_stats']['reviewer_entries'], 5)

    def test_duplication_claims_are_disproved_by_facts(self):
        # D-01: материалы F10/F22 идентичны, правила — разные
        self.assertEqual(jaccard(self.items['F10']['text'], self.items['F22']['text']), 1.0)
        statements = {r['id']: r['statement'] for r in self.rules['rules']}
        self.assertNotEqual(statements['F10'], statements['F22'])
        self.assertEqual(self.journal['D-01']['status'], 'rejected_as_stated')
        self.assertEqual(self.journal['D-01']['linked'], 'H-01')
        # D-02: материалы пересекаются, правило F12 не склейка
        ratio = containment(self.items['F09']['text'], self.items['F12']['text'])
        self.assertTrue(0.8 < ratio < 0.9)
        self.assertNotIn(statements['F12'], self.items['F09']['text'])
        self.assertEqual(self.journal['D-02']['status'], 'rejected_as_stated')
        self.assertEqual(self.journal['D-02']['linked'], 'H-02')

    def test_q4_answers_are_about_material_not_rules(self):
        by_rule = {j['rule']: j for j in self.result['journal']
                   if j['found_by'] == 'independent_reviewer'}
        for rid in ('F04', 'F16', 'F19'):
            entry = by_rule[rid]
            self.assertEqual(entry['status'], 'not_applicable_to_rule')
            self.assertEqual(entry['linked'], 'H-04')
        self.assertNotIn('W', statements_of(self.rules, 'F16'))
        self.assertEqual(self.result['package_defects'][2]['id'], 'H-03')

    def test_rule_findings_and_stats_match_their_basis(self):
        stats = self.result['comparison']['stats']
        self.assertEqual(stats['reviewer_contains'], {'full': 8, 'partial': 10, 'none': 5})
        self.assertEqual(stats['cited_anchor_supports_quoted'],
                         {'full': 4, 'partial': 10, 'none': 3})
        self.assertEqual(stats['cited_anchor_supports_all_rules'],
                         {'full': 10, 'partial': 10, 'none': 3})
        self.assertEqual(stats['quoted_rules'], 17)
        self.assertEqual(stats['note_rules'], 6)
        self.assertEqual(len(stats['weak_anchor_rules']), 13)
        findings = [j for j in self.result['journal'] if j['id'][0] in 'AS']
        self.assertEqual(len(findings), 9)
        self.assertEqual(sum(1 for j in findings if j['severity'] == 'S2'), 5)
        self.assertEqual(sum(1 for j in findings if j['severity'] == 'S3'), 4)
        for entry in findings:
            self.assertEqual(entry['status'], 'open')
            self.assertEqual(entry['found_by'], 'author_precheck')

    def test_b4_is_not_declared_closed(self):
        self.assertEqual(self.result['b4_status'], 'open')
        self.assertEqual(self.result['round_status'], 'completed_with_findings_not_closed')
        criteria = self.result['verdict']['b4_close_criteria_status']
        self.assertTrue(criteria['blind_pass_done'])
        self.assertFalse(criteria['checklist_filled_for_rules'])
        self.assertFalse(criteria['all_discrepancies_resolved_by_owner'])
        self.assertFalse(criteria['no_open_S1_S2'])
        flags = self.result['flags']
        self.assertFalse(flags['b4_closed'])
        self.assertEqual(flags['independent_review_performed'], 'claimed_not_verified')
        for key in ('release_allowed', 'export_allowed', 'activation_allowed',
                    'compatible_release_allowed', 'environment_created', 'kit_materialized',
                    'registry_changed', 'text_changed', 'behavior_verified'):
            self.assertFalse(flags[key], key)
        self.assertFalse(self.result['verdict']['release_ready'])

    def test_subject_bytes_are_untouched(self):
        self.assertEqual(self.result['subject']['sha256'], sha(read(RULES_MD)))
        self.assertEqual(self.result['subject']['ledger']['sha256'], sha(read(RULES)))
        self.assertEqual(self.result['subject']['portable_v2']['sha256'], sha(read(V2)))
        registry = json.loads(read(REGISTRY))
        self.assertEqual(len(registry['entities']), 19)
        self.assertEqual(sum(len(e['revisions']) for e in registry['entities']), 31)

    def test_report_states_the_honest_conclusion(self):
        for marker in ('B4 остаётся открытым', 'H-01', 'H-03', 'S-01', 'A-02',
                       'Независимость подтверждена | **нет**'):
            self.assertIn(marker, self.report, marker)
        self.assertNotIn('B4 закрыт**', self.report)
        self.assertEqual(len(self.result['round2_requirements']), 4)
        self.assertEqual([q['id'] for q in self.result['owner_decisions_required']],
                         ['Q1', 'Q2', 'Q3'])


def statements_of(rules, rid):
    return {r['id']: r['statement'] for r in rules['rules']}[rid]


if __name__ == '__main__':
    unittest.main()
