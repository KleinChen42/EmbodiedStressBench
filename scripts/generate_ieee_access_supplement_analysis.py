from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


DISPLAY = {
    "oracle_target": "Oracle target",
    "box_center_depth": "Box-center depth",
    "crop_median_depth": "Crop-median depth",
    "crop_top_surface": "Crop-top-surface",
    "crop_trimmed_median_depth": "Crop-trimmed median",
    "box_center_depth_query_aware": "Box-center + metadata",
    "crop_median_depth_query_aware": "Crop-median + metadata",
    "crop_trimmed_median_depth_query_aware": "Trimmed median + metadata",
    "box_center_depth_first_detection": "Box-center + first",
    "crop_median_depth_first_detection": "Crop-median + first",
    "crop_trimmed_median_depth_first_detection": "Trimmed median + first",
    "box_center_depth_grounding_dino": "Box-center + GroundingDINO",
    "crop_median_depth_grounding_dino": "Crop-median + GroundingDINO",
    "crop_trimmed_median_depth_grounding_dino": "Trimmed median + GroundingDINO",
}


def _load_records(roots: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for spec in roots:
        if "=" in spec:
            run, raw_path = spec.split("=", 1)
        else:
            raw_path = spec
            run = Path(spec).name
        root = Path(raw_path)
        if not root.exists():
            continue
        for path in root.rglob("*.json"):
            if path.name == "experiment_config_snapshot.json":
                continue
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            pred = item.get("prediction") or {}
            debug = pred.get("debug_info") or {}
            rows.append(
                {
                    "run": run,
                    "task": item.get("task"),
                    "baseline": item.get("baseline"),
                    "stressor": item.get("stressor"),
                    "level": item.get("level"),
                    "seed": item.get("seed"),
                    "success": bool(item.get("success")),
                    "target_error_l2": item.get("target_error_l2"),
                    "failure_type": item.get("failure_type") or "success",
                    "grounding_dino_target_iou": debug.get("grounding_dino_target_iou"),
                    "selected_detection_is_target": debug.get("selected_detection_is_target"),
                }
            )
    return pd.DataFrame(rows)


def _clean(name: str) -> str:
    return DISPLAY.get(str(name), str(name).replace("_", " "))


def _save(fig: plt.Figure, out_dir: Path, name: str) -> None:
    fig.tight_layout()
    fig.savefig(out_dir / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(out_dir / f"{name}.png", dpi=240, bbox_inches="tight")
    plt.close(fig)


def task_stressor_heatmap(df: pd.DataFrame, out_dir: Path, fig_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    if df.empty:
        return
    grouped = (
        df.groupby(["task", "stressor", "baseline"], dropna=False)
        .agg(success_rate=("success", "mean"), n=("success", "size"))
        .reset_index()
    )
    grouped.to_csv(out_dir / "task_stressor_target_source_heatmap.csv", index=False)
    focus = grouped[grouped["baseline"].isin(["box_center_depth", "crop_median_depth", "crop_trimmed_median_depth"])]
    if focus.empty:
        return
    focus["row"] = focus["task"].astype(str) + " / " + focus["stressor"].astype(str)
    pivot = focus.pivot_table(index="row", columns="baseline", values="success_rate", aggfunc="mean")
    if pivot.empty:
        return
    fig, ax = plt.subplots(figsize=(7.0, max(3.0, 0.28 * len(pivot))))
    im = ax.imshow(pivot.values, aspect="auto", vmin=0, vmax=1, cmap="viridis")
    ax.set_yticks(np.arange(len(pivot.index)), pivot.index)
    ax.set_xticks(np.arange(len(pivot.columns)), [_clean(c) for c in pivot.columns], rotation=20, ha="right")
    ax.set_title("Task/stressor success by target source")
    fig.colorbar(im, ax=ax, label="Success rate")
    _save(fig, fig_dir, "task_stressor_target_source_heatmap")


def error_cdf(df: pd.DataFrame, out_dir: Path, fig_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    data = df[df["target_error_l2"].notna()].copy()
    if data.empty:
        return
    baselines = ["oracle_target", "box_center_depth", "crop_median_depth", "crop_trimmed_median_depth", "crop_top_surface"]
    rows = []
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    for baseline in baselines:
        vals = np.sort(data.loc[data["baseline"] == baseline, "target_error_l2"].astype(float).to_numpy())
        if len(vals) == 0:
            continue
        y = np.arange(1, len(vals) + 1) / len(vals)
        ax.plot(vals, y, label=_clean(baseline))
        for q in [0.5, 0.75, 0.9, 0.95]:
            rows.append({"baseline": baseline, "quantile": q, "target_error_l2": float(np.quantile(vals, q)), "n": len(vals)})
    if not rows:
        return
    pd.DataFrame(rows).to_csv(out_dir / "target_error_cdf_quantiles.csv", index=False)
    ax.set_xlabel("Target error L2 (m)")
    ax.set_ylabel("CDF")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    _save(fig, fig_dir, "target_error_cdf")


def paired_bootstrap(df: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    pairs = [
        ("crop_median_depth", "box_center_depth"),
        ("crop_trimmed_median_depth", "crop_median_depth"),
        ("crop_trimmed_median_depth", "box_center_depth"),
    ]
    keys = ["run", "task", "stressor", "level", "seed"]
    rows = []
    rng = np.random.default_rng(20260520)
    for a, b in pairs:
        pivot = df[df["baseline"].isin([a, b])].pivot_table(index=keys, columns="baseline", values="success", aggfunc="first")
        if a not in pivot or b not in pivot:
            continue
        vals = (pivot[a].astype(float) - pivot[b].astype(float)).dropna().to_numpy()
        if len(vals) == 0:
            continue
        samples = [float(rng.choice(vals, size=len(vals), replace=True).mean()) for _ in range(2000)]
        rows.append(
            {
                "baseline_a": a,
                "baseline_b": b,
                "mean_success_diff": float(vals.mean()),
                "ci_low": float(np.quantile(samples, 0.025)),
                "ci_high": float(np.quantile(samples, 0.975)),
                "paired_blocks": int(len(vals)),
            }
        )
    pd.DataFrame(rows).to_csv(out_dir / "paired_bootstrap_effects.csv", index=False)


def grounding_dino_iou_analysis(df: pd.DataFrame, out_dir: Path, fig_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    data = df[df["baseline"].astype(str).str.contains("grounding_dino", na=False)].copy()
    data = data[data["grounding_dino_target_iou"].notna()]
    if data.empty:
        return
    rows = []
    for threshold in [0.10, 0.25, 0.50, 0.75]:
        hit = data["grounding_dino_target_iou"].astype(float) >= threshold
        rows.append(
            {
                "iou_threshold": threshold,
                "hit_rate": float(hit.mean()),
                "success_when_hit": float(data.loc[hit, "success"].mean()) if hit.any() else float("nan"),
                "success_when_miss": float(data.loc[~hit, "success"].mean()) if (~hit).any() else float("nan"),
                "n": int(len(data)),
            }
        )
    pd.DataFrame(rows).to_csv(out_dir / "grounding_dino_iou_sweep.csv", index=False)
    if data["target_error_l2"].notna().any():
        fig, ax = plt.subplots(figsize=(5.4, 3.6))
        ax.scatter(
            data["grounding_dino_target_iou"].astype(float),
            data["target_error_l2"].astype(float),
            c=data["success"].astype(int),
            cmap="coolwarm",
            alpha=0.65,
            s=14,
        )
        ax.set_xlabel("GroundingDINO target IoU")
        ax.set_ylabel("3D target error L2 (m)")
        ax.grid(alpha=0.25)
        _save(fig, fig_dir, "grounding_dino_iou_vs_3d_error")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--roots", nargs="+", required=True, help="Run roots as LABEL=PATH or PATH.")
    parser.add_argument("--output-dir", default="ieee_access_revision_20260520/supplement_analysis")
    parser.add_argument("--figures-dir", default="paper/ieee_access/figures/supplement")
    args = parser.parse_args()
    out_dir = Path(args.output_dir)
    fig_dir = Path(args.figures_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    df = _load_records(args.roots)
    df.to_csv(out_dir / "loaded_episode_index.csv", index=False)
    task_stressor_heatmap(df, out_dir, fig_dir)
    error_cdf(df, out_dir, fig_dir)
    paired_bootstrap(df, out_dir)
    grounding_dino_iou_analysis(df, out_dir, fig_dir)
    print(f"Wrote supplement analysis under {out_dir} and {fig_dir}")


if __name__ == "__main__":
    main()
