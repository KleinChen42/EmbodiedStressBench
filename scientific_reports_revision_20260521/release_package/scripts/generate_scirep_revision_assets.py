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
    "open_vocab_bridge_v2": "Bridge v2",
    "open_vocab_bridge_v2_ycb_clutter_heldout": "YCB/clutter held-out",
    "metadata query-aware": "Metadata query-aware",
    "first detection": "First detection",
    "GroundingDINO": "GroundingDINO",
    "oracle": "Oracle",
    "box_center_depth": "Box-center depth",
    "crop_median_depth": "Crop-median depth",
    "crop_trimmed_median_depth": "Crop-trimmed median",
    "oracle_target": "Oracle target",
    "generic": "Generic",
    "object_label": "Object-label template",
    "category": "Category template",
    "label_phrase": "Label phrase",
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
        r"\caption{Open-vocabulary detector bridge results for Scientific Reports. Rates are percentages. The YCB/clutter held-out run exposes a detector-query mismatch: GroundingDINO produces no usable detections under the generic target-object query, while metadata and first-detection controls remain executable.}",
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
            actual_queries[str(variant)] = "; ".join(values[:3])

    rows = []
    variant_order = ["generic", "object_label", "category", "label_phrase"]
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
        r"\caption{GroundingDINO query-ablation on YCB/clutter. Rates are percentages for crop-median target lifting. Template-based variants collapse to generic object-level prompts in the current ManiSkill adapter, so the table tests detector-query sensitivity rather than full object-name prompting.}",
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

The ablation removes the previous no-detection artifact but GroundingDINO remains
dominated by wrong-detection failures on YCB/clutter. Template variants do not
recover object-specific prompting because the current ManiSkill adapter exposes
generic labels (`target object` / `object`) for these tasks. The paper should
therefore claim detector-query sensitivity and adapter-metadata limitations, not
full object-name prompt recovery.
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
        f"Task success & {_fmt_rate(summary['task_success_rate'])} & not claimable \\\\",
        f"Oracle task success & {_fmt_rate(summary['oracle_task_success_rate'])} & gate failed \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ]
    (tables_dir / "closed_loop_smoke_outcome.tex").write_text("\n".join(lines), encoding="utf-8")


def _write_closed_loop_v2_table(tables_dir: Path) -> None:
    root = Path("outputs/scirep_closed_loop_oracle_calibration_v2_20260521/smoke")
    if not (root / "closed_loop_sanity_summary.csv").exists():
        return
    summary = pd.read_csv(root / "closed_loop_sanity_summary.csv").iloc[0]
    gate = pd.read_csv(root / "closed_loop_oracle_gate_by_task.csv")
    gate.to_csv(tables_dir / "closed_loop_oracle_calibration_v2_gate.csv", index=False)
    rows = []
    for _, row in gate.iterrows():
        rows.append((row["task"], int(row["oracle_episodes"]), 100 * float(row["oracle_task_success_rate"])))
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Closed-loop oracle calibration v2 gate. The oracle scripted executor remains below the pre-registered task-success thresholds, so no positive execution-calibration claim is made.}",
        r"\label{tab:closed-loop-v2-gate}",
        r"\scriptsize",
        r"\begin{tabular}{lrr}",
        r"\toprule",
        r"Task & Oracle episodes & Oracle task success \\",
        r"\midrule",
    ]
    for task, episodes, success in rows:
        lines.append(f"{task} & {episodes} & {success:.1f} \\\\")
    lines.extend(
        [
            r"\midrule",
            f"Total & {int(summary['completed_episodes'])} & {100*float(summary['oracle_task_success_rate']):.1f} \\\\",
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
            "",
        ]
    )
    (tables_dir / "closed_loop_oracle_calibration_v2_gate.tex").write_text("\n".join(lines), encoding="utf-8")


