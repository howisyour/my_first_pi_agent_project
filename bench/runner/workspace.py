from __future__ import annotations

import importlib.util
import os
import shutil
import stat
import subprocess
from pathlib import Path

from bench.runner.config import FIXTURE_DIR, Condition, Task

IGNORE = shutil.ignore_patterns("__pycache__", ".pytest_cache", ".ruff_cache", "*.pyc")
# Files the agent must not need to touch. Verification restores them before grading.
PROTECTED = ("scripts/check.py", "scripts/gen_models.py", "taskapp_testing", "pyproject.toml", "tests")


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"bench_{path.parent.name}_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _force_remove(func, path, _exc):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def rmtree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, onexc=_force_remove)


def git(workdir: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-c", "user.name=bench", "-c", "user.email=bench@example.invalid", "-c", "core.autocrlf=false", *args],
        cwd=workdir,
        capture_output=True,
        check=True,
    )
    return proc.stdout.decode("utf-8", errors="replace")


def prepare(task: Task | None, condition: Condition, run_dir: Path) -> Path:
    rmtree(run_dir)
    workdir = run_dir / "work"
    shutil.copytree(FIXTURE_DIR, workdir, ignore=IGNORE)
    if task is not None and (task.dir / "setup.py").exists():
        load_module(task.dir / "setup.py").apply(workdir)
    for rel in condition.remove_files:
        (workdir / rel).unlink(missing_ok=True)
    shutil.copytree(workdir, run_dir / "baseline")
    git(workdir, "init", "-q")
    git(workdir, "add", "-A")
    git(workdir, "commit", "-q", "-m", "baseline")
    return workdir


def diff(workdir: Path) -> dict:
    git(workdir, "add", "-A")
    return {
        "stat": git(workdir, "diff", "--cached", "--stat", "HEAD"),
        "numstat": git(workdir, "diff", "--cached", "--numstat", "HEAD"),
        "patch": git(workdir, "diff", "--cached", "HEAD"),
    }
