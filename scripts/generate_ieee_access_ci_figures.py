from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _clean(text: str) -> str:
    return text.replace("_query_aware", " query").replace("_first_detection", " first").replace("_", " ")


def _err(y: pd.Series, lo: pd.Series, hi: pd.Series) -> np.ndarray:
    return np.vstack([(y - lo).clip(lower=0), (hi - y).clip(lower=0)])


def _save(fig: plt.Figure, out_dir: Path, name: str) -> None:
    fig.tight_layout()
    fig.savefig(out_dir / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(out_dir / f"{name}.png", dpi=240, bbox_inches="tight")
    plt.close(fig)


def main_success_with_ci(revision_dir: Path, out_dir: Path) -> None:
    df = pd.read_csv(revision_dir / "main_results_with_ci.csv")
    keep_runs = ["Primary", "Heldout", "HardL3Confirm"]
    keep_baselines = ["oracle_target", "crop_median_depth", "box_center_depth", "crop_top_surface"]
    df = df[df["run"].isin(keep_runs) & df["baseline"].isin(keep_baselines)].copy()
    if df.empty:
        return
    order = {b: i for i, b in enumerate(keep_baselines)}
    df["baseline_order"] = df["baseline"].map(order)
    df = df.sort_values(["run", "baseline_order"])
    fig, ax = plt.subplots(figsize=(8.0, 3.4))
    width = 0.22
    x = np.arange(len(keep_baselines))
    for idx, run in enumerate(keep_runs):
        group = df[df["run"] == run].sort_values("baseline_order")
        xpos = x + (idx - 1) * width
        ax.bar(
            xpos,
            group["success_rate"],
            width=width,
            yerr=_err(group["success_rate"], group["ci_low"], group["ci_high"]),
            capsize=2,
            label=run,
        )
    ax.set_xticks(x, [_clean(b) for b in keep_baselines], rotation=0)
    ax.set_ylabel("Success rate with 95% CI")
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, ncols=3)
    _save(fig, out_dir, "main_success_with_ci")


def hard_stressors_with_ci(revision_dir: Path, out_dir: Path) -> None:
    df = pd.read_csv(revision_dir / "stressor_ranking_with_ci.csv")
    df = df[df["run"] == "HardL3Confirm"].sort_values("success_rate")
    if df.empty:
        return
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ax.barh(
        [_clean(x) for x in df["stressor"]],
        df["success_rate"],
        xerr=_err(df["success_rate"], df["ci_low"], df["ci_high"]),
        capsize=2,
        color="#3f6f8f",
    )
    ax.set_xlabel("Success rate with 95% CI")
    ax.set_xlim(0, 1.05)
    ax.grid(axis="x", alpha=0.25)
    _save(fig, out_dir, "hard_l3_stressor_ranking_with_ci")


def oracle_gap_by_stressor(revision_dir: Path, out_dir: Path) -> None:
    path = revision_dir / "oracle_gap_by_stressor_with_ci.csv"
    if not path.exists():
        return
    df = pd.read_csv(path)
    df = df[(df["run"] == "Heldout") & (df["baseline"] == "crop_median_depth")].sort_values("oracle_gap")
    if df.empty:
        return
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ax.barh(
        [_clean(x) for x in df["stressor"]],
        df["oracle_gap"],
        xerr=_err(df["oracle_gap"], df["ci_low"], df["ci_high"]),
        capsize=2,
        color="#8b5e3c",
    )
    ax.set_xlabel("Oracle gap with 95% CI")
    ax.set_xlim(0, max(0.05, float(df["ci_high"].max()) + 0.05))
    ax.grid(axis="x", alpha=0.25)
    _save(fig, out_dir, "oracle_gap_by_stressor_with_ci")


def threshold_sensitivity_from_csv(revision_dir: Path, out_dir: Path) -> None:
    path = revision_dir / "threshold_sensitivity.csv"
    if not path.exists():
        return
    df = pd.read_csv(path)
    keep_baselines = ["oracle_target", "box_center_depth", "crop_median_depth", "crop_top_surface"]
    df = df[df["baseline"].isin(keep_baselines)].copy()
    if "Heldout" in set(df["run"]):
        df = df[df["run"] == "Heldout"].copy()
    if df.empty:
        return
    order = {name: idx for idx, name in enumerate(keep_baselines)}
    df["baseline_order"] = df["baseline"].map(order)
    fig, ax = plt.subplots(figsize=(6.8, 3.2))
    for baseline, group in df.sort_values("baseline_order").groupby("baseline"):
        group = group.sort_values("threshold_m")
        ax.plot(group["threshold_m"], group["success_rate"], marker="o", label=_clean(baseline))
    ax.set_xlabel("Success threshold (m)")
    ax.set_ylabel("Recomputed success rate")
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=8, ncols=2)
    _save(fig, out_dir, "threshold_sensitivity")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision-dir", default="ieee_access_revision_20260520")
    parser.add_argument("--output-dir", default="paper/ieee_access/figures")
    args = parser.parse_args()
    revision_dir = Path(args.revision_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    main_success_with_ci(revision_dir, out_dir)
    hard_stressors_with_ci(revision_dir, out_dir)
    oracle_gap_by_stressor(revision_dir, out_dir)
    threshold_sensitivity_from_csv(revision_dir, out_dir)
    print(f"Wrote CI figures under {out_dir}")


if __name__ == "__main__":
    main()
