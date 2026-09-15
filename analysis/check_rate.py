"""Behaviour chart: how often the agent ran the project's own quality gate (Day 9).

  python -m analysis.check_rate <experiment> <out.png>
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
    CONDITION_LABELS,
    DISPLAY_SCALE,
    DPI,
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


def main(argv: list[str]) -> int:
    experiment, out = argv[0], Path(argv[1])
    setup_style()
    runs = [
        json.loads(line)
        for line in (RESULTS / experiment / "runs.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    manifest = json.loads((RESULTS / experiment / "manifest.json").read_text(encoding="utf-8"))
    tasks = manifest["config"]["tasks"]
    conditions = [c["name"] for c in manifest["config"]["conditions"]]
    ran: dict[tuple[str, str], list[bool]] = defaultdict(list)
    for run in runs:
        if run["metrics"] and not is_infra_failure(run):
            ran[(run["task"], run["condition"])].append(bool(run["metrics"]["ran_check_script"]))

    header_in, footer_in = 1.05, 0.6
    height = header_in + 0.62 * len(tasks) + 0.3 + footer_in
    fig, ax = plt.subplots(figsize=(7.2, height), dpi=DPI)
    fig.subplots_adjust(left=0.22, right=0.9, top=1 - header_in / height, bottom=footer_in / height)
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.6, len(tasks) - 0.4)
    fig.canvas.draw()
    bbox = ax.get_window_extent()
    ux, uy = 1 / bbox.width, (len(tasks) + 0.2) / bbox.height
    bar_h = min(0.28, 24 * DISPLAY_SCALE * uy)
    radius = 4 * DISPLAY_SCALE * ux
    offsets = [(i - (len(conditions) - 1) / 2) * 0.34 for i in range(len(conditions))]

    for row, task in enumerate(tasks):
        y_base = len(tasks) - 1 - row
        for ci, condition in enumerate(conditions):
            values = ran.get((task, condition), [])
            if not values:
                continue
            rate = sum(values) / len(values)
            y = y_base + offsets[ci]
            if rate > 0:
                r = min(radius, rate / 2)
                ax.add_patch(FancyBboxPatch((0, y - bar_h / 2), rate, bar_h,
                                            boxstyle=f"round,pad=0,rounding_size={r}", mutation_aspect=uy / ux,
                                            linewidth=0, facecolor=SERIES[ci]))
                ax.add_patch(Rectangle((0, y - bar_h / 2), min(r, rate), bar_h, linewidth=0, facecolor=SERIES[ci]))
            ax.text(rate + 0.012, y, f"{sum(values)}/{len(values)}", va="center", ha="left", fontsize=9, color=INK_2)

    ax.set_yticks(range(len(tasks) - 1, -1, -1), [TASK_LABELS.get(t, t) for t in tasks])
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1], ["0%", "25%", "50%", "75%", "100%"])
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
    fig.text(0.015, 1 - 0.1 / h, "完成前有沒有跑 scripts/check.py", ha="left", va="top", fontsize=14, color=INK,
             fontweight="bold")
    fig.text(0.015, 1 - 0.43 / h, "專案規定的驗收指令；每格 n=5。成功率兩組都是 100%，差別在做事的方法",
             ha="left", va="top", fontsize=9.5, color=INK_2)
    handles = [
        Line2D([], [], marker="s", linestyle="", markersize=px(10), markerfacecolor=SERIES[i], markeredgewidth=0,
               label=CONDITION_LABELS.get(c, c))
        for i, c in enumerate(conditions)
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
