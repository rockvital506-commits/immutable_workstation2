#!/usr/bin/env python3
"""Declared inactive binding and physical immutable lineage, not activation."""
import os
from pathlib import Path
import runpy
import unittest
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
BindingTests = runpy.run_path(str(Path(ROOT)/'agent_system/adapters/ent-0019/r0001/verify.py'))['BindingTests']
if __name__ == '__main__':
    unittest.main(verbosity=2)
