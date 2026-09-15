"""Turn experiments/results/<exp>/runs.jsonl into tables and figures.

  python -m analysis.summarize <experiment_id>
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

from bench.runner.cli import is_infra_failure  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "experiments" / "results"
FIGURES = REPO / "experiments" / "figures"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
# Documented categorical order (blue, orange, aqua, yellow, magenta, green, violet, red).
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]

DPI = 200
DISPLAY_SCALE = 2  # PNGs are shown at ~half size in articles; 1 CSS px = 2 image px

TASK_LABELS = {
    "t1_fix_pagination": "T1 修分頁 bug",
    "t2_add_endpoint": "T2 新增 endpoint",
    "t3_fix_check": "T3 修 CI 檢查",
    "t4_split_constant": "T4 拆常數",
    "t5_migration": "T5 資料遷移",
}
CONDITION_LABELS = {
    "agents_md_on": "有 AGENTS.md",
    "agents_md_off": "無 AGENTS.md",
    "skill_off": "無 Skill",
    "skill_on": "有 Skill",
    "appended_prompt": "規則灌進 system prompt",
    "default_tools": "預設四個工具",
    "search_tools": "加上 grep/find/ls",
    "thinking_off": "thinking off",
    "thinking_low": "thinking low",
    "thinking_high": "thinking high",
}


def px(n: float) -> float:
    """CSS px -> points at the article's display scale."""
    return n * DISPLAY_SCALE * 72 / DPI


def setup_style() -> None:
    preferred = ["Microsoft JhengHei", "Noto Sans CJK TC", "Noto Sans TC", "PingFang TC"]
    available = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": [name for name in preferred if name in available] + ["DejaVu Sans"],
        "axes.unicode_minus": False,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "axes.edgecolor": AXIS,
        "axes.labelcolor": INK_2,
        "xtick.color": MUTED,
        "ytick.color": INK_2,
        "font.size": 10,
    })


def load_runs(exp: str) -> tuple[list[dict], dict]:
    out = RESULTS / exp
    runs = [json.loads(line) for line in (out / "runs.jsonl").read_text(encoding="utf-8").splitlines() if line]
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    return runs, manifest


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def summarize(runs: list[dict], manifest: dict, dropped: list[dict] | None = None) -> list[dict]:
    task_order = manifest["config"]["tasks"]
    condition_order = [c["name"] for c in manifest["config"]["conditions"]]
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for run in runs:
        groups[(run["task"], run["condition"])].append(run)
    rows = []
    for task in task_order:
        for condition in condition_order:
            everything = groups.get((task, condition), [])
            infra_pending = [r for r in everything if is_infra_failure(r)]
            group = [r for r in everything if not is_infra_failure(r)]
            if not group:
                continue
            metrics = [r["metrics"] or {} for r in group]
            wins = sum(1 for r in group if r["success"])
            low, high = wilson(wins, len(group))
            failure_steps = Counter(
                step for r in group if not r["success"] for step in (r["check_failed_steps"] or ["hidden_tests"])
            )
            rows.append({
                "task": task,
                "condition": condition,
                "n": len(group),
                "successes": wins,
                "success_rate": round(wins / len(group), 3),
                "ci95_low": round(low, 3),
                "ci95_high": round(high, 3),
                "cost_median_usd": _median([m.get("cost_usd", 0) for m in metrics]),
                "cost_min_usd": min(m.get("cost_usd", 0) for m in metrics),
                "cost_max_usd": max(m.get("cost_usd", 0) for m in metrics),
                "tokens_median": _median([m.get("total_tokens", 0) for m in metrics]),
                "tool_calls_median": _median([m.get("tool_calls", 0) for m in metrics]),
                "assistant_turns_median": _median([m.get("assistant_messages", 0) for m in metrics]),
                "wall_seconds_median": _median([r["wall_seconds"] for r in group]),
                "ran_check_script": sum(1 for m in metrics if m.get("ran_check_script")),
                "read_docs_runs": sum(1 for m in metrics if m.get("read_docs")),
                "skill_file_read": sum(1 for m in metrics if m.get("skill_file_read")),
                "bash_search_runs": sum(1 for m in metrics if m.get("bash_search_commands")),
                "grep_tool_runs": sum(
                    1 for m in metrics if set(m.get("tool_calls_by_name", {})) & {"grep", "find", "ls"}
                ),
                "tool_errors_total": sum(m.get("tool_errors", 0) for m in metrics),
                "transport_failures_total": sum(m.get("transport_failures", 0) for m in metrics),
                "tampered_runs": sum(1 for r in group if r["tampered_protected_files"]),
                "timeouts": sum(1 for r in group if r["timed_out"]),
                "infra_retried": sum(1 for d in dropped or [] if d["task"] == task and d["condition"] == condition),
                "infra_pending": len(infra_pending),
                "failure_steps": dict(failure_steps),
            })
    return rows


