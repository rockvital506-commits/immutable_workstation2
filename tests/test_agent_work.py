#!/usr/bin/env python3
"""Traceability of exact work protocol/model-review vectors, not agent behavior tests."""
import os
from pathlib import Path
import runpy
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
WorkMethodologyTests = runpy.run_path(str(Path(ROOT) / 'agent_system/protocols/ent-0011/r0001/verify.py'))['WorkMethodologyTests']

if __name__ == '__main__':
    unittest.main(verbosity=2)
