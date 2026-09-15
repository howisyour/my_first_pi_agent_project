"""Project quality gate. CI runs this; a change is done only when it exits 0.

Usage: python scripts/check.py [--json]
"""

from __future__ import annotations

import ast
import importlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = ("taskapp/routes", "taskapp/services")
ALLOWED_NUMBERS = {0, 1, -1}
FORBIDDEN_RAISES = {"Exception", "ValueError", "KeyError", "LookupError", "RuntimeError", "TypeError"}


def _python_files(rel_dir: str) -> list[Path]:
    return sorted((ROOT / rel_dir).rglob("*.py"))


def step_ruff() -> list[str]:
    proc = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "taskapp", "scripts", "tests"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return [] if proc.returncode == 0 else [(proc.stdout or proc.stderr).strip()]


def step_pytest() -> list[str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "taskapp_testing.plugin", "tests/unit", "tests/contract"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return [] if proc.returncode == 0 else [proc.stdout[-4000:]]


def step_generated() -> list[str]:
    sys.path.insert(0, str(ROOT / "scripts"))
    gen_models = importlib.import_module("gen_models")
    lock = json.loads((ROOT / "schema" / "models.lock").read_text(encoding="utf-8"))
    actual = (ROOT / "taskapp" / "models_generated.py").read_text(encoding="utf-8").replace("\r\n", "\n")
    problems = []
    if gen_models.sha256(actual) != lock["sha256"]:
        problems.append(
            "taskapp/models_generated.py does not match schema/models.lock (was it edited by hand?). "
            "Edit schema/models.json and run: python scripts/gen_models.py"
        )
    schema = json.loads((ROOT / "schema" / "models.json").read_text(encoding="utf-8"))
    if actual != gen_models.render(schema):
        problems.append(
            "taskapp/models_generated.py is out of date with schema/models.json. Run: python scripts/gen_models.py"
        )
    return problems


def _raise_name(node: ast.Raise) -> str | None:
    exc = node.exc
    if isinstance(exc, ast.Call):
        exc = exc.func
    return exc.id if isinstance(exc, ast.Name) else None


def step_raise_scan() -> list[str]:
    problems = []
    for rel_dir in SCAN_DIRS:
        for path in _python_files(rel_dir):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Raise) and _raise_name(node) in FORBIDDEN_RAISES:
                    rel = path.relative_to(ROOT).as_posix()
                    name = _raise_name(node)
                    problems.append(f"{rel}:{node.lineno} raises {name}; use an AppError subclass from taskapp.errors")
    return problems


def step_magic_numbers() -> list[str]:
    problems = []
    for rel_dir in SCAN_DIRS:
        for path in _python_files(rel_dir):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if (
                    isinstance(node, ast.Constant)
                    and isinstance(node.value, int | float)
                    and not isinstance(node.value, bool)
                    and node.value not in ALLOWED_NUMBERS
                ):
                    rel = path.relative_to(ROOT).as_posix()
                    problems.append(
                        f"{rel}:{node.lineno} inline number {node.value!r}; define it in taskapp/constants.py"
                    )
    return problems


def step_registry() -> list[str]:
    sys.path.insert(0, str(ROOT))
    registry = importlib.import_module("taskapp.registry")
    schemas = importlib.import_module("taskapp.schemas")
    problems = []
    for route in registry.ROUTE_REGISTRY:
        module_name, func_name = route.handler.split(":")
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            problems.append(f"{route.method} {route.path}: cannot import {module_name} ({exc})")
            continue
        if not hasattr(module, func_name):
            problems.append(f"{route.method} {route.path}: {route.handler} does not exist")
        if route.schema not in schemas.__all__:
            problems.append(
                f"{route.method} {route.path}: schema {route.schema} is not exported from taskapp/schemas/__init__.py"
            )
    return problems


STEPS = {
    "ruff": step_ruff,
    "pytest": step_pytest,
    "generated": step_generated,
    "raise_scan": step_raise_scan,
    "magic_numbers": step_magic_numbers,
    "registry": step_registry,
}


def main(argv: list[str]) -> int:
    results = {}
    for name, step in STEPS.items():
        try:
            results[name] = step()
        except Exception as exc:
            results[name] = [f"step crashed: {type(exc).__name__}: {exc}"]
    failed = [name for name, problems in results.items() if problems]
    if "--json" in argv:
        print(json.dumps({"ok": not failed, "failed": failed, "results": results}, ensure_ascii=False))
    else:
        for name, problems in results.items():
            print(f"[{'FAIL' if problems else ' OK '}] {name}")
            for problem in problems:
                print("       " + problem.replace("\n", "\n       "))
        print("check passed" if not failed else f"check failed: {', '.join(failed)}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
