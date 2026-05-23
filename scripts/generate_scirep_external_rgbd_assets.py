from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


DISPLAY = {
    "oracle_mask": "Oracle mask",
    "oracle_2d_box": "Oracle 2D box",
    "first_gt_box": "First GT box",
    "grounding_dino": "GroundingDINO",
    "mask_median_depth": "Mask median",
    "box_center_depth": "Box-center",
    "crop_median_depth": "Crop median",
    "crop_trimmed_median_depth": "Crop-trimmed median",
    "oracle": "Oracle",
    "generic": "Generic query",
    "true_name": "True-name query",
    "photo_true_name": "Photo true-name query",
}


FOCUS_ROWS = [
    ("oracle_mask", "mask_median_depth", "oracle", "Oracle mask + mask median"),
    ("oracle_2d_box", "box_center_depth", "oracle", "Oracle 2D + box-center"),
    ("oracle_2d_box", "crop_median_depth", "oracle", "Oracle 2D + crop median"),
    ("oracle_2d_box", "crop_trimmed_median_depth", "oracle", "Oracle 2D + trimmed median"),
    ("first_gt_box", "crop_trimmed_median_depth", "oracle", "First GT box + trimmed median"),
    ("grounding_dino", "crop_trimmed_median_depth", "generic", "DINO generic + trimmed median"),
    ("grounding_dino", "crop_trimmed_median_depth", "photo_true_name", "DINO photo-name + trimmed median"),
    ("grounding_dino", "crop_trimmed_median_depth", "true_name", "DINO true-name + trimmed median"),
]


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


def _fmt_cm(value: float | int | str) -> str:
    if pd.isna(value):
        return "--"
    return f"{100 * float(value):.1f}"


