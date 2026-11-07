#!/usr/bin/env python3
"""Run the exact versioned entity decision event tests."""
import os
from pathlib import Path
import runpy
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
DecisionEventTests = runpy.run_path(str(Path(ROOT) / 'agent_system/specification/ent-0007/r0001/verify.py'))['DecisionEventTests']

if __name__ == '__main__':
    unittest.main(verbosity=2)
