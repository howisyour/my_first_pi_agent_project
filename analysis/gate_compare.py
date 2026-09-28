"""Day 26: the three gate arms side by side — outcome, cost and how often the gate fired.

  python -m analysis.gate_compare <out.png>

The arms live in two experiment directories (the v2 gate was a separate run), so this cannot
go through analysis.evals, which compares conditions inside one experiment.
"""

from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from analysis.summarize import (  # noqa: E402
    AXIS,
    DPI,
    GRID,
    INK,
    INK_2,
    MUTED,
    RESULTS,
    SERIES,
    is_infra_failure,
    px,
    setup_style,
)

ARMS = [
    ("e26_tool_gate", "no_gate", "沒有閘門"),
    ("e26_tool_gate", "with_gate", "閘門 v1"),
    ("e26b_tool_gate_v2", "with_gate_v2", "閘門 v2"),
]


def load(experiment: str, condition: str) -> list[dict]:
    path = RESULTS / experiment / "runs.jsonl"
    runs = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [
        run
        for run in runs
        if run["condition"] == condition and run["metrics"] and not is_infra_failure(run)
    ]


def blocked_count(run: dict) -> int:
    match = re.search(r"blocked (\d+) deletion", run.get("stderr_tail") or "")
    return int(match.group(1)) if match else 0


def main(argv: list[str]) -> int:
    out = Path(argv[0])
    setup_style()
    arms = [(label, load(experiment, condition)) for experiment, condition, label in ARMS]

    header_in, footer_in = 1.35, 0.62
    height = header_in + 0.78 * len(arms) + footer_in
    fig, ax = plt.subplots(figsize=(7.4, height), dpi=DPI)
    fig.subplots_adjust(left=0.15, right=0.71, top=1 - header_in / height, bottom=footer_in / height)

    costs = [run["metrics"]["cost_usd"] for _, runs in arms for run in runs]
    lo, hi = min(costs), max(costs)
    pad = (hi - lo) * 0.18
    ax.set_xlim(lo - pad, hi + pad)
    ax.set_ylim(-0.6, len(arms) - 0.4)

    for index, (label, runs) in enumerate(arms):
        y = len(arms) - 1 - index
        median = statistics.median(run["metrics"]["cost_usd"] for run in runs)
        ax.plot([median, median], [y - 0.26, y + 0.26], color=AXIS, linewidth=px(2), zorder=2,
                solid_capstyle="round")
        for run in runs:
            cost = run["metrics"]["cost_usd"]
            if run["success"]:
                ax.scatter([cost], [y], s=px(9) ** 2, color=SERIES[0], zorder=4,
                           edgecolors="#fcfcfb", linewidths=px(1.5))
            else:
                ax.scatter([cost], [y], s=px(11) ** 2, color=SERIES[1], marker="x", zorder=4,
                           linewidths=px(2.2))
        successes = sum(1 for run in runs if run["success"])
        blocks = sum(blocked_count(run) for run in runs)
        ax.annotate(
            f"成功 {successes}/{len(runs)}｜擋下 {blocks} 次｜中位 ${median:.4f}",
            xy=(1.02, y), xycoords=("axes fraction", "data"), va="center", ha="left",
            fontsize=9, color=INK_2, annotation_clip=False,
        )

    ax.set_yticks(range(len(arms) - 1, -1, -1), [label for label, _ in arms], fontsize=10)
    ax.set_xlabel("單次執行成本", fontsize=9, color=MUTED)
    ax.xaxis.set_major_formatter(lambda value, _pos: f"${value:.4f}")
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
    fig.text(0.015, 1 - 0.1 / h, "同一個清理任務，三種閘門設定", ha="left", va="top", fontsize=14, color=INK,
             fontweight="bold")
    fig.text(0.015, 1 - 0.44 / h,
             "每個點是一次執行；灰線是該組的成本中位數。v1 失敗的三次都不是模型的錯，是閘門擋掉了正確的指令",
             ha="left", va="top", fontsize=9.5, color=INK_2)
    handles = [
        Line2D([], [], marker="o", linestyle="", markersize=px(9), markerfacecolor=SERIES[0],
               markeredgewidth=0, label="任務成功"),
        Line2D([], [], marker="x", linestyle="", markersize=px(9), color=SERIES[1],
               markeredgewidth=px(2.2), label="任務失敗"),
    ]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.008, 1 - 0.7 / h), ncol=2, frameon=False,
               labelcolor=INK_2, handletextpad=0.5, columnspacing=1.8, fontsize=9.5)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
