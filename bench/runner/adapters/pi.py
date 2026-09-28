from __future__ import annotations

import os
import shutil
import subprocess
import time
from functools import cache
from pathlib import Path, PurePosixPath

from bench.runner.adapters.base import AgentRun
from bench.runner.config import PYTHON_EXE, REPO_ROOT, Condition

# Silent event stream this long = hung harness/provider, not a slow agent. Longer than Pi's own
# 300 s httpIdleTimeoutMs so Pi gets a chance to retry first.
STALL_SECONDS = int(os.environ.get("BENCH_STALL_SECONDS", "420"))
POLL_SECONDS = 5

# Day 28: where the host keeps Pi's credentials and model store. Mounting this into the
# container is what lets the containerised agent authenticate without its own /login.
HOST_AGENT_DIR = os.environ.get("PI_CODING_AGENT_DIR", "")

CONTAINER_WORK = "/work"
CONTAINER_SESSION = "/session"
CONTAINER_REPO = "/repo"
CONTAINER_AGENT_DIR = "/pi-agent"
CONTAINER_CLI_JS = "/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js"


def _default_cli_js() -> str:
    override = os.environ.get("PI_CLI_JS")
    if override:
        return override
    shim = shutil.which("pi")
    if not shim:
        raise RuntimeError("pi is not on PATH; set PI_CLI_JS to .../pi-coding-agent/dist/bundle/cli.js")
    return str(Path(shim).parent / "node_modules" / "@earendil-works" / "pi-coding-agent" / "dist" / "bundle" / "cli.js")


def _kill_tree(proc: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
    else:
        proc.kill()


class PiAdapter:
    name = "pi"

    def __init__(self, model: str, python_exe: str = PYTHON_EXE) -> None:
        self.model = model
        self.python_exe = python_exe
        self.cli_js = _default_cli_js()

    @cache  # noqa: B019
    def version(self) -> str:
        out = subprocess.run(["node", self.cli_js, "--version"], capture_output=True, text=True)
        return out.stdout.strip()

    def build_command(
        self,
        prompt: str,
        condition: Condition,
        session_dir: Path | PurePosixPath,
        *,
        cli_js: str | None = None,
        repo_root: Path | PurePosixPath = REPO_ROOT,
    ) -> list[str]:
        cmd = [
            "node", cli_js or self.cli_js, "-p", "--mode", "json",
            "--no-extensions", "--no-skills", "--no-prompt-templates", "--no-themes",
            "--session-dir", str(session_dir),
            "--model", self.model,
            "--thinking", condition.thinking,
        ]
        if not condition.context_files:
            cmd.append("--no-context-files")
        for skill in condition.skills:
            cmd += ["--skill", str(repo_root / skill)]
        for extension in condition.extensions:
            cmd += ["-e", str(repo_root / extension)]
        if condition.tools is not None:
            cmd += ["--tools", ",".join(condition.tools)]
        if condition.append_system_prompt:
            cmd += ["--append-system-prompt", condition.append_system_prompt]
        cmd += list(condition.pi_args)
        return [*cmd, "--", prompt]

    def _docker_command(
        self, prompt: str, condition: Condition, workdir: Path, session_dir: Path
    ) -> list[str]:
        """Same pi invocation, but the whole process runs inside the container.

        Only paths change: the workdir, the session directory and the repo are bind-mounted,
        and Pi's agent directory comes from the host so the container inherits the login.
        """
        if not HOST_AGENT_DIR:
            raise RuntimeError("PI_CODING_AGENT_DIR is not set; the container would have no credentials")
        inner = self.build_command(
            prompt,
            condition,
            PurePosixPath(CONTAINER_SESSION),
            cli_js=CONTAINER_CLI_JS,
            repo_root=PurePosixPath(CONTAINER_REPO),
        )
        return [
            "docker", "run", "--rm",
            "-v", f"{workdir}:{CONTAINER_WORK}",
            "-v", f"{session_dir}:{CONTAINER_SESSION}",
            "-v", f"{REPO_ROOT}:{CONTAINER_REPO}:ro",
            "-v", f"{HOST_AGENT_DIR}:{CONTAINER_AGENT_DIR}",
            "-w", CONTAINER_WORK,
            "-e", f"PI_CODING_AGENT_DIR={CONTAINER_AGENT_DIR}",
            "-e", "PYTHONUTF8=1",
            condition.docker_image,
            *inner,
        ]

    def run(self, workdir: Path, prompt: str, condition: Condition, run_dir: Path, timeout: int) -> AgentRun:
        session_dir = run_dir / "session"
        session_dir.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["PATH"] = str(Path(self.python_exe).parent) + os.pathsep + env.get("PATH", "")
        env["PYTHONUTF8"] = "1"
        env.pop("VIRTUAL_ENV", None)
        if condition.docker_image:
            cmd = self._docker_command(prompt, condition, workdir, session_dir)
        else:
            cmd = self.build_command(prompt, condition, session_dir)
        stdout_path, stderr_path = run_dir / "events.jsonl", run_dir / "stderr.txt"
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        start = time.monotonic()
        timed_out = stalled = False
        with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
            proc = subprocess.Popen(
                cmd, cwd=workdir, env=env, stdout=out, stderr=err, stdin=subprocess.DEVNULL, creationflags=flags
            )
            last_size, last_growth = 0, start
            while True:
                try:
                    exit_code = proc.wait(timeout=POLL_SECONDS)
                    break
                except subprocess.TimeoutExpired:
                    now = time.monotonic()
                    size = stdout_path.stat().st_size
                    if size != last_size:
                        last_size, last_growth = size, now
                    if now - start > timeout or now - last_growth > STALL_SECONDS:
                        timed_out = now - start > timeout
                        stalled = not timed_out
                        _kill_tree(proc)
                        exit_code = proc.wait()
                        break
        sessions = sorted(session_dir.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime)
        return AgentRun(
            command=cmd,
            exit_code=exit_code,
            timed_out=timed_out,
            wall_seconds=round(time.monotonic() - start, 2),
            session_path=sessions[-1] if sessions else None,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            stalled=stalled,
        )
