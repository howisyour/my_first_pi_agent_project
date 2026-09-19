"""Benchmark runner.

  python -m bench.runner.cli selfcheck
  python -m bench.runner.cli run experiments/configs/<exp>.json [--workers N] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

from bench.runner import metrics, verify, workspace
from bench.runner.adapters import ADAPTERS
from bench.runner.config import (
    PYTHON_EXE,
    RESULTS_DIR,
    RUNS_ROOT,
    TASKS_DIR,
    Condition,
    Experiment,
    load_experiment,
    load_task,
)
from bench.runner.sanitize import build_sanitizer

_lock = threading.Lock()


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def selfcheck() -> int:
    """Grade every task without an agent: baseline must fail, the reference solution must pass."""
    ok = True
    root = RUNS_ROOT / "_selfcheck"
    clean = workspace.prepare(None, Condition("clean"), root / "clean")
    proc = verify.subprocess.run([PYTHON_EXE, "scripts/check.py"], cwd=clean, capture_output=True, text=True)
    print(f"[{'PASS' if proc.returncode == 0 else 'FAIL'}] clean fixture passes scripts/check.py")
    ok &= proc.returncode == 0
    for task_dir in sorted(p for p in TASKS_DIR.iterdir() if (p / "task.json").exists()):
        task = load_task(task_dir.name)
        work = workspace.prepare(task, Condition("default"), root / task.id / "baseline_run")
        before = verify.verify(task, work, work.parent / "baseline", PYTHON_EXE)
        work = workspace.prepare(task, Condition("default"), root / task.id / "solution_run")
        workspace.load_module(task.dir / "solution.py").apply(work)
        after = verify.verify(task, work, work.parent / "baseline", PYTHON_EXE)
        good = (not before["success"]) and after["success"]
        ok &= good
        print(
            f"[{'PASS' if good else 'FAIL'}] {task.id}: baseline success={before['success']} "
            f"(failed: {before['check_failed_steps'] + before['hidden']['failed_tests']}), "
            f"solution success={after['success']}"
        )
        if not after["success"]:
            print(json.dumps(after, indent=2, ensure_ascii=False)[:4000])
    return 0 if ok else 1


def infra_failure_reason(stalled: bool, timed_out: bool, metrics: dict | None) -> str | None:
    """Failures caused by the harness/provider rather than the agent's work. These are rerun, not scored."""
    if stalled:
        return "stalled"
    if not metrics or metrics.get("assistant_messages", 0) == 0:
        return "no_model_turn"
    stops = metrics.get("stop_reasons") or {}
    if metrics.get("tool_calls", 0) == 0 and set(stops) <= {"error", "aborted"}:
        return f"provider_error: {metrics.get('error_message')}"
    # The run never reached a final answer and the provider errored along the way (e.g. "servers overloaded").
    if "stop" not in stops and stops.get("error", 0) > 0:
        return f"provider_error_midrun: {metrics.get('error_message')}"
    if timed_out and "stop" not in stops and metrics.get("assistant_messages", 0) <= 5:
        return "hung_before_timeout"
    return None


def is_infra_failure(record: dict) -> bool:
    if record.get("infra_failure"):
        return True
    return infra_failure_reason(record.get("stalled", False), record.get("timed_out", False), record.get("metrics")) is not None


