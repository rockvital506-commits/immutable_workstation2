#!/usr/bin/env python3
"""Run unregistered operator foundations; never claim complete M1 acceptance."""
import os
from pathlib import Path
import runpy
import unittest

HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(HERE)
os.chdir(ROOT)
TOOLS=runpy.run_path(str(Path(ROOT)/'agent_system/operator/ent-0018/r0001/verify.py'))
SessionTests=TOOLS['SessionTests']
EvidenceTests=TOOLS['EvidenceTests']

if __name__=='__main__':unittest.main(verbosity=2)
