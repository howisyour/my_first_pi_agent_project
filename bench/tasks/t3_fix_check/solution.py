import importlib.util
from pathlib import Path

from bench.runner.edits import replace_once


def apply(workdir):
    spec = importlib.util.spec_from_file_location("t3_setup", Path(__file__).with_name("setup.py"))
    setup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(setup)
    for rel, old, new in reversed(setup.CHANGES):
        replace_once(workdir / rel, new, old)
