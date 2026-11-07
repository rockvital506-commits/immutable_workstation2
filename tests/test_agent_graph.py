#!/usr/bin/env python3
"""Run the exact versioned catalog binding and graph regression suite."""
import os
from pathlib import Path
import runpy
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
BindingGraphTests = runpy.run_path(str(Path(ROOT) / 'agent_system/validation/ent-0006/r0001/verify.py'))['BindingGraphTests']

if __name__ == '__main__':
    unittest.main(verbosity=2)
