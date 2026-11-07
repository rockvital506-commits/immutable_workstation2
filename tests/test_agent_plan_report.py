#!/usr/bin/env python3
"""Run exact versioned plan/report structural tests, without skipping failures."""
import os
from pathlib import Path
import runpy
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
PlanReportSchemaTests = runpy.run_path(str(Path(ROOT) / 'agent_system/specification/ent-0008/r0001/verify.py'))['PlanReportSchemaTests']

if __name__ == '__main__':
    unittest.main(verbosity=2)
