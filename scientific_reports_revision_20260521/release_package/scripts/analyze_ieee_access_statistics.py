from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from embodied_stressbench.metrics.aggregation import load_results


def _parse_run(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise argparse.ArgumentTypeError("Run must be LABEL=PATH")
    label, path = spec.split("=", 1)
    return label.strip(), Path(path)


def _bootstrap_ci(values: np.ndarray, rng: np.random.Generator, n_boot: int) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return float("nan"), float("nan"), float("nan")
    mean = float(values.mean())
    if len(values) == 1:
        return mean, mean, mean
    samples = rng.choice(values, size=(n_boot, len(values)), replace=True).mean(axis=1)
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return mean, float(lo), float(hi)


def _seed_metric(df: pd.DataFrame, group_cols: list[str], metric_col: str = "success") -> pd.DataFrame:
    return (
        df.groupby(group_cols + ["seed"], dropna=False)
        .agg(value=(metric_col, "mean"), episodes=(metric_col, "size"))
        .reset_index()
    )


def _summarize_seed_bootstrap(
    df: pd.DataFrame,
    run_label: str,
    group_cols: list[str],
    rng: np.random.Generator,
    n_boot: int,
) -> pd.DataFrame:
    per_seed = _seed_metric(df, group_cols)
    rows = []
    for key, group in per_seed.groupby(group_cols, dropna=False):
        if not isinstance(key, tuple):
            key = (key,)
        mean, lo, hi = _bootstrap_ci(group["value"].to_numpy(), rng, n_boot)
        row = {"run": run_label, "success_rate": mean, "ci_low": lo, "ci_high": hi, "n": int(group["episodes"].sum()), "seed_blocks": int(len(group))}
        row.update(dict(zip(group_cols, key)))
        rows.append(row)
    return pd.DataFrame(rows)


def _oracle_gap_with_ci(df: pd.DataFrame, run_label: str, rng: np.random.Generator, n_boot: int) -> pd.DataFrame:
    per_seed = _seed_metric(df, ["baseline"])
    pivot = per_seed.pivot_table(index="seed", columns="baseline", values="value", aggfunc="mean")
    if "oracle_target" not in pivot.columns:
        return pd.DataFrame()
    rows = []
    for baseline in pivot.columns:
        if baseline == "oracle_target":
            continue
        values = (pivot["oracle_target"] - pivot[baseline]).dropna().to_numpy()
        mean, lo, hi = _bootstrap_ci(values, rng, n_boot)
        n = int(df[df["baseline"] == baseline].shape[0])
        rows.append({"run": run_label, "baseline": baseline, "oracle_gap": mean, "ci_low": lo, "ci_high": hi, "n": n, "seed_blocks": int(len(values))})
    return pd.DataFrame(rows)


def _oracle_gap_by_stressor_with_ci(df: pd.DataFrame, run_label: str, rng: np.random.Generator, n_boot: int) -> pd.DataFrame:
    per_seed = _seed_metric(df, ["stressor", "baseline"])
    pivot = per_seed.pivot_table(index=["seed", "stressor"], columns="baseline", values="value", aggfunc="mean")
    if "oracle_target" not in pivot.columns:
        return pd.DataFrame()
    rows = []
    for baseline in pivot.columns:
        if baseline == "oracle_target":
            continue
        gap = (pivot["oracle_target"] - pivot[baseline]).dropna().reset_index(name="gap")
        for stressor, group in gap.groupby("stressor"):
            values = group["gap"].to_numpy()
            mean, lo, hi = _bootstrap_ci(values, rng, n_boot)
            rows.append(
                {
                    "run": run_label,
                    "stressor": stressor,
                    "baseline": baseline,
                    "oracle_gap": mean,
                    "ci_low": lo,
                    "ci_high": hi,
                    "seed_blocks": int(len(values)),
                }
            )
    return pd.DataFrame(rows)


def _failure_distribution_with_ci(df: pd.DataFrame, run_label: str, rng: np.random.Generator, n_boot: int) -> pd.DataFrame:
    tmp = df.copy()
    tmp["failure_label"] = tmp["failure_type"].fillna("success")
    labels = sorted(tmp["failure_label"].unique())
    per_seed_rows = []
    for seed, group in tmp.groupby("seed"):
        counts = Counter(group["failure_label"])
        total = len(group)
        for label in labels:
            per_seed_rows.append({"seed": seed, "failure_type": label, "fraction": counts[label] / total if total else 0.0, "count": counts[label]})
    per_seed = pd.DataFrame(per_seed_rows)
    rows = []
    total_counts = tmp["failure_label"].value_counts().to_dict()
    for label, group in per_seed.groupby("failure_type"):
        mean, lo, hi = _bootstrap_ci(group["fraction"].to_numpy(), rng, n_boot)
        rows.append({"run": run_label, "failure_type": label, "fraction": mean, "ci_low": lo, "ci_high": hi, "count": int(total_counts.get(label, 0))})
    return pd.DataFrame(rows)


def _escape_tex(value: object) -> str:
    text = str(value)
    for src, dst in {"_": r"\_", "%": r"\%", "&": r"\&", "#": r"\#", "$": r"\$"}.items():
        text = text.replace(src, dst)
    return text


def _fmt(value: object) -> str:
    if pd.isna(value):
        return "--"
    return f"{float(value):.3f}"


def _write_tex(df: pd.DataFrame, path: Path, columns: list[str], caption: str, label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        r"\begin{tabular}{" + "l" * len(columns) + "}",
        r"\hline",
        " & ".join(_escape_tex(c) for c in columns) + r" \\",
        r"\hline",
    ]
    for _, row in df.iterrows():
        vals = []
        for c in columns:
            v = row[c]
            vals.append(_fmt(v) if isinstance(v, float) or c in {"success_rate", "ci_low", "ci_high", "oracle_gap", "fraction"} else _escape_tex(v))
        lines.append(" & ".join(vals) + r" \\")
    lines.extend([r"\hline", r"\end{tabular}", r"\end{table*}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def load_all(runs: list[tuple[str, Path]]) -> dict[str, pd.DataFrame]:
    out = {}
    for label, path in runs:
        df = load_results(path)
        if df.empty:
            raise SystemExit(f"No JSON result records found for {label}: {path}")
        df = df.copy()
        df["success"] = df["success"].astype(bool)
        out[label] = df
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute IEEE Access statistics with seed-block bootstrap CIs.")
    parser.add_argument("--run", action="append", type=_parse_run, required=True, metavar="LABEL=PATH")
    parser.add_argument("--output-dir", default="ieee_access_revision_20260520")
    parser.add_argument("--tables-dir", default="paper/ieee_access/tables")
    parser.add_argument("--bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260520)
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    tables_dir = Path(args.tables_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    runs = load_all(args.run)

    main_rows = []
    gap_rows = []
    stressor_rows = []
    gap_stressor_rows = []
    failure_rows = []
    for label, df in runs.items():
        main_rows.append(_summarize_seed_bootstrap(df, label, ["baseline"], rng, args.bootstrap))
        gap_rows.append(_oracle_gap_with_ci(df, label, rng, args.bootstrap))
        gap_stressor_rows.append(_oracle_gap_by_stressor_with_ci(df, label, rng, args.bootstrap))
        stressor_rows.append(_summarize_seed_bootstrap(df, label, ["stressor"], rng, args.bootstrap))
        failure_rows.append(_failure_distribution_with_ci(df, label, rng, args.bootstrap))

    main_results = pd.concat(main_rows, ignore_index=True)
    oracle_gap = pd.concat([x for x in gap_rows if not x.empty], ignore_index=True)
    oracle_gap_by_stressor = pd.concat([x for x in gap_stressor_rows if not x.empty], ignore_index=True)
    stressor_ranking = pd.concat(stressor_rows, ignore_index=True).sort_values(["run", "success_rate"])
    failure_dist = pd.concat(failure_rows, ignore_index=True)

    outputs = [
        ("main_results_with_ci", main_results, ["run", "baseline", "success_rate", "ci_low", "ci_high", "n", "seed_blocks"]),
        ("oracle_gap_with_ci", oracle_gap, ["run", "baseline", "oracle_gap", "ci_low", "ci_high", "n", "seed_blocks"]),
        ("oracle_gap_by_stressor_with_ci", oracle_gap_by_stressor, ["run", "stressor", "baseline", "oracle_gap", "ci_low", "ci_high", "seed_blocks"]),
        ("stressor_ranking_with_ci", stressor_ranking, ["run", "stressor", "success_rate", "ci_low", "ci_high", "n", "seed_blocks"]),
        ("failure_distribution_with_ci", failure_dist, ["run", "failure_type", "fraction", "ci_low", "ci_high", "count"]),
    ]
    for name, df, cols in outputs:
        csv_path = out_dir / f"{name}.csv"
        tex_path = tables_dir / f"{name}.tex"
        df.to_csv(csv_path, index=False)
        _write_tex(df[cols], tex_path, cols, name.replace("_", " ").title(), f"tab:{name.replace('_', '-')}")
        print(f"Wrote {csv_path}")
        print(f"Wrote {tex_path}")


if __name__ == "__main__":
    main()
