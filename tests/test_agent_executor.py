#!/usr/bin/env python3
"""Run exact pinned-plan executor regressions; never skip unavailable dependencies."""
import os
from pathlib import Path
import runpy
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
PlanExecutionTests = runpy.run_path(str(Path(ROOT) / 'agent_system/validation/ent-0009/r0001/verify.py'))['PlanExecutionTests']

if __name__ == '__main__':
    unittest.main(verbosity=2)
