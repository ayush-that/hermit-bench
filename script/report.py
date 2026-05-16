#!/usr/bin/env python3
"""HermitBench report generator.

Consumes per-model summary JSON dumps written by
``src/utils/grading.py::print_global_summary`` (and the per-category
``print_summary``) and emits:

* matplotlib PNG charts under ``docs/reports/``
* a markdown leaderboard (``docs/reports/leaderboard.md``)
* a README-ready block (``docs/reports/README_BLOCK.md``) the parent agent
  can paste between ``<!-- BENCH:START -->`` / ``<!-- BENCH:END -->``
  markers in the repo README.

If no global ``summary_all_*.json`` files exist, the script union-s
per-category ``summary_<model>.json`` files into synthetic global
summaries so even a partial sweep can render charts.

CLI:
    python3 script/report.py [--output-dir output] [--reports-dir docs/reports]
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


# Canonical category list (matches ``output/<NN>_<Name>/`` directories).
# Order is the canonical ordering used across heatmaps and grouped bars.
CATEGORIES = [
    "01_CLI_Fluency",
    "02_Tool_Composition",
    "03_Access_Control",
    "04_Channel_Routing",
    "05_Memory_Introspection",
    "06_Scheduling_Automation",
    "07_Amiko_Social",
    "08_Amiko_Pipelines",
]

# Short display labels for compact axes/legends.
CATEGORY_SHORT = {
    "01_CLI_Fluency": "01 CLI",
    "02_Tool_Composition": "02 Tools",
    "03_Access_Control": "03 Access",
    "04_Channel_Routing": "04 Channel",
    "05_Memory_Introspection": "05 Memory",
    "06_Scheduling_Automation": "06 Sched",
    "07_Amiko_Social": "07 Social",
    "08_Amiko_Pipelines": "08 Pipes",
}

# Map the two-digit task_id prefix (``01_task_...``) to the full
# category directory name. Lets us classify global results that don't
# already carry a ``category`` field.
PREFIX_TO_CATEGORY = {c.split("_", 1)[0]: c for c in CATEGORIES}

TOTAL_TASK_COUNT = 79


def _safe_overall(scores: Any) -> float:
    """Return overall_score as float, falling back to 0.0 on errors.

    Per spec: missing dict, ``{"error": ...}``, ``None``, or non-numeric
    values count as 0.0 (with a note rendered in the table footer).
    """
    if not isinstance(scores, dict):
        return 0.0
    val = scores.get("overall_score")
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return float(val)
    return 0.0


def _is_error_row(row: dict) -> bool:
    if row.get("error"):
        return True
    scores = row.get("scores")
    if not isinstance(scores, dict):
        return True
    if "error" in scores and not any(
        isinstance(v, (int, float)) for k, v in scores.items() if k != "error"
    ):
        return True
    return False


def _classify_category(row: dict) -> str | None:
    """Return canonical category for a result row, or None if unknown."""
    cat = row.get("category")
    if isinstance(cat, str) and cat in CATEGORIES:
        return cat
    task_id = row.get("task_id", "")
    if not isinstance(task_id, str):
        return None
    m = re.match(r"^(\d{2})_", task_id)
    if m and m.group(1) in PREFIX_TO_CATEGORY:
        return PREFIX_TO_CATEGORY[m.group(1)]
    return None


def _safe_model_from_filename(path: Path) -> str:
    """Recover the original model id from a ``summary_all_<safe_model>.json`` name.

    The runner substitutes ``/`` with ``_`` when forming the safe name. We
    re-substitute the *first* underscore back to ``/`` so e.g.
    ``openai_gpt-4o-mini`` becomes ``openai/gpt-4o-mini``. If the safe name
    contains no underscore at all, return it unchanged.
    """
    stem = path.stem
    if stem.startswith("summary_all_"):
        safe = stem[len("summary_all_") :]
    elif stem.startswith("summary_"):
        safe = stem[len("summary_") :]
    else:
        safe = stem
    if "_" in safe:
        head, tail = safe.split("_", 1)
        return f"{head}/{tail}"
    return safe


def _model_safe_name(model_id: str) -> str:
    return model_id.replace("/", "_")


def _load_global_summaries(output_dir: Path) -> dict[str, list[dict]]:
    """Return mapping ``model_id -> list[result_row]`` from global dumps."""
    found: dict[str, list[dict]] = {}
    for path in sorted(output_dir.glob("summary_all_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"warn: failed to read {path}: {exc}", file=sys.stderr)
            continue
        results = data.get("results") if isinstance(data, dict) else None
        if not isinstance(results, list):
            print(f"warn: {path} has no 'results' list, skipping", file=sys.stderr)
            continue
        model_id = _safe_model_from_filename(path)
        found[model_id] = results
    return found


def _union_category_summaries(output_dir: Path) -> dict[str, list[dict]]:
    """Fallback: stitch per-category summaries into per-model global lists."""
    per_model: dict[str, list[dict]] = defaultdict(list)
    for category in CATEGORIES:
        cat_dir = output_dir / category
        if not cat_dir.is_dir():
            continue
        for path in sorted(cat_dir.glob("summary_*.json")):
            # Skip nested summary_all_ in case the runner ever drops one here.
            if path.name.startswith("summary_all_"):
                continue
            try:
                rows = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                print(f"warn: failed to read {path}: {exc}", file=sys.stderr)
                continue
            if not isinstance(rows, list):
                continue
            # Recover model id from filename ``summary_<safe_model>.json``.
            model_id = _safe_model_from_filename(path)
            # Tag rows with category so downstream classifier doesn't have
            # to rely solely on task_id prefix parsing.
            for row in rows:
                if isinstance(row, dict) and "category" not in row:
                    row["category"] = category
            per_model[model_id].extend(rows)
    return dict(per_model)


def _aggregate_model(results: list[dict]) -> dict[str, Any]:
    """Compute summary stats for a single model's result list."""
    overall_scores: list[float] = []
    costs: list[float] = []
    times: list[float] = []
    cat_scores: dict[str, list[float]] = defaultdict(list)
    cat_costs: dict[str, list[float]] = defaultdict(list)
    error_count = 0

    for row in results:
        if not isinstance(row, dict):
            continue
        if _is_error_row(row):
            error_count += 1
        score = _safe_overall(row.get("scores"))
        overall_scores.append(score)

        usage = row.get("usage") or {}
        cost = usage.get("cost_usd")
        if isinstance(cost, (int, float)):
            costs.append(float(cost))
        elapsed = usage.get("elapsed_time")
        if isinstance(elapsed, (int, float)):
            times.append(float(elapsed))

        cat = _classify_category(row)
        if cat:
            cat_scores[cat].append(score)
            if isinstance(cost, (int, float)):
                cat_costs[cat].append(float(cost))

    def _mean(xs: list[float]) -> float:
        return sum(xs) / len(xs) if xs else 0.0

    return {
        "task_count": len(results),
        "error_count": error_count,
        "overall_mean": _mean(overall_scores),
        "mean_cost": _mean(costs),
        "total_cost": sum(costs),
        "mean_time": _mean(times),
        "category_scores": {c: _mean(cat_scores.get(c, [])) for c in CATEGORIES},
        "category_costs": {c: _mean(cat_costs.get(c, [])) for c in CATEGORIES},
        "category_task_counts": {c: len(cat_scores.get(c, [])) for c in CATEGORIES},
    }


