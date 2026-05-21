from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
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
    "box_center_depth_first_detection": "Box-center + first detection",
    "crop_median_depth_first_detection": "Crop-median + first detection",
    "crop_trimmed_median_depth_first_detection": "Trimmed median + first detection",
    "box_center_depth_grounding_dino": "Box-center + GroundingDINO",
    "crop_median_depth_grounding_dino": "Crop-median + GroundingDINO",
    "crop_trimmed_median_depth_grounding_dino": "Trimmed median + GroundingDINO",
    "same_color_distractor": "same-color distractor",
    "same_shape_distractor": "same-shape distractor",
    "nearby_distractor": "nearby distractor",
    "partial_target_occlusion": "partial target occlusion",
    "depth_sparsity": "depth sparsity",
    "visual_occlusion": "visual occlusion",
    "execution_offset": "execution offset",
    "execution_offset_strong": "strong execution offset",
    "none": "clean",
}


def _display(value: Any) -> str:
    return DISPLAY.get(str(value), str(value).replace("_", " "))


def _read_records(roots: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for spec in roots:
        if "=" in spec:
            run_name, raw_path = spec.split("=", 1)
        else:
            raw_path = spec
            run_name = Path(raw_path).name
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
            stress = item.get("stress_info") or {}
            rows.append(
                {
                    "run": run_name,
                    "source_file": str(path),
                    "task": item.get("task"),
                    "baseline": item.get("baseline"),
                    "stressor": item.get("stressor"),
                    "level": item.get("level"),
                    "seed": item.get("seed"),
                    "success": bool(item.get("success")),
                    "failure_type": item.get("failure_type") or "success",
                    "target_error_l2": item.get("target_error_l2"),
                    "query_used": item.get("query_used"),
                    "bbox": debug.get("bbox"),
                    "pixel": debug.get("pixel"),
                    "depth": debug.get("depth"),
                    "num_valid": debug.get("num_valid"),
                    "selected_detection_label": debug.get("selected_detection_label"),
                    "selected_detection_is_target": debug.get("selected_detection_is_target"),
                    "selected_detection_distractor_type": debug.get("selected_detection_distractor_type"),
                    "grounding_dino_target_iou": debug.get("grounding_dino_target_iou"),
                    "grounding_dino_score": debug.get("grounding_dino_score"),
                    "selection_strategy": debug.get("selection_strategy"),
                    "selection_failure_reason": debug.get("selection_failure_reason"),
                    "stressor_params": stress.get("params"),
                }
            )
    return pd.DataFrame(rows)


def _first(df: pd.DataFrame, mask: pd.Series, sort_by: str | None = None, ascending: bool = True) -> pd.Series | None:
    subset = df[mask].copy()
    if subset.empty:
        return None
    if sort_by and sort_by in subset:
        subset = subset.sort_values(sort_by, ascending=ascending, na_position="last")
    return subset.iloc[0]


def _select_cases(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    cases: list[pd.Series] = []
    used: set[str] = set()

    def add(label: str, row: pd.Series | None) -> None:
        if row is None:
            return
        key = str(row.get("source_file"))
        if key in used:
            return
        row = row.copy()
        row["case_label"] = label
        cases.append(row)
        used.add(key)

    add(
        "Clean or level-0 success",
        _first(
            df,
            (df["success"])
            & (df["baseline"].astype(str).isin(["crop_median_depth", "box_center_depth", "oracle_target"]))
            & ((df["stressor"].astype(str) == "none") | (df["level"].astype(str) == "0")),
            sort_by="target_error_l2",
            ascending=True,
        ),
    )
    add(
        "Wrong detection selected",
        _first(
            df,
            (df["failure_type"].astype(str) == "wrong_detection_selected")
            | (df["selected_detection_is_target"].astype(str) == "False"),
            sort_by="target_error_l2",
            ascending=False,
        ),
    )
    add(
        "Depth/occlusion failure",
        _first(
            df,
            (~df["success"])
            & (
                df["failure_type"].astype(str).isin(["depth_invalid", "no_valid_depth_in_crop"])
                | df["stressor"].astype(str).isin(["depth_sparsity", "partial_target_occlusion", "visual_occlusion"])
            ),
            sort_by="target_error_l2",
            ascending=False,
        ),
    )
    add(
        "Large target displacement",
        _first(
            df,
            (~df["success"]) & (df["failure_type"].astype(str) == "target_error_too_large"),
            sort_by="target_error_l2",
            ascending=False,
        ),
    )
    iou = pd.to_numeric(df.get("grounding_dino_target_iou"), errors="coerce")
    add(
        "Low 2D IoU, valid 3D target",
        _first(
            df,
            df["success"]
            & df["baseline"].astype(str).str.contains("grounding_dino", na=False)
            & iou.notna()
            & (iou < 0.25),
            sort_by="grounding_dino_target_iou",
            ascending=True,
        ),
    )
    add(
        "Strong target-source failure",
        _first(
            df,
            (~df["success"]) & pd.to_numeric(df.get("target_error_l2"), errors="coerce").notna(),
            sort_by="target_error_l2",
            ascending=False,
        ),
    )

    return pd.DataFrame(cases)


def _parse_seq(value: Any) -> list[float] | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except Exception:
            return None
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        try:
            return [float(v) for v in value]
        except Exception:
            return None
    return None


def _draw_bbox_card(ax: plt.Axes, row: pd.Series) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("#f8fafc")
    for spine in ax.spines.values():
        spine.set_color("#cbd5e1")

    bbox = _parse_seq(row.get("bbox"))
    pixel = _parse_seq(row.get("pixel"))
    if bbox and len(bbox) >= 4:
        x1, y1, x2, y2 = bbox[:4]
        width = max(x2 + 20.0, 256.0)
        height = max(y2 + 20.0, 256.0)
        rx = x1 / width
        ry = 1.0 - y2 / height
        rw = max((x2 - x1) / width, 0.02)
        rh = max((y2 - y1) / height, 0.02)
        edge = "#16a34a" if bool(row.get("success")) else "#dc2626"
        ax.add_patch(Rectangle((rx, ry), rw, rh, fill=False, linewidth=2.0, edgecolor=edge))
        ax.text(rx, min(0.96, ry + rh + 0.03), "selected bbox", fontsize=7, color=edge)
        if pixel and len(pixel) >= 2:
            px = pixel[0] / width
            py = 1.0 - pixel[1] / height
            ax.scatter([px], [py], s=28, c="#0f172a", marker="x")
    else:
        ax.text(0.5, 0.57, "No bbox\nstored", ha="center", va="center", fontsize=9, color="#64748b")

    success = "success" if bool(row.get("success")) else "failure"
    error = row.get("target_error_l2")
    error_text = "n/a" if pd.isna(error) else f"{float(error):.3f} m"
    iou = row.get("grounding_dino_target_iou")
    iou_text = "" if pd.isna(iou) else f"\nIoU={float(iou):.3f}"
    label = row.get("case_label", "case")
    text = (
        f"{label}\n"
        f"{_display(row.get('task'))} | {_display(row.get('baseline'))}\n"
        f"{_display(row.get('stressor'))} L{row.get('level')} | seed {row.get('seed')}\n"
        f"{success}; error={error_text}{iou_text}\n"
        f"failure={_display(row.get('failure_type'))}"
    )
    ax.text(
        0.02,
        0.02,
        text,
        ha="left",
        va="bottom",
        fontsize=7.4,
        linespacing=1.22,
        bbox={"facecolor": "white", "edgecolor": "#e2e8f0", "boxstyle": "round,pad=0.25"},
    )


def _save_figure(cases: pd.DataFrame, figures_dir: Path) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    n = max(1, len(cases))
    cols = min(3, n)
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(3.25 * cols, 2.65 * rows), squeeze=False)
    for ax in axes.ravel():
        ax.axis("off")
    for ax, (_, row) in zip(axes.ravel(), cases.iterrows()):
        ax.axis("on")
        _draw_bbox_card(ax, row)
    fig.suptitle("Artifact-backed qualitative diagnostic cases", fontsize=12, weight="bold")
    fig.text(
        0.5,
        0.012,
        "Panels are generated from stored JSON debug fields; each source file is listed in the manifest.",
        ha="center",
        fontsize=8,
        color="#475569",
    )
    fig.tight_layout(rect=[0.0, 0.04, 1.0, 0.96])
    fig.savefig(figures_dir / "qualitative_failure_teaser.pdf", bbox_inches="tight")
    fig.savefig(figures_dir / "qualitative_failure_teaser.png", dpi=240, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--roots", nargs="+", required=True, help="Run roots as LABEL=PATH or PATH.")
    parser.add_argument("--output-dir", default="ieee_access_revision_20260520/qualitative")
    parser.add_argument("--figures-dir", default="paper/ieee_access/figures")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    fig_dir = Path(args.figures_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    records = _read_records(args.roots)
    records.to_csv(out_dir / "qualitative_episode_index.csv", index=False)
    cases = _select_cases(records)
    cases.to_csv(out_dir / "qualitative_case_manifest.csv", index=False)
    if cases.empty:
        raise SystemExit("No qualitative cases could be selected from the provided roots.")
    _save_figure(cases, fig_dir)
    print(f"Wrote {len(cases)} qualitative cases to {out_dir}")
    print(f"Wrote figure to {fig_dir / 'qualitative_failure_teaser.pdf'}")


if __name__ == "__main__":
    main()
