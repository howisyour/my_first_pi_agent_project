"""Split each turn of one session into "waiting for the model" and "running tools" (Day 18).

  python -m analysis.turn_time <session.jsonl> <out.png>

Both numbers are inferred from message timestamps, which is exactly the limitation the
article is about: a tool's start is never recorded, so parallel calls cannot be separated.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
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
    SERIES,
    SURFACE,
    px,
    setup_style,
)


def _ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_turns(path: Path) -> list[dict]:
    entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    turns: list[dict] = []
    previous = None
    for entry in entries:
        if entry.get("type") != "message":
            continue
        message = entry["message"]
        stamp = _ts(entry["timestamp"])
        if previous is None:
            previous = stamp
            continue
        gap = (stamp - previous).total_seconds()
        if message["role"] == "assistant":
            calls = [b for b in message.get("content") or [] if b.get("type") == "toolCall"]
            turns.append({"wait": gap, "tools": 0.0, "calls": len(calls)})
        elif message["role"] == "toolResult" and turns:
            turns[-1]["tools"] += gap
        previous = stamp
    return turns


def main(argv: list[str]) -> int:
    session, out = Path(argv[0]), Path(argv[1])
    setup_style()
    turns = load_turns(session)
    total_wait = sum(t["wait"] for t in turns)
    total_tools = sum(t["tools"] for t in turns)

    header_in, footer_in = 1.05, 0.6
    height = header_in + 0.42 * len(turns) + 0.4 + footer_in
    fig, ax = plt.subplots(figsize=(7.2, height), dpi=DPI)
    fig.subplots_adjust(left=0.16, right=0.95, top=1 - header_in / height, bottom=footer_in / height)
    longest = max(t["wait"] + t["tools"] for t in turns)
    ax.set_xlim(0, longest * 1.16)
    ax.set_ylim(-0.6, len(turns) - 0.4)
    fig.canvas.draw()
    bbox = ax.get_window_extent()
    ux = (longest * 1.16) / bbox.width
    uy = (len(turns) + 0.2) / bbox.height
    bar_h = min(0.3, 24 * DISPLAY_SCALE * uy)
    gap = 2 * DISPLAY_SCALE * ux
    radius = 4 * DISPLAY_SCALE * ux

    for index, turn in enumerate(turns):
        y = len(turns) - 1 - index
        segments = [(turn["wait"], SERIES[0]), (turn["tools"], SERIES[1])]
        segments = [(value, color) for value, color in segments if value > 0]
        x = 0.0
        for position, (value, color) in enumerate(segments):
            last = position == len(segments) - 1
            width = value - (0 if last else gap)
            if width <= 0:
                x += value
                continue
            if last:
                r = min(radius, width / 2)
                ax.add_patch(FancyBboxPatch((x, y - bar_h / 2), width, bar_h,
                                            boxstyle=f"round,pad=0,rounding_size={r}", mutation_aspect=uy / ux,
                                            linewidth=0, facecolor=color))
                ax.add_patch(Rectangle((x, y - bar_h / 2), min(r, width), bar_h, linewidth=0, facecolor=color))
            else:
                ax.add_patch(Rectangle((x, y - bar_h / 2), width, bar_h, linewidth=0, facecolor=color))
            x += value
        note = f"{turn['wait'] + turn['tools']:.1f}s"
        if turn["calls"] > 1:
            note += f"（{turn['calls']} 個工具同時跑）"
        ax.text(x + longest * 0.015, y, note, va="center", ha="left", fontsize=8.5, color=INK_2)

    ax.set_yticks(range(len(turns) - 1, -1, -1), [f"第 {i + 1} 輪" for i in range(len(turns))])
    ax.set_xlabel("秒", fontsize=9, color=MUTED)
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
    fig.text(0.015, 1 - 0.1 / h, "一次執行的時間都花在哪？", ha="left", va="top", fontsize=14, color=INK,
             fontweight="bold")
    fig.text(0.015, 1 - 0.43 / h,
             f"總共 {total_wait + total_tools:.0f} 秒：等模型 {total_wait:.0f} 秒、跑工具 {total_tools:.1f} 秒；"
             f"時間由訊息時間戳推算，工具的開始時間沒有被記錄",
             ha="left", va="top", fontsize=9.5, color=INK_2)
    handles = [
        Line2D([], [], marker="s", linestyle="", markersize=px(10), markerfacecolor=SERIES[0], markeredgewidth=0,
               label="等模型回應"),
        Line2D([], [], marker="s", linestyle="", markersize=px(10), markerfacecolor=SERIES[1], markeredgewidth=0,
               label="跑工具"),
    ]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.008, 1 - 0.64 / h), ncol=2, frameon=False,
               labelcolor=INK_2, handletextpad=0.4, columnspacing=1.6, fontsize=9.5)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    print(f"{len(turns)} turns, wait {total_wait:.1f}s, tools {total_tools:.1f}s -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
