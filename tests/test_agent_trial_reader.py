#!/usr/bin/env python3
"""Read-only pinned private trial consistency, not current permission or execution truth."""
import os
from pathlib import Path
import runpy
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
TrialReaderTests = runpy.run_path(str(Path(ROOT) / 'agent_system/staging/ent-0016/r0001/verify.py'))['TrialReaderTests']

if __name__ == '__main__':
    unittest.main(verbosity=2)
