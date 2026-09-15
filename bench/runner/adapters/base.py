from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from bench.runner.config import Condition


@dataclass
class AgentRun:
    command: list[str]
    exit_code: int | None
    timed_out: bool
    wall_seconds: float
    session_path: Path | None
    stdout_path: Path
    stderr_path: Path
    stalled: bool = False


class HarnessAdapter(Protocol):
    """What the runner needs from a harness. Tasks, conditions and grading stay harness-agnostic."""

    name: str

    def version(self) -> str: ...

    def run(self, workdir: Path, prompt: str, condition: Condition, run_dir: Path, timeout: int) -> AgentRun: ...
