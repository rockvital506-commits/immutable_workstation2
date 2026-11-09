#!/usr/bin/env python3
"""R6 readiness qualification: 25 rows, verbatim rule links, verdict not release-ready."""
import hashlib
import json
import os
import re
from pathlib import Path
import unittest

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

FIXTURE = 'research/58-agent-system-r6-readiness-qualification.json'
FIXTURE_SHA = 'f32502774e3fbf220960937b3271af93a335f2512d20d1ac5833b0255a83020e'
REPORT = 'research/58-agent-system-r6-readiness-qualification.md'
V2 = 'research/57-agent-system-portable-rules-text-v2.md'
DECISION = 'research/57-agent-system-q1-q2-decision.json'
RULES = 'research/53-agent-system-condition-rules.json'
REGISTRY = 'agent_system/catalog/registry.json'
BEGIN = '<!-- BEGIN VERBATIM BODY -->\n'
END = '\n<!-- END VERBATIM BODY -->\n'
EXPECTED = (['G0%d' % i for i in range(1, 8)] + ['W0%d' % i for i in range(1, 10)]
            + ['C%02d' % i for i in range(2, 11)])
RANK = {'L0': 0, 'L1': 1, 'L2': 2, 'L3': 3, 'L4': 4, 'L5': 5}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return (ROOT / path).read_bytes()


def load():
    raw = read(FIXTURE)
    if sha(raw) != FIXTURE_SHA:
        raise ValueError('FIXTURE_PIN')
    text = read(V2).decode('utf-8')
    body = text[text.index(BEGIN) + len(BEGIN):text.index(END)]
    if sha(body.encode('utf-8')) != json.loads(read(DECISION))['portable_text_v2']['body_sha256']:
        raise ValueError('V2_CHANGED')
    rules = {r['id']: r for r in json.loads(read(RULES))['rules']}
    return json.loads(raw), body, rules


class ReadinessQualificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger, cls.body, cls.rules = load()
        cls.rows = {r['id']: r for r in cls.ledger['rows']}
        cls.report = read(REPORT).decode('utf-8')

    def test_matrix_is_complete_and_unique(self):
        ids = [r['id'] for r in self.ledger['rows']]
        self.assertEqual(ids, EXPECTED)
        self.assertEqual(len(set(ids)), 25)
        self.assertEqual(sum(1 for r in self.ledger['rows'] if r['group'] == 'capability'), 16)
        self.assertEqual(sum(1 for r in self.ledger['rows'] if r['group'] == 'condition'), 9)

    def test_rule_links_exist_and_are_verbatim(self):
        statements = {rid: rule['statement'] for rid, rule in self.rules.items()}
        self.assertEqual(len(statements), 23)
        total = 0
        for row in self.ledger['rows']:
            self.assertTrue(row['clauses'], row['id'])
            for clause in row['clauses']:
                self.assertIn(clause, statements, row['id'])
                self.assertIn(statements[clause], self.body, (row['id'], clause))
                total += 1
        self.assertGreater(total, 60)

    def test_statuses_and_levels_are_consistent(self):
        for row in self.ledger['rows']:
            self.assertIn(row['text_status'], {'covered', 'partial', 'not_covered'}, row['id'])
            self.assertIn(row['implementation_status'],
                          {'absent', 'present_unverified', 'verified_structural'}, row['id'])
            self.assertLessEqual(RANK[row['evidence_level_now']],
                                 RANK[row['required_evidence_level']] if row['meets_required_level']
                                 else RANK[row['required_evidence_level']], row['id'])
            expected = RANK[row['evidence_level_now']] >= RANK[row['required_evidence_level']]
            self.assertEqual(row['meets_required_level'], expected, row['id'])

    def test_no_behaviour_claim_anywhere(self):
        for row in self.ledger['rows']:
            self.assertLess(RANK[row['evidence_level_now']], RANK['L2'], row['id'])
        summary = self.ledger['summary']
        self.assertEqual(summary['rows_with_behaviour_evidence'], 0)
        self.assertEqual(summary['rows_meeting_required_level'], 3)
        self.assertEqual(summary['rows_below_required_level'], 22)
        self.assertEqual(summary['rows_total'], 25)
        self.assertEqual(summary['text_status'], {'covered': 22, 'partial': 3})
        self.assertEqual(summary['implementation_status'],
                         {'absent': 11, 'present_unverified': 11, 'verified_structural': 3})

    def test_verdict_is_not_release_ready(self):
        verdict = self.ledger['verdict']
        self.assertFalse(verdict['release_ready'])
        self.assertFalse(self.ledger['flags']['compatible_release_allowed'])
        self.assertFalse(self.ledger['flags']['release_allowed'])
        self.assertTrue(all(value is False for value in self.ledger['flags'].values()))
        blockers = verdict['blocking_reasons']
        self.assertEqual(len(blockers), 25)
        text_blockers = [b['id'] for b in blockers if b['kind'] == 'text']
        self.assertEqual(sorted(text_blockers), ['G05', 'W03', 'W08'])
        evidence_blockers = [b['id'] for b in blockers if b['kind'] == 'evidence']
        self.assertEqual(len(evidence_blockers), 22)
        self.assertEqual(len(verdict['blocker_groups']), 4)
        self.assertEqual(len(verdict['what_would_change_it']), 4)
        gaps = {g['id'] for g in self.ledger['text_gaps']}
        self.assertEqual(gaps, {'G05', 'W03', 'W08'})

    def test_registry_untouched_and_no_grants(self):
        registry = json.loads(read(REGISTRY))
        live = {
            'entities': len(registry['entities']),
            'revisions': sum(len(e['revisions']) for e in registry['entities']),
            'artifact_refs': sum(len(rv['artifacts']) + 1
                                 for e in registry['entities'] for rv in e['revisions']),
        }
        snapshot = self.ledger['registry_snapshot']
        for key, value in live.items():
            self.assertEqual(snapshot[key], value, key)
        self.assertEqual(snapshot['sha256'], sha(read(REGISTRY)))
        self.assertFalse(snapshot['changed_by_this_run'])
        self.assertEqual(self.ledger['subject']['sha256'], sha(read(V2)))
        self.assertEqual(self.ledger['honesty']['judgement_origin'],
                         'author_classification_not_independent')

    def test_checks_and_report_agree(self):
        results = {c['id']: c['result'] for c in self.ledger['checks']}
        self.assertEqual(results, {'N0%d' % i: 'PASS' for i in range(1, 7)})
        for row in self.ledger['rows']:
            self.assertIn('| %s |' % row['id'], self.report, row['id'])
        self.assertIn('не готов', self.report.lower())
        self.assertIn('3 из 25', self.report)
        self.assertIn('author_classification_not_independent', self.report)
        self.assertNotIn('готов к выпуску', self.report.lower().replace('не готов к выпуску', ''))
        for level, meaning in self.ledger['evidence_levels'].items():
            self.assertIn('| %s |' % level, self.report)


if __name__ == '__main__':
    unittest.main()
