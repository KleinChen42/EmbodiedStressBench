from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ERROR_BINS = [0.0, 0.04, 0.06, 0.08, 0.10, 0.15, float("inf")]
ERROR_LABELS = ["0-0.04", "0.04-0.06", "0.06-0.08", "0.08-0.10", "0.10-0.15", ">0.15"]


def _wilson_ci(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        return (float("nan"), float("nan"))
    phat = successes / total
    denom = 1.0 + z * z / total
    centre = phat + z * z / (2 * total)
    margin = z * np.sqrt((phat * (1.0 - phat) + z * z / (4 * total)) / total)
    return ((centre - margin) / denom, (centre + margin) / denom)


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
        rows.append(
            {
                "source_file": str(path),
                "filename": path.name,
                "status": item.get("status"),
                "task": item.get("task"),
                "baseline": item.get("baseline"),
                "target_source": item.get("baseline"),
                "stressor": item.get("stressor"),
                "level": item.get("level"),
                "seed": item.get("seed"),
                "diagnostic_success": bool(item.get("diagnostic_success", item.get("success", False))),
                "task_success": bool(item.get("task_success", item.get("success", False))),
                "agreement": bool(item.get("agreement", False)),
                "success": bool(item.get("success", False)),
                "target_error_l2": item.get("target_error_l2"),
                "failure_type": item.get("failure_type") or "success",
            }
        )
    df = pd.DataFrame(rows)
    duplicates = {name: count for name, count in Counter(names).items() if count > 1}
    df.attrs["duplicate_count"] = sum(count - 1 for count in duplicates.values())
    df.attrs["duplicate_names"] = duplicates
    return df


def _group(df: pd.DataFrame, keys: list[str], out: Path) -> None:
    grouped = (
        df.groupby(keys, dropna=False)
        .agg(
            episodes=("task_success", "size"),
            diagnostic_success_rate=("diagnostic_success", "mean"),
            task_success_rate=("task_success", "mean"),
            agreement_rate=("agreement", "mean"),
            mean_target_error_l2=("target_error_l2", "mean"),
            runner_exception_rate=("failure_type", lambda s: float((s == "runner_exception").mean())),
        )
        .reset_index()
    )
    grouped.to_csv(out, index=False)


def _auroc(scores: np.ndarray, labels: np.ndarray) -> float:
    valid = np.isfinite(scores)
    scores = scores[valid]
    labels = labels[valid].astype(int)
    n_pos = int(labels.sum())
    n_neg = int(len(labels) - n_pos)
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(scores)
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(scores) + 1)
    pos_rank_sum = float(ranks[labels == 1].sum())
    return (pos_rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def _summary(df: pd.DataFrame, expected: int) -> pd.DataFrame:
    runner = int(((df["failure_type"] == "runner_exception") | (df.get("status") == "error")).sum()) if len(df) else 0
    oracle = df[df["baseline"] == "oracle_target"] if len(df) else df
    scores = pd.to_numeric(df["target_error_l2"], errors="coerce").to_numpy() if len(df) else np.array([])
    failure = (~df["task_success"].astype(bool)).astype(int).to_numpy() if len(df) else np.array([])
    corr = float(np.corrcoef(scores[np.isfinite(scores)], df.loc[np.isfinite(scores), "task_success"].astype(float))[0, 1]) if len(df) and np.isfinite(scores).sum() > 1 else float("nan")
    return pd.DataFrame(
        [
            {
                "expected_episodes": int(expected),
                "completed_episodes": int(len(df)),
                "complete": bool(len(df) >= expected),
                "duplicate_result_count": int(df.attrs.get("duplicate_count", 0)),
                "runner_exception_count": runner,
                "diagnostic_success_rate": float(df["diagnostic_success"].mean()) if len(df) else float("nan"),
                "task_success_rate": float(df["task_success"].mean()) if len(df) else float("nan"),
                "agreement_rate": float(df["agreement"].mean()) if len(df) else float("nan"),
                "oracle_task_success_rate": float(oracle["task_success"].mean()) if len(oracle) else float("nan"),
                "target_error_task_success_corr": corr,
                "target_error_predicts_task_failure_auroc": _auroc(scores, failure) if len(df) else float("nan"),
            }
        ]
    )


def _diagnostic_vs_task(df: pd.DataFrame, out: Path) -> None:
    grouped = (
        df.groupby(["diagnostic_success", "task_success"], dropna=False)
        .size()
        .reset_index(name="episodes")
    )
    grouped["rate"] = grouped["episodes"] / grouped["episodes"].sum() if len(grouped) else float("nan")
    grouped.to_csv(out, index=False)


def _error_bins(df: pd.DataFrame, out: Path) -> None:
    data = df.copy()
    data["target_error_l2"] = pd.to_numeric(data["target_error_l2"], errors="coerce")
    data = data[data["target_error_l2"].notna()]
    if data.empty:
        pd.DataFrame(columns=["target_error_bin", "episodes", "task_success_rate", "diagnostic_success_rate"]).to_csv(out, index=False)
        return
    data["target_error_bin"] = pd.cut(
        data["target_error_l2"], bins=ERROR_BINS, labels=ERROR_LABELS, include_lowest=True, right=False
    )
    grouped = (
        data.groupby("target_error_bin", observed=False)
        .agg(
            episodes=("task_success", "size"),
            task_success_rate=("task_success", "mean"),
            diagnostic_success_rate=("diagnostic_success", "mean"),
        )
        .reset_index()
    )
    grouped.to_csv(out, index=False)


def _oracle_gate(df: pd.DataFrame, out: Path) -> None:
    oracle = df[df["baseline"] == "oracle_target"]
    oracle = oracle.copy()
    oracle["task_success_int"] = oracle["task_success"].astype(bool).astype(int)
    grouped = (
        oracle.groupby("task", dropna=False)
        .agg(
            oracle_episodes=("task_success", "size"),
            oracle_successes=("task_success_int", "sum"),
            oracle_task_success_rate=("task_success", "mean"),
        )
        .reset_index()
    )
    intervals = [
        _wilson_ci(int(row["oracle_successes"]), int(row["oracle_episodes"]))
        for _, row in grouped.iterrows()
    ]
    grouped["oracle_task_success_ci_low"] = [lo for lo, _ in intervals]
    grouped["oracle_task_success_ci_high"] = [hi for _, hi in intervals]
    failures = oracle.copy()
    failures["failure_type"] = failures["failure_type"].fillna("success")
    failure_mode = (
        failures[~failures["task_success"].astype(bool)]
        .groupby("task")["failure_type"]
        .agg(lambda s: s.value_counts().index[0] if len(s) else "none")
    )
    grouped["dominant_failure_type"] = grouped["task"].map(failure_mode).fillna("none")
    grouped["passes_pickcube_gate_080"] = np.where(grouped["task"] == "PickCube", grouped["oracle_task_success_rate"] >= 0.80, "")
    grouped["passes_picksingleycb_gate_070"] = np.where(grouped["task"] == "PickSingleYCB", grouped["oracle_task_success_rate"] >= 0.70, "")
    grouped["passes_stackcube_gate_080"] = np.where(grouped["task"] == "StackCube", grouped["oracle_task_success_rate"] >= 0.80, "")
    grouped.to_csv(out, index=False)


def _failure_distribution(df: pd.DataFrame, out: Path) -> None:
    data = df.copy()
    data["failure_type"] = data["failure_type"].fillna("success")
    grouped = (
        data.groupby(["task", "failure_type"], dropna=False)
        .size()
        .reset_index(name="episodes")
    )
    totals = grouped.groupby("task")["episodes"].transform("sum")
    grouped["rate"] = grouped["episodes"] / totals
    grouped.to_csv(out, index=False)


def _report(df: pd.DataFrame, summary: pd.DataFrame, out: Path, input_root: Path) -> None:
    row = summary.iloc[0].to_dict()
    lines = [
        "# Closed-Loop Sanity Report",
        "",
        f"Input root: `{input_root}`",
        "",
        "## Counts",
        "",
        f"- Expected episodes: {row['expected_episodes']}",
        f"- Completed episodes: {row['completed_episodes']}",
        f"- Duplicate result count: {row['duplicate_result_count']}",
        f"- Runner exceptions: {row['runner_exception_count']}",
        "",
        "## Diagnostic Calibration",
        "",
        f"- Diagnostic success rate: {row['diagnostic_success_rate']:.4f}",
        f"- Task success rate: {row['task_success_rate']:.4f}",
        f"- Agreement rate: {row['agreement_rate']:.4f}",
        f"- Oracle task success rate: {row['oracle_task_success_rate']:.4f}",
        f"- Correlation(target error, task success): {row['target_error_task_success_corr']:.4f}",
        f"- AUROC(target error predicts task failure): {row['target_error_predicts_task_failure_auroc']:.4f}",
        "",
        "## Paper-Use Rule",
        "",
        "Use closed-loop results as Scientific Reports calibration evidence only if duplicate count is zero, runner exceptions are zero, and oracle task success passes the configured task gates.",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--expected", type=int, default=4800)
    args = parser.parse_args()

    root = Path(args.input)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = _load_records(root)
    df.to_csv(out_dir / "closed_loop_episode_index.csv", index=False)
    summary = _summary(df, args.expected)
    summary.to_csv(out_dir / "closed_loop_sanity_summary.csv", index=False)
    _group(df, ["task"], out_dir / "closed_loop_sanity_by_task.csv")
    _group(df, ["target_source"], out_dir / "closed_loop_sanity_by_source.csv")
    _group(df, ["stressor", "level"], out_dir / "closed_loop_sanity_by_stressor.csv")
    _diagnostic_vs_task(df, out_dir / "closed_loop_diagnostic_vs_task_success.csv")
    _error_bins(df, out_dir / "closed_loop_target_error_bins.csv")
    _oracle_gate(df, out_dir / "closed_loop_oracle_gate_by_task.csv")
    _failure_distribution(df, out_dir / "closed_loop_failure_distribution.csv")
    _report(df, summary, out_dir / "closed_loop_sanity_report.md", root)
    print(f"Wrote closed-loop sanity artifacts under {out_dir}")


if __name__ == "__main__":
    main()
