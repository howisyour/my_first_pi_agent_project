"""Draw progressive disclosure: what sits in the prompt vs what loads on demand (Day 10).

  python -m analysis.skills_diagram experiments/figures/day10_progressive_disclosure.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

from analysis.summarize import DPI, INK, INK_2, MUTED, SERIES, SURFACE, px, setup_style  # noqa: E402

NEUTRAL_FILL = "#f0efec"
ACCENT_WASH = "#cde2fb"
ORANGE_WASH = "#fbe3d7"


def box(ax, x, y, w, h, fill, edge=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.1", linewidth=px(2) if edge else 0,
                                edgecolor=edge or "none", facecolor=fill))


def main(argv: list[str]) -> int:
    out = Path(argv[0]) if argv else Path("experiments/figures/day10_progressive_disclosure.png")
    setup_style()
    fig = plt.figure(figsize=(8.4, 4.4), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 52)
    ax.axis("off")

    ax.text(3, 50, "Skills：描述常駐，內容隨選", ha="left", va="top", fontsize=14, color=INK, fontweight="bold")
    ax.text(3, 45.6, "AGENTS.md 每一輪都整份重送；skill 只有名稱與描述常駐，完整內容要模型自己去讀",
            ha="left", va="top", fontsize=9.5, color=INK_2)

    box(ax, 3, 20, 40, 18, NEUTRAL_FILL)
    ax.text(5.5, 35.5, "每一輪都送出的 system prompt", ha="left", va="center", fontsize=10, color=INK, fontweight="bold")
    box(ax, 5.5, 28.5, 35, 5, ORANGE_WASH)
    ax.text(7.5, 31, "<project_context> AGENTS.md 全文", ha="left", va="center", fontsize=8.6, color=INK)
    box(ax, 5.5, 22, 35, 5.4, ACCENT_WASH)
    ax.text(7.5, 25.6, "<available_skills>", ha="left", va="center", fontsize=8.6, color=INK)
    ax.text(7.5, 23.3, "只有 name / description / location", ha="left", va="center", fontsize=7.8, color=INK_2)

    box(ax, 57, 26.5, 40, 11.5, ACCENT_WASH, edge=SERIES[0])
    ax.text(59.5, 35.5, "模型判斷任務對得上描述", ha="left", va="center", fontsize=9.5, color=INK, fontweight="bold")
    ax.text(59.5, 31.8, "read(SKILL.md)", ha="left", va="center", fontsize=9, color=INK, family="monospace")
    ax.text(59.5, 29, "完整步驟這時候才進 context", ha="left", va="center", fontsize=8.2, color=INK_2)

    box(ax, 57, 12, 40, 10, NEUTRAL_FILL)
    ax.text(59.5, 19.5, "模型沒讀怎麼辦？", ha="left", va="center", fontsize=9.5, color=INK, fontweight="bold")
    ax.text(59.5, 16.3, "skill 等於不存在——所以 Day11 要同時量", ha="left", va="center", fontsize=8.2, color=INK_2)
    ax.text(59.5, 13.8, "「有沒有效」和「實際載入率」", ha="left", va="center", fontsize=8.2, color=INK_2)

    ax.add_patch(FancyArrowPatch((43.5, 25), (56.3, 31), arrowstyle="-|>", mutation_scale=px(14), color=MUTED,
                                 linewidth=px(1.5), connectionstyle="arc3,rad=0.12"))
    ax.text(43.5, 21.5, "有讀才生效", ha="left", va="center", fontsize=8, color=MUTED)

    ax.text(3, 14, "成本差別", ha="left", va="center", fontsize=10, color=INK, fontweight="bold")
    ax.text(3, 9.5, "AGENTS.md：不管用不用得到，每輪都付\nskill：平常只付描述，用到才付全文",
            ha="left", va="top", fontsize=8.6, color=INK_2, linespacing=1.6)

    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
