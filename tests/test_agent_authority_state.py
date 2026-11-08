#!/usr/bin/env python3
"""Private authority state physics; assents synthetic, no actual action grants."""
import os
from pathlib import Path
import runpy
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
StateTests = runpy.run_path(str(Path(ROOT)/'agent_system/permissions/ent-0014/r0003/verify.py'))['StateTests']

if __name__ == '__main__':
    unittest.main(verbosity=2)
