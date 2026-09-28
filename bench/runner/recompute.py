"""Re-derive every run's metrics from its stored session, without re-running the agent.

  python -m bench.runner.recompute                 # report differences only
  python -m bench.runner.recompute --write         # rewrite runs.jsonl with the new metrics

This is what makes the recorded sessions worth keeping: when the measurement code is wrong,
the runs do not have to be repeated — they are replayed (Day 29).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from bench.runner.config import RESULTS_DIR
from bench.runner.metrics import parse_session

IGNORED = {"bash_commands", "read_paths", "final_text", "read_docs"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--experiment", action="append")
    args = parser.parse_args(argv)

    experiments = args.experiment or sorted(
        path.name for path in RESULTS_DIR.iterdir() if (path / "runs.jsonl").exists()
    )
    changed_total = 0
    for experiment in experiments:
        runs_path = RESULTS_DIR / experiment / "runs.jsonl"
        rows = [json.loads(line) for line in runs_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        changed = []
        for row in rows:
            session = RESULTS_DIR / experiment / "sessions" / f"{row['run_id']}.jsonl"
            if not session.exists() or not row.get("metrics"):
                continue
            fresh = parse_session(session)
            diff = {
                key: (row["metrics"].get(key), value)
                for key, value in fresh.items()
                # A key the old metrics never had is only worth reporting when it is non-zero.
                if key not in IGNORED
                and row["metrics"].get(key) != value
                and not (key not in row["metrics"] and not value)
            }
            if diff:
                changed.append((row["run_id"], diff))
                row["metrics"] = {**row["metrics"], **fresh}
        if changed:
            changed_total += len(changed)
            print(f"{experiment}: {len(changed)} run(s) changed")
            for run_id, diff in changed:
                keys = ", ".join(f"{k}: {old} -> {new}" for k, (old, new) in sorted(diff.items()))
                print(f"  {run_id}  {keys}")
            if args.write:
                runs_path.write_text(
                    "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8"
                )
    print(f"\n{changed_total} run(s) differ from the recorded metrics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
