#!/usr/bin/env python3
"""Run offline journal replay candidates; no real approval or behavior claim."""
import os
from pathlib import Path
import runpy
import unittest

HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(HERE)
os.chdir(ROOT)
ReplayTests=runpy.run_path(str(Path(ROOT)/'agent_system/operator/ent-0018/r0001/replay_verify.py'))['ReplayTests']

if __name__=='__main__':unittest.main(verbosity=2)
