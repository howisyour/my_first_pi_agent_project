from __future__ import annotations

import filecmp
import json
import os
import shutil
import subprocess
from pathlib import Path

from bench.runner.config import Task
from bench.runner.workspace import PROTECTED, rmtree


def _files(root: Path) -> set[str]:
    if not root.is_dir():
        return set()
    return {
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts
    }


def changed_protected(workdir: Path, baseline: Path) -> list[str]:
    changed = []
    for rel in PROTECTED:
        base, work = baseline / rel, workdir / rel
        if base.is_file():
            if not work.is_file() or not filecmp.cmp(base, work, shallow=False):
                changed.append(rel)
            continue
        base_files, work_files = _files(base), _files(work)
        for name in sorted(base_files | work_files):
            if name not in base_files or name not in work_files or not filecmp.cmp(base / name, work / name, shallow=False):
                changed.append(f"{rel}/{name}")
    return changed


def restore_protected(workdir: Path, baseline: Path) -> None:
    for rel in PROTECTED:
        src, dst = baseline / rel, workdir / rel
        if dst.is_dir():
            rmtree(dst)
        elif dst.exists():
            dst.unlink()
        if src.is_dir():
            shutil.copytree(src, dst)
        elif src.exists():
            shutil.copy2(src, dst)


def _env() -> dict:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    return env


def verify(task: Task, workdir: Path, baseline: Path, python_exe: str) -> dict:
    tampered = changed_protected(workdir, baseline)
    restore_protected(workdir, baseline)

    proc = subprocess.run(
        [python_exe, "scripts/check.py", "--json"],
        cwd=workdir, capture_output=True, text=True, encoding="utf-8", timeout=600, env=_env(),
    )
    try:
        check = json.loads(proc.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        check = {"ok": False, "failed": ["check_crashed"], "results": {"check_crashed": [proc.stderr[-2000:]]}}

    hidden = {"ran": False, "ok": True, "failed_tests": [], "tail": ""}
    hidden_dir = task.dir / "hidden"
    if hidden_dir.is_dir():
        target = workdir / "_verify"
        shutil.copytree(hidden_dir, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
        proc = subprocess.run(
            [python_exe, "-m", "pytest", "-p", "taskapp_testing.plugin", "-p", "no:cacheprovider", "-q", "-rfE", "_verify"],
            cwd=workdir, capture_output=True, text=True, encoding="utf-8", timeout=600, env=_env(),
        )
        failed = [
            line.split(" ", 1)[1].split(" - ")[0]
            for line in proc.stdout.splitlines()
            if line.startswith(("FAILED ", "ERROR "))
        ]
        hidden = {"ran": True, "ok": proc.returncode == 0, "failed_tests": failed, "tail": "" if proc.returncode == 0 else proc.stdout[-3000:]}
        rmtree(target)

    return {
        "success": bool(check.get("ok")) and hidden["ok"],
        "check_ok": bool(check.get("ok")),
        "check_failed_steps": check.get("failed", []),
        "check_details": {name: problems for name, problems in check.get("results", {}).items() if problems},
        "hidden": hidden,
        "tampered_protected_files": tampered,
    }