def _pareto_indices(points: list[tuple[float, float]]) -> set[int]:
    """Return indices on the Pareto frontier (minimize x, maximize y)."""
    frontier: set[int] = set()
    for i, (cx, cy) in enumerate(points):
        dominated = False
        for j, (ox, oy) in enumerate(points):
            if i == j:
                continue
            if ox <= cx and oy >= cy and (ox < cx or oy > cy):
                dominated = True
                break
        if not dominated:
            frontier.add(i)
    return frontier


# ---------- chart rendering ---------------------------------------------------


def _import_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: E402

    return matplotlib, plt


def _cmap_colors(n: int):
    _, plt = _import_matplotlib()
    if n <= 10:
        cmap = plt.get_cmap("tab10")
        return [cmap(i % 10) for i in range(n)]
    cmap = plt.get_cmap("viridis")
    return [cmap(i / max(n - 1, 1)) for i in range(n)]


def render_cost_vs_quality(stats: dict[str, dict], out_path: Path) -> None:
    _, plt = _import_matplotlib()
    models = list(stats.keys())
    xs = [max(stats[m]["mean_cost"], 1e-6) for m in models]
    ys = [stats[m]["overall_mean"] for m in models]
    colors = _cmap_colors(len(models))
    frontier = _pareto_indices(list(zip(xs, ys)))

    fig, ax = plt.subplots(figsize=(9, 6), dpi=144)
    for i, (m, x, y) in enumerate(zip(models, xs, ys)):
        on_front = i in frontier
        ax.scatter(
            x,
            y,
            s=180 if on_front else 90,
            color=colors[i],
            edgecolors="black" if on_front else "none",
            linewidths=2 if on_front else 0,
            zorder=3 if on_front else 2,
            label=f"{m}{' (Pareto)' if on_front else ''}",
        )
        ax.annotate(
            m,
            (x, y),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=8,
        )

    if any(x > 0 for x in xs):
        ax.set_xscale("log")
    ax.set_xlabel("Mean cost per task (USD, log scale)")
    ax.set_ylabel("Overall score (0–1)")
    ax.set_ylim(-0.02, 1.02)
    ax.set_title("Cost vs quality (Pareto frontier highlighted)")
    ax.grid(True, which="both", linestyle="--", alpha=0.3)
    ax.legend(loc="lower right", fontsize=7, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=144)
    plt.close(fig)


