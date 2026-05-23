from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def _load_records(root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for path in root.rglob("records.jsonl"):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                row["source_file"] = str(path)
                rows.append(row)
    return pd.DataFrame(rows)


def _rate(series: pd.Series) -> float:
    if series.empty:
        return float("nan")
    return float(series.astype(bool).mean())


def _seed_block_ci(frame: pd.DataFrame, column: str, n_boot: int = 1000) -> tuple[float, float]:
    if frame.empty or "image_id" not in frame:
        return float("nan"), float("nan")
    rng = np.random.default_rng(20260522)
    blocks = frame.groupby(["scene_id", "image_id"], dropna=False)[column].mean().dropna().to_numpy(dtype=float)
    if len(blocks) == 0:
        return float("nan"), float("nan")
    samples = []
    for _ in range(n_boot):
        draw = rng.choice(blocks, size=len(blocks), replace=True)
        samples.append(float(np.mean(draw)))
    lo, hi = np.quantile(samples, [0.025, 0.975])
    return float(lo), float(hi)


def _group(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    rows = []
    for keys, group in df.groupby(cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = {col: key for col, key in zip(cols, keys)}
        row["episodes"] = int(len(group))
        row["success_rate"] = _rate(group["success"])
        row["success_ci_low"], row["success_ci_high"] = _seed_block_ci(group, "success")
        row["no_detection_rate"] = float((group["failure_type"] == "no_detection").mean())
        row["wrong_detection_rate"] = float((group["failure_type"] == "wrong_detection_selected").mean())
        row["depth_failure_rate"] = float(group["failure_type"].isin(["depth_invalid", "no_valid_depth_in_crop", "no_valid_depth_in_mask"]).mean())
        row["median_target_error_l2"] = float(pd.to_numeric(group["target_error_l2"], errors="coerce").median())
        row["mean_bbox_iou"] = float(pd.to_numeric(group["bbox_iou"], errors="coerce").mean())
        rows.append(row)
    return pd.DataFrame(rows).sort_values(cols).reset_index(drop=True)


def _threshold_table(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["detector", "target_source", "query_variant"]
    rows = []
    for keys, group in df.groupby(cols, dropna=False):
        row = {col: key for col, key in zip(cols, keys)}
        row["episodes"] = int(len(group))
        for cm in [4, 6, 8, 10]:
            col = f"success_at_{cm:02d}cm"
            row[col] = _rate(group[col]) if col in group else float("nan")
        rows.append(row)
    return pd.DataFrame(rows).sort_values(cols).reset_index(drop=True)


def _write_report(df: pd.DataFrame, out_dir: Path) -> None:
    lines = [
        "# YCB-V External RGB-D Probe Report",
        "",
        f"- Records: {len(df)}",
        f"- Scenes: {df['scene_id'].nunique() if 'scene_id' in df else 0}",
        f"- Frames: {df[['scene_id', 'image_id']].drop_duplicates().shape[0] if {'scene_id','image_id'}.issubset(df.columns) else 0}",
        f"- Object instances: {df[['scene_id', 'image_id', 'gt_index']].drop_duplicates().shape[0] if {'scene_id','image_id','gt_index'}.issubset(df.columns) else 0}",
        f"- Overall success@8cm: {_rate(df['success']):.4f}" if "success" in df else "- Overall success@8cm: n/a",
        "",
        "## Paper-Use Interpretation",
        "",
        "This probe uses real YCB-V/BOP RGB-D frames with ground-truth visible masks/boxes. "
        "Oracle-mask rows isolate RGB-D lifting against a visible-surface median reference. "
        "Oracle-2D-box rows test whether simple target-source heuristics reproduce that reference. "
        "GroundingDINO rows combine open-vocabulary 2D localization with the same lifting methods.",
        "",
    ]
    out_dir.joinpath("report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    root = Path(args.input)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = _load_records(root)
    df.to_csv(out_dir / "episode_index.csv", index=False)
    if df.empty:
        raise SystemExit(f"No records found under {root}")
    _group(df, ["detector", "target_source", "query_variant"]).to_csv(out_dir / "summary_by_detector_source.csv", index=False)
    _group(df, ["object_name", "detector", "target_source"]).to_csv(out_dir / "summary_by_object.csv", index=False)
    _group(df, ["scene_id", "detector", "target_source"]).to_csv(out_dir / "summary_by_scene.csv", index=False)
    _threshold_table(df).to_csv(out_dir / "threshold_sensitivity.csv", index=False)
    _write_report(df, out_dir)
    print(f"Wrote YCB-V external RGB-D analysis under {out_dir}")


if __name__ == "__main__":
    main()
