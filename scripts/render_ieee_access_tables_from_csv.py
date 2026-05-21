from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


BASELINE_NAMES = {
    "oracle_target": "Oracle target",
    "box_center_depth": "Box-center depth",
    "crop_median_depth": "Crop-median depth",
    "crop_trimmed_median_depth": "Crop-trimmed median",
    "crop_top_surface": "Crop-top-surface",
    "box_center_depth_first_detection": "Box-center + first detection",
    "box_center_depth_query_aware": "Box-center + query-aware",
    "crop_median_depth_first_detection": "Crop-median + first detection",
    "crop_median_depth_query_aware": "Crop-median + query-aware",
    "crop_trimmed_median_depth_first_detection": "Crop-trimmed median + first detection",
    "crop_trimmed_median_depth_query_aware": "Crop-trimmed median + query-aware",
    "crop_trimmed_median_depth_grounding_dino": "Crop-trimmed median + GroundingDINO",
    "crop_top_surface_first_detection": "Crop-top-surface + first detection",
    "crop_top_surface_query_aware": "Crop-top-surface + query-aware",
}


STRESSOR_NAMES = {
    "none": "None",
    "same_shape_distractor": "Same-shape distractor",
    "same_color_distractor": "Same-color distractor",
    "nearby_distractor": "Nearby distractor",
    "partial_target_occlusion": "Partial target occlusion",
    "same_color_partial_occlusion": "Same-color + partial occlusion",
    "same_shape_nearby_occlusion": "Same-shape + nearby occlusion",
    "visual_occlusion": "Visual occlusion",
    "depth_sparsity": "Depth sparsity",
    "depth_noise": "Depth noise",
    "camera_pose_noise": "Camera-pose noise",
    "execution_offset": "Execution offset",
    "execution_offset_strong": "Strong execution offset",
}


RUN_NAMES = {
    "Primary": "Main v1",
    "Heldout": "Held-out seeds",
    "VisualBridge": "Visual/sensor bridge",
    "HardL3Confirm": "Hard L3 confirmation",
    "Semantic": "Semantic distractors",
}


FAILURE_NAMES = {
    "success": "Success",
    "target_error_too_large": "Target error too large",
    "depth_invalid": "Invalid depth",
    "wrong_detection_selected": "Wrong detection selected",
    "no_detection": "No detection",
    "runner_exception": "Runner exception",
}


def _escape_tex(value: object) -> str:
    text = str(value)
    for src, dst in {
        "\\": r"\textbackslash{}",
        "_": r"\_",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
        "$": r"\$",
    }.items():
        text = text.replace(src, dst)
    return text


def _fmt(value: object) -> str:
    if pd.isna(value):
        return "--"
    if isinstance(value, float):
        return f"{value:.3f}"
    return _escape_tex(value)


def _rate_ci(row: pd.Series, rate_col: str) -> str:
    return f"{row[rate_col]:.3f} [{row['ci_low']:.3f}, {row['ci_high']:.3f}]"


