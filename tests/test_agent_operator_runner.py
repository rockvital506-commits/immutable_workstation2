#!/usr/bin/env python3
"""Run candidate runner integration; approval fixtures never change the real index."""
import os
from pathlib import Path
import runpy
import unittest

HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(HERE)
os.chdir(ROOT)
RunnerTests=runpy.run_path(str(Path(ROOT)/'agent_system/operator/ent-0018/r0001/runner_verify.py'))['RunnerTests']

if __name__=='__main__':unittest.main(verbosity=2)