def write_tables(exp: str, rows: list[dict]) -> None:
    out = RESULTS / exp
    fields = [k for k in rows[0] if k != "failure_steps"] + ["failure_steps"]
    with (out / "summary.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "failure_steps": json.dumps(row["failure_steps"], ensure_ascii=False)})
    lines = [
        "| 任務 | 條件 | 成功 | 成功率（95% CI） | 成本中位數 | tokens 中位數 | 工具呼叫中位數 | 耗時中位數 | 跑了 check.py | 失敗在哪一關 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        steps = "、".join(f"{k}×{v}" for k, v in r["failure_steps"].items()) or "—"
        lines.append(
            f"| {TASK_LABELS.get(r['task'], r['task'])} | {CONDITION_LABELS.get(r['condition'], r['condition'])} "
            f"| {r['successes']}/{r['n']} | {r['success_rate']:.0%}（{r['ci95_low']:.0%}–{r['ci95_high']:.0%}） "
            f"| ${r['cost_median_usd']:.4f} | {r['tokens_median']:,.0f} | {r['tool_calls_median']:.0f} "
            f"| {r['wall_seconds_median']:.0f}s | {r['ran_check_script']}/{r['n']} | {steps} |"
        )
    retried = [r for r in rows if r["infra_retried"]]
    if retried:
        detail = "、".join(
            f"{TASK_LABELS.get(r['task'], r['task'])}／{CONDITION_LABELS.get(r['condition'], r['condition'])}"
            f"×{r['infra_retried']}"
            for r in retried
        )
        total = sum(r["infra_retried"] for r in retried)
        lines += ["", f"另有 {total} 次執行因 harness 或網路卡住（連續無輸出）被判定為基礎設施失敗並重跑，不計入成功率：{detail}。"]
    pending = [r for r in rows if r["infra_pending"]]
    if pending:
        detail = "、".join(
            f"{TASK_LABELS.get(r['task'], r['task'])}／{CONDITION_LABELS.get(r['condition'], r['condition'])}"
            f"×{r['infra_pending']}"
            for r in pending
        )
        total = sum(r["infra_pending"] for r in pending)
        lines += ["", f"另有 {total} 次執行是基礎設施失敗（harness 卡住或 provider 錯誤），尚未重跑，不計入上表：{detail}。"]
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


HEADER_IN = 1.05
FOOTER_IN = 0.6


def _new_figure(n_tasks: int, n_conditions: int, right: float):
    plot_h = 0.42 * n_tasks * max(2, n_conditions) + 0.3
    height = HEADER_IN + plot_h + FOOTER_IN
    fig, ax = plt.subplots(figsize=(7.2, height), dpi=DPI)
    fig.subplots_adjust(left=0.2, right=right, top=1 - HEADER_IN / height, bottom=FOOTER_IN / height)
    return fig, ax


def _legend(fig, conditions: list[str], extra: list[Line2D] | None = None) -> None:
    handles = [
        Line2D([], [], marker="s", linestyle="", markersize=px(10), markerfacecolor=SERIES[i], markeredgewidth=0,
               label=CONDITION_LABELS.get(c, c))
        for i, c in enumerate(conditions)
    ] + (extra or [])
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.008, 1 - 0.64 / fig.get_figheight()),
               ncol=len(handles), frameon=False, labelcolor=INK_2, handletextpad=0.4, columnspacing=1.6, fontsize=9.5)


def _titles(fig, title: str, subtitle: str) -> None:
    h = fig.get_figheight()
    fig.text(0.015, 1 - 0.1 / h, title, ha="left", va="top", fontsize=14, color=INK, fontweight="bold")
    fig.text(0.015, 1 - 0.43 / h, subtitle, ha="left", va="top", fontsize=9.5, color=INK_2)


def _style_axes(ax, grid_axis: str) -> None:
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.spines["bottom"].set_linewidth(px(1))
    ax.grid(axis=grid_axis, color=GRID, linewidth=px(1), linestyle="-")
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=0, labelsize=9)


def _layout(tasks, conditions):
    band = 1.0
    offsets = [(i - (len(conditions) - 1) / 2) * 0.34 for i in range(len(conditions))]
    ys = {task: (len(tasks) - 1 - i) * band for i, task in enumerate(tasks)}
    return ys, offsets