def render_leaderboard_bars(stats: dict[str, dict], out_path: Path) -> None:
    _, plt = _import_matplotlib()
    ordered = sorted(stats.items(), key=lambda kv: kv[1]["overall_mean"], reverse=True)
    models = [m for m, _ in ordered]
    scores = [s["overall_mean"] for _, s in ordered]
    costs = [s["mean_cost"] for _, s in ordered]
    colors = _cmap_colors(len(models))

    fig, ax = plt.subplots(figsize=(9, max(3, 0.6 * len(models) + 2)), dpi=144)
    y_positions = list(range(len(models)))
    bars = ax.barh(y_positions, scores, color=colors, label="Overall score")
    ax.set_yticks(y_positions)
    ax.set_yticklabels(models)
    ax.invert_yaxis()
    ax.set_xlabel("Overall score (0–1)")
    ax.set_ylabel("Model")
    ax.set_xlim(0, max(1.0, max(scores) * 1.15 if scores else 1.0))
    ax.set_title("HermitBench leaderboard — overall score (cost shown per bar)")
    ax.grid(True, axis="x", linestyle="--", alpha=0.3)

    for bar, score, cost in zip(bars, scores, costs):
        ax.text(
            bar.get_width() + 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{score * 100:.1f}%  (${cost:.4f}/task)",
            va="center",
            fontsize=8,
        )

    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=144)
    plt.close(fig)


def render_category_heatmap(stats: dict[str, dict], out_path: Path) -> None:
    matplotlib, plt = _import_matplotlib()
    import numpy as np  # type: ignore

    models = list(stats.keys())
    matrix = np.array(
        [[stats[m]["category_scores"][c] for c in CATEGORIES] for m in models],
        dtype=float,
    )

    fig, ax = plt.subplots(
        figsize=(10, max(3, 0.5 * len(models) + 2.5)), dpi=144
    )
    im = ax.imshow(matrix, aspect="auto", cmap="viridis", vmin=0.0, vmax=1.0)
    ax.set_xticks(range(len(CATEGORIES)))
    ax.set_xticklabels([CATEGORY_SHORT[c] for c in CATEGORIES], rotation=30, ha="right")
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(models)
    ax.set_xlabel("Category")
    ax.set_ylabel("Model")
    ax.set_title("Mean score by category (0 = worst, 1 = best)")

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            val = matrix[i, j]
            ax.text(
                j,
                i,
                f"{val:.2f}",
                ha="center",
                va="center",
                fontsize=8,
                color="white" if val < 0.5 else "black",
            )

    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("Mean overall score")
    fig.tight_layout()
    fig.savefig(out_path, dpi=144)
    plt.close(fig)


