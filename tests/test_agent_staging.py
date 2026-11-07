#!/usr/bin/env python3
"""Private local trial staging and real fd safety, not export or activation."""
import os
from pathlib import Path
import runpy
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
TrialStagingTests = runpy.run_path(str(Path(ROOT) / 'agent_system/staging/ent-0015/r0001/verify.py'))['TrialStagingTests']

if __name__ == '__main__':
    unittest.main(verbosity=2)