def run_one(exp: Experiment, adapter, task_id: str, condition: Condition, rep: int, sanitize) -> dict:
    task = load_task(task_id)
    run_id = f"{task.id}__{condition.name}__r{rep:02d}"
    run_dir = RUNS_ROOT / exp.id / run_id
    out_dir = RESULTS_DIR / exp.id
    started = _now()
    workdir = workspace.prepare(task, condition, run_dir)
    agent = adapter.run(workdir, task.prompt, condition, run_dir, task.timeout_seconds)
    change = workspace.diff(workdir)
    graded = verify.verify(task, workdir, run_dir / "baseline", PYTHON_EXE)
    session_metrics = metrics.parse_session(agent.session_path) if agent.session_path else None

    (out_dir / "sessions").mkdir(parents=True, exist_ok=True)
    (out_dir / "diffs").mkdir(parents=True, exist_ok=True)
    if agent.session_path:
        text = agent.session_path.read_text(encoding="utf-8")
        (out_dir / "sessions" / f"{run_id}.jsonl").write_text(sanitize(text), encoding="utf-8", newline="\n")
    (out_dir / "diffs" / f"{run_id}.patch").write_text(sanitize(change["patch"]), encoding="utf-8", newline="\n")

    files_changed = [line.split("\t")[-1] for line in change["numstat"].splitlines() if line.strip()]
    record = {
        "experiment": exp.id,
        "run_id": run_id,
        "task": task.id,
        "component": task.component,
        "condition": condition.name,
        "rep": rep,
        "harness": adapter.name,
        "harness_version": adapter.version(),
        "model": exp.model,
        "thinking": condition.thinking,
        "started_at": started,
        "finished_at": _now(),
        "exit_code": agent.exit_code,
        "timed_out": agent.timed_out,
        "stalled": agent.stalled,
        "infra_failure": infra_failure_reason(agent.stalled, agent.timed_out, session_metrics),
        "wall_seconds": agent.wall_seconds,
        "files_changed": files_changed,
        **graded,
        "metrics": session_metrics,
        "stderr_tail": agent.stderr_path.read_text(encoding="utf-8", errors="replace")[-1500:],
    }
    record = json.loads(sanitize(json.dumps(record, ensure_ascii=False)))
    with _lock, (out_dir / "runs.jsonl").open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def run_experiment(config: Path, workers: int | None, limit: int | None, retry_infra: bool = False) -> int:
    exp = load_experiment(config)
    adapter = ADAPTERS[exp.harness](exp.model)
    out_dir = RESULTS_DIR / exp.id
    out_dir.mkdir(parents=True, exist_ok=True)
    runs_path = out_dir / "runs.jsonl"
    records = []
    if runs_path.exists():
        records = [json.loads(line) for line in runs_path.read_text(encoding="utf-8").splitlines() if line]
    if retry_infra:
        infra = [r for r in records if is_infra_failure(r)]
        if infra:
            with (out_dir / "runs.infra_dropped.jsonl").open("a", encoding="utf-8", newline="\n") as fh:
                for r in infra:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            records = [r for r in records if not is_infra_failure(r)]
            runs_path.write_text(
                "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8", newline="\n"
            )
            print(f"re-queued {len(infra)} infra failures: {[r['run_id'] for r in infra]}", flush=True)
    done = {r["run_id"] for r in records}
    manifest = {
        "experiment": exp.id,
        "title": exp.title,
        "harness": exp.harness,
        "harness_version": adapter.version(),
        "model": exp.model,
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "config": json.loads(config.read_text(encoding="utf-8")),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Interleave conditions and tasks so provider drift over time hits every arm equally.
    jobs = [
        (task_id, condition, rep)
        for rep in range(1, exp.repetitions + 1)
        for task_id in exp.tasks
        for condition in exp.conditions
        if f"{task_id}__{condition.name}__r{rep:02d}" not in done
    ]
    if limit:
        jobs = jobs[:limit]
    print(f"{exp.id}: {len(jobs)} runs to do ({len(done)} already recorded)", flush=True)
    sanitize = build_sanitizer()
    failures = 0
    consecutive_infra = 0
    breaker = int(os.environ.get("BENCH_INFRA_BREAKER", "3"))
    with ThreadPoolExecutor(max_workers=workers or exp.workers) as pool:
        futures = {pool.submit(run_one, exp, adapter, *job, sanitize): job for job in jobs}
        for future in as_completed(futures):
            task_id, condition, rep = futures[future]
            try:
                r = future.result()
                m = r["metrics"] or {}
                print(
                    f"{_now()} {r['run_id']}: success={r['success']} cost=${m.get('cost_usd', 0):.4f} "
                    f"tools={m.get('tool_calls')} wall={r['wall_seconds']}s infra={r['infra_failure']} "
                    f"failed={r['check_failed_steps']}",
                    flush=True,
                )
                consecutive_infra = consecutive_infra + 1 if r["infra_failure"] else 0
                if consecutive_infra >= breaker:
                    print(f"{_now()} ABORT: {breaker} infra failures in a row (provider down or quota exhausted?)", flush=True)
                    for pending in futures:
                        pending.cancel()
                    failures += 1
                    break
            except Exception:
                failures += 1
                print(f"{_now()} {task_id}__{condition.name}__r{rep:02d}: RUNNER ERROR", flush=True)
                traceback.print_exc()
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bench")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("selfcheck")
    run = sub.add_parser("run")
    run.add_argument("config", type=Path)
    run.add_argument("--workers", type=int)
    run.add_argument("--limit", type=int)
    run.add_argument("--retry-infra", action="store_true", help="move hung/stalled runs to runs.infra_dropped.jsonl and rerun them")
    args = parser.parse_args(argv)
    if args.command == "selfcheck":
        return selfcheck()
    return run_experiment(args.config, args.workers, args.limit, args.retry_infra)


if __name__ == "__main__":
    raise SystemExit(main())
