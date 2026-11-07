#!/usr/bin/env python3
"""Isolated filesystem tests. No real private source is used."""
import hashlib
import json
import os
from pathlib import Path
import platform
import runpy
import tempfile
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[3]
READER_PATH = BASE / 'adapters/ent-0005/r0003/reader.py'
module = runpy.run_path(str(READER_PATH))
read_artifact = module['read_artifact']
ReadBlocked = module['ReadBlocked']
observe_directory = module['observe_directory']
read_set = module['read_set']
# Functions created by runpy retain their own globals dictionary.
GLOBALS = read_artifact.__globals__


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'root'
        self.root.mkdir()
        (self.root / 'dir').mkdir()
        (self.root / 'dir/file.md').write_bytes(b'example\n')
        self.outside = self.base / 'outside'
        self.outside.mkdir()
        (self.outside / 'private').write_bytes(b'never read\n')

    def fixture_expected(self, path):
        # Build expectations ONLY for trusted synthetic fixtures before the hook.
        # Production callers must obtain these from an independently selected
        # approved composition; the reader never learns expectations from input.
        result = dict(path=path, sha256=hashlib.sha256(b'example\n').hexdigest(), size_bytes=8)
        prefix, pending, links = [], path.split('/'), []
        try:
            for _ in range(40):
                if not pending:
                    break
                part, pending = pending[0], pending[1:]
                if part in ('', '.'):
                    continue
                if part == '..':
                    if not prefix:
                        return result
                    prefix.pop()
                    continue
                candidate = self.root.joinpath(*prefix, part)
                if candidate.is_symlink():
                    target = os.readlink(candidate)
                    links.append(dict(path='/'.join(prefix + [part]),
                                      link_type='symbolic_link', target=target))
                    if target.startswith('/'):
                        target = str(Path(target).relative_to(self.root))
                        prefix = []
                    pending = target.split('/') + pending
                else:
                    prefix.append(part)
            if links and not pending:
                result.update(links=links, resolved_path='/'.join(prefix))
        except (OSError, ValueError):
            pass
        return result

    def read(self, path, **kwargs):
        expected = kwargs.pop('expected', self.fixture_expected(path))
        return read_artifact(self.root, path, expected=expected, **kwargs)

    def blocked(self, path, code=None, **kwargs):
        with self.assertRaises(ReadBlocked) as ctx:
            self.read(path, **kwargs)
        if code:
            self.assertEqual(ctx.exception.code, code)
        self.assertNotIn(str(self.base), str(ctx.exception))
        return ctx.exception.code

    def test_platform_is_explicit(self):
        self.assertEqual((platform.system(), platform.machine()), ('Linux', 'x86_64'))
        with patch('platform.system', return_value='Windows'):
            self.blocked('dir/file.md', 'UNSUPPORTED_PLATFORM')

    def test_plain_file_and_expected_bytes(self):
        data, record = self.read('dir/file.md')
        self.assertEqual(data, b'example\n')
        self.assertEqual(record, dict(path='dir/file.md', size_bytes=8,
                                     sha256=hashlib.sha256(data).hexdigest()))
        self.assertEqual(self.read('dir/file.md', expected=dict(record, role='normative'))[0], data)

    def test_file_link_and_exact_target(self):
        (self.root / 'link').symlink_to('dir/./file.md')
        data, r = self.read('link')
        self.assertEqual(data, b'example\n')
        self.assertEqual(r['resolved_path'], 'dir/file.md')
        self.assertEqual(r['links'], [dict(path='link', link_type='symbolic_link', target='dir/./file.md')])
        self.assertEqual(self.read('link', expected=r)[0], data)

    def test_directory_link_and_chain(self):
        (self.root / 'alias').symlink_to('dir', target_is_directory=True)
        (self.root / 'dir/link').symlink_to('file.md')
        (self.root / 'start').symlink_to('alias/link')
        data, r = self.read('start')
        self.assertEqual(data, b'example\n')
        self.assertEqual([x['path'] for x in r['links']], ['start', 'alias', 'dir/link'])
        self.assertEqual(r['resolved_path'], 'dir/file.md')

    def test_root_link(self):
        alias = self.base / 'selected'
        alias.symlink_to(self.root, target_is_directory=True)
        self.assertEqual(read_artifact(alias, 'dir/file.md', self.fixture_expected('dir/file.md'))[0], b'example\n')

    def test_internal_absolute_target(self):
        (self.root / 'link').symlink_to(self.root / 'dir/file.md')
        self.assertEqual(self.read('link')[1]['links'][0]['target'], str(self.root / 'dir/file.md'))

    def test_internal_parent_target(self):
        (self.root / 'dir/link').symlink_to('../dir/file.md')
        self.assertEqual(self.read('dir/link')[1]['resolved_path'], 'dir/file.md')

    def test_shared_target_is_not_cycle(self):
        (self.root / 'a').symlink_to('dir/file.md')
        (self.root / 'b').symlink_to('dir/file.md')
        self.assertEqual(self.read('a')[0], self.read('b')[0])
        (self.root / 'dir/up').symlink_to('..', target_is_directory=True)
        self.assertEqual(self.read('dir/up/dir/file.md')[0], b'example\n')

    def test_external_and_return_inside_block_before_read(self):
        (self.outside / 'back').symlink_to(self.root, target_is_directory=True)
        (self.root / 'absolute').symlink_to(self.outside / 'back/dir/file.md')
        (self.root / 'relative').symlink_to('../outside/back/dir/file.md')
        with patch.dict(GLOBALS, _read_data=lambda *a: self.fail('Data read before rejection')):
            self.blocked('absolute', 'OUTSIDE_ROOT')
            self.blocked('relative', 'OUTSIDE_ROOT')

    def test_outside_then_parent_back_not_normalized_away(self):
        (self.root / 'link').symlink_to(str(self.root) + '/../root/dir/file.md')
        self.blocked('link', 'OUTSIDE_ROOT')

    def test_cycles_and_dangling(self):
        (self.root / 'a').symlink_to('b')
        (self.root / 'b').symlink_to('a')
        self.blocked('a', 'LINK_CYCLE')
        (self.root / 'broken').symlink_to('missing')
        self.blocked('broken')
        (self.root / 'self').symlink_to('self')
        self.blocked('self', 'LINK_CYCLE')

    def test_limits(self):
        self.blocked('dir/file.md', 'BYTE_LIMIT', max_bytes=4)
        (self.root / 'a').symlink_to('b')
        (self.root / 'b').symlink_to('dir/file.md')
        self.blocked('a', 'LINK_LIMIT', max_links=1)
        self.blocked('dir/file.md', 'STEP_LIMIT', max_steps=1)
        self.blocked('dir/file.md', 'INVALID_LIMIT', max_bytes=True)

    def test_invalid_logical_paths(self):
        for value in ['', '/file', '../file', 'dir/../file', 'dir//file',
                      'dir/./file', 'dir\\file', 'C:/file', 'dir/file.md\n']:
            with self.subTest(value=repr(value)):
                self.blocked(value, 'INVALID_LOGICAL_PATH')

    def test_no_directory_fifo_or_socket_read(self):
        os.mkfifo(self.root / 'fifo')
        with patch.dict(GLOBALS, _read_data=lambda *a: self.fail('Special data read')):
            self.blocked('dir', 'NOT_A_REGULAR_FILE')
            self.blocked('fifo', 'NOT_A_REGULAR_FILE')

    def test_hidden_or_changed_link_metadata_mismatch(self):
        (self.root / 'link').symlink_to('dir/file.md')
        _, record = self.read('link')
        hidden = {k: v for k, v in record.items() if k not in ('links', 'resolved_path')}
        self.blocked('link', 'ARTIFACT_MISMATCH', expected=hidden)
        wrong = dict(record, sha256='0' * 64)
        self.blocked('link', 'ARTIFACT_MISMATCH', expected=wrong)
        links = [dict(record['links'][0], target='different')]
        self.blocked('link', 'ARTIFACT_MISMATCH', expected=dict(record, links=links))
        self.blocked('link', 'ARTIFACT_MISMATCH', expected=dict(record, size_bytes=9))

    def test_link_swap_during_read(self):
        link = self.root / 'link'
        link.symlink_to('dir/file.md')
        original = GLOBALS['_read_data']
        def changed(fd, maximum):
            link.unlink()
            link.symlink_to(self.outside / 'private')
            return original(fd, maximum)
        with patch.dict(GLOBALS, _read_data=changed):
            self.blocked('link')

    def test_file_replacement_during_read(self):
        original = GLOBALS['_read_data']
        def changed(fd, maximum):
            new = self.root / 'dir/new'
            new.write_bytes(b'replacement\n')
            new.replace(self.root / 'dir/file.md')
            return original(fd, maximum)
        with patch.dict(GLOBALS, _read_data=changed):
            self.blocked('dir/file.md', 'INPUT_CHANGED')

    def test_file_write_during_read(self):
        original = GLOBALS['_read_data']
        def changed(fd, maximum):
            (self.root / 'dir/file.md').write_bytes(b'mutated\n')
            return original(fd, maximum)
        with patch.dict(GLOBALS, _read_data=changed):
            self.assertIn(self.blocked('dir/file.md'), ['INPUT_CHANGED', 'ARTIFACT_MISMATCH'])

    def test_directory_swap_between_open_calls(self):
        original = GLOBALS['_open_node']
        calls = []
        def changed(rootfd, parts):
            if parts == ['dir', 'file.md'] and not calls:
                calls.append(True)
                (self.root / 'dir').rename(self.root / 'saved')
                (self.root / 'dir').symlink_to(self.outside, target_is_directory=True)
            return original(rootfd, parts)
        with patch.dict(GLOBALS, _open_node=changed):
            self.blocked('dir/file.md', 'PATH_UNAVAILABLE_OR_UNSAFE')

    def test_kernel_unavailable_is_blocked_not_fallback(self):
        with patch('ctypes.CDLL', side_effect=OSError('unavailable')):
            self.blocked('dir/file.md', 'INPUT_UNAVAILABLE')


    def test_expected_is_mandatory_and_strict(self):
        with patch.dict(GLOBALS, _read_data=lambda *a: self.fail('Read without expectation')):
            self.blocked('dir/file.md', 'EXPECTED_REQUIRED', expected=None)
            for changes in [dict(size_bytes=True), dict(size_bytes=-1),
                            dict(sha256='A' * 64), dict(path='other'), dict(extra=True)]:
                expected = dict(self.fixture_expected('dir/file.md'), **changes)
                self.blocked('dir/file.md', 'INVALID_EXPECTED', expected=expected)
        with self.assertRaises(TypeError):
            read_artifact(self.root, 'dir/file.md')

    def test_expected_is_frozen_before_read(self):
        expected = self.fixture_expected('dir/file.md')
        original = GLOBALS['_read_data']
        def changed(fd, maximum):
            (self.root / 'dir/file.md').write_bytes(b'mutated\n')
            expected['sha256'] = hashlib.sha256(b'mutated\n').hexdigest()
            return original(fd, maximum)
        with patch.dict(GLOBALS, _read_data=changed):
            self.assertIn(self.blocked('dir/file.md', expected=expected),
                          ['INPUT_CHANGED', 'ARTIFACT_MISMATCH'])

    def test_unobserved_restored_state_does_not_prove_atomic_snapshot(self):
        original_read = GLOBALS['_read_data']
        original_fingerprint = GLOBALS['_fingerprint']
        def without_time(fd):
            return original_fingerprint(fd)[:-2] + (0, 0)
        def restored(fd, maximum):
            path = self.root / 'dir/file.md'
            path.write_bytes(b'mutated\n')
            path.write_bytes(b'example\n')
            return original_read(fd, maximum)
        # Explicit model of unchanged observable timestamps; no atomicity claim.
        with patch.dict(GLOBALS, _read_data=restored, _fingerprint=without_time):
            data, record = self.read('dir/file.md')
            self.assertEqual(data, b'example\n')
            self.assertNotIn('atomic_snapshot', record)

    def test_read_permission_failure_is_not_success(self):
        def denied(*args):
            raise PermissionError('private-path-must-not-appear')
        with patch.dict(GLOBALS, _read_data=denied):
            self.blocked('dir/file.md', 'INPUT_UNAVAILABLE')

    def test_descriptors_closed_on_success_and_failure(self):
        before = len(os.listdir('/proc/self/fd'))
        for _ in range(25):
            self.read('dir/file.md')
            self.blocked('missing')
        self.assertEqual(len(os.listdir('/proc/self/fd')), before)

    def test_declared_catalog_artifacts(self):
        base = BASE
        registry = json.loads((base / 'catalog/registry.json').read_bytes())
        for entity in registry['entities']:
            for revision in entity['revisions']:
                for artifact in revision['artifacts']:
                    data, record = read_artifact(base, artifact['path'], artifact)
                    self.assertEqual(hashlib.sha256(data).hexdigest(), artifact['sha256'])
                    self.assertEqual(record['size_bytes'], artifact['size_bytes'])


