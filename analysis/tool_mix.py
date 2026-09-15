"""Stacked tool mix per task, averaged over runs of one condition (Day 12).

  python -m analysis.tool_mix <experiment> <condition> <out.png>
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

from analysis.summarize import (  # noqa: E402
    AXIS,
    DISPLAY_SCALE,
    DPI,
    GRID,
    INK,
    INK_2,
    MUTED,
    RESULTS,
    SERIES,
    SURFACE,
    TASK_LABELS,
    CONDITION_LABELS,
    is_infra_failure,
    px,
    setup_style,
)

TOOL_ORDER = ["read", "bash", "edit", "write"]


def main(argv: list[str]) -> int:
    experiment, condition, out = argv[0], argv[1], Path(argv[2])
    setup_style()
    runs = [
        json.loads(line)
        for line in (RESULTS / experiment / "runs.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    manifest = json.loads((RESULTS / experiment / "manifest.json").read_text(encoding="utf-8"))
    # condition == "ALL": one row per condition instead of one row per task.
    by_condition = condition == "ALL"
    per_task: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    counts: dict[str, int] = defaultdict(int)
    for run in runs:
        if (not by_condition and run["condition"] != condition) or not run["metrics"] or is_infra_failure(run):
            continue
        key = run["condition"] if by_condition else run["task"]
        counts[key] += 1
        for name, calls in run["metrics"]["tool_calls_by_name"].items():
            per_task[key][name] += calls
    if by_condition:
        tasks = [c["name"] for c in manifest["config"]["conditions"] if c["name"] in per_task]
    else:
        tasks = [t for t in manifest["config"]["tasks"] if t in per_task]
    tools = TOOL_ORDER + sorted({n for task in per_task.values() for n in task} - set(TOOL_ORDER))

    header_in, footer_in = 1.05, 0.6
    height = header_in + 0.52 * len(tasks) + 0.4 + footer_in
    fig, ax = plt.subplots(figsize=(7.2, height), dpi=DPI)
    fig.subplots_adjust(left=0.3 if by_condition else 0.2, right=0.95, top=1 - header_in / height,
                        bottom=footer_in / height)
    totals = [sum(per_task[t].values()) / counts[t] for t in tasks]
    ax.set_xlim(0, max(totals) * 1.12)
    ax.set_ylim(-0.6, len(tasks) - 0.4)
    fig.canvas.draw()
    bbox = ax.get_window_extent()
    ux = (max(totals) * 1.12) / bbox.width
    uy = (len(tasks) + 0.2) / bbox.height
    bar_h = min(0.34, 24 * DISPLAY_SCALE * uy)
    gap = 2 * DISPLAY_SCALE * ux
    radius = 4 * DISPLAY_SCALE * ux

    for row, task in enumerate(tasks):
        y = (len(tasks) - 1 - row)
        x = 0.0
        segments = [(tool, per_task[task].get(tool, 0) / counts[task]) for tool in tools]
        segments = [(name, value) for name, value in segments if value > 0]
        for index, (name, value) in enumerate(segments):
            width = value - (gap if index < len(segments) - 1 else 0)
            color = SERIES[tools.index(name) % len(SERIES)]
            last = index == len(segments) - 1
            if last:
                r = min(radius, width / 2)
                ax.add_patch(FancyBboxPatch((x, y - bar_h / 2), width, bar_h,
                                            boxstyle=f"round,pad=0,rounding_size={r}", mutation_aspect=uy / ux,
                                            linewidth=0, facecolor=color))
                ax.add_patch(Rectangle((x, y - bar_h / 2), min(r, width), bar_h, linewidth=0, facecolor=color))
            else:
                ax.add_patch(Rectangle((x, y - bar_h / 2), width, bar_h, linewidth=0, facecolor=color))
            x += value
        ax.text(x + max(totals) * 0.012, y, f"{x:.0f} 次", va="center", ha="left", fontsize=9, color=INK_2)

    labels = [(CONDITION_LABELS if by_condition else TASK_LABELS).get(t, t) for t in tasks]
    ax.set_yticks(range(len(tasks) - 1, -1, -1), labels)
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
    title = "開了搜尋工具之後，agent 改用什麼" if by_condition else "每個任務用了哪些工具"
    fig.text(0.015, 1 - 0.1 / h, title, ha="left", va="top", fontsize=14, color=INK, fontweight="bold")
    subtitle = (
        f"同一個任務、兩種工具設定（預設為 read/bash/edit/write），每格取 n={min(counts.values())} 次執行的平均"
        if by_condition
        else f"{CONDITION_LABELS.get(condition, condition)}，每格取 n={min(counts.values())} 次執行的平均；"
        f"Pi 預設只開 read／bash／edit／write"
    )
    fig.text(0.015, 1 - 0.43 / h, subtitle, ha="left", va="top", fontsize=9.5, color=INK_2)
    handles = [
        Line2D([], [], marker="s", linestyle="", markersize=px(10), markerfacecolor=SERIES[i % len(SERIES)],
               markeredgewidth=0, label=name)
        for i, name in enumerate(tools)
    ]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.008, 1 - 0.64 / h), ncol=len(handles),
               frameon=False, labelcolor=INK_2, handletextpad=0.4, columnspacing=1.6, fontsize=9.5)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