def _write_target_name_probe_table(tables_dir: Path, revision_dir: Path) -> None:
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
        r"\caption{YCB/clutter target-name probe. The current ManiSkill adapter exposes generic target labels, so a true object-name prompt ablation is not claimable from this probe.}",
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
    pivot = focus.pivot_table(index="detector", columns="run", values="success_rate", aggfunc="mean")
    order = ["metadata query-aware", "first detection", "GroundingDINO"]
    pivot = pivot.reindex(order)
    ax = pivot.rename(index=_display, columns=_display).plot(kind="bar", figsize=(6.8, 3.6), width=0.72)
    ax.set_ylabel("Success rate")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, loc="upper right")
    ax.set_title("Detector transfer under crop-median target lifting")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(figures_dir / "open_vocab_detector_transfer_success.pdf", bbox_inches="tight")
    plt.savefig(figures_dir / "open_vocab_detector_transfer_success.png", dpi=240, bbox_inches="tight")
    plt.close()

    pivot_no = focus.pivot_table(index="detector", columns="run", values="no_detection_rate", aggfunc="mean")
    pivot_no = pivot_no.reindex(order)
    ax = pivot_no.rename(index=_display, columns=_display).plot(kind="bar", figsize=(6.8, 3.6), width=0.72)
    ax.set_ylabel("No-detection rate")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, loc="upper right")
    ax.set_title("No-detection failure exposed by YCB/clutter held-out")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(figures_dir / "open_vocab_detector_transfer_no_detection.pdf", bbox_inches="tight")
    plt.savefig(figures_dir / "open_vocab_detector_transfer_no_detection.png", dpi=240, bbox_inches="tight")
    plt.close()


