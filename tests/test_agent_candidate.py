#!/usr/bin/env python3
"""Frozen incomplete-candidate consistency, not semantic coverage or release tests."""
import os
from pathlib import Path
import runpy
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
CandidateCoverageTests = runpy.run_path(str(Path(ROOT) / 'agent_system/candidates/ent-0013/r0001/verify.py'))['CandidateCoverageTests']

if __name__ == '__main__':
    unittest.main(verbosity=2)
