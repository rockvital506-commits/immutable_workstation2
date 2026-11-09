#!/usr/bin/env python3
"""Q1/Q2 decision: no registration, one-line redaction, v2 text byte-exact elsewhere."""
import hashlib
import json
import os
import re
from pathlib import Path
import unittest

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

DECISION = 'research/57-agent-system-q1-q2-decision.json'
DECISION_SHA = '0514ad4f14703767b306c16b298d42fd375c284dd7c8fcc4acf5e5f9b5653cb8'
V2 = 'research/57-agent-system-portable-rules-text-v2.md'
V2_SHA = '15338d93103875dff2dad53218a827d9c2f26f8aa6ac8bd7af338529ac99cd85'
V1 = 'research/56-agent-system-portable-rules-text.md'
V1_SHA = '47f8a107fb8c92491342ab8c5913790ee95ce23889dc48075bd8feb8f535dda1'
CLOSURE = 'research/56-agent-system-r5-transfer-closure.json'
CLOSURE_SHA = 'e56c350479d557546fe5b21c3e78291f2120e9d9247f3f30482bb390814e2a5b'
ACCEPTANCE = 'research/54-agent-system-owner-acceptance.json'
REGISTRY = 'agent_system/catalog/registry.json'
BEGIN = '<!-- BEGIN VERBATIM BODY -->\n'
END = '\n<!-- END VERBATIM BODY -->\n'
OLD = '- Не отменяет открытые пункты R4/R6/G05/G07 и не закрывает пробелы состава.'
NEW = '- Не отменяет открытые вопросы сопровождения и не закрывает пробелы состава.'
PRIVATE = {
    'absolute_user_path': r'/home\b|/Users\b|~/\S',
    'windows_drive_path': r'\b[A-Za-z]:[\\/]',
    'repository_path': r'\bresearch/|\bagent_system/|\btests/|\bscripts/|\bmanifest\.csv|'
                       r'\bventoy-partition/|\btools/',
    'implementation_file': r'\.py\b|\.ps1\b|\.sh\b|\.json\b|\.xml\b',
    'private_staging_marker': r'_TEMP',
    'entity_identifier': r'\bENT-?\d{3,4}\b',
    'product_or_platform_name': r'\bStrelec\b|\bVentoy\b|\bVeraCrypt\b|\bBitLocker\b|'
                                r'\bMSI\b|\bWindows\b|\bLinux\b|\bNTFS\b|\bexFAT\b|\bUSB\b',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return (ROOT / path).read_bytes()


def body_of(text):
    return text[text.index(BEGIN) + len(BEGIN):text.index(END)]


def load():
    raw = read(DECISION)
    if sha(raw) != DECISION_SHA:
        raise ValueError('DECISION_PIN')
    if sha(read(V2)) != V2_SHA:
        raise ValueError('V2_PIN')
    if sha(read(V1)) != V1_SHA:
        raise ValueError('V1_PIN')
    if sha(read(CLOSURE)) != CLOSURE_SHA:
        raise ValueError('V1_LEDGER_PIN')
    return json.loads(raw), json.loads(read(CLOSURE))


class Q1Q2DecisionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decision, cls.closure = load()
        cls.v2_body = body_of(read(V2).decode('utf-8'))
        cls.v1_body = body_of(read(V1).decode('utf-8'))

    def test_owner_statement_and_answers(self):
        self.assertEqual(self.decision['owner_statement']['verbatim'],
                         'Q1. - не регистрировать; Q2 - принять замену строки')
        answers = {d['id']: d['answer'] for d in self.decision['decisions']}
        self.assertEqual(answers, {'Q1': 'не регистрировать', 'Q2': 'принять замену строки'})
        for decision in self.decision['decisions']:
            self.assertEqual(decision['grants'], [], decision['id'])

    def test_redaction_is_exactly_one_line(self):
        redaction = self.decision['redaction']
        self.assertTrue(redaction['applied'])
        self.assertTrue(redaction['applied_exactly_as_proposed'])
        self.assertEqual(redaction['before'], OLD)
        self.assertEqual(redaction['after'], NEW)
        self.assertEqual(self.closure['redaction_proposal']['before'], OLD)
        self.assertEqual(self.closure['redaction_proposal']['after'], NEW)
        self.assertEqual(self.v1_body.count(OLD), 1)
        self.assertNotIn(OLD, self.v2_body)
        self.assertEqual(self.v2_body.count(NEW), 1)
        before, after = self.v1_body.split('\n'), self.v2_body.split('\n')
        self.assertEqual(len(before), len(after))
        changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
        self.assertEqual(changed, [redaction['line_index']])
        self.assertEqual(before[changed[0]], OLD)
        self.assertEqual(after[changed[0]], NEW)

    def test_everything_else_is_byte_identical(self):
        units = {u['unit_id']: u for u in self.decision['units']}
        self.assertEqual(len(units), 28)
        raw = self.v2_body.encode('utf-8')
        for uid, unit in units.items():
            piece = raw[unit['offset']:unit['offset'] + unit['size']]
            self.assertEqual(sha(piece), unit['sha256'], uid)
            self.assertEqual(unit['changed_from_v1'], uid == 'C-limits', uid)
        for uid in units:
            if uid == 'C-limits':
                self.assertEqual(self.v1_body.count(OLD), 1)
            else:
                piece = raw[units[uid]['offset']:units[uid]['offset'] + units[uid]['size']]
                self.assertIn(piece.decode('utf-8'), self.v1_body, uid)
        rules = [u for u in units.values() if u['section'] == 'rule']
        self.assertEqual(len(rules), 23)
        v1_rules = {u['unit_id']: u['sha256'] for u in self.closure['units'] if u['section'] == 'rule'}
        for unit in rules:
            self.assertEqual(unit['sha256'], v1_rules[unit['unit_id']], unit['unit_id'])
        self.assertEqual(self.decision['unit_diff'],
                         {'total': 28, 'unchanged': 27, 'changed': ['C-limits'],
                          'changed_lines': 1, 'total_lines': 245})

    def test_v2_is_clean(self):
        for name, pattern in PRIVATE.items():
            self.assertEqual(re.findall(pattern, self.v2_body), [], name)
            self.assertEqual(re.findall(pattern, read(V2).decode('utf-8')), [], name)
        self.assertEqual(self.decision['scan']['body_private'],
                         {name: 0 for name in PRIVATE})
        self.assertEqual(self.decision['scan']['file_private'],
                         {name: 0 for name in PRIVATE})
        internal = self.decision['scan']['forbidden_internal_identifiers']
        self.assertEqual(internal['count'], 0)
        self.assertEqual(internal['matches'], [])
        allowed = self.decision['scan']['allowed_source_rule_references']
        self.assertEqual(allowed['count'], 5)
        self.assertEqual(allowed['matches'], ['G05', 'G07'])
        self.assertEqual(self.decision['portable_text_v2']['body_sha256'],
                         sha(self.v2_body.encode('utf-8')))

    def test_q1_no_registration_and_no_authority(self):
        self.assertEqual(self.decision['status_after']['registration'], 'declined_by_owner')
        self.assertEqual(self.decision['status_after']['normative_status'],
                         'not_a_registered_revision')
        self.assertEqual(self.decision['status_after']['text'],
                         'owner_accepted_text_v2_not_registered')
        self.assertTrue(all(value is False for value in self.decision['flags'].values()))
        registry = json.loads(read(REGISTRY))
        live = {
            'entities': len(registry['entities']),
            'revisions': sum(len(e['revisions']) for e in registry['entities']),
            'artifact_refs': sum(len(rv['artifacts']) + 1
                                 for e in registry['entities'] for rv in e['revisions']),
        }
        snapshot = self.decision['registry_snapshot']
        for key, value in live.items():
            self.assertEqual(snapshot[key], value, key)
        self.assertEqual(snapshot['sha256'], sha(read(REGISTRY)))
        self.assertFalse(snapshot['registration_performed'])
        self.assertFalse(snapshot['approval_added'])
        self.assertFalse(snapshot['changed_by_this_run'])

    def test_v1_and_acceptance_stay_untouched(self):
        self.assertEqual(sha(read(V1)), V1_SHA)
        self.assertEqual(sha(read(CLOSURE)), CLOSURE_SHA)
        binding = self.decision['acceptance_binding']
        self.assertEqual(binding['v1_acceptance']['sha256'], sha(read(ACCEPTANCE)))
        self.assertTrue(binding['v1_acceptance']['still_valid_for_v1'])
        self.assertFalse(binding['v1_acceptance']['applies_to_v2'])
        self.assertEqual(binding['v2_acceptance']['binding_kind'],
                         'owner_decision_recorded_by_agent_not_authenticated')
        accepted = {a['path']: a['sha256']
                    for a in json.loads(read(ACCEPTANCE))['accepted']}
        self.assertNotIn(V2, accepted)

    def test_checks_all_pass_and_blockers_named(self):
        results = {c['id']: c['result'] for c in self.decision['checks']}
        self.assertEqual(len(results), 10)
        self.assertEqual([k for k, v in results.items() if v != 'PASS'], [])
        blockers = {b['id']: b['state'] for b in self.decision['remaining_blockers']}
        self.assertEqual(set(blockers), {'B1', 'B2', 'B3', 'B4', 'B5'})
        self.assertTrue(blockers['B2'].startswith('закрыт'))
        for key in ('B3', 'B4', 'B5'):
            self.assertTrue(blockers[key].startswith('открыт'), key)


if __name__ == '__main__':
    unittest.main()
