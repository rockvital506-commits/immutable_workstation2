#!/usr/bin/env python3
"""Run the versioned mutable-tree reader tests; errors are never skipped."""
import os
from pathlib import Path
import runpy
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
ReaderTests = runpy.run_path(str(Path(ROOT) / 'agent_system/adapters/ent-0005/r0002/verify.py'))['ReaderTests']

if __name__ == '__main__':
    unittest.main(verbosity=2)