def _select_focus(summary: pd.DataFrame, thresholds: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for detector, target_source, query_variant, label in FOCUS_ROWS:
        hit = summary[
            summary["detector"].eq(detector)
            & summary["target_source"].eq(target_source)
            & summary["query_variant"].eq(query_variant)
        ]
        thr = thresholds[
            thresholds["detector"].eq(detector)
            & thresholds["target_source"].eq(target_source)
            & thresholds["query_variant"].eq(query_variant)
        ]
        if hit.empty:
            continue
        row = hit.iloc[0].to_dict()
        if not thr.empty:
            row.update({k: thr.iloc[0][k] for k in thr.columns if k.startswith("success_at_")})
        row["display_label"] = label
        row["condition_display"] = f"{DISPLAY.get(detector, detector)} / {DISPLAY.get(query_variant, query_variant)}"
        row["target_display"] = DISPLAY.get(target_source, target_source.replace("_", " "))
        rows.append(row)
    out = pd.DataFrame(rows)
    ordered = {label: idx for idx, *_, label in []}
    return out


def _write_table(focus: pd.DataFrame, tables_dir: Path) -> None:
    csv_path = tables_dir / "external_rgbd_validation_summary.csv"
    focus.to_csv(csv_path, index=False)

    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{External real RGB-D validation on YCB-V/BOP. The visible-mask median is the 3D reference. Oracle-mask and oracle-2D-box controls isolate RGB-D lifting from detector localization, while GroundingDINO rows combine open-vocabulary 2D detection with the same target sources. Rates are percentages; success uses the default 0.08 m target-distance threshold.}",
        r"\label{tab:external-rgbd-validation}",
        r"\scriptsize",
        r"\begin{tabular}{lrrrrrr}",
        r"\toprule",
        r"Condition & Episodes & Success (95\% CI) & Success@4 cm & Success@10 cm & Wrong det. & Median error (cm) \\",
        r"\midrule",
    ]
    for _, row in focus.iterrows():
        lines.append(
            f"{row['display_label']} & {int(row['episodes'])} & "
            f"{_fmt_pct_ci(row['success_rate'], row.get('success_ci_low', float('nan')), row.get('success_ci_high', float('nan')))} & "
            f"{_fmt_pct(row.get('success_at_04cm', float('nan')))} & "
            f"{_fmt_pct(row.get('success_at_10cm', float('nan')))} & "
            f"{_fmt_pct(row.get('wrong_detection_rate', float('nan')))} & "
            f"{_fmt_cm(row.get('median_target_error_l2', float('nan')))} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""])
    (tables_dir / "external_rgbd_validation_summary.tex").write_text("\n".join(lines), encoding="utf-8")


def _make_figure(focus: pd.DataFrame, thresholds: pd.DataFrame, fig_dir: Path) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    source = focus.copy()
    short_labels = {
        "Oracle mask + mask median": "Mask\noracle",
        "Oracle 2D + box-center": "2D box\nbox-center",
        "Oracle 2D + crop median": "2D box\ncrop median",
        "Oracle 2D + trimmed median": "2D box\ntrimmed",
        "First GT box + trimmed median": "First GT\ntrimmed",
        "DINO generic + trimmed median": "DINO generic\ntrimmed",
        "DINO photo-name + trimmed median": "DINO photo-name\ntrimmed",
        "DINO true-name + trimmed median": "DINO true-name\ntrimmed",
    }
    source["plot_label"] = source["display_label"].map(short_labels).fillna(source["display_label"])
    source["target_error_or_other_rate"] = (
        1.0
        - source["success_rate"].fillna(0.0)
        - source["no_detection_rate"].fillna(0.0)
        - source["wrong_detection_rate"].fillna(0.0)
        - source["depth_failure_rate"].fillna(0.0)
    ).clip(lower=0.0)
    source.to_csv(fig_dir / "external_rgbd_validation_source.csv", index=False)

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

    colors = {
        "success": "#4C78A8",
        "oracle": "#72B7B2",
        "dino": "#F58518",
        "first": "#8E6C8A",
        "wrong": "#E45756",
        "depth": "#B279A2",
        "other": "#BAB0AC",
        "none": "#9D755D",
    }

    fig = plt.figure(figsize=(7.8, 5.1), constrained_layout=True)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.0], width_ratios=[1.25, 1.0])
    ax_a = fig.add_subplot(gs[0, :])
    ax_b = fig.add_subplot(gs[1, 0])
    ax_c = fig.add_subplot(gs[1, 1])

    labels = source["plot_label"].tolist()
    x = np.arange(len(source))
    y = source["success_rate"].to_numpy(dtype=float)
    lo = source["success_ci_low"].to_numpy(dtype=float)
    hi = source["success_ci_high"].to_numpy(dtype=float)
    yerr = np.vstack([np.maximum(0, y - lo), np.maximum(0, hi - y)])
    bar_colors = [
        colors["oracle"] if str(row.detector).startswith("oracle") else colors["dino"] if row.detector == "grounding_dino" else colors["first"]
        for row in source.itertuples()
    ]
    ax_a.bar(x, y * 100, yerr=yerr * 100, capsize=2.0, color=bar_colors, edgecolor="black", linewidth=0.35)
    ax_a.set_ylabel("Success at 8 cm (%)")
    ax_a.set_ylim(0, 105)
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(labels, rotation=18, ha="right")
    ax_a.tick_params(axis="x", labelsize=6.4)
    ax_a.set_title("a  External RGB-D target generation separates lifting and detector failures", loc="left", fontweight="bold", fontsize=8.5)
    ax_a.grid(axis="y", color="#E6E6E6", linewidth=0.5)

    curve_specs = [
        ("oracle_mask", "mask_median_depth", "oracle", "Oracle mask + mask median", "#72B7B2"),
        ("oracle_2d_box", "box_center_depth", "oracle", "Oracle 2D + box-center", "#4C78A8"),
        ("oracle_2d_box", "crop_trimmed_median_depth", "oracle", "Oracle 2D + trimmed median", "#54A24B"),
        ("grounding_dino", "crop_trimmed_median_depth", "true_name", "DINO true-name + trimmed", "#F58518"),
        ("grounding_dino", "crop_trimmed_median_depth", "generic", "DINO generic + trimmed", "#E45756"),
    ]
    xs = np.array([4, 6, 8, 10], dtype=float)
    for detector, target_source, query, label, color in curve_specs:
        row = thresholds[
            thresholds["detector"].eq(detector)
            & thresholds["target_source"].eq(target_source)
            & thresholds["query_variant"].eq(query)
        ]
        if row.empty:
            continue
        vals = [float(row.iloc[0][f"success_at_{cm:02d}cm"]) * 100 for cm in [4, 6, 8, 10]]
        ax_b.plot(xs, vals, marker="o", markersize=3.0, linewidth=1.4, color=color, label=label)
    ax_b.set_title("b  Threshold sensitivity", loc="left", fontweight="bold", fontsize=8.5)
    ax_b.set_xlabel("Target-distance threshold (cm)")
    ax_b.set_ylabel("Success (%)")
    ax_b.set_xticks(xs)
    ax_b.set_ylim(0, 105)
    ax_b.grid(axis="y", color="#E6E6E6", linewidth=0.5)
    ax_b.legend(fontsize=5.9, loc="lower right")

    fail_focus = source[
        source["display_label"].isin(
            [
                "Oracle 2D + trimmed median",
                "First GT box + trimmed median",
                "DINO generic + trimmed median",
                "DINO true-name + trimmed median",
            ]
        )
    ].copy()
    stack_labels = fail_focus["display_label"].map(
        {
            "Oracle 2D + trimmed median": "2D box",
            "First GT box + trimmed median": "First GT",
            "DINO generic + trimmed median": "DINO\ngeneric",
            "DINO true-name + trimmed median": "DINO\ntrue-name",
        }
    ).fillna(fail_focus["display_label"]).tolist()
    sx = np.arange(len(fail_focus))
    bottom = np.zeros(len(fail_focus))
    for col, label, color in [
        ("success_rate", "Success", colors["success"]),
        ("wrong_detection_rate", "Wrong detection", colors["wrong"]),
        ("depth_failure_rate", "Depth failure", colors["depth"]),
        ("no_detection_rate", "No detection", colors["none"]),
        ("target_error_or_other_rate", "Target error/other", colors["other"]),
    ]:
        vals = fail_focus[col].fillna(0.0).to_numpy(dtype=float) * 100
        ax_c.bar(sx, vals, bottom=bottom, color=color, edgecolor="white", linewidth=0.35, label=label)
        bottom += vals
    ax_c.set_title("c  Failure attribution", loc="left", fontweight="bold", fontsize=8.5)
    ax_c.set_ylabel("Outcome share (%)")
    ax_c.set_xticks(sx)
    ax_c.set_xticklabels(stack_labels, rotation=0, ha="center")
    ax_c.set_ylim(0, 100)
    ax_c.legend(fontsize=5.8, loc="upper left", bbox_to_anchor=(1.01, 1.0))

    for ext in ["png", "pdf", "svg"]:
        fig.savefig(fig_dir / f"external_rgbd_validation.{ext}", dpi=600 if ext == "png" else None, bbox_inches="tight")
    plt.close(fig)


