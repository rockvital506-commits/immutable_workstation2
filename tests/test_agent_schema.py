#!/usr/bin/env python3
"""Run the versioned schema regression suite; missing engine is an error."""
import os
from pathlib import Path
import runpy
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
TEST_FILE = Path(ROOT) / 'agent_system/validation/ent-0004/r0001/verify.py'
StructuralSchemaTests = runpy.run_path(str(TEST_FILE))['StructuralSchemaTests']

if __name__ == '__main__':
    unittest.main(verbosity=2)
