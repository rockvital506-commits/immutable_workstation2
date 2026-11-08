#!/usr/bin/env python3
"""Inactive composition qualification; no export/release/activation."""
import os
from pathlib import Path
import runpy
import unittest
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
PreparationTests = runpy.run_path(str(Path(ROOT)/'agent_system/transfer/ent-0012/r0002/verify.py'))['PreparationTests']
if __name__ == '__main__':
    unittest.main(verbosity=2)