def _write_protocol_schematic(figures_dir: Path) -> None:
    labels = [
        ("Language query", "target object / object name"),
        ("Detector or selector", "metadata, first detection, GroundingDINO"),
        ("RGB-D target source", "box center, crop median, trimmed median"),
        ("Parameterized stressor", "list ambiguity, occlusion, depth, offset"),
        ("Diagnostic output", "3D error, success, failure type, oracle gap"),
    ]
    fig, ax = plt.subplots(figsize=(7.2, 2.1))
    ax.axis("off")
    xs = [0.04, 0.25, 0.47, 0.68, 0.89]
    for idx, ((title, subtitle), x) in enumerate(zip(labels, xs)):
        ax.text(
            x,
            0.62,
            title,
            ha="center",
            va="center",
            fontsize=8.5,
            weight="bold",
            bbox={"boxstyle": "round,pad=0.35", "facecolor": "#eff6ff", "edgecolor": "#60a5fa"},
        )
        ax.text(x, 0.30, subtitle, ha="center", va="center", fontsize=6.7, color="#334155", wrap=True)
        if idx < len(xs) - 1:
            ax.annotate(
                "",
                xy=(xs[idx + 1] - 0.08, 0.62),
                xytext=(x + 0.08, 0.62),
                arrowprops={"arrowstyle": "->", "lw": 1.2, "color": "#475569"},
            )
    fig.tight_layout()
    fig.savefig(figures_dir / "protocol_schematic.pdf", bbox_inches="tight")
    fig.savefig(figures_dir / "protocol_schematic.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _write_experiment_design_table(tables_dir: Path) -> None:
    rows = [
        ("Main diagnostic sweeps", "PickCube, StackCube, PickSingleYCB, PickClutterYCB", "oracle, box-center, crop-median, crop-top", "parameterized stressors", "seed-block bootstrap"),
        ("Detector bridge", "PickCube, PickSingleYCB, PickClutterYCB", "metadata, first detection, GroundingDINO", "semantic ambiguity, occlusion, depth sparsity", "detector failure taxonomy"),
        ("YCB/clutter query checks", "PickSingleYCB, PickClutterYCB", "GroundingDINO, metadata control", "query variants, hard stressors", "actual query audit"),
        ("Execution calibration audit", "PickCube, PickSingleYCB", "oracle, box-center, crop-median", "scripted executor smoke", "oracle gate required"),
    ]
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{Experimental design summary. Detailed stressor parameters are provided in Supplementary Table S1.}",
        r"\label{tab:scirep-experiment-design}",
        r"\scriptsize",
        r"\begin{tabular}{lllll}",
        r"\toprule",
        r"Evidence set & Tasks & Compared modules & Perturbations & Statistical unit \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(row) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""])
    (tables_dir / "experiment_design_summary.tex").write_text("\n".join(lines), encoding="utf-8")


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


def _load_episode_indices(root: Path) -> pd.DataFrame:
    paths = [
        root / "open_vocab_bridge_v2" / "open_vocab_bridge_v2_episode_index.csv",
        root / "open_vocab_bridge_v2_ycb_clutter_heldout" / "open_vocab_bridge_v2_episode_index.csv",
    ]
    frames = []
    for path in paths:
        if path.exists():
            frame = pd.read_csv(path)
            frame["evidence_set"] = "YCB/clutter held-out" if "ycb_clutter" in str(path) else "Bridge v2"
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
    add("No detection", df[(~success) & df["failure_type"].astype(str).eq("no_detection")])
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
    fig, axes = plt.subplots(2, 2, figsize=(8.8, 6.2), squeeze=False)
    for ax in axes.ravel():
        ax.axis("off")
    for ax, (label, path) in zip(axes.ravel(), images):
        ax.imshow(plt.imread(path))
        ax.set_title(label, fontsize=9, weight="bold")
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(figures_dir / "maniskill_qualitative_main_figure.pdf", bbox_inches="tight")
    fig.savefig(figures_dir / "maniskill_qualitative_main_figure.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _write_result_to_claim(root: Path, out_docs: Path) -> None:
    bridge = pd.read_csv(root / "open_vocab_bridge_v2" / "open_vocab_bridge_v2_summary.csv").iloc[0]
    held = pd.read_csv(root / "open_vocab_bridge_v2_ycb_clutter_heldout" / "open_vocab_bridge_v2_summary.csv").iloc[0]
    closed = pd.read_csv(root / "closed_loop_sanity_smoke" / "closed_loop_sanity_summary.csv").iloc[0]
    v2_summary_path = Path("outputs/scirep_closed_loop_oracle_calibration_v2_20260521/smoke/closed_loop_sanity_summary.csv")
    closed_v2 = pd.read_csv(v2_summary_path).iloc[0] if v2_summary_path.exists() else None
    by_detector = pd.read_csv(root / "open_vocab_bridge_v2_ycb_clutter_heldout" / "open_vocab_bridge_v2_by_detector_target_source.csv")
    gdino_no = by_detector[by_detector["detector"] == "GroundingDINO"]["no_detection_rate"].mean()
    closed_v2_row = ""
    if closed_v2 is not None:
        closed_v2_row = f"| Closed-loop oracle calibration v2 | {int(closed_v2['completed_episodes'])}/{int(closed_v2['expected_episodes'])} | {closed_v2['complete']} | {int(closed_v2['duplicate_result_count'])} | {int(closed_v2['runner_exception_count'])} | Oracle task success remained below gate ({float(closed_v2['oracle_task_success_rate']):.3f}); execution calibration remains unresolved |\n"

    text = f"""# Scientific Reports Result-to-Claim Gate

Date: 2026-05-21

## Verdict

The new results support a Scientific Reports manuscript centered on reproducible
simulation diagnosis of language-to-target generation failures. They do **not**
support a positive claim about scripted execution success calibration.

## Evidence Summary

| Evidence set | Episodes | Complete | Duplicate count | Runner exceptions | Key finding |
| --- | ---: | --- | ---: | ---: | --- |
| Open-Vocab Bridge v2 | {int(bridge['completed_episodes'])}/{int(bridge['expected_episodes'])} | {bridge['complete']} | {int(bridge['duplicate_result_count'])} | {int(bridge['runner_exception_count'])} | Learned detector plug-in is runnable and produces detector-specific target-generation failures |
| YCB/clutter held-out bridge | {int(held['completed_episodes'])}/{int(held['expected_episodes'])} | {held['complete']} | {int(held['duplicate_result_count'])} | {int(held['runner_exception_count'])} | Generic open-vocabulary detector transfer fails through no-detection on YCB/clutter |
| Closed-loop smoke | {int(closed['completed_episodes'])}/{int(closed['expected_episodes'])} | {closed['complete']} | {int(closed['duplicate_result_count'])} | {int(closed['runner_exception_count'])} | Scripted executor gate failed; do not use for positive task-success claims |
{closed_v2_row}

## Claim Decisions

| Intended claim | Verdict | Supported wording |
| --- | --- | --- |
| Parameterized simulation stressors expose target-generation failures | Supported | The benchmark exposes target-source and detector failure modes through controlled stressor sweeps and per-episode artifacts. |
| Target sources show a precision-vs-robustness tradeoff | Supported | Threshold sensitivity supports a precision--robustness tradeoff; crop-median is not universally strongest under strict thresholds. |
| Open-vocabulary detectors can be evaluated through the same protocol | Supported with scope | GroundingDINO can be evaluated through the protocol, and the YCB/clutter held-out plus query checks expose detector-query and adapter-label limitations. |
| Diagnostic target success is informative for scripted execution success | Not supported yet | The current scripted executor smoke failed the oracle task-success gate, so execution calibration remains unresolved. |
| Failure taxonomy separates wrong detection, invalid depth, target displacement, and execution sensitivity | Supported for diagnostic runs | Failure labels are useful for diagnosis; execution claims require a calibrated executor. |

## Important Negative Result

In the YCB/clutter held-out bridge, GroundingDINO rows have an average
no-detection rate of {gdino_no:.3f}. This should be written as a limitation of
the generic target-object query and current adapter labels, not as a general
statement that GroundingDINO cannot work on YCB or clutter.

## Query-Ablation Update

The follow-up query ablation completes the prompt-sensitivity check. It removes
the no-detection artifact but GroundingDINO remains dominated by wrong-detection
failures on YCB/clutter. A target-name probe found no non-generic target_label
rows, so a true object-name prompt ablation is not claimable from the current
adapter. This supports detector-query sensitivity and adapter-metadata
limitations rather than full object-name prompt recovery.

## Manuscript Routing

1. Move closed-loop execution from a positive result to a limitation and sanity
   audit.
2. Promote detector-transfer diagnosis to a main Scientific Reports finding.
3. Keep all claims simulation-only and target-generation-specific.
4. Do not add SOTA VLA, real-robot, or policy-benchmark claims.
"""
    (out_docs / "scientific_reports_result_to_claim.md").write_text(text, encoding="utf-8")


def _write_claim_evidence(root: Path, out_docs: Path) -> None:
    text = """# Scientific Reports Claim-Evidence Table

| Claim | Verdict | Evidence source | Paper wording |
| --- | --- | --- | --- |
| Parameterized simulation stressors expose target-generation failures | Supported | Main v1, held-out, hard L3, detection-list ambiguity, and Bridge v2 artifacts | "stressors expose target-generation and detector failure modes" |
| Target sources show a precision-vs-robustness tradeoff | Supported | Threshold sensitivity and target-error analyses | "crop-median is robust at default/relaxed thresholds; box-center is more precise under strict thresholds" |
| Open-vocabulary detectors can be evaluated through the same protocol | Supported with scope | `outputs/scirep_overnight_20260520_analysis/open_vocab_bridge_v2*`; `outputs/scirep_query_ablation_20260521`; `outputs/ycb_true_name_probe_20260521` | "GroundingDINO can be plugged in, and YCB/clutter exposes detector-query sensitivity and adapter-label limitations" |
| Diagnostic target success predicts scripted execution success | Not supported | `outputs/scirep_overnight_20260520_analysis/closed_loop_sanity_smoke`; `outputs/scirep_closed_loop_oracle_calibration_v2_20260521` | "scripted execution calibration remains unresolved" |
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
    parser.add_argument("--query-root", default="outputs/scirep_query_ablation_20260521")
    args = parser.parse_args()

    root = Path(args.analysis_root)
    query_root = Path(args.query_root)
    revision = Path(args.revision_dir)
    paper = Path(args.paper_dir)
    docs = Path(args.docs_dir)
    tables = paper / "tables"
    figures = paper / "figures"
    for path in [revision, paper, tables, figures, docs]:
        path.mkdir(parents=True, exist_ok=True)

    bridge = _load_bridge(root, "open_vocab_bridge_v2")
    held = _load_bridge(root, "open_vocab_bridge_v2_ycb_clutter_heldout")
    combined = pd.concat([bridge, held], ignore_index=True)
    combined.to_csv(revision / "scirep_open_vocab_detector_transfer_combined.csv", index=False)
    _write_protocol_schematic(figures)
    _write_experiment_design_table(tables)
    _write_oracle_success_table(tables)
    _write_detector_table(combined, tables)
    _write_query_ablation_table(query_root, tables, revision)
    _write_closed_loop_table(root, tables)
    _write_closed_loop_v2_table(tables)
    _write_target_name_probe_table(tables, revision)
    _write_detector_figure(combined, figures)
    episode_index = _load_episode_indices(root)
    _write_qualitative_figure(_select_qualitative_cases(episode_index), revision, figures)
    _write_main_qualitative_from_renders(figures)
    _write_result_to_claim(root, docs)
    _write_claim_evidence(root, docs)
    print(f"Wrote Scientific Reports assets under {revision}, {paper}, and {docs}")


if __name__ == "__main__":
    main()
