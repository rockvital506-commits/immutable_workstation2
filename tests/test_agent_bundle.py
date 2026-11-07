#!/usr/bin/env python3
"""Run exact offline bundle consistency regressions without skips."""
import os
from pathlib import Path
import runpy
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
BundleConsistencyTests = runpy.run_path(str(Path(ROOT) / 'agent_system/validation/ent-0010/r0001/verify.py'))['BundleConsistencyTests']

class RepositoryScopeTests(unittest.TestCase):
    def test_private_archive_not_public_inventory(self):
        import tempfile
        from _repo_scope import walk_public_tree
        with tempfile.TemporaryDirectory() as root:
            for name in ['agent_system/local/run/payloads/a.md', 'agent_system/local/run/secret.ps1',
                         'agent_system/README.md', 'research/notes.md']:
                path = Path(root) / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('fixture')
            found = {str((Path(directory) / name).relative_to(root))
                     for directory, _, files in walk_public_tree(root) for name in files}
            self.assertEqual(found, {'agent_system/README.md', 'research/notes.md'})

    def test_other_local_directories_and_new_public_files_still_count(self):
        import tempfile
        from _repo_scope import walk_public_tree
        with tempfile.TemporaryDirectory() as root:
            for name in ['local/notes.md', 'tools/local/test.sh', 'agent_system/new/usage.md']:
                path = Path(root) / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('fixture')
            found = {str((Path(directory) / name).relative_to(root))
                     for directory, _, files in walk_public_tree(root) for name in files}
            self.assertEqual(found, {'local/notes.md', 'tools/local/test.sh', 'agent_system/new/usage.md'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
