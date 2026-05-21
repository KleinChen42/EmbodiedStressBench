from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


GENERIC_LABELS = {"", "object", "target object", "requested object", "thing", "item"}


def _load_records(root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    names: list[str] = []
    for path in root.rglob("*.json"):
        if path.name == "experiment_config_snapshot.json":
            continue
        names.append(path.name)
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            rows.append(
                {
                    "source_file": str(path),
                    "status": "json_read_error",
                    "failure_type": "json_read_error",
                    "error_message": str(exc),
                }
            )
            continue
        pred = item.get("prediction") or {}
        debug = pred.get("debug_info") or {}
        stress = item.get("stress_info") or {}
        params = stress.get("params") or {}
        bbox = debug.get("bbox")
        target_bbox = params.get("target_bbox_xyxy")
        center_error_2d = None
        if isinstance(bbox, list) and len(bbox) >= 4 and isinstance(target_bbox, list) and len(target_bbox) >= 4:
            bx = (float(bbox[0]) + float(bbox[2])) / 2.0
            by = (float(bbox[1]) + float(bbox[3])) / 2.0
            tx = (float(target_bbox[0]) + float(target_bbox[2])) / 2.0
            ty = (float(target_bbox[1]) + float(target_bbox[3])) / 2.0
            center_error_2d = float(np.hypot(bx - tx, by - ty))
        rows.append(
            {
                "source_file": str(path),
                "filename": path.name,
                "status": item.get("status"),
                "task": item.get("task"),
                "baseline": item.get("baseline"),
                "query_variant": item.get("query_variant") or "default",
                "query_template": item.get("query_template"),
                "detector": _detector(item.get("baseline")),
                "target_source": _target_source(item.get("baseline")),
                "stressor": item.get("stressor"),
                "level": item.get("level"),
                "seed": item.get("seed"),
                "success": bool(item.get("success")),
                "failure_type": item.get("failure_type") or "success",
                "target_error_l2": item.get("target_error_l2"),
                "query_used": item.get("query_used"),
                "selected_detection_label": debug.get("selected_detection_label"),
                "selected_detection_is_target": debug.get("selected_detection_is_target"),
                "selection_failure_reason": debug.get("selection_failure_reason"),
                "grounding_dino_target_iou": debug.get("grounding_dino_target_iou"),
                "grounding_dino_score": debug.get("grounding_dino_score"),
                "has_grounding_dino_debug": all(
                    key in debug for key in ["grounding_dino_target_iou", "grounding_dino_score"]
                ),
                "num_detections": item.get("num_detections"),
                "num_candidate_detections": debug.get("num_candidate_detections"),
                "center_error_2d_px": center_error_2d,
            }
        )
    df = pd.DataFrame(rows)
    duplicates = {name: count for name, count in Counter(names).items() if count > 1}
    df.attrs["duplicate_count"] = sum(count - 1 for count in duplicates.values())
    df.attrs["duplicate_names"] = duplicates
    return df


def _detector(baseline: Any) -> str:
    name = str(baseline)
    if name == "oracle_target":
        return "oracle"
    if name.endswith("_grounding_dino"):
        return "GroundingDINO"
    if name.endswith("_first_detection"):
        return "first detection"
    if name.endswith("_query_aware"):
        return "metadata query-aware"
    return "metadata query-aware"


def _target_source(baseline: Any) -> str:
    name = str(baseline)
    for suffix in ["_grounding_dino", "_first_detection", "_query_aware", "_clip_rerank"]:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name


def _rate(value: pd.Series) -> float:
    return float(value.astype(bool).mean()) if len(value) else float("nan")


def _seed_block_ci(frame: pd.DataFrame, column: str, rng: np.random.Generator, n_boot: int = 2000) -> tuple[float, float]:
    if frame.empty or "seed" not in frame:
        return (float("nan"), float("nan"))
    values = (
        frame.groupby("seed", dropna=False)[column]
        .mean()
        .dropna()
        .astype(float)
        .to_numpy()
    )
    if len(values) == 0:
        return (float("nan"), float("nan"))
    if len(values) == 1:
        return (float(values[0]), float(values[0]))
    samples = rng.choice(values, size=(n_boot, len(values)), replace=True).mean(axis=1)
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return (float(lo), float(hi))


def _write_group(df: pd.DataFrame, keys: list[str], out: Path) -> None:
    work = df.copy()
    work["no_detection_flag"] = work["failure_type"].eq("no_detection").astype(float)
    work["wrong_detection_flag"] = work["failure_type"].eq("wrong_detection_selected").astype(float)
    grouped = (
        work.groupby(keys, dropna=False)
        .agg(
            episodes=("success", "size"),
            success_rate=("success", "mean"),
            mean_target_error_l2=("target_error_l2", "mean"),
            no_detection_rate=("no_detection_flag", "mean"),
            runner_exception_rate=("failure_type", lambda s: float((s == "runner_exception").mean())),
            wrong_detection_rate=("wrong_detection_flag", "mean"),
            iou_mean=("grounding_dino_target_iou", "mean"),
            iou_hit_010=("grounding_dino_target_iou", lambda s: float((pd.to_numeric(s, errors="coerce") >= 0.10).mean())),
            iou_hit_025=("grounding_dino_target_iou", lambda s: float((pd.to_numeric(s, errors="coerce") >= 0.25).mean())),
            iou_hit_050=("grounding_dino_target_iou", lambda s: float((pd.to_numeric(s, errors="coerce") >= 0.50).mean())),
            iou_hit_075=("grounding_dino_target_iou", lambda s: float((pd.to_numeric(s, errors="coerce") >= 0.75).mean())),
        )
        .reset_index()
    )
    rng = np.random.default_rng(20260521)
    ci_rows: list[dict[str, Any]] = []
    for _, row in grouped.iterrows():
        mask = pd.Series(True, index=work.index)
        for key in keys:
            value = row[key]
            if pd.isna(value):
                mask &= work[key].isna()
            else:
                mask &= work[key].eq(value)
        sub = work[mask]
        success_lo, success_hi = _seed_block_ci(sub.assign(success_float=sub["success"].astype(float)), "success_float", rng)
        no_lo, no_hi = _seed_block_ci(sub, "no_detection_flag", rng)
        wrong_lo, wrong_hi = _seed_block_ci(sub, "wrong_detection_flag", rng)
        ci_rows.append(
            {
                **{key: row[key] for key in keys},
                "success_ci_low": success_lo,
                "success_ci_high": success_hi,
                "no_detection_ci_low": no_lo,
                "no_detection_ci_high": no_hi,
                "wrong_detection_ci_low": wrong_lo,
                "wrong_detection_ci_high": wrong_hi,
            }
        )
    if ci_rows:
        grouped = grouped.merge(pd.DataFrame(ci_rows), on=keys, how="left")
    grouped.to_csv(out, index=False)


def _write_paired_detector_differences(df: pd.DataFrame, out: Path) -> None:
    rows: list[dict[str, Any]] = []
    pairs = [
        ("metadata query-aware", "GroundingDINO"),
        ("first detection", "GroundingDINO"),
        ("metadata query-aware", "first detection"),
    ]
    keys = ["task", "stressor", "level", "seed", "target_source"]
    pivot = (
        df[df["detector"].isin({p for pair in pairs for p in pair})]
        .pivot_table(index=keys, columns="detector", values="success", aggfunc="mean")
        .reset_index()
    )
    rng = np.random.default_rng(20260521)
    for target_source, group in pivot.groupby("target_source", dropna=False):
        for left, right in pairs:
            if left not in group or right not in group:
                continue
            diff = (group[left] - group[right]).dropna()
            if diff.empty:
                continue
            by_seed = (
                group.assign(diff=group[left] - group[right])
                .groupby("seed", dropna=False)["diff"]
                .mean()
                .dropna()
                .to_numpy()
            )
            if len(by_seed) > 1:
                boot = rng.choice(by_seed, size=(2000, len(by_seed)), replace=True).mean(axis=1)
                lo, hi = np.percentile(boot, [2.5, 97.5])
            elif len(by_seed) == 1:
                lo = hi = by_seed[0]
            else:
                lo = hi = float("nan")
            rows.append(
                {
                    "target_source": target_source,
                    "left_detector": left,
                    "right_detector": right,
                    "success_rate_difference": float(diff.mean()),
                    "ci_low": float(lo),
                    "ci_high": float(hi),
                    "paired_blocks": int(len(diff)),
                    "seed_blocks": int(len(by_seed)),
                }
            )
    pd.DataFrame(rows).to_csv(out, index=False)


def _bridge_summary(df: pd.DataFrame, expected: int) -> pd.DataFrame:
    runner = int(((df["failure_type"] == "runner_exception") | (df.get("status") == "error")).sum()) if not df.empty else 0
    no_detection = int((df["failure_type"] == "no_detection").sum()) if not df.empty else 0
    gdino = df[df["detector"] == "GroundingDINO"] if not df.empty else df
    generic = df[
        df["task"].isin(["PickSingleYCB", "PickClutterYCB"])
        & df["selected_detection_label"].fillna("").astype(str).str.lower().isin(GENERIC_LABELS)
    ] if not df.empty else df
    return pd.DataFrame(
        [
            {
                "expected_episodes": int(expected),
                "completed_episodes": int(len(df)),
                "complete": bool(len(df) >= expected),
                "duplicate_result_count": int(df.attrs.get("duplicate_count", 0)),
                "runner_exception_count": runner,
                "runner_exception_rate": runner / len(df) if len(df) else float("nan"),
                "no_detection_count": no_detection,
                "no_detection_rate": no_detection / len(df) if len(df) else float("nan"),
                "grounding_dino_rows": int(len(gdino)),
                "grounding_dino_rows_with_debug": int(gdino["has_grounding_dino_debug"].sum()) if len(gdino) else 0,
                "ycb_or_clutter_generic_selected_label_rows": int(len(generic)),
                "overall_success_rate": _rate(df["success"]) if len(df) else float("nan"),
            }
        ]
    )


def _write_iou_sweep(df: pd.DataFrame, out: Path) -> None:
    rows = []
    gdino = df[df["detector"] == "GroundingDINO"].copy()
    iou = pd.to_numeric(gdino["grounding_dino_target_iou"], errors="coerce")
    for threshold in [0.10, 0.25, 0.50, 0.75]:
        hit = iou >= threshold
        rows.append(
            {
                "iou_threshold": threshold,
                "hit_rate": float(hit.mean()) if len(hit) else float("nan"),
                "success_when_hit": float(gdino.loc[hit, "success"].mean()) if hit.any() else float("nan"),
                "success_when_miss": float(gdino.loc[~hit, "success"].mean()) if (~hit).any() else float("nan"),
                "episodes": int(len(gdino)),
            }
        )
    pd.DataFrame(rows).to_csv(out, index=False)


def _write_audit(df: pd.DataFrame, summary: pd.DataFrame, out: Path, input_root: Path) -> None:
    row = summary.iloc[0].to_dict()
    duplicate_names = df.attrs.get("duplicate_names", {})
    generic_examples = df[
        df["task"].isin(["PickSingleYCB", "PickClutterYCB"])
        & df["selected_detection_label"].fillna("").astype(str).str.lower().isin(GENERIC_LABELS)
    ].head(10)
    lines = [
        "# Open-Vocab Bridge v2 Audit",
        "",
        f"Input root: `{input_root}`",
        "",
        "## Counts",
        "",
        f"- Expected episodes: {row['expected_episodes']}",
        f"- Completed episodes: {row['completed_episodes']}",
        f"- Duplicate result count: {row['duplicate_result_count']}",
        f"- Runner exceptions: {row['runner_exception_count']}",
        f"- No-detection count: {row['no_detection_count']} ({row['no_detection_rate']:.4f})",
        f"- Overall success rate: {row['overall_success_rate']:.4f}",
        "",
        "## Detector Debug",
        "",
        f"- GroundingDINO rows: {row['grounding_dino_rows']}",
        f"- GroundingDINO rows with IoU/score debug: {row['grounding_dino_rows_with_debug']}",
        "",
        "## YCB/Clutter Label Check",
        "",
        f"- Generic selected-label rows: {row['ycb_or_clutter_generic_selected_label_rows']}",
    ]
    if len(generic_examples):
        lines.append("- Example generic-label rows:")
        for _, item in generic_examples.iterrows():
            lines.append(
                f"  - {item['task']} {item['baseline']} {item['stressor']} "
                f"L{item['level']} seed {item['seed']} label={item['selected_detection_label']}"
            )
    if duplicate_names:
        lines.extend(["", "## Duplicate Filenames", ""])
        for name, count in sorted(duplicate_names.items()):
            lines.append(f"- `{name}`: {count}")
    lines.extend(
        [
            "",
            "## Paper-Use Rule",
            "",
            "Use this run for paper claims only if completed episodes reach the expected count, duplicate count is zero, runner exceptions are zero, and detector debug fields are present for GroundingDINO rows.",
            "",
        ]
    )
    out.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--expected", type=int, default=13500)
    args = parser.parse_args()

    input_root = Path(args.input)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = _load_records(input_root)
    df.to_csv(out_dir / "open_vocab_bridge_v2_episode_index.csv", index=False)
    summary = _bridge_summary(df, args.expected)
    summary.to_csv(out_dir / "open_vocab_bridge_v2_summary.csv", index=False)
    _write_group(df, ["task"], out_dir / "open_vocab_bridge_v2_by_task.csv")
    _write_group(df, ["stressor", "level"], out_dir / "open_vocab_bridge_v2_by_stressor.csv")
    _write_group(
        df,
        ["detector", "target_source"],
        out_dir / "open_vocab_bridge_v2_by_detector_target_source.csv",
    )
    if "query_variant" in df.columns and df["query_variant"].nunique(dropna=False) > 1:
        _write_group(
            df,
            ["query_variant", "query_template", "task", "detector", "target_source"],
            out_dir / "open_vocab_bridge_v2_by_query_variant.csv",
        )
    _write_iou_sweep(df, out_dir / "open_vocab_bridge_v2_iou_sweep.csv")
    _write_paired_detector_differences(df, out_dir / "open_vocab_bridge_v2_paired_detector_differences.csv")
    cols = [
        "task",
        "baseline",
        "stressor",
        "level",
        "seed",
        "success",
        "target_error_l2",
        "grounding_dino_target_iou",
        "center_error_2d_px",
        "source_file",
    ]
    df[df["detector"] == "GroundingDINO"][cols].to_csv(
        out_dir / "open_vocab_bridge_v2_2d_center_vs_3d_error.csv", index=False
    )
    _write_audit(df, summary, out_dir / "open_vocab_bridge_v2_audit.md", input_root)
    print(f"Wrote Bridge v2 audit artifacts under {out_dir}")


if __name__ == "__main__":
    main()
