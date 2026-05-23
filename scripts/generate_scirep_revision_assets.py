from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle


DISPLAY = {
    "open_vocab_bridge_v2": "Detector-bridge sweep",
    "open_vocab_bridge_v2_ycb_clutter_heldout": "YCB/clutter held-out",
    "metadata query-aware": "Metadata query-aware",
    "first detection": "First detection",
    "GroundingDINO": "GroundingDINO",
    "grounding_dino": "GroundingDINO",
    "oracle": "Oracle",
    "oracle_2d_box": "Oracle 2D box",
    "oracle_mask": "Oracle mask",
    "first_gt_box": "First GT box",
    "box_center_depth": "Box-center depth",
    "crop_median_depth": "Crop-median depth",
    "crop_trimmed_median_depth": "Crop-trimmed median",
    "crop_top_surface": "Crop-top-surface",
    "mask_median_depth": "Mask median depth",
    "oracle_target": "Oracle target",
    "generic": "Generic",
    "object_label": "Object-label template",
    "category": "Category template",
    "label_phrase": "Label phrase",
    "true_name": "True name",
    "true_name_phrase": "True-name phrase",
}


def _display(value: str) -> str:
    return DISPLAY.get(str(value), str(value).replace("_", " "))


def _fmt_rate(value: float | str) -> str:
    try:
        return f"{100 * float(value):.1f}"
    except Exception:
        return "--"


def _fmt_rate_ci(value: float | str, low: float | str | None, high: float | str | None) -> str:
    main = _fmt_rate(value)
    try:
        if pd.isna(low) or pd.isna(high):
            return main
        return f"{main} [{100 * float(low):.1f}, {100 * float(high):.1f}]"
    except Exception:
        return main


