"""Draw the runner pipeline used in the Day 7 article.

  python -m analysis.pipeline_diagram experiments/figures/runner_pipeline.png
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

STEPS = [
    ("1 準備工作目錄", "複製受測專案\n套用任務 setup 與實驗條件"),
    ("2 建立 baseline", "git init + commit\n另存一份乾淨副本"),
    ("3 交給 harness 執行", "Pi adapter：\npi -p --mode json"),
    ("4 收集改動", "git diff\n記錄改了哪些檔案"),
    ("5 還原受保護檔案", "check.py、tests/…\n被改過就記錄並還原"),
    ("6 驗收", "scripts/check.py\n＋ 隱藏測試"),
    ("7 解析 session", "tokens、成本、工具呼叫\n讀了哪些檔、跑了哪些指令"),
    ("8 寫入 runs.jsonl", "一次執行一行\n去識別化後公開"),
]


def main(argv: list[str]) -> int:
    out = Path(argv[0]) if argv else Path("experiments/figures/runner_pipeline.png")
    setup_style()
    cols, rows = 4, 2
    fig = plt.figure(figsize=(8.4, 4.3), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 52)
    ax.axis("off")
    box_w, box_h = 20.5, 13.5
    xs = [4 + c * 24 for c in range(cols)]
    ys = [26.5, 5.5]
    centers = []
    for i, (title, body) in enumerate(STEPS):
        row, col = divmod(i, cols)
        if row == 1:
            col = cols - 1 - col
        x, y = xs[col], ys[row]
        harness_specific = i == 2
        ax.add_patch(FancyBboxPatch((x, y), box_w, box_h, boxstyle="round,pad=0,rounding_size=1.2",
                                    linewidth=px(2) if harness_specific else 0,
                                    edgecolor=SERIES[0], facecolor=ACCENT_WASH if harness_specific else NEUTRAL_FILL))
        ax.text(x + 1.4, y + box_h - 2.2, title, ha="left", va="top", fontsize=10, color=INK, fontweight="bold")
        ax.text(x + 1.4, y + box_h - 6.3, body, ha="left", va="top", fontsize=8.3, color=INK_2, linespacing=1.45)
        centers.append((x, y))

    def arrow(p, q):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=px(14), color=MUTED, linewidth=px(1.5),
                                     shrinkA=0, shrinkB=0))

    for i in range(len(STEPS) - 1):
        (x0, y0), (x1, y1) = centers[i], centers[i + 1]
        if y0 == y1 and x1 > x0:
            arrow((x0 + box_w + 0.4, y0 + box_h / 2), (x1 - 0.4, y1 + box_h / 2))
        elif y0 == y1:
            arrow((x0 - 0.4, y0 + box_h / 2), (x1 + box_w + 0.4, y1 + box_h / 2))
        else:
            arrow((x0 + box_w / 2, y0 - 0.4), (x1 + box_w / 2, y1 + box_h + 0.4))

    ax.text(4, 49.5, "量測台的一次執行", ha="left", va="top", fontsize=14, color=INK, fontweight="bold")
    ax.text(4, 45.2, "只有藍框那一步跟 harness 有關；換成 Claude Code 或 Codex 只要換掉 adapter，其餘七步完全不變",
            ha="left", va="top", fontsize=9.5, color=INK_2)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