def _write_claim_note(focus: pd.DataFrame, revision_dir: Path, analysis_dir: Path) -> None:
    row = lambda d, s, q: focus[
        focus["detector"].eq(d) & focus["target_source"].eq(s) & focus["query_variant"].eq(q)
    ].iloc[0]
    oracle_mask = row("oracle_mask", "mask_median_depth", "oracle")
    oracle_trim = row("oracle_2d_box", "crop_trimmed_median_depth", "oracle")
    generic = row("grounding_dino", "crop_trimmed_median_depth", "generic")
    true_name = row("grounding_dino", "crop_trimmed_median_depth", "true_name")
    note = f"""# External RGB-D Validation Claim Note

Input artifact: `{analysis_dir.as_posix()}`

## Supported claim

The YCB-V/BOP probe provides external real RGB-D evidence that EmbodiedStressBench
can separate RGB-D target lifting from detector/query failure. The visible-mask
oracle reaches {_fmt_pct(oracle_mask['success_rate'])}% success at 8 cm, while
oracle 2D boxes with crop-trimmed median depth reach {_fmt_pct(oracle_trim['success_rate'])}%.
GroundingDINO with generic prompts reaches only {_fmt_pct(generic['success_rate'])}%
with crop-trimmed median lifting, but true-name prompts recover to
{_fmt_pct(true_name['success_rate'])}% on the same real RGB-D probe.

## Boundary

This is not a real-robot manipulation result and does not compare detector
leaderboards. It is an external RGB-D target-generation probe using YCB-V/BOP
ground-truth visible masks/boxes as references and controls.
"""
    revision_dir.mkdir(parents=True, exist_ok=True)
    (revision_dir / "external_rgbd_validation_claim_note.md").write_text(note, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-dir", default="outputs/ycbv_external_rgbd_probe_160k_20260522_analysis")
    parser.add_argument("--paper-dir", default="paper/scientific_reports")
    parser.add_argument("--revision-dir", default="scientific_reports_revision_20260521")
    args = parser.parse_args()

    analysis_dir = Path(args.analysis_dir)
    paper_dir = Path(args.paper_dir)
    revision_dir = Path(args.revision_dir)
    tables_dir = paper_dir / "tables"
    fig_dir = paper_dir / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    summary = pd.read_csv(analysis_dir / "summary_by_detector_source.csv")
    thresholds = pd.read_csv(analysis_dir / "threshold_sensitivity.csv")
    focus = _select_focus(summary, thresholds)
    if len(focus) < len(FOCUS_ROWS):
        missing = len(FOCUS_ROWS) - len(focus)
        raise SystemExit(f"Missing {missing} expected focus rows in {analysis_dir}")

    _write_table(focus, tables_dir)
    _make_figure(focus, thresholds, fig_dir)
    _write_claim_note(focus, revision_dir, analysis_dir)
    print(f"Wrote external RGB-D table and figure under {paper_dir}")


if __name__ == "__main__":
    main()
