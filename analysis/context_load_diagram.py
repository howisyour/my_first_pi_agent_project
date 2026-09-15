"""Draw how Pi picks context files and where they land in the system prompt (Day 8).

  python -m analysis.context_load_diagram experiments/figures/day08_context_loading.png
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

FILES = [
    ("~/.pi/agent/AGENTS.md", "1", "全域"),
    ("repo/AGENTS.md", "2", ""),
    ("repo/service/AGENTS.md", "3", ""),
    ("repo/service/CLAUDE.md", None, "同目錄已有 AGENTS.md"),
    ("repo/service/api/AGENTS.override.md", "4", "離工作目錄最近，最後出現"),
    ("repo/service/api/AGENTS.md", None, "同目錄有 AGENTS.override.md"),
]

PROMPT = [
    ("Pi 預設 system prompt", "工具清單、Guidelines", False),
    ("--append-system-prompt", "有指定才會出現", False),
    ("<project_context>", "依序放入 1 → 2 → 3 → 4", True),
    ("<available_skills>", "只有名稱與描述", False),
    ("Current working directory", "repo/service/api", False),
]


def main(argv: list[str]) -> int:
    out = Path(argv[0]) if argv else Path("experiments/figures/day08_context_loading.png")
    setup_style()
    fig = plt.figure(figsize=(8.4, 4.9), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 58)
    ax.axis("off")

    ax.text(3, 56, "Pi 怎麼挑 context 檔、放到哪裡", ha="left", va="top", fontsize=14, color=INK, fontweight="bold")
    ax.text(3, 51.8, "工作目錄是 repo/service/api；每個目錄只取一個檔，目錄之間不覆蓋，而是依序疊加",
            ha="left", va="top", fontsize=9.5, color=INK_2)

    ax.text(3, 45.5, "候選檔案", ha="left", va="center", fontsize=10, color=INK_2, fontweight="bold")
    row_y = [41, 35.2, 29.4, 23.6, 17.8, 12]
    for (path, order, note), y in zip(FILES, row_y, strict=True):
        loaded = order is not None
        ax.add_patch(FancyBboxPatch((3, y - 2.4), 49, 4.8, boxstyle="round,pad=0,rounding_size=0.8", linewidth=0,
                                    facecolor=ACCENT_WASH if loaded else NEUTRAL_FILL))
        if loaded:
            ax.scatter([6], [y], s=px(20) ** 2, color=SERIES[0], edgecolors=SURFACE, linewidths=px(2), zorder=3)
            ax.text(6, y, order, ha="center", va="center", fontsize=8.5, color="#ffffff", fontweight="bold", zorder=4)
        else:
            ax.text(6, y, "×", ha="center", va="center", fontsize=12, color=MUTED)
        ax.text(9, y + 0.9, path, ha="left", va="center", fontsize=9, color=INK if loaded else MUTED, family="monospace")
        ax.text(9, y - 1.3, note or "載入", ha="left", va="center", fontsize=7.8, color=INK_2 if loaded else MUTED)

    ax.text(62, 45.5, "最後組成的 system prompt", ha="left", va="center", fontsize=10, color=INK_2, fontweight="bold")
    prompt_y = [40.2, 33.6, 27, 20.4, 13.8]
    for (title, body, highlight), y in zip(PROMPT, prompt_y, strict=True):
        ax.add_patch(FancyBboxPatch((62, y - 2.8), 35, 5.6, boxstyle="round,pad=0,rounding_size=0.8",
                                    linewidth=px(2) if highlight else 0, edgecolor=SERIES[0],
                                    facecolor=ACCENT_WASH if highlight else NEUTRAL_FILL))
        ax.text(64, y + 1, title, ha="left", va="center", fontsize=9, color=INK)
        ax.text(64, y - 1.4, body, ha="left", va="center", fontsize=7.8, color=INK_2)

    ax.add_patch(FancyArrowPatch((53.5, 27), (61.3, 27), arrowstyle="-|>", mutation_scale=px(14), color=MUTED,
                                 linewidth=px(1.5)))
    ax.text(3, 5.5, "由上往下是 system prompt 裡的出現順序；同一個目錄的優先序：AGENTS.override.md > AGENTS.md > CLAUDE.md",
            ha="left", va="center", fontsize=8.3, color=MUTED)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
