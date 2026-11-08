#!/usr/bin/env python3
"""Run I4 scenario gaps; no fixture approval is written to the real catalog."""
import os
from pathlib import Path
import runpy
import unittest

HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(HERE)
os.chdir(ROOT)
AcceptanceTests=runpy.run_path(str(Path(ROOT)/'agent_system/operator/ent-0018/r0001/acceptance_verify.py'))['AcceptanceTests']

if __name__=='__main__':unittest.main(verbosity=2)