def success_figure(exp: str, rows: list[dict], manifest: dict) -> Path:
    tasks = [t for t in manifest["config"]["tasks"] if any(r["task"] == t for r in rows)]
    conditions = [c["name"] for c in manifest["config"]["conditions"]]
    ys, offsets = _layout(tasks, conditions)
    fig, ax = _new_figure(len(tasks), len(conditions), right=0.9)
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.6, len(tasks) - 0.4)
    fig.canvas.draw()
    bbox = ax.get_window_extent()
    ux, uy = 1 / bbox.width, (len(tasks) + 0.2) / bbox.height
    bar_h = min(0.28, 24 * DISPLAY_SCALE * uy)
    radius = 4 * DISPLAY_SCALE * ux
    for row in rows:
        ci = conditions.index(row["condition"])
        y = ys[row["task"]] + offsets[ci]
        width = row["success_rate"]
        color = SERIES[ci]
        if width > 0:
            r = min(radius, width / 2)
            ax.add_patch(FancyBboxPatch((0, y - bar_h / 2), width, bar_h, boxstyle=f"round,pad=0,rounding_size={r}",
                                        mutation_aspect=uy / ux, linewidth=0, facecolor=color))
            ax.add_patch(Rectangle((0, y - bar_h / 2), min(r, width), bar_h, linewidth=0, facecolor=color))
        ax.text(width + 0.012, y, f"{row['successes']}/{row['n']}", va="center", ha="left", fontsize=9, color=INK_2)
    ax.set_yticks([ys[t] for t in tasks], [TASK_LABELS.get(t, t) for t in tasks])
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1], ["0%", "25%", "50%", "75%", "100%"])
    _style_axes(ax, "x")
    n = rows[0]["n"]
    _titles(fig, "任務成功率", f"每格 n={n}，{manifest['model']}，Pi {manifest['harness_version']}；成功＝check.py 與隱藏測試全過")
    _legend(fig, conditions)
    path = FIGURES / f"{exp}_success.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def dot_figure(exp: str, runs: list[dict], manifest: dict, metric: str, title: str, unit: str, fmt) -> Path:
    tasks = [t for t in manifest["config"]["tasks"] if any(r["task"] == t for r in runs)]
    conditions = [c["name"] for c in manifest["config"]["conditions"]]
    ys, offsets = _layout(tasks, conditions)
    fig, ax = _new_figure(len(tasks), len(conditions), right=0.96)
    values_all = []
    for ci, condition in enumerate(conditions):
        for task in tasks:
            group = [
                r for r in runs
                if r["task"] == task and r["condition"] == condition and r["metrics"] and not is_infra_failure(r)
            ]
            values = [r["metrics"][metric] for r in group]
            if not values:
                continue
            values_all += values
            y = ys[task] + offsets[ci]
            jitter = [((i % 3) - 1) * 0.05 for i in range(len(values))]
            ok = [r["success"] for r in group]
            ax.scatter([v for v, s in zip(values, ok, strict=True) if s],
                       [y + j for j, s in zip(jitter, ok, strict=True) if s],
                       s=px(9) ** 2, color=SERIES[ci], edgecolors=SURFACE, linewidths=px(2), zorder=3)
            ax.scatter([v for v, s in zip(values, ok, strict=True) if not s],
                       [y + j for j, s in zip(jitter, ok, strict=True) if not s],
                       s=px(9) ** 2, facecolors=SURFACE, edgecolors=SERIES[ci], linewidths=px(2), zorder=3)
            med = statistics.median(values)
            ax.plot([med, med], [y - 0.13, y + 0.13], color=INK_2, linewidth=px(2), solid_capstyle="round", zorder=4)
    ax.set_ylim(-0.6, len(tasks) - 0.4)
    ax.set_xlim(0, max(values_all) * 1.08 if values_all else 1)
    ax.set_yticks([ys[t] for t in tasks], [TASK_LABELS.get(t, t) for t in tasks])
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: fmt(v)))
    _style_axes(ax, "x")
    ax.set_xlabel(unit, fontsize=9, color=MUTED)
    n = max(sum(1 for r in runs if r["task"] == t and r["condition"] == c) for t in tasks for c in conditions)
    _titles(fig, title, f"每個點是一次執行（每格 n={n}）；短直線是中位數；空心點代表該次失敗")
    extra = [
        Line2D([], [], marker="o", linestyle="", markersize=px(9), markerfacecolor=SURFACE,
               markeredgecolor=MUTED, markeredgewidth=px(2), label="失敗"),
        Line2D([0, 1], [0, 0], color=INK_2, linewidth=px(2), label="中位數"),
    ]
    _legend(fig, conditions, extra)
    path = FIGURES / f"{exp}_{metric}.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment")
    args = parser.parse_args(argv)
    setup_style()
    FIGURES.mkdir(parents=True, exist_ok=True)
    runs, manifest = load_runs(args.experiment)
    dropped_path = RESULTS / args.experiment / "runs.infra_dropped.jsonl"
    dropped = []
    if dropped_path.exists():
        dropped = [json.loads(line) for line in dropped_path.read_text(encoding="utf-8").splitlines() if line]
    rows = summarize(runs, manifest, dropped)
    write_tables(args.experiment, rows)
    paths = [
        success_figure(args.experiment, rows, manifest),
        dot_figure(args.experiment, runs, manifest, "cost_usd", "每次執行的成本", "美元／次", lambda v: f"${v:.4f}"),
        dot_figure(args.experiment, runs, manifest, "total_tokens", "每次執行用掉的 tokens", "tokens／次",
                   lambda v: f"{v / 1000:.0f}K"),
        dot_figure(args.experiment, runs, manifest, "tool_calls", "每次執行的工具呼叫次數", "次", lambda v: f"{v:.0f}"),
    ]
    print((RESULTS / args.experiment / "summary.md").read_text(encoding="utf-8"))
    for path in paths:
        print(path.relative_to(REPO).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
