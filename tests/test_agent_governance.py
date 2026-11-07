#!/usr/bin/env python3
"""Exact preparation behavior and lifecycle document checks, not release/activation tests."""
import os
from pathlib import Path
import runpy
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
GovernancePreparationTests = runpy.run_path(str(Path(ROOT) / 'agent_system/protocols/ent-0012/r0001/verify.py'))['GovernancePreparationTests']

if __name__ == '__main__':
    unittest.main(verbosity=2)
