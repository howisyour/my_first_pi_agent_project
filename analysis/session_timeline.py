"""Plot how much context each turn of one Pi session re-sends.

  python -m analysis.session_timeline <session.jsonl> <out.png> [--title TEXT]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

from analysis.summarize import AXIS, DISPLAY_SCALE, DPI, GRID, INK, INK_2, MUTED, SERIES, SURFACE, px, setup_style  # noqa: E402

TOOL_SHORT = {"bash": "bash", "read": "read", "edit": "edit", "write": "write", "grep": "grep", "find": "find", "ls": "ls"}


def load_turns(path: Path) -> list[dict]:
    turns = []
    for line in path.read_text(encoding="utf-8").splitlines():
        entry = json.loads(line) if line.strip() else {}
        message = entry.get("message") or {}
        if entry.get("type") != "message" or message.get("role") != "assistant":
            continue
        usage = message.get("usage") or {}
        tools = [b.get("name") for b in message.get("content") or [] if b.get("type") == "toolCall"]
        turns.append({
            "uncached": usage.get("input") or 0,
            "cached": usage.get("cacheRead") or 0,
            "output": usage.get("output") or 0,
            "label": "\n".join(TOOL_SHORT.get(t, t) for t in tools) if tools else "回答",
        })
    return turns


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("session", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--title", default="每一輪送給模型的 context 有多大")
    args = parser.parse_args(argv)
    setup_style()
    turns = load_turns(args.session)
    totals = [t["uncached"] + t["cached"] for t in turns]
    max_label_lines = max(t["label"].count("\n") + 1 for t in turns)

    header_in, footer_in, plot_in = 1.05, 0.35 + 0.17 * max_label_lines, 2.6
    width_in = max(7.2, 0.42 * len(turns) + 1.4)
    height = header_in + plot_in + footer_in
    fig, ax = plt.subplots(figsize=(width_in, height), dpi=DPI)
    fig.subplots_adjust(left=0.1, right=0.97, top=1 - header_in / height, bottom=footer_in / height)
    top = max(totals) * 1.15
    ax.set_xlim(0.4, len(turns) + 0.6)
    ax.set_ylim(0, top)
    fig.canvas.draw()
    bbox = ax.get_window_extent()
    ux = (len(turns) + 0.2) / bbox.width
    uy = top / bbox.height
    bar_w = min(0.62, 24 * DISPLAY_SCALE * ux)
    gap = 2 * DISPLAY_SCALE * uy
    aspect = uy / ux
    radius_x = 4 * DISPLAY_SCALE * ux

    for i, turn in enumerate(turns, start=1):
        x0 = i - bar_w / 2
        lower, upper = turn["cached"], turn["uncached"]
        if lower:
            ax.add_patch(Rectangle((x0, 0), bar_w, lower, linewidth=0, facecolor=SERIES[1]))
        base = lower + (gap if lower else 0)
        height_upper = max(upper - (gap if lower else 0), 0)
        if height_upper > 0:
            r = min(radius_x, bar_w / 2, height_upper / (2 * aspect))
            ax.add_patch(FancyBboxPatch((x0, base), bar_w, height_upper, boxstyle=f"round,pad=0,rounding_size={r}",
                                        mutation_aspect=aspect, linewidth=0, facecolor=SERIES[0]))
            ax.add_patch(Rectangle((x0, base), bar_w, min(r * aspect, height_upper), linewidth=0, facecolor=SERIES[0]))

    for i in {0, len(turns) - 1, totals.index(max(totals))}:
        ax.text(i + 1, totals[i] + top * 0.02, f"{totals[i]:,}", ha="center", va="bottom", fontsize=8.5, color=INK_2)

    ax.set_xticks(range(1, len(turns) + 1), [t["label"] for t in turns], fontsize=8)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.spines["bottom"].set_linewidth(px(1))
    ax.grid(axis="y", color=GRID, linewidth=px(1))
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.tick_params(axis="x", colors=INK_2)
    ax.tick_params(axis="y", colors=MUTED, labelsize=8.5)

    h = fig.get_figheight()
    fig.text(0.015, 1 - 0.1 / h, args.title, ha="left", va="top", fontsize=14, color=INK, fontweight="bold")
    fig.text(0.015, 1 - 0.43 / h,
             f"一個真實 session 的 {len(turns)} 輪模型呼叫；每根柱子是該輪送出的 input tokens，下方是這一輪決定呼叫的工具",
             ha="left", va="top", fontsize=9.5, color=INK_2)
    handles = [
        Line2D([], [], marker="s", linestyle="", markersize=px(10), markerfacecolor=SERIES[0], markeredgewidth=0,
               label="未命中快取"),
        Line2D([], [], marker="s", linestyle="", markersize=px(10), markerfacecolor=SERIES[1], markeredgewidth=0,
               label="命中 prompt cache"),
    ]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.008, 1 - 0.64 / h), ncol=2, frameon=False,
               labelcolor=INK_2, handletextpad=0.4, columnspacing=1.6, fontsize=9.5)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out)
    plt.close(fig)
    print(f"{len(turns)} turns, max context {max(totals):,} tokens -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
