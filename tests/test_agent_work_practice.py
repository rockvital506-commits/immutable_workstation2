#!/usr/bin/env python3
"""ENT11r2 integrity/traceability checks; NOT agent behavior evaluation."""
import os
from pathlib import Path
import runpy
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
MODULE = runpy.run_path(str(Path(ROOT)/'agent_system/protocols/ent-0011/r0002/verify.py'))
WorkMethodologyTests = MODULE['WorkMethodologyTests']
PracticeProcedureTests = MODULE['PracticeProcedureTests']

if __name__ == '__main__':
    unittest.main(verbosity=2)
