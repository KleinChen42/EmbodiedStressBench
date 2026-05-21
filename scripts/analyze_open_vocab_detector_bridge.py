from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


def _load_records(root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.json")):
        if path.name == "experiment_config_snapshot.json":
            continue
        item = json.loads(path.read_text(encoding="utf-8"))
        pred = item.get("prediction") or {}
        debug = pred.get("debug_info") or {}
        rows.append(
            {
                "path": str(path),
                "status": item.get("status"),
                "task": item.get("task"),
                "baseline": item.get("baseline"),
                "stressor": item.get("stressor"),
                "level": item.get("level"),
                "seed": item.get("seed"),
                "success": bool(item.get("success")),
                "failure_type": item.get("failure_type") or "success",
                "target_error_l2": item.get("target_error_l2"),
                "selection_strategy": debug.get("selection_strategy"),
                "selection_failure_reason": debug.get("selection_failure_reason"),
                "selected_detection_is_target": debug.get("selected_detection_is_target"),
                "grounding_dino_score": debug.get("grounding_dino_score"),
                "grounding_dino_target_iou": debug.get("grounding_dino_target_iou"),
            }
        )
    return pd.DataFrame(rows)


def _rate(series: pd.Series) -> float:
    if len(series) == 0:
        return float("nan")
    return float(series.mean())


def _summarize(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    rows = []
    for key, group in df.groupby(group_cols, dropna=False):
        if not isinstance(key, tuple):
            key = (key,)
        failure_counts = Counter(group["failure_type"])
        hit_values = group["selected_detection_is_target"].map(lambda value: bool(value) if pd.notna(value) else False)
        row = {
            "n": int(len(group)),
            "success_rate": _rate(group["success"].astype(float)),
            "mean_target_error_l2": float(group["target_error_l2"].dropna().mean()) if group["target_error_l2"].notna().any() else float("nan"),
            "detection_hit_rate": _rate(hit_values.astype(float)),
            "no_detection_rate": _rate((group["failure_type"] == "no_detection").astype(float)),
            "runner_exception_rate": _rate((group["failure_type"] == "runner_exception").astype(float)),
        }
        row.update(dict(zip(group_cols, key)))
        row["failure_counts"] = "; ".join(f"{name}:{count}" for name, count in sorted(failure_counts.items()))
        rows.append(row)
    return pd.DataFrame(rows)


DISPLAY_NAMES = {
    "baseline": {
        "box_center_depth_grounding_dino": "Box center + GroundingDINO",
        "box_center_depth_query_aware": "Box center + metadata selector",
        "crop_median_depth_grounding_dino": "Crop median + GroundingDINO",
        "crop_median_depth_query_aware": "Crop median + metadata selector",
        "crop_trimmed_median_depth_grounding_dino": "Trimmed median + GroundingDINO",
        "crop_trimmed_median_depth_query_aware": "Trimmed median + metadata selector",
        "crop_trimmed_median_depth_first_detection": "Trimmed median + first detection",
        "oracle_target": "Oracle target",
    },
    "stressor": {
        "depth_sparsity": "Depth sparsity",
        "partial_target_occlusion": "Partial target occlusion",
        "visual_occlusion": "Visual occlusion",
    },
}

COLUMN_NAMES = {
    "baseline_display": "Target source / detector",
    "stressor_display": "Stressor",
    "n": "Episodes",
    "success_rate": "Success rate",
    "mean_target_error_l2": "Mean error (m)",
    "detection_hit_rate": "IoU hit rate",
    "no_detection_rate": "No-detection rate",
    "runner_exception_rate": "Runner-exception rate",
}


def _add_display_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for column, mapping in DISPLAY_NAMES.items():
        if column in out.columns:
            out[f"{column}_display"] = out[column].map(mapping).fillna(out[column])
    return out


def _escape_tex(value: object) -> str:
    text = str(value)
    for src, dst in {"_": r"\_", "%": r"\%", "&": r"\&", "#": r"\#", "$": r"\$"}.items():
        text = text.replace(src, dst)
    return text


def _fmt(value: object) -> str:
    if pd.isna(value):
        return "--"
    if isinstance(value, float):
        return f"{value:.3f}"
    return _escape_tex(value)


def _write_tex(df: pd.DataFrame, path: Path, columns: list[str], caption: str, label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if len(columns) == 7:
        colspec = (
            r"@{}p{0.26\linewidth}p{0.07\linewidth}p{0.10\linewidth}"
            r"p{0.10\linewidth}p{0.09\linewidth}p{0.12\linewidth}"
            r"p{0.13\linewidth}@{}"
        )
    elif len(columns) == 6:
        colspec = (
            r"@{}p{0.28\linewidth}p{0.19\linewidth}p{0.07\linewidth}"
            r"p{0.10\linewidth}p{0.11\linewidth}p{0.13\linewidth}@{}"
        )
    else:
        colspec = "l" * len(columns)
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{2pt}",
        r"\begin{tabular}{" + colspec + "}",
        r"\hline",
        " & ".join(_escape_tex(COLUMN_NAMES.get(c, c)) for c in columns) + r" \\",
        r"\hline",
    ]
    for _, row in df.iterrows():
        lines.append(" & ".join(_fmt(row[c]) for c in columns) + r" \\")
    lines.extend([r"\hline", r"\end{tabular}", r"\end{table*}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize optional open-vocabulary detector bridge runs.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", default="ieee_access_revision_20260520/open_vocab_detector_bridge")
    parser.add_argument("--tables-dir", default="paper/ieee_access/tables/open_vocab_detector_bridge")
    args = parser.parse_args()

    root = Path(args.input)
    out_dir = Path(args.output_dir)
    tables_dir = Path(args.tables_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    df = _load_records(root)
    if df.empty:
        raise SystemExit(f"No result JSON files found under {root}")

    overall = _add_display_columns(_summarize(df, ["baseline"]).sort_values("baseline"))
    by_stressor = _add_display_columns(_summarize(df, ["baseline", "stressor"]).sort_values(["stressor", "baseline"]))
    by_level = _add_display_columns(_summarize(df, ["baseline", "stressor", "level"]).sort_values(["stressor", "level", "baseline"]))

    outputs = {
        "open_vocab_detector_bridge_summary": overall,
        "open_vocab_detector_bridge_by_stressor": by_stressor,
        "open_vocab_detector_bridge_by_level": by_level,
    }
    for name, table in outputs.items():
        csv_path = out_dir / f"{name}.csv"
        table.to_csv(csv_path, index=False)
        print(f"Wrote {csv_path}")

    summary_cols = [
        "baseline_display",
        "n",
        "success_rate",
        "mean_target_error_l2",
        "detection_hit_rate",
        "no_detection_rate",
        "runner_exception_rate",
    ]
    _write_tex(
        overall[summary_cols],
        tables_dir / "open_vocab_detector_bridge_summary.tex",
        summary_cols,
        "GroundingDINO bridge summary on the 1,200-episode open-vocabulary proof-of-concept.",
        "tab:open-vocab-detector-bridge",
    )
    _write_tex(
        by_stressor[["baseline_display", "stressor_display", "n", "success_rate", "detection_hit_rate", "no_detection_rate"]],
        tables_dir / "open_vocab_detector_bridge_by_stressor.tex",
        ["baseline_display", "stressor_display", "n", "success_rate", "detection_hit_rate", "no_detection_rate"],
        "GroundingDINO bridge by stressor.",
        "tab:open-vocab-detector-bridge-stressor",
    )
    print(f"Wrote {tables_dir / 'open_vocab_detector_bridge_summary.tex'}")
    print(f"Wrote {tables_dir / 'open_vocab_detector_bridge_by_stressor.tex'}")


if __name__ == "__main__":
    main()
