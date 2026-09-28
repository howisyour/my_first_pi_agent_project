"""Draw a span waterfall from a trace captured by lab/trace/pi-trace.mjs (Day 20).

  python -m analysis.trace_waterfall <trace.json> <out.png>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from analysis.summarize import (  # noqa: E402
    AXIS,
    DISPLAY_SCALE,
    DPI,
    GRID,
    INK,
    INK_2,
    MUTED,
    SERIES,
    SURFACE,
    px,
    setup_style,
)

COLORS = {
    "pi.harness.run": SERIES[2],
    "pi.harness.turn": SERIES[3],
    "pi.ai.request": SERIES[0],
    "pi.harness.tool": SERIES[1],
}


def depth_of(span: dict, by_id: dict) -> int:
    depth, parent = 0, span["parentSpanId"]
    while parent and parent in by_id:
        depth += 1
        parent = by_id[parent]["parentSpanId"]
    return depth


def main(argv: list[str]) -> int:
    trace_path, out = Path(argv[0]), Path(argv[1])
    setup_style()
    spans = json.loads(trace_path.read_text(encoding="utf-8"))["spans"]
    by_id = {span["spanId"]: span for span in spans}
    spans.sort(key=lambda span: (span["startMs"], depth_of(span, by_id)))
    total = max(span["startMs"] + span["durationMs"] for span in spans) / 1000

    header_in, footer_in = 1.05, 0.62
    height = header_in + 0.3 * len(spans) + 0.3 + footer_in
    fig, ax = plt.subplots(figsize=(7.6, height), dpi=DPI)
    fig.subplots_adjust(left=0.29, right=0.97, top=1 - header_in / height, bottom=footer_in / height)
    ax.set_xlim(0, total * 1.34)
    ax.set_ylim(-0.6, len(spans) - 0.4)
    fig.canvas.draw()
    bbox = ax.get_window_extent()
    ux = (total * 1.34) / bbox.width
    uy = (len(spans) + 0.2) / bbox.height
    bar_h = min(0.52, 14 * DISPLAY_SCALE * uy)
    radius = 3 * DISPLAY_SCALE * ux

    labels = []
    for index, span in enumerate(spans):
        y = len(spans) - 1 - index
        start = span["startMs"] / 1000
        width = max(span["durationMs"] / 1000, total * 0.002)
        color = COLORS.get(span["name"], MUTED)
        r = min(radius, width / 2)
        ax.add_patch(FancyBboxPatch((start, y - bar_h / 2), width, bar_h,
                                    boxstyle=f"round,pad=0,rounding_size={r}", mutation_aspect=uy / ux,
                                    linewidth=0, facecolor=color))
        detail = span["attributes"].get("pi.harness.tool.name", "")
        if span["name"] == "pi.ai.request":
            detail = f"{span['attributes'].get('pi.ai.usage.input_tokens', '?')} in / {span['attributes'].get('pi.ai.usage.output_tokens', '?')} out"
        labels.append("  " * depth_of(span, by_id) + span["name"].replace("pi.harness.", "").replace("pi.ai.", "ai."))
        ax.text(start + width + total * 0.008, y, f"{span['durationMs'] / 1000:.1f}s {detail}".strip(),
                va="center", ha="left", fontsize=7.6, color=INK_2)

    ax.set_yticks(range(len(spans) - 1, -1, -1), labels, fontsize=8)
    ax.set_xlabel("秒（從 agent 啟動算起）", fontsize=9, color=MUTED)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.spines["bottom"].set_linewidth(px(1))
    ax.grid(axis="x", color=GRID, linewidth=px(1))
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.tick_params(axis="x", colors=MUTED, labelsize=9)
    ax.tick_params(axis="y", colors=INK_2)

    ai = sum(s["durationMs"] for s in spans if s["name"] == "pi.ai.request") / 1000
    tools = sum(s["durationMs"] for s in spans if s["name"] == "pi.harness.tool") / 1000
    h = fig.get_figheight()
    fig.text(0.015, 1 - 0.1 / h, "一次執行的 span 瀑布圖", ha="left", va="top", fontsize=14, color=INK,
             fontweight="bold")
    fig.text(0.015, 1 - 0.43 / h,
             f"總長 {total:.1f} 秒：模型請求 {ai:.1f} 秒、工具 {tools:.1f} 秒，其餘是 harness 自己的開銷",
             ha="left", va="top", fontsize=9.5, color=INK_2)
    handles = [
        Line2D([], [], marker="s", linestyle="", markersize=px(10), markerfacecolor=COLORS[name],
               markeredgewidth=0, label=name)
        for name in ("pi.harness.run", "pi.harness.turn", "pi.ai.request", "pi.harness.tool")
    ]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.008, 1 - 0.64 / h), ncol=4, frameon=False,
               labelcolor=INK_2, handletextpad=0.4, columnspacing=1.4, fontsize=9)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