class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        ReaderTests.setUp(self)
        self.decision_name = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa.json'
        self.store = self.root / 'catalog/approvals'
        self.store.mkdir(parents=True)
        self.decision_path = 'catalog/approvals/' + self.decision_name
        (self.root / self.decision_path).write_bytes(b'{}\n')
        self.payload = dict(path='dir/file.md', sha256=hashlib.sha256(b'example\n').hexdigest(), size_bytes=8)
        self.decision = dict(path=self.decision_path, sha256=hashlib.sha256(b'{}\n').hexdigest(), size_bytes=3)

    def scan(self, path='catalog/approvals', **kwargs):
        fd = os.open(self.root, os.O_PATH | os.O_DIRECTORY)
        try:
            return observe_directory(fd, path, **kwargs)
        finally:
            os.close(fd)

    def batch(self):
        return read_set(self.root, [self.payload], [self.decision])

    def blocked(self, function, code=None):
        with self.assertRaises(ReadBlocked) as context:
            function()
        if code is not None:
            self.assertEqual(context.exception.code, code)
        self.assertNotIn(str(self.base), str(context.exception))
        return context.exception.code

    def test_directory_observation(self):
        result = self.scan()
        self.assertEqual(result['entries'], [self.decision_name])
        self.assertEqual(result['resolved_path'], 'catalog/approvals')
        self.assertEqual(result['links'], [])

    def test_directory_symlink_relative_and_absolute(self):
        moved = self.root / 'event-store'
        self.store.rename(moved)
        for target in ['../event-store', str(moved)]:
            self.store.symlink_to(target, target_is_directory=True)
            self.decision.update(links=[dict(path='catalog/approvals', link_type='symbolic_link', target=target)],
                                 resolved_path='event-store/' + self.decision_name)
            self.assertEqual(self.scan()['entries'], [self.decision_name])
            self.assertEqual(self.batch()['decisions'][self.decision_path], b'{}\n')
            self.store.unlink()

    def test_directory_alias_to_root(self):
        (self.root / 'alias').symlink_to('.', target_is_directory=True)
        result = self.scan('alias')
        self.assertEqual(result['resolved_path'], '')
        self.assertIn('catalog', result['entries'])

    def test_external_directory_link_never_listed(self):
        self.store.rename(self.root / 'saved')
        self.store.symlink_to(self.outside, target_is_directory=True)
        self.blocked(self.scan, 'OUTSIDE_ROOT')

    def test_directory_cycles_and_missing(self):
        (self.root / 'a').symlink_to('b')
        (self.root / 'b').symlink_to('a')
        self.blocked(lambda: self.scan('a'), 'LINK_CYCLE')
        self.blocked(lambda: self.scan('missing'))

    def test_directory_limits_and_wrong_type(self):
        (self.store / 'second').write_bytes(b'x')
        self.blocked(lambda: self.scan(max_entries=1), 'ENTRY_LIMIT')
        self.blocked(lambda: self.scan('dir/file.md'), 'NOT_A_DIRECTORY')

    def test_pinned_root_descriptor_not_reopened_by_name(self):
        fd = os.open(self.root, os.O_PATH | os.O_DIRECTORY)
        try:
            saved = self.base / 'moved-source'
            self.root.rename(saved)
            self.root.symlink_to(self.outside, target_is_directory=True)
            data, _ = read_artifact(None, 'dir/file.md', self.payload, root_fd=fd)
            self.assertEqual(data, b'example\n')
            self.assertTrue(os.fstat(fd))
        finally:
            os.close(fd)

    def test_batch_positive_and_evidence(self):
        result = self.batch()
        self.assertEqual(result['artifacts'], {'dir/file.md': b'example\n'})
        self.assertEqual(result['decisions'], {self.decision_path: b'{}\n'})
        evidence = result['evidence']
        self.assertEqual(evidence['directory_before'], evidence['directory_after'])
        self.assertTrue(evidence['same_root_capability'])
        self.assertFalse(evidence['transition_allowed'])
        self.assertIn('global_event_completeness', evidence['not_checked'])

    def test_batch_selected_root_symlink(self):
        alias = self.base / 'selected'
        alias.symlink_to(self.root, target_is_directory=True)
        self.assertEqual(read_set(alias, [self.payload], [self.decision])['artifacts']['dir/file.md'], b'example\n')

    def test_unplanned_decision_blocks_before_data_read(self):
        (self.store / 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb.json').write_bytes(b'not to read')
        with patch.dict(GLOBALS, _read_data=lambda *a: self.fail('Unplanned source data read')):
            self.blocked(self.batch, 'DECISION_INVENTORY_MISMATCH')

    def test_unexpected_filename_is_not_silently_filtered(self):
        (self.store / '.hidden').write_bytes(b'not to read')
        self.blocked(self.batch, 'DECISION_INVENTORY_MISMATCH')

    def test_missing_planned_decision(self):
        (self.root / self.decision_path).unlink()
        self.blocked(self.batch, 'DECISION_INVENTORY_MISMATCH')

    def test_batch_file_symlink(self):
        target = self.root / 'record.json'
        target.write_bytes(b'{}\n')
        entry = self.root / self.decision_path
        entry.unlink()
        entry.symlink_to('../../record.json')
        self.decision.update(links=[dict(path=self.decision_path, link_type='symbolic_link', target='../../record.json')],
                             resolved_path='record.json')
        self.assertEqual(self.batch()['decisions'][self.decision_path], b'{}\n')

    def test_inventory_changed_during_batch(self):
        original = GLOBALS['observe_directory']
        calls = []
        def changed(*args, **kwargs):
            result = original(*args, **kwargs)
            if not calls:
                calls.append(True)
                (self.store / 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb.json').write_bytes(b'new')
            return result
        with patch.dict(GLOBALS, observe_directory=changed):
            self.blocked(self.batch, 'SOURCE_OBSERVATION_CHANGED')

    def test_source_root_retarget_is_not_followed(self):
        original = GLOBALS['_read_data']
        observations = []
        def changed(fd, maximum):
            self.root.rename(self.base / 'moved-source')
            self.root.symlink_to(self.outside, target_is_directory=True)
            data = original(fd, maximum)
            observations.append(data)
            return data
        with patch.dict(GLOBALS, _read_data=changed):
            self.blocked(self.batch)
        self.assertEqual(observations, [b'example\n'])

    def test_bad_expectations_and_limits_before_io(self):
        self.blocked(lambda: read_set(self.root, [self.payload], [dict(self.decision, path='catalog/approvals/wrong.json')]),
                     'INVALID_DECISION_PATH')
        self.blocked(lambda: read_set(self.root, [self.payload, self.payload], [self.decision]), 'DUPLICATE_EXPECTED_PATH')
        self.blocked(lambda: read_set(self.root, [self.decision], []), 'DECISION_MISCLASSIFIED')
        self.blocked(lambda: read_set(self.root, [self.payload] * 10001, []), 'SET_LIMIT')
        self.blocked(lambda: read_set(self.root, [dict(self.payload, size_bytes=65 * 1024 * 1024)], []), 'SET_LIMIT')

    def test_root_probe_failure_closes_duplicate(self):
        fd = os.open(self.root, os.O_PATH | os.O_DIRECTORY)
        try:
            before = len(os.listdir('/proc/self/fd'))
            with patch.object(os, 'readlink', side_effect=OSError('unavailable')):
                for _ in range(10):
                    self.blocked(lambda: read_artifact(None, self.payload['path'], self.payload, root_fd=fd),
                                 'INPUT_UNAVAILABLE')
            self.assertEqual(len(os.listdir('/proc/self/fd')), before)
            self.assertTrue(os.fstat(fd))
        finally:
            os.close(fd)

    def test_changed_directory_fingerprint_between_observations(self):
        original = GLOBALS['observe_directory']
        calls = []
        def changed(*args, **kwargs):
            result = original(*args, **kwargs)
            if not calls:
                calls.append(True)
                # Deterministic visible metadata change without changing names.
                os.utime(self.store, ns=(1, 1))
            return result
        with patch.dict(GLOBALS, observe_directory=changed):
            self.blocked(self.batch, 'SOURCE_OBSERVATION_CHANGED')

    def test_batch_descriptors_closed(self):
        before = len(os.listdir('/proc/self/fd'))
        for _ in range(10):
            self.batch()
            self.blocked(lambda: read_set(self.root, [], []), 'DECISION_INVENTORY_MISMATCH')
        self.assertEqual(len(os.listdir('/proc/self/fd')), before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
