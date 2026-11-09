#!/usr/bin/env python3
"""R5 closure candidate: verbatim portable text, no private material, no grants."""
import hashlib
import json
import os
import re
from pathlib import Path
import unittest

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

LEDGER = 'research/56-agent-system-r5-transfer-closure.json'
LEDGER_SHA = 'e56c350479d557546fe5b21c3e78291f2120e9d9247f3f30482bb390814e2a5b'
PORTABLE = 'research/56-agent-system-portable-rules-text.md'
PORTABLE_SHA = '47f8a107fb8c92491342ab8c5913790ee95ce23889dc48075bd8feb8f535dda1'
RULES_MD = 'research/53-agent-system-condition-rules.md'
RULES_JSON = 'research/53-agent-system-condition-rules.json'
ACCEPTANCE = 'research/54-agent-system-owner-acceptance.json'
REGISTRY = 'agent_system/catalog/registry.json'
BEGIN = '<!-- BEGIN VERBATIM BODY -->\n'
END = '\n<!-- END VERBATIM BODY -->\n'
PRIVATE_PATTERNS = {
    'absolute_user_path': r'/home\b|/Users\b|~/\S',
    'windows_drive_path': r'\b[A-Za-z]:[\\/]',
    'repository_path': r'\bresearch/|\bagent_system/|\btests/|\bscripts/|\bmanifest\.csv|'
                       r'\bventoy-partition/|\btools/',
    'implementation_file': r'\.py\b|\.ps1\b|\.sh\b|\.json\b|\.xml\b',
    'private_staging_marker': r'_TEMP',
    'entity_identifier': r'\bENT-?\d{3,4}\b',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return (ROOT / path).read_bytes()


def body_of(text):
    if not text.startswith('') and BEGIN not in text:
        raise ValueError('MARKERS')
    start = text.index(BEGIN) + len(BEGIN)
    end = text.index(END)
    return text[start:end]


def source_segments():
    """Тело, собранное напрямую из принятого файла, без обращения к ledger."""
    lines = read(RULES_MD).decode('utf-8').split('\n')
    def head(prefix):
        idx = [i for i, line in enumerate(lines) if line.startswith(prefix)]
        if len(idx) != 1:
            raise ValueError('HEADING_' + prefix)
        return idx[0]
    first, rules, limits, review = (head('## Назначение'), head('## Правила'),
                                    head('## Чего этот текст'), head('## Что требуется от review'))
    seg1 = '\n'.join(lines[first:rules]).rstrip('\n')
    seg2 = '\n'.join(lines[rules:limits]).rstrip('\n')
    seg3 = '\n'.join(lines[limits:review]).rstrip('\n')
    return seg1, seg2, seg3, '\n\n'.join([seg1, seg2, seg3]) + '\n'


def load():
    raw = read(LEDGER)
    if sha(raw) != LEDGER_SHA:
        raise ValueError('LEDGER_PIN')
    portable_raw = read(PORTABLE)
    if sha(portable_raw) != PORTABLE_SHA:
        raise ValueError('PORTABLE_PIN')
    ledger = json.loads(raw)
    return ledger, portable_raw.decode('utf-8'), json.loads(read(RULES_JSON))


class TransferClosureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger, cls.portable, cls.rules = load()
        cls.body = body_of(cls.portable)
        cls.seg1, cls.seg2, cls.seg3, cls.expected_body = source_segments()

    def test_pins_match_accepted_bytes(self):
        pins = self.ledger['run_pins']
        for key, pin in pins.items():
            self.assertEqual(sha(read(pin['path'])), pin['sha256'], key)
            self.assertEqual(len(read(pin['path'])), pin['size_bytes'], key)
        accepted = {a['path']: a['sha256']
                    for a in json.loads(read(ACCEPTANCE))['accepted']}
        self.assertEqual(accepted[RULES_MD], pins['accepted_rule_text']['sha256'])
        self.assertEqual(accepted[RULES_JSON], pins['rule_ledger']['sha256'])

    def test_body_is_exact_concatenation_of_accepted_text(self):
        self.assertEqual(self.body, self.expected_body)
        self.assertEqual(sha(self.body.encode('utf-8')),
                         self.ledger['portable_text']['body_sha256'])
        self.assertEqual(len(self.body.encode('utf-8')),
                         self.ledger['portable_text']['body_size_bytes'])
        self.assertFalse(self.ledger['portable_text']['header_is_normative'])
        self.assertNotIn('## Что требуется от review', self.body)

    def test_units_cover_body_once_and_are_unique(self):
        units = self.ledger['units']
        self.assertEqual(len(units), 28)
        self.assertEqual(len({u['unit_id'] for u in units}), 28)
        rules = [u['unit_id'] for u in units if u['section'] == 'rule']
        self.assertEqual(rules, ['F%02d' % i for i in range(1, 24)])
        raw_body = self.body.encode('utf-8')
        texts = {}
        for unit in units:
            raw = raw_body[unit['offset']:unit['offset'] + unit['size']]
            self.assertEqual(sha(raw), unit['sha256'], unit['unit_id'])
            text = raw.decode('utf-8')
            self.assertTrue(text.startswith(unit['heading']), unit['unit_id'])
            self.assertEqual(self.body.count(text), 1, unit['unit_id'])
            texts[unit['unit_id']] = text
        order = [u['unit_id'] for u in units]
        frame = [texts[i] for i in order if i.startswith('C-') and i != 'C-limits']
        rules = [texts[i] for i in order if i.startswith('F')]
        rebuilt = ('\n\n'.join(frame) + '\n\n## Правила\n\n' +
                   '\n\n'.join(rules) + '\n\n' + texts['C-limits'] + '\n')
        self.assertEqual(rebuilt, self.body)
        self.assertEqual(self.ledger['unit_stats'],
                         {'total': 28, 'frame': 4, 'rules': 23, 'limits': 1,
                          'universality': {'high': 22, 'limited': 6},
                          'route': {'preserve': 22,
                                    'preserve_within_declared_scope': 6}})

    def test_classification_follows_declared_mapping(self):
        evidence = {r['id']: r['evidence'] for r in self.rules['rules']}
        for unit in self.ledger['units']:
            if unit['section'] != 'rule':
                self.assertEqual(unit['universality'], 'high', unit['unit_id'])
                self.assertEqual(unit['route'], 'preserve', unit['unit_id'])
                continue
            kind = evidence[unit['unit_id']]['kind']
            if kind == 'rule':
                self.assertEqual(unit['universality'], 'high', unit['unit_id'])
                self.assertEqual(unit['route'], 'preserve', unit['unit_id'])
            elif kind == 'conditional_note':
                self.assertEqual(unit['universality'], 'limited', unit['unit_id'])
                self.assertEqual(unit['route'],
                                 'preserve_within_declared_scope', unit['unit_id'])
            else:
                self.fail('UNKNOWN_EVIDENCE_KIND ' + unit['unit_id'])

    def test_no_private_material_in_whole_file(self):
        for name, pattern in PRIVATE_PATTERNS.items():
            self.assertEqual(re.findall(pattern, self.portable), [], name)
        self.assertEqual(self.ledger['portable_file_scan']['counts'],
                         {name: 0 for name in PRIVATE_PATTERNS})
        self.assertIn('agent_system', self.body)  # имя самой системы — не приватность

    def test_internal_identifiers_recorded_as_blocker(self):
        scan = self.ledger['identifier_scan']
        self.assertEqual(scan['internal_work_package_references']['count'], 4)
        self.assertEqual(scan['internal_work_package_references']['matches'],
                         ['G05', 'G07', 'R4', 'R6'])
        self.assertFalse(scan['internal_work_package_references']['allowed'])
        self.assertEqual(scan['source_rule_references']['count'], 5)
        self.assertTrue(scan['source_rule_references']['allowed'])
        line = scan['internal_work_package_references']['line']
        self.assertIn(line, self.body)
        proposal = self.ledger['redaction_proposal']
        self.assertFalse(proposal['applied'])
        self.assertEqual(proposal['before'], line)
        self.assertNotEqual(proposal['after'], line)
        self.assertNotIn(proposal['after'], self.body)

    def test_no_authority_granted_and_registry_untouched(self):
        self.assertEqual(self.ledger['status'], 'prepared_inactive_closure_candidate')
        self.assertTrue(all(value is False for value in self.ledger['flags'].values()))
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
        self.assertFalse(snapshot['approval_added'])
        decisions = [d['id'] for d in self.ledger['decisions']]
        self.assertEqual(decisions, ['D1', 'D2', 'D3'])
        for decision in self.ledger['decisions']:
            self.assertEqual(decision['grants'], [], decision['id'])
        self.assertEqual([q['id'] for q in self.ledger['owner_decisions_required']],
                         ['Q1', 'Q2'])

    def test_checks_and_blockers_are_consistent(self):
        checks = {c['id']: c['result'] for c in self.ledger['closure_checks']}
        self.assertEqual(len(checks), 14)
        self.assertEqual([cid for cid, result in checks.items() if result != 'PASS'],
                         ['K08'])
        blockers = {b['id'] for b in self.ledger['blockers']}
        self.assertEqual(blockers, {'B1', 'B2', 'B3', 'B4', 'B5'})
        self.assertEqual(self.ledger['identifier_scan']['internal_work_package_references']
                         ['blocker'], 'B2')
        self.assertEqual(self.ledger['exclusions']['local_implementation_blocks']['count'], 103)
        self.assertFalse(self.ledger['exclusions']['local_implementation_blocks']
                         ['content_exported'])
        self.assertFalse(self.ledger['exclusions']['narrower_and_misassigned']['exported'])

    def test_receiver_prompt_is_non_normative_and_clean(self):
        prompt = self.ledger['receiver_prompt']
        self.assertTrue(prompt['non_normative'])
        self.assertTrue(prompt['not_a_permission'])
        self.assertEqual(prompt['draft_version'], 'r5-draft-1')
        self.assertTrue(all(v == 0 for v in prompt['scan'].values()))
        for name, pattern in PRIVATE_PATTERNS.items():
            self.assertEqual(re.findall(pattern, prompt['text']), [], name)


if __name__ == '__main__':
    unittest.main()
