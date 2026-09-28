"""Cross-experiment evaluation: compare every condition against its experiment's baseline arm.

  python -m analysis.evals                 # table + forest plot over all experiments
  python -m analysis.evals --experiment e09_agents_md

For each (experiment, task, condition-vs-baseline) it reports the success counts, the median
cost/token difference, and a percentile bootstrap CI for that difference. With n=5 per arm the
CIs are wide on purpose: the point is to show which of the earlier conclusions survive.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from analysis.summarize import (  # noqa: E402
    AXIS,
    CONDITION_LABELS,
    DPI,
    FIGURES,
    GRID,
    INK,
    INK_2,
    MUTED,
    RESULTS,
    SERIES,
    TASK_LABELS,
    is_infra_failure,
    px,
    setup_style,
)

BOOTSTRAP = 10_000
SEED = 20260928


def load_experiment(path: Path) -> tuple[dict, list[dict]]:
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    runs = [
        json.loads(line)
        for line in (path / "runs.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return manifest, [run for run in runs if run["metrics"] and not is_infra_failure(run)]


def bootstrap_median_difference(baseline: list[float], variant: list[float]) -> tuple[float, float]:
    """Percentile bootstrap CI for median(variant) - median(baseline)."""
    rng = random.Random(SEED)
    diffs = []
    for _ in range(BOOTSTRAP):
        a = [rng.choice(baseline) for _ in baseline]
        b = [rng.choice(variant) for _ in variant]
        diffs.append(statistics.median(b) - statistics.median(a))
    diffs.sort()
    return diffs[int(0.025 * BOOTSTRAP)], diffs[int(0.975 * BOOTSTRAP) - 1]


def comparisons(experiments: list[str]) -> list[dict]:
    rows = []
    for experiment in experiments:
        path = RESULTS / experiment
        if not (path / "runs.jsonl").exists():
            continue
        manifest, runs = load_experiment(path)
        condition_names = [c["name"] for c in manifest["config"]["conditions"]]
        baseline_name = condition_names[0]
        for task in manifest["config"]["tasks"]:
            base = [r for r in runs if r["task"] == task and r["condition"] == baseline_name]
            if not base:
                continue
            # Every unordered pair, so a three-arm experiment also gets its middle-vs-top comparison.
            pairs = [
                (condition_names[index], condition_names[other])
                for index in range(len(condition_names))
                for other in range(index + 1, len(condition_names))
            ]
            for baseline_name, condition in pairs:
                base = [r for r in runs if r["task"] == task and r["condition"] == baseline_name]
                variant = [r for r in runs if r["task"] == task and r["condition"] == condition]
                if not base or not variant:
                    continue
                base_cost = [r["metrics"]["cost_usd"] for r in base]
                variant_cost = [r["metrics"]["cost_usd"] for r in variant]
                low, high = bootstrap_median_difference(base_cost, variant_cost)
                base_median = statistics.median(base_cost)
                rows.append({
                    "experiment": experiment,
                    "task": task,
                    "baseline": baseline_name,
                    "condition": condition,
                    "n": min(len(base), len(variant)),
                    "baseline_success": f"{sum(r['success'] for r in base)}/{len(base)}",
                    "condition_success": f"{sum(r['success'] for r in variant)}/{len(variant)}",
                    "baseline_cost_median": round(base_median, 5),
                    "condition_cost_median": round(statistics.median(variant_cost), 5),
                    "cost_diff_pct": round((statistics.median(variant_cost) - base_median) / base_median * 100, 1),
                    "ci_low_pct": round(low / base_median * 100, 1),
                    "ci_high_pct": round(high / base_median * 100, 1),
                    "conclusive": (low > 0) or (high < 0),
                    "baseline_tokens_median": round(statistics.median(r["metrics"]["total_tokens"] for r in base)),
                    "condition_tokens_median": round(statistics.median(r["metrics"]["total_tokens"] for r in variant)),
                    "baseline_check_rate": f"{sum(r['metrics']['ran_check_script'] for r in base)}/{len(base)}",
                    "condition_check_rate": f"{sum(r['metrics']['ran_check_script'] for r in variant)}/{len(variant)}",
                })
    return rows


def write_tables(rows: list[dict]) -> Path:
    out = RESULTS / "evals"
    out.mkdir(parents=True, exist_ok=True)
    with (out / "comparisons.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "| 實驗 | 任務 | 比較 | n | 成功率 | 成本中位數變化 | 95% CI（bootstrap） | 有把握？ |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        label = f"{CONDITION_LABELS.get(row['condition'], row['condition'])} vs {CONDITION_LABELS.get(row['baseline'], row['baseline'])}"
        lines.append(
            f"| {row['experiment']} | {TASK_LABELS.get(row['task'], row['task'])} | {label} | {row['n']} "
            f"| {row['baseline_success']} → {row['condition_success']} | {row['cost_diff_pct']:+.1f}% "
            f"| {row['ci_low_pct']:+.1f}% ~ {row['ci_high_pct']:+.1f}% | {'是' if row['conclusive'] else '否'} |"
        )
    conclusive = sum(1 for row in rows if row["conclusive"])
    lines += [
        "",
        f"共 {len(rows)} 組比較，其中 {conclusive} 組的區間不含 0。"
        f"CI 為 {BOOTSTRAP:,} 次 percentile bootstrap；n 是每組的執行次數。",
    ]
    (out / "comparisons.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def forest_plot(rows: list[dict]) -> Path:
    setup_style()
    height = 1.15 + 0.42 * len(rows) + 0.6
    fig, ax = plt.subplots(figsize=(7.6, height), dpi=DPI)
    fig.subplots_adjust(left=0.42, right=0.97, top=1 - 1.15 / height, bottom=0.6 / height)
    lows = [row["ci_low_pct"] for row in rows]
    highs = [row["ci_high_pct"] for row in rows]
    span = max(max(highs), 0) - min(min(lows), 0)
    ax.set_xlim(min(min(lows), 0) - span * 0.08, max(max(highs), 0) + span * 0.18)
    ax.set_ylim(-0.6, len(rows) - 0.4)

    labels = []
    for index, row in enumerate(rows):
        y = len(rows) - 1 - index
        color = SERIES[0] if row["conclusive"] else MUTED
        ax.plot([row["ci_low_pct"], row["ci_high_pct"]], [y, y], color=color, linewidth=px(2),
                solid_capstyle="round", zorder=3)
        ax.scatter([row["cost_diff_pct"]], [y], s=px(9) ** 2, color=color, zorder=4,
                   edgecolors="#fcfcfb", linewidths=px(2))
        ax.text(row["ci_high_pct"] + span * 0.02, y, f"{row['cost_diff_pct']:+.0f}%", va="center", ha="left",
                fontsize=8.5, color=INK_2)
        labels.append(
            f"{TASK_LABELS.get(row['task'], row['task'])}\n{CONDITION_LABELS.get(row['condition'], row['condition'])}"
        )

    ax.axvline(0, color=AXIS, linewidth=px(1.5), zorder=2)
    ax.set_yticks(range(len(rows) - 1, -1, -1), labels, fontsize=8)
    ax.set_xlabel("相對於對照組的成本變化（%）", fontsize=9, color=MUTED)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.spines["bottom"].set_linewidth(px(1))
    ax.grid(axis="x", color=GRID, linewidth=px(1))
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.tick_params(axis="x", colors=MUTED, labelsize=9)
    ax.tick_params(axis="y", colors=INK_2)

    h = fig.get_figheight()
    fig.text(0.015, 1 - 0.1 / h, "哪些結論撐得住？", ha="left", va="top", fontsize=14, color=INK, fontweight="bold")
    fig.text(0.015, 1 - 0.43 / h,
             f"點是成本中位數變化，橫線是 {BOOTSTRAP:,} 次 bootstrap 的 95% 區間；壓到 0 那條線上就代表沒把握",
             ha="left", va="top", fontsize=9.5, color=INK_2)
    handles = [
        Line2D([], [], marker="o", linestyle="-", markersize=px(9), color=SERIES[0], linewidth=px(2),
               markeredgewidth=0, label="區間不含 0（有把握）"),
        Line2D([], [], marker="o", linestyle="-", markersize=px(9), color=MUTED, linewidth=px(2),
               markeredgewidth=0, label="區間含 0（沒把握）"),
    ]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.008, 1 - 0.66 / h), ncol=2, frameon=False,
               labelcolor=INK_2, handletextpad=0.5, columnspacing=1.6, fontsize=9.5)
    out = FIGURES / "day24_forest.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", action="append")
    args = parser.parse_args(argv)
    experiments = args.experiment or sorted(
        path.name for path in RESULTS.iterdir() if (path / "runs.jsonl").exists() and path.name != "evals"
    )
    rows = comparisons(experiments)
    if not rows:
        print("no comparisons found")
        return 1
    out = write_tables(rows)
    figure = forest_plot(rows)
    print((out / "comparisons.md").read_text(encoding="utf-8"))
    print(figure)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