def _write_table(df: pd.DataFrame, path: Path, columns: list[str], headers: list[str], caption: str, label: str, table_star: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    env = "table*" if table_star else "table"
    lines = [
        rf"\begin{{{env}}}[t]",
        r"\centering",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        r"\small",
        r"\begin{tabular}{" + "l" * len(columns) + "}",
        r"\hline",
        " & ".join(_escape_tex(h) for h in headers) + r" \\",
        r"\hline",
    ]
    for _, row in df.iterrows():
        lines.append(" & ".join(_fmt(row[col]) for col in columns) + r" \\")
    lines.extend([r"\hline", r"\end{tabular}", rf"\end{{{env}}}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {path}")


def _display_common(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "run" in out.columns:
        out["Run"] = out["run"].map(RUN_NAMES).fillna(out["run"])
    if "baseline" in out.columns:
        out["Target source"] = out["baseline"].map(BASELINE_NAMES).fillna(out["baseline"])
    if "stressor" in out.columns:
        out["Stressor"] = out["stressor"].map(STRESSOR_NAMES).fillna(out["stressor"])
    if "failure_type" in out.columns:
        out["Failure type"] = out["failure_type"].map(FAILURE_NAMES).fillna(out["failure_type"])
    return out


def render_main_results(input_dir: Path, tables_dir: Path) -> None:
    df = _display_common(pd.read_csv(input_dir / "main_results_with_ci.csv"))
    df["Success rate (95% CI)"] = df.apply(lambda row: _rate_ci(row, "success_rate"), axis=1)
    df["Episodes"] = df["n"].astype(int)
    df["Seed blocks"] = df["seed_blocks"].astype(int)
    core_runs = ["Main v1", "Held-out seeds", "Visual/sensor bridge", "Hard L3 confirmation"]
    core_sources = ["Oracle target", "Box-center depth", "Crop-median depth", "Crop-top-surface"]
    core = df[df["Run"].isin(core_runs) & df["Target source"].isin(core_sources)].copy()
    core["Run"] = pd.Categorical(core["Run"], categories=core_runs, ordered=True)
    core["Target source"] = pd.Categorical(core["Target source"], categories=core_sources, ordered=True)
    pivot = (
        core.pivot_table(
            index="Target source",
            columns="Run",
            values="Success rate (95% CI)",
            aggfunc="first",
            observed=False,
        )
        .reset_index()
        .sort_values("Target source")
    )
    _write_table(
        pivot,
        tables_dir / "main_results_with_ci.tex",
        ["Target source", "Main v1", "Held-out seeds", "Visual/sensor bridge", "Hard L3 confirmation"],
        ["Target source", "Main v1", "Held-out seeds", "Visual/sensor bridge", "Hard L3 confirmation"],
        r"Main diagnostic success rates with 95\% seed-block bootstrap confidence intervals.",
        "tab:main-results-with-ci",
    )
    _write_table(
        df,
        tables_dir / "supplement" / "main_results_full_with_ci.tex",
        ["Run", "Target source", "Success rate (95% CI)", "Episodes", "Seed blocks"],
        ["Run", "Target source", "Success rate (95% CI)", "Episodes", "Seed blocks"],
        r"Full diagnostic success rates with 95\% seed-block bootstrap confidence intervals.",
        "tab:supp-main-results-full-with-ci",
    )


def render_oracle_gap(input_dir: Path, tables_dir: Path) -> None:
    df = _display_common(pd.read_csv(input_dir / "oracle_gap_with_ci.csv"))
    df["Oracle gap (95% CI)"] = df.apply(lambda row: _rate_ci(row, "oracle_gap"), axis=1)
    df["Episodes"] = df["n"].astype(int)
    df["Seed blocks"] = df["seed_blocks"].astype(int)
    _write_table(
        df,
        tables_dir / "supplement" / "oracle_gap_with_ci.tex",
        ["Run", "Target source", "Oracle gap (95% CI)", "Episodes", "Seed blocks"],
        ["Run", "Target source", "Oracle gap (95% CI)", "Episodes", "Seed blocks"],
        r"Oracle gaps with 95\% seed-block bootstrap confidence intervals.",
        "tab:supp-oracle-gap-with-ci",
    )


def render_oracle_gap_by_stressor(input_dir: Path, tables_dir: Path) -> None:
    df = _display_common(pd.read_csv(input_dir / "oracle_gap_by_stressor_with_ci.csv"))
    df["Oracle gap (95% CI)"] = df.apply(lambda row: _rate_ci(row, "oracle_gap"), axis=1)
    df["Seed blocks"] = df["seed_blocks"].astype(int)
    _write_table(
        df,
        tables_dir / "supplement" / "oracle_gap_by_stressor_with_ci.tex",
        ["Run", "Stressor", "Target source", "Oracle gap (95% CI)", "Seed blocks"],
        ["Run", "Stressor", "Target source", "Oracle gap (95% CI)", "Seed blocks"],
        r"Oracle gaps by stressor with 95\% seed-block bootstrap confidence intervals.",
        "tab:supp-oracle-gap-by-stressor-with-ci",
    )


def render_stressor_ranking(input_dir: Path, tables_dir: Path) -> None:
    df = _display_common(pd.read_csv(input_dir / "stressor_ranking_with_ci.csv"))
    df["Success rate (95% CI)"] = df.apply(lambda row: _rate_ci(row, "success_rate"), axis=1)
    df["Episodes"] = df["n"].astype(int)
    df["Seed blocks"] = df["seed_blocks"].astype(int)
    _write_table(
        df,
        tables_dir / "supplement" / "stressor_ranking_with_ci.tex",
        ["Run", "Stressor", "Success rate (95% CI)", "Episodes", "Seed blocks"],
        ["Run", "Stressor", "Success rate (95% CI)", "Episodes", "Seed blocks"],
        r"Stressor robustness ranking with 95\% seed-block bootstrap confidence intervals.",
        "tab:supp-stressor-ranking-with-ci",
    )


def render_failure_distribution(input_dir: Path, tables_dir: Path) -> None:
    df = _display_common(pd.read_csv(input_dir / "failure_distribution_with_ci.csv"))
    df["Fraction (95% CI)"] = df.apply(lambda row: _rate_ci(row, "fraction"), axis=1)
    df["Count"] = df["count"].astype(int)
    _write_table(
        df,
        tables_dir / "supplement" / "failure_distribution_with_ci.tex",
        ["Run", "Failure type", "Fraction (95% CI)", "Count"],
        ["Run", "Failure type", "Fraction (95% CI)", "Count"],
        r"Failure-type distribution with 95\% seed-block bootstrap confidence intervals.",
        "tab:supp-failure-distribution-with-ci",
    )


def render_threshold_sensitivity(input_dir: Path, tables_dir: Path) -> None:
    df = _display_common(pd.read_csv(input_dir / "threshold_sensitivity.csv"))
    pivot = (
        df.pivot_table(index=["Run", "Target source"], columns="threshold_m", values="success_rate", aggfunc="first")
        .reset_index()
        .sort_values(["Run", "Target source"])
    )
    for threshold in [0.04, 0.06, 0.08, 0.10]:
        pivot[f"SR@{threshold:.2f}m"] = pivot[threshold].map(lambda value: f"{value:.3f}")
    _write_table(
        pivot,
        tables_dir / "threshold_sensitivity.tex",
        ["Run", "Target source", "SR@0.04m", "SR@0.06m", "SR@0.08m", "SR@0.10m"],
        ["Run", "Target source", "0.04 m", "0.06 m", "0.08 m", "0.10 m"],
        "Threshold sensitivity of diagnostic target success recomputed from stored target-error values.",
        "tab:threshold-sensitivity",
        table_star=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Render IEEE Access LaTeX tables from generated CSV artifacts.")
    parser.add_argument("--input-dir", default="ieee_access_revision_20260520")
    parser.add_argument("--tables-dir", default="paper/ieee_access/tables")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    tables_dir = Path(args.tables_dir)
    render_main_results(input_dir, tables_dir)
    render_oracle_gap(input_dir, tables_dir)
    render_oracle_gap_by_stressor(input_dir, tables_dir)
    render_stressor_ranking(input_dir, tables_dir)
    render_failure_distribution(input_dir, tables_dir)
    render_threshold_sensitivity(input_dir, tables_dir)


if __name__ == "__main__":
    main()
