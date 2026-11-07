#!/usr/bin/env python3
"""Permission proposals and blocked transitions, not real release/export decisions."""
import os
from pathlib import Path
import runpy
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
PermissionProposalTests = runpy.run_path(str(Path(ROOT) / 'agent_system/permissions/ent-0014/r0001/verify.py'))['PermissionProposalTests']

if __name__ == '__main__':
    unittest.main(verbosity=2)