def _seed_block_ci(frame: pd.DataFrame, column: str) -> tuple[float, float]:
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
    rng = np.random.default_rng(20260521)
    boot = rng.choice(values, size=(2000, len(values)), replace=True).mean(axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return (float(lo), float(hi))


def _group_bridge_episode_index(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    work["success"] = work["success"].astype(str).str.lower().isin(["true", "1", "yes"])
    work["no_detection_flag"] = work["failure_type"].astype(str).eq("no_detection").astype(float)
    work["wrong_detection_flag"] = work["failure_type"].astype(str).eq("wrong_detection_selected").astype(float)
    rows = []
    for keys, group in work.groupby(["detector", "target_source"], dropna=False):
        detector, target_source = keys
        success_lo, success_hi = _seed_block_ci(group.assign(success_float=group["success"].astype(float)), "success_float")
        no_lo, no_hi = _seed_block_ci(group, "no_detection_flag")
        wrong_lo, wrong_hi = _seed_block_ci(group, "wrong_detection_flag")
        iou = pd.to_numeric(group.get("grounding_dino_target_iou"), errors="coerce")
        rows.append(
            {
                "detector": detector,
                "target_source": target_source,
                "episodes": int(len(group)),
                "success_rate": float(group["success"].mean()),
                "mean_target_error_l2": pd.to_numeric(group.get("target_error_l2"), errors="coerce").mean(),
                "no_detection_rate": float(group["no_detection_flag"].mean()),
                "runner_exception_rate": float(group["failure_type"].astype(str).eq("runner_exception").mean()),
                "wrong_detection_rate": float(group["wrong_detection_flag"].mean()),
                "iou_mean": float(iou.mean()) if len(iou) else float("nan"),
                "iou_hit_010": float((iou >= 0.10).mean()) if len(iou) else float("nan"),
                "iou_hit_025": float((iou >= 0.25).mean()) if len(iou) else float("nan"),
                "iou_hit_050": float((iou >= 0.50).mean()) if len(iou) else float("nan"),
                "iou_hit_075": float((iou >= 0.75).mean()) if len(iou) else float("nan"),
                "success_ci_low": success_lo,
                "success_ci_high": success_hi,
                "no_detection_ci_low": no_lo,
                "no_detection_ci_high": no_hi,
                "wrong_detection_ci_low": wrong_lo,
                "wrong_detection_ci_high": wrong_hi,
            }
        )
    return pd.DataFrame(rows)


def _load_bridge(root: Path, name: str) -> pd.DataFrame:
    episode_path = root / name / "open_vocab_bridge_v2_episode_index.csv"
    if episode_path.exists():
        df = _group_bridge_episode_index(pd.read_csv(episode_path))
        df.insert(0, "run", name)
        return df
    path = root / name / "open_vocab_bridge_v2_by_detector_target_source.csv"
    df = pd.read_csv(path)
    df.insert(0, "run", name)
    return df


def _write_detector_table(df: pd.DataFrame, tables_dir: Path) -> None:
    focus = df[df["target_source"].isin(["box_center_depth", "crop_median_depth", "crop_trimmed_median_depth"])].copy()
    focus = focus[
        focus["detector"].isin(["metadata query-aware", "first detection", "GroundingDINO"])
    ].copy()
    focus["run_display"] = focus["run"].map(_display)
    focus["detector_display"] = focus["detector"].map(_display)
    focus["target_display"] = focus["target_source"].map(_display)
    csv_cols = [
        "run_display",
        "detector_display",
        "target_display",
        "episodes",
        "success_rate",
        "no_detection_rate",
        "wrong_detection_rate",
        "iou_hit_010",
        "iou_hit_025",
    ]
    for optional in [
        "success_ci_low",
        "success_ci_high",
        "no_detection_ci_low",
        "no_detection_ci_high",
        "wrong_detection_ci_low",
        "wrong_detection_ci_high",
    ]:
        if optional in focus:
            csv_cols.append(optional)
    focus[csv_cols].to_csv(tables_dir / "open_vocab_detector_transfer_summary.csv", index=False)

    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{Learned-detector bridge results for Scientific Reports. Rates are percentages. This table uses detector-valid rows with recorded GroundingDINO debug fields; the separate YCB/clutter query check is reported in Table~\ref{tab:scirep-query-ablation}.}",
        r"\label{tab:scirep-open-vocab-transfer}",
        r"\scriptsize",
        r"\begin{tabular}{llrrrr}",
        r"\toprule",
        r"Evidence set & Detector / target source & Episodes & Success (95\% CI) & No detection & Wrong detection \\",
        r"\midrule",
    ]
    for _, row in focus.iterrows():
        lines.append(
            f"{row['run_display']} & {row['detector_display']} / {row['target_display']} & "
            f"{int(row['episodes'])} & {_fmt_rate_ci(row['success_rate'], row.get('success_ci_low'), row.get('success_ci_high'))} & "
            f"{_fmt_rate(row['no_detection_rate'])} & {_fmt_rate(row['wrong_detection_rate'])} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""])
    (tables_dir / "open_vocab_detector_transfer_summary.tex").write_text("\n".join(lines), encoding="utf-8")


def _write_main_diagnostic_summary(ieee_dir: Path, tables_dir: Path, revision_dir: Path) -> None:
    main_path = ieee_dir / "main_results_with_ci.csv"
    gap_path = ieee_dir / "oracle_gap_with_ci.csv"
    if not main_path.exists() or not gap_path.exists():
        return
    main = pd.read_csv(main_path)
    gaps = pd.read_csv(gap_path)
    focus_sources = ["oracle_target", "box_center_depth", "crop_median_depth", "crop_top_surface"]
    run_success = ["Heldout", "HardL3Confirm"]
    rows = []
    for source in focus_sources:
        row: dict[str, object] = {"target_source": source, "target_source_display": _display(source)}
        for run in run_success:
            match = main[(main["run"] == run) & (main["baseline"] == source)]
            if not match.empty:
                item = match.iloc[0]
                row[f"{run}_success"] = item["success_rate"]
                row[f"{run}_ci_low"] = item["ci_low"]
                row[f"{run}_ci_high"] = item["ci_high"]
                row[f"{run}_n"] = item["n"]
        gap = gaps[(gaps["run"] == "Heldout") & (gaps["baseline"] == source)]
        if not gap.empty:
            item = gap.iloc[0]
            row["heldout_oracle_gap"] = item["oracle_gap"]
            row["heldout_oracle_gap_low"] = item["ci_low"]
            row["heldout_oracle_gap_high"] = item["ci_high"]
        elif source == "oracle_target":
            row["heldout_oracle_gap"] = 0.0
            row["heldout_oracle_gap_low"] = 0.0
            row["heldout_oracle_gap_high"] = 0.0
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(tables_dir / "main_diagnostic_summary.csv", index=False)
    out.to_csv(revision_dir / "main_diagnostic_summary.csv", index=False)

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Compact diagnostic success and oracle-gap summary. Success rates are shown as percentages with 95\% seed-block percentile bootstrap confidence intervals. The held-out extension contains 134,400 episodes over 300 seed blocks, and the hard-L3 confirmation contains 14,400 episodes. Held-out oracle gap is computed against the oracle target within the held-out seed extension.}",
        r"\label{tab:main-diagnostic-summary}",
        r"\footnotesize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"Target source & Held-out success & Held-out oracle gap & Hard-L3 success \\",
        r"\midrule",
    ]
    for _, row in out.iterrows():
        gap_text = (
            "Reference"
            if row["target_source"] == "oracle_target"
            else _fmt_rate_ci(row["heldout_oracle_gap"], row["heldout_oracle_gap_low"], row["heldout_oracle_gap_high"])
        )
        lines.append(
            f"{row['target_source_display']} & "
            f"{_fmt_rate_ci(row.get('Heldout_success'), row.get('Heldout_ci_low'), row.get('Heldout_ci_high'))} & "
            f"{gap_text} & "
            f"{_fmt_rate_ci(row.get('HardL3Confirm_success'), row.get('HardL3Confirm_ci_low'), row.get('HardL3Confirm_ci_high'))} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    (tables_dir / "main_diagnostic_summary.tex").write_text("\n".join(lines), encoding="utf-8")


def _write_target_threshold_tradeoff(ieee_dir: Path, figures_dir: Path, revision_dir: Path) -> None:
    path = ieee_dir / "threshold_sensitivity.csv"
    if not path.exists():
        return
    data = pd.read_csv(path)
    focus = data[
        data["run"].eq("Heldout")
        & data["baseline"].isin(["oracle_target", "box_center_depth", "crop_median_depth", "crop_top_surface"])
    ].copy()
    focus["baseline_display"] = focus["baseline"].map(_display)
    focus.to_csv(figures_dir / "target_source_threshold_tradeoff_source.csv", index=False)
    focus.to_csv(revision_dir / "target_source_threshold_tradeoff_source.csv", index=False)
    order = ["oracle_target", "box_center_depth", "crop_median_depth", "crop_top_surface"]
    colors = {
        "oracle_target": "#111827",
        "box_center_depth": "#2563eb",
        "crop_median_depth": "#059669",
        "crop_top_surface": "#dc2626",
    }
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    for baseline in order:
        group = focus[focus["baseline"].eq(baseline)].sort_values("threshold_m")
        if group.empty:
            continue
        ax.plot(
            group["threshold_m"] * 100,
            group["success_rate"] * 100,
            marker="o",
            linewidth=2.2,
            label=_display(baseline),
            color=colors.get(baseline),
        )
    ax.set_xlabel("Target-distance threshold (cm)")
    ax.set_ylabel("Diagnostic success (%)")
    ax.set_title("Precision--robustness tradeoff across target sources", fontsize=11, weight="bold")
    ax.set_ylim(0, 105)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(figures_dir / "target_source_threshold_tradeoff.pdf", bbox_inches="tight")
    fig.savefig(figures_dir / "target_source_threshold_tradeoff.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _write_low_iou_valid_summary(root: Path, query_root: Path, tables_dir: Path, revision_dir: Path) -> None:
    paths = [
        ("Detector-bridge sweep", root / "open_vocab_bridge_v2" / "open_vocab_bridge_v2_episode_index.csv"),
        ("YCB/clutter query audit", query_root / "open_vocab_bridge_v2_episode_index.csv"),
    ]
    rows = []
    for label, path in paths:
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if "grounding_dino_target_iou" not in df:
            continue
        gdino = df[df.get("detector", "").astype(str).eq("GroundingDINO")].copy()
        gdino["success_bool"] = gdino["success"].astype(str).str.lower().isin(["true", "1", "yes"])
        gdino["iou"] = pd.to_numeric(gdino["grounding_dino_target_iou"], errors="coerce")
        gdino = gdino[gdino["iou"].notna()]
        for threshold in [0.10, 0.25, 0.50]:
            subset = gdino[gdino["iou"] < threshold]
            rows.append(
                {
                    "evidence_set": label,
                    "iou_lt": threshold,
                    "episodes": int(len(subset)),
                    "success_rate": float(subset["success_bool"].mean()) if len(subset) else float("nan"),
                    "median_target_error_l2": float(pd.to_numeric(subset.get("target_error_l2"), errors="coerce").median()) if len(subset) else float("nan"),
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return
    out.to_csv(tables_dir / "low_iou_valid_3d_summary.csv", index=False)
    out.to_csv(revision_dir / "low_iou_valid_3d_summary.csv", index=False)
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Low-IoU but valid-3D summary for GroundingDINO rows with recorded IoU fields. Success is still evaluated by 3D target distance at the default 0.08 m threshold, so low 2D overlap can preserve valid 3D crop evidence in some cases.}",
        r"\label{tab:low-iou-valid-3d}",
        r"\footnotesize",
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"Evidence set & IoU bin & Episodes & 3D success \\",
        r"\midrule",
    ]
    for _, row in out.iterrows():
        lines.append(
            f"{row['evidence_set']} & IoU $<$ {float(row['iou_lt']):.2f} & {int(row['episodes'])} & {_fmt_rate(row['success_rate'])} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    (tables_dir / "low_iou_valid_3d_summary.tex").write_text("\n".join(lines), encoding="utf-8")


def _paired_seed_difference(
    df: pd.DataFrame,
    value_column: str,
    left_filter: dict[str, str],
    right_filter: dict[str, str],
    label: str,
) -> dict[str, object] | None:
    work = df.copy()
    for key, value in left_filter.items():
        if key not in work:
            return None
    left = work.copy()
    right = work.copy()
    for key, value in left_filter.items():
        left = left[left[key].astype(str).eq(str(value))]
    for key, value in right_filter.items():
        right = right[right[key].astype(str).eq(str(value))]
    if left.empty or right.empty or "seed" not in work:
        return None
    left_seed = left.groupby("seed")[value_column].mean()
    right_seed = right.groupby("seed")[value_column].mean()
    paired = pd.concat([left_seed, right_seed], axis=1, join="inner")
    if paired.empty:
        return None
    paired.columns = ["left", "right"]
    values = (paired["left"] - paired["right"]).astype(float).to_numpy()
    rng = np.random.default_rng(20260523)
    boot = rng.choice(values, size=(2000, len(values)), replace=True).mean(axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {
        "comparison": label,
        "estimate": float(values.mean()),
        "ci_low": float(lo),
        "ci_high": float(hi),
        "paired_blocks": int(len(values)),
        "unit": "seed",
    }


def _write_paired_effects(root: Path, query_root: Path, tables_dir: Path, revision_dir: Path) -> None:
    rows: list[dict[str, object]] = []
    bridge_path = root / "open_vocab_bridge_v2" / "open_vocab_bridge_v2_episode_index.csv"
    if bridge_path.exists():
        bridge = pd.read_csv(bridge_path)
        bridge["success_float"] = bridge["success"].astype(str).str.lower().isin(["true", "1", "yes"]).astype(float)
        rows.extend(
            item
            for item in [
                _paired_seed_difference(
                    bridge,
                    "success_float",
                    {"detector": "metadata query-aware", "target_source": "crop_median_depth"},
                    {"detector": "GroundingDINO", "target_source": "crop_median_depth"},
                    "Metadata query-aware minus GroundingDINO (crop-median, detector bridge)",
                ),
                _paired_seed_difference(
                    bridge,
                    "success_float",
                    {"detector": "metadata query-aware", "target_source": "crop_median_depth"},
                    {"detector": "first detection", "target_source": "crop_median_depth"},
                    "Metadata query-aware minus first detection (crop-median, detector bridge)",
                ),
            ]
            if item is not None
        )
    query_path = query_root / "open_vocab_bridge_v2_episode_index.csv"
    if query_path.exists():
        query = pd.read_csv(query_path)
        query["success_float"] = query["success"].astype(str).str.lower().isin(["true", "1", "yes"]).astype(float)
        rows.extend(
            item
            for item in [
                _paired_seed_difference(
                    query,
                    "success_float",
                    {"detector": "GroundingDINO", "query_variant": "true_name", "target_source": "crop_median_depth"},
                    {"detector": "GroundingDINO", "query_variant": "generic", "target_source": "crop_median_depth"},
                    "GroundingDINO true-name minus generic query (YCB/clutter audit)",
                ),
                _paired_seed_difference(
                    query,
                    "success_float",
                    {"detector": "GroundingDINO", "query_variant": "true_name_phrase", "target_source": "crop_median_depth"},
                    {"detector": "GroundingDINO", "query_variant": "generic", "target_source": "crop_median_depth"},
                    "GroundingDINO photo true-name minus generic query (YCB/clutter audit)",
                ),
            ]
            if item is not None
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return
    out.to_csv(tables_dir / "paired_effects_scirep.csv", index=False)
    out.to_csv(revision_dir / "paired_effects_scirep.csv", index=False)
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Seed-paired effect summaries for selected detector/selector comparisons. Effects are percentage-point differences in diagnostic success; intervals use 2,000 paired seed-block percentile bootstrap resamples.}",
        r"\label{tab:paired-effects-scirep}",
        r"\footnotesize",
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"Comparison & Effect & 95\% CI & Paired seeds \\",
        r"\midrule",
    ]
    for _, row in out.iterrows():
        lines.append(
            f"{row['comparison']} & {100 * float(row['estimate']):.1f} & "
            f"[{100 * float(row['ci_low']):.1f}, {100 * float(row['ci_high']):.1f}] & {int(row['paired_blocks'])} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    (tables_dir / "paired_effects_scirep.tex").write_text("\n".join(lines), encoding="utf-8")


def _write_external_stratification(ycbv_root: Path, tables_dir: Path, revision_dir: Path) -> None:
    object_path = ycbv_root / "summary_by_object.csv"
    scene_path = ycbv_root / "summary_by_scene.csv"
    if object_path.exists():
        obj = pd.read_csv(object_path)
        obj.to_csv(tables_dir / "external_rgbd_by_object.csv", index=False)
        obj.to_csv(revision_dir / "external_rgbd_by_object.csv", index=False)
        focus = obj[
            obj["detector"].isin(["oracle_mask", "oracle_2d_box", "grounding_dino"])
            & obj["target_source"].isin(["mask_median_depth", "crop_trimmed_median_depth"])
        ].copy()
        focus = focus.sort_values(["object_name", "detector", "target_source"]).head(12)
        lines = [
            r"\begin{table}[t]",
            r"\centering",
            r"\caption{External YCB-V/BOP object-level stratification excerpt. The full object-level CSV is included in the source-data release.}",
            r"\label{tab:external-rgbd-by-object}",
            r"\scriptsize",
            r"\begin{tabular}{llrrr}",
            r"\toprule",
            r"Object & Detector/source & Episodes & Success & Median error (m) \\",
            r"\midrule",
        ]
        for _, row in focus.iterrows():
            lines.append(
                f"{row['object_name']} & {_display(row['detector'])}/{_display(row['target_source'])} & "
                f"{int(row['episodes'])} & {_fmt_rate(row['success_rate'])} & {float(row['median_target_error_l2']):.3f} \\\\"
            )
        lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
        (tables_dir / "external_rgbd_by_object.tex").write_text("\n".join(lines), encoding="utf-8")
    if scene_path.exists():
        scene = pd.read_csv(scene_path)
        scene.to_csv(tables_dir / "external_rgbd_by_scene.csv", index=False)
        scene.to_csv(revision_dir / "external_rgbd_by_scene.csv", index=False)
        focus = scene[
            scene["detector"].isin(["oracle_2d_box", "grounding_dino"])
            & scene["target_source"].eq("crop_trimmed_median_depth")
        ].copy()
        focus = focus.sort_values(["scene_id", "detector"]).head(12)
        lines = [
            r"\begin{table}[t]",
            r"\centering",
            r"\caption{External YCB-V/BOP scene-level stratification excerpt. The full scene-level CSV is included in the source-data release.}",
            r"\label{tab:external-rgbd-by-scene}",
            r"\scriptsize",
            r"\begin{tabular}{llrrr}",
            r"\toprule",
            r"Scene & Detector/source & Episodes & Success & Median error (m) \\",
            r"\midrule",
        ]
        for _, row in focus.iterrows():
            lines.append(
                f"{row['scene_id']} & {_display(row['detector'])}/{_display(row['target_source'])} & "
                f"{int(row['episodes'])} & {_fmt_rate(row['success_rate'])} & {float(row['median_target_error_l2']):.3f} \\\\"
            )
        lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
        (tables_dir / "external_rgbd_by_scene.tex").write_text("\n".join(lines), encoding="utf-8")


def _weighted_mean(group: pd.DataFrame, column: str) -> float:
    weights = pd.to_numeric(group["episodes"], errors="coerce").fillna(0.0)
    values = pd.to_numeric(group[column], errors="coerce")
    total = float(weights.sum())
    if total <= 0:
        return float("nan")
    return float((values * weights).sum() / total)


def _write_query_ablation_table(query_root: Path, tables_dir: Path, revision_dir: Path) -> None:
    by_query_path = query_root / "open_vocab_bridge_v2_by_query_variant.csv"
    episode_path = query_root / "open_vocab_bridge_v2_episode_index.csv"
    summary_path = query_root / "open_vocab_bridge_v2_summary.csv"
    if not by_query_path.exists() and not episode_path.exists():
        return
    if episode_path.exists():
        episodes_full = pd.read_csv(episode_path)
        work = episodes_full.copy()
        work["success"] = work["success"].astype(str).str.lower().isin(["true", "1", "yes"])
        work["wrong_detection_flag"] = work["failure_type"].astype(str).eq("wrong_detection_selected").astype(float)
        rows = []
        for keys, group in work.groupby(["query_variant", "query_template", "task", "detector", "target_source"], dropna=False):
            qv, qt, task, detector, target_source = keys
            success_lo, success_hi = _seed_block_ci(group.assign(success_float=group["success"].astype(float)), "success_float")
            wrong_lo, wrong_hi = _seed_block_ci(group, "wrong_detection_flag")
            iou = pd.to_numeric(group.get("grounding_dino_target_iou"), errors="coerce")
            rows.append(
                {
                    "query_variant": qv,
                    "query_template": qt,
                    "task": task,
                    "detector": detector,
                    "target_source": target_source,
                    "episodes": int(len(group)),
                    "success_rate": float(group["success"].mean()),
                    "success_ci_low": success_lo,
                    "success_ci_high": success_hi,
                    "wrong_detection_rate": float(group["wrong_detection_flag"].mean()),
                    "wrong_detection_ci_low": wrong_lo,
                    "wrong_detection_ci_high": wrong_hi,
                    "iou_hit_025": float((iou >= 0.25).mean()) if len(iou) else float("nan"),
                }
            )
        by_query = pd.DataFrame(rows)
    else:
        by_query = pd.read_csv(by_query_path)
    summary = pd.read_csv(summary_path).iloc[0] if summary_path.exists() else None
    focus = by_query[
        by_query["target_source"].eq("crop_median_depth")
        & by_query["detector"].isin(["GroundingDINO", "metadata query-aware"])
    ].copy()
    actual_queries: dict[str, str] = {}
    if episode_path.exists():
        episodes = pd.read_csv(episode_path, usecols=["query_variant", "query_used"])
        for variant, group in episodes.groupby("query_variant"):
            values = sorted({str(v) for v in group["query_used"].dropna().unique()})
            shown = "; ".join(values[:2])
            actual_queries[str(variant)] = shown + ("; ..." if len(values) > 2 else "")

    rows = []
    variant_order = ["generic", "object_label", "category", "label_phrase", "true_name", "true_name_phrase"]
    detector_order = ["GroundingDINO", "metadata query-aware"]
    for variant in variant_order:
        for detector in detector_order:
            group = focus[(focus["query_variant"] == variant) & (focus["detector"] == detector)]
            if group.empty:
                continue
            rows.append(
                {
                    "query_variant": variant,
                    "query_variant_display": _display(variant),
                    "query_template": str(group["query_template"].iloc[0]),
                    "actual_query": actual_queries.get(variant, ""),
                    "detector": detector,
                    "detector_display": _display(detector),
                    "episodes": int(pd.to_numeric(group["episodes"], errors="coerce").sum()),
                    "success_rate": _weighted_mean(group, "success_rate"),
                    "success_ci_low": _weighted_mean(group, "success_ci_low") if "success_ci_low" in group else float("nan"),
                    "success_ci_high": _weighted_mean(group, "success_ci_high") if "success_ci_high" in group else float("nan"),
                    "wrong_detection_rate": _weighted_mean(group, "wrong_detection_rate"),
                    "wrong_detection_ci_low": _weighted_mean(group, "wrong_detection_ci_low") if "wrong_detection_ci_low" in group else float("nan"),
                    "wrong_detection_ci_high": _weighted_mean(group, "wrong_detection_ci_high") if "wrong_detection_ci_high" in group else float("nan"),
                    "iou_hit_025": _weighted_mean(group, "iou_hit_025"),
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(tables_dir / "query_ablation_summary.csv", index=False)
    out.to_csv(revision_dir / "query_ablation_summary.csv", index=False)

    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{GroundingDINO query-ablation on YCB/clutter. Rates are percentages for crop-median target lifting. True-name rows are included only when the deep identity probe resolves non-generic YCB object names; otherwise the table should be interpreted as an adapter-label/query-mismatch audit.}",
        r"\label{tab:scirep-query-ablation}",
        r"\scriptsize",
        r"\begin{tabular}{lllrrrr}",
        r"\toprule",
        r"Query variant & Actual query & Detector & Episodes & Success (95\% CI) & Wrong detection & IoU@0.25 \\",
        r"\midrule",
    ]
    for _, row in out.iterrows():
        lines.append(
            f"{row['query_variant_display']} & {row['actual_query']} & {row['detector_display']} & "
            f"{int(row['episodes'])} & {_fmt_rate_ci(row['success_rate'], row.get('success_ci_low'), row.get('success_ci_high'))} & "
            f"{_fmt_rate(row['wrong_detection_rate'])} & {_fmt_rate(row['iou_hit_025'])} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""])
    (tables_dir / "query_ablation_summary.tex").write_text("\n".join(lines), encoding="utf-8")

    if summary is not None:
        audit = f"""# Scientific Reports Query-Ablation Summary

Input root: `{query_root}`

- Expected episodes: {int(summary['expected_episodes'])}
- Completed episodes: {int(summary['completed_episodes'])}
- Duplicate result count: {int(summary['duplicate_result_count'])}
- Runner exceptions: {int(summary['runner_exception_count'])}
- GroundingDINO rows with debug fields: {int(summary['grounding_dino_rows_with_debug'])}/{int(summary['grounding_dino_rows'])}
- Overall success rate: {float(summary['overall_success_rate']):.4f}

## Interpretation

The ablation audits whether generic prompts, resolved true names, or true-name
phrases change the YCB/clutter detector bridge. If GroundingDINO remains at
high no-detection or wrong-detection rates, the paper should describe this as a
detector-query/domain and adapter-label limitation, not as a detector leaderboard
or a broad claim about all YCB recognition.
"""
        (revision_dir / "query_ablation_audit.md").write_text(audit, encoding="utf-8")


def _write_closed_loop_table(root: Path, tables_dir: Path) -> None:
    summary = pd.read_csv(root / "closed_loop_sanity_smoke" / "closed_loop_sanity_summary.csv").iloc[0]
    by_task = pd.read_csv(root / "closed_loop_sanity_smoke" / "closed_loop_sanity_by_task.csv")
    gate = pd.read_csv(root / "closed_loop_sanity_smoke" / "closed_loop_oracle_gate_by_task.csv")
    by_task.to_csv(tables_dir / "closed_loop_smoke_by_task.csv", index=False)
    gate.to_csv(tables_dir / "closed_loop_oracle_gate_by_task.csv", index=False)
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Closed-loop sanity smoke outcome. The scripted executor is not used for positive claims because oracle task success is zero despite zero runner exceptions.}",
        r"\label{tab:scirep-closed-loop-smoke}",
        r"\scriptsize",
        r"\begin{tabular}{lrr}",
        r"\toprule",
        r"Metric & Value & Paper use \\",
        r"\midrule",
        f"Completed episodes & {int(summary['completed_episodes'])}/{int(summary['expected_episodes'])} & audit only \\\\",
        f"Runner exceptions & {int(summary['runner_exception_count'])} & pass \\\\",
        f"Diagnostic success & {_fmt_rate(summary['diagnostic_success_rate'])} & target metric only \\\\",
        f"Task success & {_fmt_rate(summary['task_success_rate'])} & scope boundary \\\\",
        f"Oracle task success & {_fmt_rate(summary['oracle_task_success_rate'])} & gate failed \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ]
    (tables_dir / "closed_loop_smoke_outcome.tex").write_text("\n".join(lines), encoding="utf-8")


def _write_closed_loop_v2_table(tables_dir: Path) -> None:
    root = Path("outputs/scirep_closed_loop_oracle_gate_audit_200_20260521")
    fallback_root = Path("outputs/scirep_closed_loop_oracle_calibration_v2_20260521/smoke")
    title = "Scripted execution oracle-gate audit"
    if not (root / "closed_loop_sanity_summary.csv").exists():
        root = fallback_root
        title = "Closed-loop oracle calibration v2 gate"
    if not (root / "closed_loop_sanity_summary.csv").exists():
        return
    summary = pd.read_csv(root / "closed_loop_sanity_summary.csv").iloc[0]
    gate = pd.read_csv(root / "closed_loop_oracle_gate_by_task.csv")
    gate.to_csv(tables_dir / "closed_loop_oracle_calibration_v2_gate.csv", index=False)
    rows = []
    for _, row in gate.iterrows():
        rows.append(
            (
                row["task"],
                int(row["oracle_episodes"]),
                100 * float(row["oracle_task_success_rate"]),
                100 * float(row.get("oracle_task_success_ci_low", row["oracle_task_success_rate"])),
                100 * float(row.get("oracle_task_success_ci_high", row["oracle_task_success_rate"])),
                str(row.get("dominant_failure_type", "n/a")).replace("_", " "),
            )
        )
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        rf"\caption{{{title}. The oracle scripted executor remains below the pre-registered task-success thresholds, so no positive execution-calibration claim is made. Wilson 95\% confidence intervals are reported for task success.}}",
        r"\label{tab:closed-loop-v2-gate}",
        r"\scriptsize",
        r"\begin{tabular}{lrrl}",
        r"\toprule",
        r"Task & Episodes & Task success (95\% CI) & Dominant failure \\",
        r"\midrule",
    ]
    for task, episodes, success, lo, hi, failure in rows:
        lines.append(f"{task} & {episodes} & {success:.1f} [{lo:.1f}, {hi:.1f}] & {failure} \\\\")
    lines.extend(
        [
            r"\midrule",
            f"Total & {int(summary['completed_episodes'])} & {100*float(summary['oracle_task_success_rate']):.1f} & gate failed \\\\",
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
            "",
        ]
    )
    (tables_dir / "closed_loop_oracle_calibration_v2_gate.tex").write_text("\n".join(lines), encoding="utf-8")


def _write_target_name_probe_table(tables_dir: Path, revision_dir: Path) -> None:
    deep_summary = Path("outputs/ycb_target_identity_deep_probe_20260521_r4/target_identity_deep_probe_summary.csv")
    if deep_summary.exists():
        raw = pd.read_csv(deep_summary)
        out = pd.DataFrame(
            {
                "task": raw["task"],
                "probe_rows": raw["probe_rows"],
                "non_generic_target_label_rows": raw["resolved_object_name_rows"],
                "non_generic_debug_rows": raw["resolved_object_name_rows"],
                "most_common_target_label": raw["unique_resolved_names"],
                "name_examples": raw["unique_resolved_names"].map(
                    lambda s: ", ".join(str(s).split(", ")[:4]) + ("; ..." if len(str(s).split(", ")) > 4 else "")
                ),
                "true_name_ablation_allowed": raw["true_name_ablation_allowed"],
            }
        )
        out.to_csv(tables_dir / "target_name_probe_summary.csv", index=False)
        out.to_csv(revision_dir / "target_name_probe_summary.csv", index=False)
        lines = [
            r"\begin{table}[t]",
            r"\centering",
            r"\caption{YCB/clutter object-name resolution audit. A true object-name prompt ablation is claimable only when non-generic names are resolved from the simulator adapter.}",
            r"\label{tab:target-name-probe}",
            r"\scriptsize",
            r"\begin{tabular}{lrrl}",
            r"\toprule",
            r"Task & Rows & Resolved names & Example names \\",
            r"\midrule",
        ]
        for _, row in out.iterrows():
            lines.append(
                f"{row['task']} & {int(row['probe_rows'])} & {int(row['non_generic_target_label_rows'])} & "
                f"{row['name_examples']} \\\\"
            )
        lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
        (tables_dir / "target_name_probe_summary.tex").write_text("\n".join(lines), encoding="utf-8")
        return

    path = Path("outputs/ycb_true_name_probe_20260521/target_name_probe.csv")
    if not path.exists():
        return
    df = pd.read_csv(path)
    rows = []
    for task, group in df.groupby("task", dropna=False):
        rows.append(
            {
                "task": task,
                "probe_rows": int(len(group)),
                "non_generic_target_label_rows": int((group["target_label_is_generic"] == False).sum()),  # noqa: E712
                "non_generic_debug_rows": int(
                    (pd.to_numeric(group["non_generic_debug_count"], errors="coerce").fillna(0) > 0).sum()
                ),
                "most_common_target_label": str(group["target_label"].mode().iloc[0]) if len(group) else "",
                "true_name_ablation_allowed": False,
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(tables_dir / "target_name_probe_summary.csv", index=False)
    out.to_csv(revision_dir / "target_name_probe_summary.csv", index=False)
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{YCB/clutter target-name probe. This historical adapter check records whether simulator metadata exposed object-specific labels; final query-sensitivity claims use the resolved-name ablation and external YCB-V/BOP probe.}",
        r"\label{tab:target-name-probe}",
        r"\scriptsize",
        r"\begin{tabular}{lrrrl}",
        r"\toprule",
        r"Task & Rows & Non-generic labels & Debug rows & Common label \\",
        r"\midrule",
    ]
    for _, row in out.iterrows():
        lines.append(
            f"{row['task']} & {int(row['probe_rows'])} & {int(row['non_generic_target_label_rows'])} & "
            f"{int(row['non_generic_debug_rows'])} & {row['most_common_target_label']} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    (tables_dir / "target_name_probe_summary.tex").write_text("\n".join(lines), encoding="utf-8")


def _write_detector_figure(df: pd.DataFrame, figures_dir: Path) -> None:
    focus = df[df["target_source"].isin(["crop_median_depth", "crop_trimmed_median_depth"])].copy()
    focus = focus[focus["detector"].isin(["metadata query-aware", "first detection", "GroundingDINO"])].copy()
    # crop_median and crop_trimmed are identical in current runs; keep crop_median for readability.
    focus = focus[focus["target_source"] == "crop_median_depth"]
    detectors = ["metadata query-aware", "first detection", "GroundingDINO"]
    preferred_runs = ["open_vocab_bridge_v2", "open_vocab_bridge_v2_ycb_clutter_heldout"]
    runs = [run for run in preferred_runs if run in set(focus["run"].astype(str))]
    source_cols = [
        "run",
        "detector",
        "target_source",
        "success_rate",
        "success_ci_low",
        "success_ci_high",
        "no_detection_rate",
        "no_detection_ci_low",
        "no_detection_ci_high",
        "wrong_detection_rate",
        "wrong_detection_ci_low",
        "wrong_detection_ci_high",
    ]
    focus[[c for c in source_cols if c in focus]].to_csv(
        figures_dir / "open_vocab_detector_transfer_combined_source.csv",
        index=False,
    )
    metric_specs = [
        ("success_rate", "success_ci_low", "success_ci_high", "a  Diagnostic success"),
        ("no_detection_rate", "no_detection_ci_low", "no_detection_ci_high", "b  No detection"),
        ("wrong_detection_rate", "wrong_detection_ci_low", "wrong_detection_ci_high", "c  Wrong detection"),
    ]
    colors = {
        "metadata query-aware": "#4e79a7",
        "first detection": "#f28e2b",
        "GroundingDINO": "#e15759",
    }
    fig, axes = plt.subplots(1, 3, figsize=(9.2, 3.0), sharey=True)
    x = np.arange(len(runs), dtype=float)
    width = 0.22
    for ax, (metric, low_col, high_col, title) in zip(axes, metric_specs):
        for offset_idx, detector in enumerate(detectors):
            vals: list[float] = []
            lows: list[float] = []
            highs: list[float] = []
            for run in runs:
                row = focus[(focus["run"].eq(run)) & (focus["detector"].eq(detector))]
                if row.empty:
                    vals.append(np.nan)
                    lows.append(np.nan)
                    highs.append(np.nan)
                    continue
                value = float(row[metric].iloc[0])
                vals.append(value)
                lo = float(row[low_col].iloc[0]) if low_col in row and not pd.isna(row[low_col].iloc[0]) else value
                hi = float(row[high_col].iloc[0]) if high_col in row and not pd.isna(row[high_col].iloc[0]) else value
                lows.append(max(0.0, value - lo))
                highs.append(max(0.0, hi - value))
            pos = x + (offset_idx - 1) * width
            ax.bar(pos, vals, width=width, color=colors[detector], label=_display(detector))
            ax.errorbar(pos, vals, yerr=[lows, highs], fmt="none", ecolor="#1f2937", elinewidth=0.8, capsize=2)
        ax.set_title(title, fontsize=8.5, weight="bold", loc="left")
        ax.set_xticks(x)
        ax.set_xticklabels([_display(run) for run in runs])
        ax.set_ylim(0, 1.05)
        ax.grid(axis="y", alpha=0.22)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    axes[0].set_ylabel("Rate")
    axes[0].legend(frameon=False, fontsize=7, loc="upper left")
    fig.suptitle("Detector bridge under crop-median target lifting", fontsize=10, weight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(figures_dir / "open_vocab_detector_transfer_combined.pdf", bbox_inches="tight")
    fig.savefig(figures_dir / "open_vocab_detector_transfer_combined.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _write_protocol_schematic(figures_dir: Path) -> None:
    labels = [
        ("Language\nquery", "target object\nobject name"),
        ("Detector /\nselector", "metadata\nGroundingDINO"),
        ("RGB-D target\nsource", "box center\ncrop median"),
        ("Stressor /\naudit", "list ambiguity\nocclusion, depth"),
        ("Diagnostic\noutput", "target error\nfailure type"),
    ]
    fig, ax = plt.subplots(figsize=(9.0, 2.7))
    ax.axis("off")
    xs = [0.10, 0.30, 0.50, 0.70, 0.90]
    width = 0.15
    for idx, ((title, subtitle), x) in enumerate(zip(labels, xs)):
        rect = Rectangle(
            (x - width / 2, 0.36),
            width,
            0.42,
            facecolor="#eff6ff",
            edgecolor="#2563eb",
            linewidth=1.2,
        )
        ax.add_patch(rect)
        ax.text(x, 0.60, title, ha="center", va="center", fontsize=10.5, weight="bold", linespacing=1.05)
        ax.text(x, 0.18, subtitle, ha="center", va="center", fontsize=8.5, color="#334155", linespacing=1.15)
        if idx < len(xs) - 1:
            ax.annotate(
                "",
                xy=(xs[idx + 1] - width / 2 - 0.015, 0.57),
                xytext=(x + width / 2 + 0.015, 0.57),
                arrowprops={"arrowstyle": "->", "lw": 1.4, "color": "#475569"},
            )
    ax.text(
        0.5,
        0.02,
        "Examples: metadata/first-detection/GroundingDINO selectors; oracle/box-center/crop-median targets; target error, success, oracle gap and failure labels.",
        ha="center",
        va="bottom",
        fontsize=8.0,
        color="#475569",
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(figures_dir / "protocol_schematic.pdf", bbox_inches="tight")
    fig.savefig(figures_dir / "protocol_schematic.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _write_experiment_design_table(tables_dir: Path) -> None:
    rows = [
        ("Main diagnostic sweeps", "oracle, box-center, crop-median, crop-top", "Parameterized ManiSkill stressors; seed-block bootstrap over task seeds."),
        ("Detector-bridge sweep", "metadata-assisted selector, first detection, one GroundingDINO plug-in", "Query, domain, and adapter-label failure taxonomy under matched RGB-D lifting."),
        ("External YCB-V/BOP probe", "oracle masks, oracle boxes, first box, one GroundingDINO route", "Static real RGB-D target-generation scope check; frame-block bootstrap."),
        ("Execution audit", "oracle, box-center, crop-median target sources", "Scripted executor smoke test; oracle gate required for any execution claim."),
    ]
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Experimental design summary. Detailed stressor parameters and full task lists are provided in Supplementary Table S1.}",
        r"\label{tab:scirep-experiment-design}",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\begin{tabular}{p{0.24\linewidth}p{0.34\linewidth}p{0.34\linewidth}}",
        r"\toprule",
        r"Evidence set & Compared modules & Purpose and statistical unit \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(row) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    (tables_dir / "experiment_design_summary.tex").write_text("\n".join(lines), encoding="utf-8")


def _write_claim_support_matrix(tables_dir: Path) -> None:
    rows = [
        ("Parameterized stressors expose target-generation failures", "Main sweeps + oracle-gap tables", "Supported", "Main diagnostic claim"),
        ("Crop-median depth is universally best", "Threshold sensitivity", "Not supported", "Replaced by precision--robustness tradeoff"),
        ("A learned detector plug-in can be audited by the protocol", "Detector-bridge sweep + YCB/clutter checks", "Supported with scope", "Query, domain, and adapter-label failure modes"),
        ("GroundingDINO generally fails on YCB/clutter", "Current generic-query evidence", "Not claimed", "Bounded to current query/adapter setup"),
        ("Diagnostic success predicts scripted task success", "Closed-loop oracle audit", "Not supported", "Claim boundary / limitation"),
        ("Benchmark is real-robot validated", "No real-robot evidence", "Not claimed", "Simulation and external RGB-D only"),
    ]
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{Claim-support matrix used to keep the Scientific Reports manuscript aligned with completed evidence.}",
        r"\label{tab:claim-support-matrix}",
        r"\scriptsize",
        r"\begin{tabular}{llll}",
        r"\toprule",
        r"Claim & Evidence & Status & Manuscript use \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(row) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""])
    (tables_dir / "claim_support_matrix.tex").write_text("\n".join(lines), encoding="utf-8")


def _write_oracle_success_table(tables_dir: Path) -> None:
    breakdown_summary = Path("outputs/scirep_oracle_failure_breakdown_20260521/oracle_success_summary.csv")
    path = Path("ieee_access_revision_20260520/main_results_with_ci.csv")
    if breakdown_summary.exists():
        oracle = pd.read_csv(breakdown_summary).rename(columns={"oracle_episodes": "episodes"})
        oracle["success_rate"] = pd.to_numeric(oracle["oracle_success_rate"], errors="coerce")
    elif path.exists():
        df = pd.read_csv(path)
        oracle = df[df["baseline"].eq("oracle_target")].copy()
    else:
        return
    oracle["failure_rate"] = 1.0 - pd.to_numeric(oracle["success_rate"], errors="coerce")
    oracle.to_csv(tables_dir / "oracle_diagnostic_success_summary.csv", index=False)
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Oracle diagnostic success is high but not forced to one. Rates are from the stored diagnostic sweeps and reflect the same finite target-distance threshold and stressor protocol as non-oracle sources.}",
        r"\label{tab:oracle-diagnostic-success}",
        r"\scriptsize",
        r"\begin{tabular}{lrr}",
        r"\toprule",
        r"Evidence set & Oracle success & Oracle failure \\",
        r"\midrule",
    ]
    for _, row in oracle.iterrows():
        lines.append(f"{row['run']} & {100*float(row['success_rate']):.1f} & {100*float(row['failure_rate']):.1f} \\\\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    (tables_dir / "oracle_diagnostic_success_summary.tex").write_text("\n".join(lines), encoding="utf-8")


def _load_episode_indices(root: Path, query_root: Path) -> pd.DataFrame:
    paths = [
        (root / "open_vocab_bridge_v2" / "open_vocab_bridge_v2_episode_index.csv", "Detector-bridge sweep"),
        (query_root / "open_vocab_bridge_v2_episode_index.csv", "True-name query ablation"),
        (root / "open_vocab_bridge_v2_ycb_clutter_heldout" / "open_vocab_bridge_v2_episode_index.csv", "YCB/clutter held-out"),
    ]
    frames = []
    for path, evidence_set in paths:
        if path.exists():
            frame = pd.read_csv(path)
            frame["evidence_set"] = evidence_set
            frames.append(frame)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _select_qualitative_cases(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    cases = []
    used = set()
    success = df["success"].astype(str).str.lower().eq("true")
    target_error = pd.to_numeric(df.get("target_error_l2"), errors="coerce")
    iou = pd.to_numeric(df.get("grounding_dino_target_iou"), errors="coerce")

    def add(label: str, subset: pd.DataFrame, sort_by: str | None = None, ascending: bool = True) -> None:
        if subset.empty:
            return
        chosen = subset.copy()
        if sort_by and sort_by in chosen:
            chosen[sort_by] = pd.to_numeric(chosen[sort_by], errors="coerce")
            chosen = chosen.sort_values(sort_by, ascending=ascending, na_position="last")
        row = chosen.iloc[0].copy()
        key = str(row.get("source_file"))
        if key in used:
            return
        row["case_label"] = label
        cases.append(row)
        used.add(key)

    add("Clean success", df[success & df["level"].astype(str).eq("0")])
    add(
        "Wrong detection",
        df[(~success) & df["failure_type"].astype(str).eq("wrong_detection_selected")],
        sort_by="target_error_l2",
        ascending=False,
    )
    no_detection = df[(~success) & df["failure_type"].astype(str).eq("no_detection")]
    if "has_grounding_dino_debug" in no_detection:
        with_debug = no_detection[no_detection["has_grounding_dino_debug"].astype(str).str.lower().eq("true")]
        add("No detection", with_debug if not with_debug.empty else no_detection)
    else:
        add("No detection", no_detection)
    add("Depth invalid", df[(~success) & df["failure_type"].astype(str).eq("depth_invalid")])
    add("Large target error", df[(~success) & target_error.notna()], sort_by="target_error_l2", ascending=False)
    add(
        "Low IoU but 3D success",
        df[success & df["detector"].astype(str).eq("GroundingDINO") & iou.notna() & (iou < 0.25)],
        sort_by="grounding_dino_target_iou",
        ascending=True,
    )
    return pd.DataFrame(cases)


def _write_qualitative_figure(cases: pd.DataFrame, revision_dir: Path, figures_dir: Path) -> None:
    cases = cases.copy()
    if "source_file" in cases:
        cases["source_file"] = cases["source_file"].map(lambda p: Path(str(p)).name)
    cases.to_csv(revision_dir / "qualitative_case_manifest.csv", index=False)
    if cases.empty:
        return
    cols = min(3, len(cases))
    rows = int((len(cases) + cols - 1) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(3.6 * cols, 2.7 * rows), squeeze=False)
    for ax in axes.ravel():
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
    for ax, (_, row) in zip(axes.ravel(), cases.iterrows()):
        ax.axis("on")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_facecolor("#f8fafc")
        for spine in ax.spines.values():
            spine.set_color("#cbd5e1")
        edge = "#16a34a" if str(row.get("success")).lower() == "true" else "#dc2626"
        ax.add_patch(Rectangle((0.08, 0.45), 0.42, 0.28, fill=False, linewidth=2.0, edgecolor=edge))
        ax.add_patch(Rectangle((0.55, 0.50), 0.22, 0.17, fill=False, linewidth=1.5, edgecolor="#64748b"))
        error = row.get("target_error_l2")
        error_text = "n/a" if pd.isna(error) else f"{float(error):.3f} m"
        iou = row.get("grounding_dino_target_iou")
        iou_text = "" if pd.isna(iou) else f"\nIoU={float(iou):.3f}"
        text = (
            f"{row.get('case_label')}\n"
            f"{_display(row.get('evidence_set'))}: {_display(row.get('task'))}\n"
            f"{_display(row.get('detector'))} / {_display(row.get('target_source'))}\n"
            f"{_display(row.get('stressor'))} L{row.get('level')} seed {row.get('seed')}\n"
            f"success={row.get('success')} error={error_text}{iou_text}\n"
            f"failure={_display(row.get('failure_type'))}"
        )
        ax.text(
            0.04,
            0.05,
            text,
            ha="left",
            va="bottom",
            fontsize=7.1,
            linespacing=1.18,
            bbox={"facecolor": "white", "edgecolor": "#e2e8f0", "boxstyle": "round,pad=0.25"},
        )
    fig.suptitle("Artifact-backed qualitative diagnostic cases", fontsize=12, weight="bold")
    fig.text(
        0.5,
        0.012,
        "Generated from stored CSV/JSON fields; full RGB/depth render extraction remains a follow-up artifact task.",
        ha="center",
        fontsize=8,
        color="#475569",
    )
    fig.tight_layout(rect=[0, 0.04, 1, 0.95])
    fig.savefig(figures_dir / "qualitative_failure_teaser.pdf", bbox_inches="tight")
    fig.savefig(figures_dir / "qualitative_failure_teaser.png", dpi=240, bbox_inches="tight")
    plt.close()


def _write_main_qualitative_from_renders(figures_dir: Path) -> None:
    render_dir = figures_dir / "maniskill_qualitative" / "maniskill_qualitative"
    if not render_dir.exists():
        return
    wanted = [
        ("Clean success", "Clean_success*.png"),
        ("Wrong detection", "Wrong_detection*.png"),
        ("No detection", "No_detection*.png"),
        ("Low IoU, valid 3D", "Low_IoU_but_3D_success*.png"),
    ]
    images: list[tuple[str, Path]] = []
    for title, pattern in wanted:
        matches = sorted(render_dir.glob(pattern))
        if matches:
            images.append((title, matches[0]))
    if len(images) < 2:
        return
    manifest_path = Path("scientific_reports_revision_20260521/qualitative_case_manifest.csv")
    manifest = pd.read_csv(manifest_path) if manifest_path.exists() else pd.DataFrame()
    case_rows = {str(row.get("case_label")): row for _, row in manifest.iterrows()}
    fig, axes = plt.subplots(2, 2, figsize=(8.8, 6.8), squeeze=False)
    for ax in axes.ravel():
        ax.axis("off")
    for ax, (label, path) in zip(axes.ravel(), images):
        image = plt.imread(path)
        crop_width = min(image.shape[1], 740)
        ax.imshow(image[:, :crop_width])
        case_key = "Low IoU but 3D success" if label == "Low IoU, valid 3D" else label
        row = case_rows.get(case_key, {})
        failure = _display(row.get("failure_type", ""))
        error = row.get("target_error_l2", "")
        if error != "" and not pd.isna(error):
            error_text = f"{float(error):.3f} m"
        else:
            error_text = "n/a"
        title = f"{label}\nerror={error_text}; failure={failure}"
        ax.set_title(title, fontsize=9.5, weight="bold")
        ax.axis("off")
    fig.text(
        0.5,
        0.01,
        "Green boxes denote oracle target regions; red boxes denote selected regions. Full per-case metadata are in the qualitative manifest.",
        ha="center",
        fontsize=8,
        color="#475569",
    )
    fig.tight_layout()
    fig.savefig(figures_dir / "maniskill_qualitative_main_figure.pdf", bbox_inches="tight")
    fig.savefig(figures_dir / "maniskill_qualitative_main_figure.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _write_result_to_claim(root: Path, out_docs: Path, query_root: Path) -> None:
    bridge = pd.read_csv(root / "open_vocab_bridge_v2" / "open_vocab_bridge_v2_summary.csv").iloc[0]
    held = pd.read_csv(root / "open_vocab_bridge_v2_ycb_clutter_heldout" / "open_vocab_bridge_v2_summary.csv").iloc[0]
    closed = pd.read_csv(root / "closed_loop_sanity_smoke" / "closed_loop_sanity_summary.csv").iloc[0]
    v2_summary_path = Path("outputs/scirep_closed_loop_oracle_calibration_v2_20260521/smoke/closed_loop_sanity_summary.csv")
    closed_v2 = pd.read_csv(v2_summary_path).iloc[0] if v2_summary_path.exists() else None
    audit_summary_path = Path("outputs/scirep_closed_loop_oracle_gate_audit_200_20260521/closed_loop_sanity_summary.csv")
    closed_audit = pd.read_csv(audit_summary_path).iloc[0] if audit_summary_path.exists() else None
    query_summary_path = query_root / "open_vocab_bridge_v2_summary.csv"
    query_summary = pd.read_csv(query_summary_path).iloc[0] if query_summary_path.exists() else None
    by_detector = pd.read_csv(root / "open_vocab_bridge_v2_ycb_clutter_heldout" / "open_vocab_bridge_v2_by_detector_target_source.csv")
    gdino_no = by_detector[by_detector["detector"] == "GroundingDINO"]["no_detection_rate"].mean()
    closed_v2_row = ""
    if closed_v2 is not None:
        closed_v2_row = f"| Closed-loop oracle calibration v2 | {int(closed_v2['completed_episodes'])}/{int(closed_v2['expected_episodes'])} | {closed_v2['complete']} | {int(closed_v2['duplicate_result_count'])} | {int(closed_v2['runner_exception_count'])} | Oracle task success remained below gate ({float(closed_v2['oracle_task_success_rate']):.3f}); execution calibration remains unresolved |\n"
    closed_audit_row = ""
    if closed_audit is not None:
        closed_audit_row = f"| Closed-loop 200-episode oracle-gate audit | {int(closed_audit['completed_episodes'])}/{int(closed_audit['expected_episodes'])} | {closed_audit['complete']} | {int(closed_audit['duplicate_result_count'])} | {int(closed_audit['runner_exception_count'])} | Larger oracle audit remains below gate ({float(closed_audit['oracle_task_success_rate']):.3f}); use as claim boundary |\n"
    query_row = ""
    query_debug_note = ""
    if query_summary is not None:
        query_row = f"| True-name YCB/clutter query ablation | {int(query_summary['completed_episodes'])}/{int(query_summary['expected_episodes'])} | {query_summary['complete']} | {int(query_summary['duplicate_result_count'])} | {int(query_summary['runner_exception_count'])} | True-name prompts make the detector runnable but wrong detections remain the dominant failure mode |\n"
        query_debug_note = (
            f"The true-name ablation has GroundingDINO debug fields for "
            f"{int(query_summary['grounding_dino_rows_with_debug'])}/{int(query_summary['grounding_dino_rows'])} rows, "
            f"with no-detection rate {float(query_summary['no_detection_rate']):.3f}."
        )

    text = f"""# Scientific Reports Result-to-Claim Gate

Date: 2026-05-21

## Verdict

The new results support a Scientific Reports manuscript centered on reproducible
simulation diagnosis of language-to-target generation failures. They do **not**
support a positive claim about scripted execution success calibration.

## Evidence Summary

| Evidence set | Episodes | Complete | Duplicate count | Runner exceptions | Key finding |
| --- | ---: | --- | ---: | ---: | --- |
| Detector-bridge sweep | {int(bridge['completed_episodes'])}/{int(bridge['expected_episodes'])} | {bridge['complete']} | {int(bridge['duplicate_result_count'])} | {int(bridge['runner_exception_count'])} | Learned detector plug-in is runnable and produces detector-specific target-generation failures |
| YCB/clutter held-out bridge | {int(held['completed_episodes'])}/{int(held['expected_episodes'])} | {held['complete']} | {int(held['duplicate_result_count'])} | {int(held['runner_exception_count'])} | Auxiliary held-out stress run; not used for detector-valid claims because GroundingDINO debug fields are absent |
| Closed-loop smoke | {int(closed['completed_episodes'])}/{int(closed['expected_episodes'])} | {closed['complete']} | {int(closed['duplicate_result_count'])} | {int(closed['runner_exception_count'])} | Scripted executor gate failed; do not use for positive task-success claims |
{closed_v2_row}
{closed_audit_row}
{query_row}

## Claim Decisions

| Intended claim | Verdict | Supported wording |
| --- | --- | --- |
| Parameterized simulation stressors expose target-generation failures | Supported | The benchmark exposes target-source and detector failure modes through controlled stressor sweeps and per-episode artifacts. |
| Target sources show a precision-vs-robustness tradeoff | Supported | Threshold sensitivity supports a precision--robustness tradeoff; crop-median is not universally strongest under strict thresholds. |
| One learned detector plug-in can be evaluated through the same protocol | Supported with scope | GroundingDINO can be evaluated through the detector-pluggable protocol, and the detector-bridge sweep plus the YCB/clutter query check expose query, domain, and adapter-label limitations. |
| Diagnostic target success is informative for scripted execution success | Not supported yet | The current scripted executor smoke failed the oracle task-success gate, so execution calibration remains unresolved. |
| Failure taxonomy separates wrong detection, invalid depth, target displacement, and execution sensitivity | Supported for diagnostic runs | Failure labels are useful for diagnosis; execution claims require a calibrated executor. |

## Important Negative Result

The large YCB/clutter held-out bridge has an average GroundingDINO no-detection
rate of {gdino_no:.3f}, but its GroundingDINO debug fields are absent. It should
therefore remain an auxiliary stress run rather than a detector-valid claim.

## Query-Ablation Update

The follow-up query ablation completes the prompt-sensitivity check. It removes
the no-detection artifact but GroundingDINO remains dominated by wrong-detection
failures on YCB/clutter. The object-name resolution audit determines whether a
true object-name prompt ablation is claimable; if resolved names are available,
the small ablation is reported as detector-query sensitivity rather than as a
detector leaderboard.

{query_debug_note}

## Manuscript Routing

1. Move closed-loop execution from a positive result to a limitation and sanity
   audit.
2. Promote detector-transfer diagnosis to a main Scientific Reports finding.
3. Keep all claims simulation-only and target-generation-specific.
4. Do not add SOTA VLA, real-robot, or policy-benchmark claims.
"""
    (out_docs / "scientific_reports_result_to_claim.md").write_text(text, encoding="utf-8")


def _write_claim_evidence(root: Path, out_docs: Path, query_root: Path) -> None:
    text = f"""# Scientific Reports Claim-Evidence Table

| Claim | Verdict | Evidence source | Paper wording |
| --- | --- | --- | --- |
| Parameterized simulation stressors expose target-generation failures | Supported | Main v1, held-out, hard L3, detection-list ambiguity, and detector-bridge artifacts | "stressors expose target-generation and detector failure modes" |
| Target sources show a precision-vs-robustness tradeoff | Supported | Threshold sensitivity and target-error analyses | "crop-median is robust at default/relaxed thresholds; box-center is more precise under strict thresholds" |
| One learned detector plug-in can be evaluated through the same protocol | Supported with scope | detector-bridge source CSVs, target-name probe, and query-ablation summaries | "GroundingDINO can be plugged in, and YCB/clutter exposes detector-query sensitivity and adapter-label limitations" |
| Diagnostic target success predicts scripted execution success | Not supported | `outputs/scirep_overnight_20260520_analysis/closed_loop_sanity_smoke`; `outputs/scirep_closed_loop_oracle_calibration_v2_20260521`; `outputs/scirep_closed_loop_oracle_gate_audit_200_20260521` | "scripted execution calibration remains unresolved" |
| Failure taxonomy separates wrong detection, invalid depth, displacement, and execution sensitivity | Supported for diagnostic runs | failure-distribution tables and qualitative case manifest | "failure taxonomy supports diagnostic triage, not causal proof beyond logged artifacts" |

## Claim Boundaries

- No real-robot robustness claim.
- No closed-loop policy benchmark claim.
- No SOTA VLA comparison claim.
- No claim that GroundingDINO solves semantic grounding.
- No claim that crop-median depth is universally strongest across all thresholds.
"""
    (out_docs / "claim_evidence_table_scientific_reports.md").write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-root", default="outputs/scirep_overnight_20260520_analysis")
    parser.add_argument("--revision-dir", default="scientific_reports_revision_20260521")
    parser.add_argument("--paper-dir", default="paper/scientific_reports")
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument("--query-root", default="outputs/scirep_true_name_ablation_small_20260521_r7")
    parser.add_argument("--ieee-dir", default="ieee_access_revision_20260520")
    parser.add_argument("--ycbv-root", default="outputs/ycbv_external_rgbd_probe_160k_20260522_analysis")
    args = parser.parse_args()

    root = Path(args.analysis_root)
    query_root = Path(args.query_root)
    ieee_dir = Path(args.ieee_dir)
    ycbv_root = Path(args.ycbv_root)
    revision = Path(args.revision_dir)
    paper = Path(args.paper_dir)
    docs = Path(args.docs_dir)
    tables = paper / "tables"
    figures = paper / "figures"
    for path in [revision, paper, tables, figures, docs]:
        path.mkdir(parents=True, exist_ok=True)

    bridge = _load_bridge(root, "open_vocab_bridge_v2")
    held = _load_bridge(root, "open_vocab_bridge_v2_ycb_clutter_heldout")
    combined = bridge.copy()
    combined.to_csv(revision / "scirep_open_vocab_detector_transfer_combined.csv", index=False)
    _write_protocol_schematic(figures)
    _write_experiment_design_table(tables)
    _write_claim_support_matrix(tables)
    _write_main_diagnostic_summary(ieee_dir, tables, revision)
    _write_target_threshold_tradeoff(ieee_dir, figures, revision)
    _write_oracle_success_table(tables)
    _write_detector_table(combined, tables)
    _write_low_iou_valid_summary(root, query_root, tables, revision)
    _write_paired_effects(root, query_root, tables, revision)
    _write_external_stratification(ycbv_root, tables, revision)
    _write_query_ablation_table(query_root, tables, revision)
    _write_closed_loop_table(root, tables)
    _write_closed_loop_v2_table(tables)
    _write_target_name_probe_table(tables, revision)
    _write_detector_figure(combined, figures)
    episode_index = _load_episode_indices(root, query_root)
    _write_qualitative_figure(_select_qualitative_cases(episode_index), revision, figures)
    _write_main_qualitative_from_renders(figures)
    # Final release-facing claim documents are maintained in docs/SCIREP_CLAIM_EVIDENCE.md
    # and its compact companions so package cleanup edits are not overwritten by
    # numeric asset regeneration.
    print(f"Wrote Scientific Reports assets under {revision}, {paper}, and {docs}")


if __name__ == "__main__":
    main()