def render_cost_per_category(stats: dict[str, dict], out_path: Path) -> None:
    matplotlib, plt = _import_matplotlib()
    import numpy as np  # type: ignore

    models = list(stats.keys())
    n_models = len(models)
    n_cats = len(CATEGORIES)
    colors = _cmap_colors(n_models)
    x = np.arange(n_cats)
    width = 0.8 / max(n_models, 1)

    fig, ax = plt.subplots(figsize=(10, 6), dpi=144)
    for i, m in enumerate(models):
        ys = [stats[m]["category_costs"][c] for c in CATEGORIES]
        offset = (i - (n_models - 1) / 2) * width
        ax.bar(x + offset, ys, width=width, color=colors[i], label=m)

    ax.set_xticks(x)
    ax.set_xticklabels([CATEGORY_SHORT[c] for c in CATEGORIES], rotation=30, ha="right")
    ax.set_xlabel("Category")
    ax.set_ylabel("Mean cost per task (USD)")
    ax.set_title("Mean cost per task, by category (07/08 use Opus-judged grading — expect spikes)")
    ax.grid(True, axis="y", linestyle="--", alpha=0.3)
    ax.legend(loc="upper left", fontsize=8, ncol=max(1, n_models // 4))
    fig.tight_layout()
    fig.savefig(out_path, dpi=144)
    plt.close(fig)


# ---------- markdown rendering -----------------------------------------------


def _format_score(score: float, bold: bool) -> str:
    pct = f"{score * 100:.1f}%"
    return f"**{pct}**" if bold else pct


def _format_time(seconds: float) -> str:
    if seconds <= 0:
        return "—"
    if seconds >= 60:
        m = int(seconds // 60)
        s = seconds - m * 60
        return f"{m}m {s:.0f}s"
    return f"{seconds:.1f}s"


def _format_cost(cost: float) -> str:
    if cost <= 0:
        return "$0.0000"
    if cost < 0.01:
        return f"${cost:.4f}"
    return f"${cost:.3f}"


def _leaderboard_rows(stats: dict[str, dict]) -> list[tuple[int, str, dict, bool]]:
    ordered = sorted(
        stats.items(), key=lambda kv: kv[1]["overall_mean"], reverse=True
    )
    rows = []
    for rank, (model, s) in enumerate(ordered, start=1):
        rows.append((rank, model, s, rank == 1))
    return rows


def _render_table(stats: dict[str, dict]) -> str:
    lines = [
        "| Rank | Model | Overall Score | Mean Time | Mean Cost/Task | Total Cost (79 tasks) |",
        "| ---: | :---- | ------------: | --------: | -------------: | --------------------: |",
    ]
    for rank, model, s, is_top in _leaderboard_rows(stats):
        score_cell = _format_score(s["overall_mean"], bold=is_top)
        time_cell = _format_time(s["mean_time"])
        mean_cost_cell = _format_cost(s["mean_cost"])
        # Scale total cost to the 79-task denominator so partial sweeps are
        # comparable to a full run.
        if s["task_count"] > 0:
            projected_total = s["mean_cost"] * TOTAL_TASK_COUNT
        else:
            projected_total = 0.0
        actual_total = _format_cost(s["total_cost"])
        projected_cell = _format_cost(projected_total)
        if s["task_count"] < TOTAL_TASK_COUNT:
            total_cell = f"{actual_total} (proj. {projected_cell})"
        else:
            total_cell = actual_total
        lines.append(
            f"| {rank} | `{model}` | {score_cell} | {time_cell} | {mean_cost_cell} | {total_cell} |"
        )
    return "\n".join(lines)


def _table_footer(stats: dict[str, dict]) -> str:
    notes: list[str] = []
    partial = [
        (m, s["task_count"]) for m, s in stats.items() if s["task_count"] < TOTAL_TASK_COUNT
    ]
    errored = [
        (m, s["error_count"]) for m, s in stats.items() if s["error_count"] > 0
    ]
    if partial:
        bits = ", ".join(f"`{m}` ({n}/{TOTAL_TASK_COUNT})" for m, n in partial)
        notes.append(f"Partial sweep — projected total cost shown for: {bits}.")
    if errored:
        bits = ", ".join(f"`{m}` ({n})" for m, n in errored)
        notes.append(
            f"Tasks with agent/grading errors counted as 0.0 overall_score: {bits}."
        )
    if not notes:
        return ""
    return "\n\n" + "\n".join(f"> {n}" for n in notes)


def render_leaderboard_md(stats: dict[str, dict], reports_dir: Path) -> str:
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    parts = [
        "## Model Leaderboard",
        "",
        f"_Generated: {timestamp}_",
        "",
        _render_table(stats),
        _table_footer(stats),
        "",
        "### Charts",
        "",
        "![Cost vs quality](cost_vs_quality.png)",
        "",
        "![Leaderboard](leaderboard_bars.png)",
        "",
        "![Category heatmap](category_heatmap.png)",
        "",
        "![Cost per category](cost_per_category.png)",
        "",
    ]
    return "\n".join(parts)


def render_readme_block(stats: dict[str, dict], reports_dir_rel: str) -> str:
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    parts = [
        "## Leaderboard",
        "",
        f"_Auto-generated by `script/report.py` on {timestamp}._",
        "",
        _render_table(stats),
        _table_footer(stats),
        "",
        f"![Cost vs quality]({reports_dir_rel}/cost_vs_quality.png)",
        "",
        f"![Leaderboard]({reports_dir_rel}/leaderboard_bars.png)",
        "",
        f"![Category heatmap]({reports_dir_rel}/category_heatmap.png)",
        "",
        f"![Cost per category]({reports_dir_rel}/cost_per_category.png)",
        "",
    ]
    return "\n".join(parts)


# ---------- driver ------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="output", help="Where summary JSONs live")
    parser.add_argument(
        "--reports-dir",
        default="docs/reports",
        help="Where to write PNGs and markdown",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Optional repo root to compute relative paths from (defaults to CWD)",
    )
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir).resolve()
    reports_dir = Path(args.reports_dir).resolve()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path.cwd().resolve()

    if not output_dir.is_dir():
        print(
            f"no summaries to chart: output directory {output_dir} does not exist",
            file=sys.stderr,
        )
        return 0

    summaries = _load_global_summaries(output_dir)
    if not summaries:
        unioned = _union_category_summaries(output_dir)
        if unioned:
            print(
                f"info: no summary_all_*.json found; union-ed {len(unioned)} model(s) "
                f"from per-category summaries.",
            )
            summaries = unioned

    if not summaries:
        print("no summaries to chart: nothing matched output/summary_all_*.json or output/<cat>/summary_*.json")
        return 0

    stats: dict[str, dict] = {m: _aggregate_model(rows) for m, rows in summaries.items()}

    reports_dir.mkdir(parents=True, exist_ok=True)

    render_cost_vs_quality(stats, reports_dir / "cost_vs_quality.png")
    render_leaderboard_bars(stats, reports_dir / "leaderboard_bars.png")
    render_category_heatmap(stats, reports_dir / "category_heatmap.png")
    render_cost_per_category(stats, reports_dir / "cost_per_category.png")

    leaderboard_md = render_leaderboard_md(stats, reports_dir)
    (reports_dir / "leaderboard.md").write_text(leaderboard_md, encoding="utf-8")

    try:
        reports_rel = reports_dir.relative_to(repo_root).as_posix()
    except ValueError:
        reports_rel = reports_dir.as_posix()
    readme_block = render_readme_block(stats, reports_rel)
    (reports_dir / "README_BLOCK.md").write_text(readme_block, encoding="utf-8")

    print(f"rendered {len(stats)} model(s) into {reports_dir}")
    for m, s in sorted(stats.items(), key=lambda kv: kv[1]["overall_mean"], reverse=True):
        print(
            f"  - {m}: score={s['overall_mean']:.4f} "
            f"tasks={s['task_count']} mean_cost=${s['mean_cost']:.4f} "
            f"total_cost=${s['total_cost']:.4f}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
