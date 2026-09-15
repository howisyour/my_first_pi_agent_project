from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCH_DIR = REPO_ROOT / "bench"
FIXTURE_DIR = BENCH_DIR / "fixtures" / "taskapp"
TASKS_DIR = BENCH_DIR / "tasks"
RESULTS_DIR = REPO_ROOT / "experiments" / "results"

RUNS_ROOT = Path(os.environ.get("BENCH_RUNS_ROOT", "D:/pi-bench-runs"))
PYTHON_EXE = os.environ.get("BENCH_PYTHON", str(RUNS_ROOT / "_env" / "venv" / "Scripts" / "python.exe"))


@dataclass(frozen=True)
class Task:
    id: str
    component: str
    prompt: str
    timeout_seconds: int
    dir: Path


@dataclass(frozen=True)
class Condition:
    name: str
    remove_files: tuple[str, ...] = ()
    skills: tuple[str, ...] = ()
    tools: tuple[str, ...] | None = None
    thinking: str = "medium"
    context_files: bool = True
    append_system_prompt: str | None = None


@dataclass(frozen=True)
class Experiment:
    id: str
    title: str
    harness: str
    model: str
    tasks: tuple[str, ...]
    conditions: tuple[Condition, ...]
    repetitions: int
    workers: int


def load_task(task_id: str) -> Task:
    task_dir = TASKS_DIR / task_id
    data = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    return Task(
        id=data["id"],
        component=data["component"],
        prompt=data["prompt"],
        timeout_seconds=data.get("timeout_seconds", 900),
        dir=task_dir,
    )


def _condition(data: dict) -> Condition:
    tools = data.get("tools")
    return Condition(
        name=data["name"],
        remove_files=tuple(data.get("remove_files", ())),
        skills=tuple(data.get("skills", ())),
        tools=tuple(tools) if tools is not None else None,
        thinking=data.get("thinking", "medium"),
        context_files=data.get("context_files", True),
        append_system_prompt=data.get("append_system_prompt"),
    )


def load_experiment(path: Path) -> Experiment:
    data = json.loads(path.read_text(encoding="utf-8"))
    return Experiment(
        id=data["id"],
        title=data["title"],
        harness=data.get("harness", "pi"),
        model=data["model"],
        tasks=tuple(data["tasks"]),
        conditions=tuple(_condition(c) for c in data["conditions"]),
        repetitions=data["repetitions"],
        workers=data.get("workers", 1),
    )
