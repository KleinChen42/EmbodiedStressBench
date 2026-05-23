from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


RUNS = [
    ("0.10/0.10", "thr010", "ycbv_external_rgbd_probe_thr010_20260522_analysis"),
    ("0.20/0.20", "default", "ycbv_external_rgbd_probe_160k_20260522_analysis"),
    ("0.30/0.25", "thr030", "ycbv_external_rgbd_probe_thr030_20260522_analysis"),
]

QUERY_LABELS = {
    "generic": "Generic",
    "photo_true_name": "Photo true-name",
    "true_name": "True-name",
}


def _fmt_pct(value: float | int | str) -> str:
    if pd.isna(value):
        return "--"
    pct = 100 * float(value)
    if pct not in (0.0, 100.0) and (pct < 0.05 or pct > 99.95):
        return f"{pct:.2f}"
    return f"{pct:.1f}"


def _fmt_pct_ci(value: float, low: float, high: float) -> str:
    if pd.isna(low) or pd.isna(high):
        return _fmt_pct(value)
    value = float(value)
    low = min(float(low), value)
    high = max(float(high), value)
    return f"{_fmt_pct(value)} [{_fmt_pct(low)}, {_fmt_pct(high)}]"


def _load(root: Path) -> pd.DataFrame:
    rows = []
    for threshold_label, run_key, dirname in RUNS:
        path = root / dirname / "summary_by_detector_source.csv"
        if not path.exists():
            raise FileNotFoundError(path)
        df = pd.read_csv(path)
        focus = df[
            df["detector"].eq("grounding_dino")
            & df["target_source"].eq("crop_trimmed_median_depth")
            & df["query_variant"].isin(["generic", "photo_true_name", "true_name"])
        ].copy()
        focus.insert(0, "run_key", run_key)
        focus.insert(0, "detector_threshold", threshold_label)
        rows.append(focus)
    out = pd.concat(rows, ignore_index=True)
    order = {label: i for i, (label, _, _) in enumerate(RUNS)}
    out["threshold_order"] = out["detector_threshold"].map(order)
    out["query_display"] = out["query_variant"].map(QUERY_LABELS)
    return out.sort_values(["threshold_order", "query_variant"]).reset_index(drop=True)


