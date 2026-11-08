#!/usr/bin/env python3
"""Run capture-worker regressions, with no dependency skips."""
import os
from pathlib import Path
import runpy
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
TOOLS = runpy.run_path(str(Path(ROOT)/'agent_system/validation/ent-0009/r0002/verify.py'))
PlanExecutionTests = TOOLS['PlanExecutionTests']
CaptureContractTests = TOOLS['CaptureContractTests']
HandoffTests = TOOLS['HandoffTests']

if __name__ == '__main__':
    unittest.main(verbosity=2)
