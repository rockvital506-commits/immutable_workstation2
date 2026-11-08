#!/usr/bin/env python3
"""Pinned archived/new-declared known views, not freshness or admission."""
import os
from pathlib import Path
import runpy
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
KnownViewComparisonTests = runpy.run_path(str(Path(ROOT) / 'agent_system/validation/ent-0017/r0001/verify.py'))['KnownViewComparisonTests']

if __name__ == '__main__':
    unittest.main(verbosity=2)