def _write_table(df: pd.DataFrame, tables_dir: Path) -> None:
    tables_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(tables_dir / "external_rgbd_detector_threshold_sensitivity.csv", index=False)
    focus = df[df["query_variant"].eq("true_name")].copy()

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{GroundingDINO detector-threshold sensitivity on the full YCB-V/BOP external RGB-D probe. Rows use crop-trimmed median depth and true object-name prompts. Rates are percentages.}",
        r"\label{tab:external-rgbd-detector-threshold}",
        r"\scriptsize",
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Box/text threshold & Success (95\% CI) & No detection & Wrong detection & IoU \\",
        r"\midrule",
    ]
    for _, row in focus.iterrows():
        lines.append(
            f"{row['detector_threshold']} & "
            f"{_fmt_pct_ci(row['success_rate'], row['success_ci_low'], row['success_ci_high'])} & "
            f"{_fmt_pct(row['no_detection_rate'])} & "
            f"{_fmt_pct(row['wrong_detection_rate'])} & "
            f"{float(row['mean_bbox_iou']):.3f} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    (tables_dir / "external_rgbd_detector_threshold_sensitivity.tex").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def _make_figure(df: pd.DataFrame, fig_dir: Path) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    source = df.copy()
    source.to_csv(fig_dir / "external_rgbd_detector_threshold_sensitivity_source.csv", index=False)

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 7,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.7,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "legend.frameon": False,
        }
    )
    palette = {
        "generic": "#E45756",
        "photo_true_name": "#F58518",
        "true_name": "#4C78A8",
    }
    fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.6), constrained_layout=True)
    x_labels = [label for label, _, _ in RUNS]
    x = np.arange(len(x_labels))

    for query in ["generic", "photo_true_name", "true_name"]:
        group = df[df["query_variant"].eq(query)].sort_values("threshold_order")
        y = group["success_rate"].to_numpy(dtype=float) * 100
        point = group["success_rate"].to_numpy(dtype=float)
        ci_low = np.minimum(group["success_ci_low"].to_numpy(dtype=float), point)
        ci_high = np.maximum(group["success_ci_high"].to_numpy(dtype=float), point)
        lo = ci_low * 100
        hi = ci_high * 100
        yerr = np.vstack([np.maximum(0, y - lo), np.maximum(0, hi - y)])
        axes[0].errorbar(
            x,
            y,
            yerr=yerr,
            marker="o",
            linewidth=1.4,
            markersize=3.5,
            capsize=2,
            label=QUERY_LABELS[query],
            color=palette[query],
        )
    axes[0].set_title("a  Detector-threshold sensitivity", loc="left", fontweight="bold")
    axes[0].set_ylabel("Success at 8 cm (%)")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(x_labels)
    axes[0].set_xlabel("Box/text threshold")
    axes[0].set_ylim(0, 75)
    axes[0].grid(axis="y", color="#E6E6E6", linewidth=0.5)
    axes[0].legend(loc="lower right", fontsize=6)

    true_name = df[df["query_variant"].eq("true_name")].sort_values("threshold_order")
    width = 0.24
    axes[1].bar(
        x - width,
        true_name["success_rate"].to_numpy(dtype=float) * 100,
        width=width,
        color="#4C78A8",
        label="Success",
    )
    axes[1].bar(
        x,
        true_name["wrong_detection_rate"].to_numpy(dtype=float) * 100,
        width=width,
        color="#E45756",
        label="Wrong detection",
    )
    axes[1].bar(
        x + width,
        true_name["no_detection_rate"].to_numpy(dtype=float) * 100,
        width=width,
        color="#9D755D",
        label="No detection",
    )
    axes[1].set_title("b  True-name failure tradeoff", loc="left", fontweight="bold")
    axes[1].set_ylabel("Outcome share (%)")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(x_labels)
    axes[1].set_xlabel("Box/text threshold")
    axes[1].set_ylim(0, 75)
    axes[1].grid(axis="y", color="#E6E6E6", linewidth=0.5)
    axes[1].legend(loc="upper right", fontsize=6)

    for ext in ["png", "pdf", "svg"]:
        fig.savefig(
            fig_dir / f"external_rgbd_detector_threshold_sensitivity.{ext}",
            dpi=600 if ext == "png" else None,
            bbox_inches="tight",
        )
    plt.close(fig)


def _write_note(df: pd.DataFrame, revision_dir: Path) -> None:
    revision_dir.mkdir(parents=True, exist_ok=True)
    pivot = df.pivot_table(index="detector_threshold", columns="query_variant", values="success_rate", aggfunc="first")
    note = [
        "# YCB-V Detector-Threshold Sensitivity Note",
        "",
        "The full YCB-V/BOP external RGB-D probe was repeated for three GroundingDINO box/text threshold settings.",
        "",
        "| Threshold | Generic | Photo true-name | True-name |",
        "| --- | ---: | ---: | ---: |",
    ]
    for label, _, _ in RUNS:
        row = pivot.loc[label]
        note.append(
            f"| {label} | {_fmt_pct(row.get('generic'))} | {_fmt_pct(row.get('photo_true_name'))} | {_fmt_pct(row.get('true_name'))} |"
        )
    note.extend(
        [
            "",
            "Interpretation: true-name prompts remain far above the generic prompt across detector-threshold settings. "
            "The stricter 0.30/0.25 setting slightly reduces true-name success and increases no-detection, but does not change the qualitative conclusion.",
        ]
    )
    (revision_dir / "external_rgbd_detector_threshold_sensitivity_note.md").write_text(
        "\n".join(note),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputs-root", default="outputs")
    parser.add_argument("--paper-dir", default="paper/scientific_reports")
    parser.add_argument("--revision-dir", default="scientific_reports_revision_20260521")
    args = parser.parse_args()

    outputs_root = Path(args.outputs_root)
    paper_dir = Path(args.paper_dir)
    revision_dir = Path(args.revision_dir)
    df = _load(outputs_root)
    _write_table(df, paper_dir / "tables")
    _make_figure(df, paper_dir / "figures")
    _write_note(df, revision_dir)
    print(f"Wrote detector-threshold sensitivity assets for {len(df)} rows")


if __name__ == "__main__":
    main()
