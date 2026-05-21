from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

from embodied_stressbench.baselines import get_baseline
from embodied_stressbench.envs.task_registry import make_env
from embodied_stressbench.stressors import apply_stressor
from embodied_stressbench.utils.seeds import set_global_seed


def _format_query(template: str, metadata: dict, task: str) -> str:
    context = {
        "task": task,
        "target_label": metadata.get("target_label", "target object"),
        "target_category": metadata.get("target_category", metadata.get("target_label", "object")),
    }
    try:
        return template.format(**context)
    except Exception:
        return template


def _bbox_from_debug(pred_debug: dict, fallback: list | None) -> list[float] | None:
    bbox = pred_debug.get("bbox")
    if isinstance(bbox, list) and len(bbox) >= 4:
        return [float(v) for v in bbox[:4]]
    if isinstance(fallback, list) and len(fallback) >= 4:
        return [float(v) for v in fallback[:4]]
    return None


def _draw_bbox(ax: plt.Axes, bbox: list[float] | None, color: str, label: str) -> None:
    if bbox is None:
        return
    x1, y1, x2, y2 = bbox
    ax.add_patch(Rectangle((x1, y1), max(1.0, x2 - x1), max(1.0, y2 - y1), fill=False, linewidth=2.0, edgecolor=color))
    ax.text(x1, max(0.0, y1 - 4), label, color=color, fontsize=7, va="bottom", bbox={"facecolor": "white", "alpha": 0.75, "edgecolor": "none"})


def _plot_case(row: pd.Series, output_dir: Path, backend: str) -> dict:
    task = str(row["task"])
    baseline_name = str(row["baseline"])
    stressor = str(row["stressor"])
    level = int(row["level"])
    seed = int(row["seed"])
    query_template = str(row.get("query_used") or row.get("query_template") or "target object")

    set_global_seed(seed)
    env = make_env(task=task, backend=backend, seed=seed)
    try:
        obs = env.reset()
        query = _format_query(query_template, obs.object_metadata, task)
        obs, query_used, stress_info = apply_stressor(obs, query=query, stressor_name=stressor, level=level, seed=seed)
        pred = get_baseline(baseline_name).predict_target(obs, query_used, context={"task": task, "seed": seed})
    finally:
        close = getattr(env, "close", None)
        if callable(close):
            close()

    rgb = np.asarray(obs.rgb)
    depth = np.asarray(obs.depth, dtype=float)
    if depth.ndim == 3:
        depth = depth[..., 0]
    target_bbox = obs.object_metadata.get("target_bbox_xyxy")
    pred_bbox = _bbox_from_debug(pred.debug_info, None)
    pixel = pred.debug_info.get("pixel")

    fig, axes = plt.subplots(1, 3, figsize=(8.8, 2.8))
    axes[0].imshow(rgb)
    _draw_bbox(axes[0], target_bbox, "#16a34a", "oracle bbox")
    _draw_bbox(axes[0], pred_bbox, "#dc2626", "selected bbox")
    if isinstance(pixel, list) and len(pixel) >= 2:
        axes[0].scatter([pixel[0]], [pixel[1]], c="#facc15", marker="x", s=48, linewidths=2)
    axes[0].set_title("RGB render")
    axes[0].axis("off")

    valid = np.isfinite(depth) & (depth > 0)
    if valid.any():
        lo, hi = np.nanpercentile(depth[valid], [2, 98])
    else:
        lo, hi = 0.0, 1.0
    axes[1].imshow(depth, cmap="viridis", vmin=lo, vmax=hi)
    _draw_bbox(axes[1], target_bbox, "#16a34a", "oracle")
    _draw_bbox(axes[1], pred_bbox, "#dc2626", "selected")
    axes[1].set_title("Depth map")
    axes[1].axis("off")

    axes[2].axis("off")
    target_error = row.get("target_error_l2")
    error_text = "n/a" if pd.isna(target_error) else f"{float(target_error):.3f} m"
    axes[2].text(
        0.02,
        0.98,
        "\n".join(
            [
                str(row.get("case_label", "case")),
                f"Task: {task}",
                f"Baseline: {baseline_name}",
                f"Stressor: {stressor} L{level}",
                f"Seed: {seed}",
                f"Query: {query_used}",
                f"Target error: {error_text}",
                f"Failure: {row.get('failure_type')}",
                f"Source: {Path(str(row.get('source_file', ''))).name}",
            ]
        ),
        ha="left",
        va="top",
        fontsize=8,
    )
    fig.tight_layout()
    safe = f"{row.get('case_label','case')}_{task}_{baseline_name}_{stressor}_L{level}_seed{seed}"
    safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in safe)
    png = output_dir / f"{safe}.png"
    pdf = output_dir / f"{safe}.pdf"
    fig.savefig(png, dpi=240, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    return {"case_label": row.get("case_label"), "png": str(png), "pdf": str(pdf), "task": task, "seed": seed}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="scientific_reports_revision_20260521/qualitative_case_manifest.csv")
    parser.add_argument("--output-dir", default="paper/scientific_reports/figures/maniskill_qualitative")
    parser.add_argument("--backend", default="maniskill")
    args = parser.parse_args()

    manifest = pd.read_csv(args.manifest)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for _, row in manifest.iterrows():
        rows.append(_plot_case(row, output_dir, args.backend))
    rendered = pd.DataFrame(rows)
    rendered.to_csv(output_dir / "render_manifest.csv", index=False)
    if len(rendered):
        cols = min(2, len(rendered))
        grid_rows = int(np.ceil(len(rendered) / cols))
        fig, axes = plt.subplots(grid_rows, cols, figsize=(8.8 * cols / 2, 2.95 * grid_rows), squeeze=False)
        for ax in axes.ravel():
            ax.axis("off")
        for ax, (_, item) in zip(axes.ravel(), rendered.iterrows()):
            ax.imshow(plt.imread(item["png"]))
            ax.set_title(str(item["case_label"]), fontsize=8)
            ax.axis("off")
        fig.suptitle("ManiSkill qualitative failure and detector-transfer cases", fontsize=11, weight="bold")
        fig.tight_layout(rect=[0, 0, 1, 0.96])
        fig.savefig(output_dir / "maniskill_qualitative_figure.png", dpi=240, bbox_inches="tight")
        fig.savefig(output_dir / "maniskill_qualitative_figure.pdf", bbox_inches="tight")
        plt.close(fig)
    print(f"Wrote {len(rows)} qualitative render panels to {output_dir}")


if __name__ == "__main__":
    main()
