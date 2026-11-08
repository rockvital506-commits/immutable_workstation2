#!/usr/bin/env python3
"""Local permission semantics/native incomplete guard; synthetic authority only."""
import os
from pathlib import Path
import runpy
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
MODULE = runpy.run_path(str(Path(ROOT)/'agent_system/permissions/ent-0014/r0002/verify.py'))
AuthorityTests = MODULE['AuthorityTests']
NativeGuardTests = MODULE['NativeGuardTests']

if __name__ == '__main__':
    unittest.main(verbosity=2)
