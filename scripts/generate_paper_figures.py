from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


BASELINE_ORDER = [
    "oracle_target",
    "crop_median_depth",
    "box_center_depth",
    "crop_top_surface",
    "crop_median_depth_query_aware",
    "crop_median_depth_first_detection",
    "box_center_depth_query_aware",
    "box_center_depth_first_detection",
    "crop_top_surface_query_aware",
    "crop_top_surface_first_detection",
]


def _parse_run(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise argparse.ArgumentTypeError("Run must be LABEL=PATH")
    label, path = spec.split("=", 1)
    return label.strip(), Path(path)


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _read_success(root: Path) -> pd.DataFrame:
    csv_path = root / "success_by_group.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing {csv_path}; run make_report first.")
    return pd.read_csv(csv_path)


def _weighted_success(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    tmp = df.copy()
    tmp["success_sum"] = tmp["success_rate"] * tmp["n"]
    out = (
        tmp.groupby(group_cols, dropna=False)
        .agg(success_sum=("success_sum", "sum"), n=("n", "sum"))
        .reset_index()
    )
    out["success_rate"] = out["success_sum"] / out["n"]
    return out.drop(columns=["success_sum"])


def _baseline_rank(name: str) -> int:
    try:
        return BASELINE_ORDER.index(name)
    except ValueError:
        return len(BASELINE_ORDER)


def _clean_label(text: str) -> str:
    return (
        text.replace("_query_aware", "\nquery")
        .replace("_first_detection", "\nfirst")
        .replace("_", " ")
    )


def _save_figure(fig: plt.Figure, out_dir: Path, name: str) -> None:
    fig.tight_layout()
    fig.savefig(out_dir / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(out_dir / f"{name}.png", dpi=240, bbox_inches="tight")
    plt.close(fig)


def _plot_baseline_summary(runs: list[tuple[str, Path]], out_dir: Path) -> pd.DataFrame:
    rows = []
    for label, root in runs:
        df = _weighted_success(_read_success(root), ["baseline"])
        oracle = df.loc[df["baseline"] == "oracle_target", "success_rate"]
        oracle_rate = float(oracle.iloc[0]) if not oracle.empty else float("nan")
        df["oracle_gap"] = oracle_rate - df["success_rate"]
        df["run"] = label
        rows.append(df)
    data = pd.concat(rows, ignore_index=True)
    data = data.sort_values(["run", "baseline"], key=lambda s: s.map(_baseline_rank) if s.name == "baseline" else s)
    data.to_csv(out_dir / "baseline_summary_generated.csv", index=False)

    plot_data = data[data["baseline"].isin(["oracle_target", "crop_median_depth", "box_center_depth", "crop_top_surface"])]
    if plot_data.empty:
        return data
    pivot = plot_data.pivot(index="baseline", columns="run", values="success_rate")
    pivot = pivot.reindex([b for b in BASELINE_ORDER if b in pivot.index])

    fig, ax = plt.subplots(figsize=(8.2, 3.2))
    pivot.plot(kind="bar", ax=ax, width=0.78)
    ax.set_ylabel("Success rate")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("")
    ax.set_xticklabels([_clean_label(x.get_text()) for x in ax.get_xticklabels()], rotation=0, ha="center")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(title="Run", frameon=False, ncols=2)
    _save_figure(fig, out_dir, "fig_baseline_success")
    return data


def _plot_hard_stressors(label: str, root: Path, out_dir: Path) -> pd.DataFrame:
    df = _read_success(root)
    if "level" not in df.columns:
        return pd.DataFrame()
    l3 = _weighted_success(df[df["level"] == 3], ["stressor"])
    if l3.empty:
        return l3
    l3 = l3.sort_values("success_rate", ascending=True)
    l3.to_csv(out_dir / f"hard_l3_stressors_{label}.csv", index=False)

    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    ax.barh([_clean_label(x) for x in l3["stressor"]], l3["success_rate"], color="#3f6f8f")
    ax.set_xlabel("Success rate at level 3")
    ax.set_xlim(0, 1.05)
    ax.grid(axis="x", alpha=0.25)
    _save_figure(fig, out_dir, f"fig_hard_l3_stressors_{label}")
    return l3


def _plot_selector_effect(label: str, root: Path, out_dir: Path) -> pd.DataFrame:
    df = _weighted_success(_read_success(root), ["baseline"])
    by_baseline = dict(zip(df["baseline"], df["success_rate"]))
    rows = []
    for target_source in ["box_center_depth", "crop_median_depth", "crop_top_surface"]:
        query = by_baseline.get(f"{target_source}_query_aware")
        first = by_baseline.get(f"{target_source}_first_detection")
        if query is None or first is None:
            continue
        rows.append(
            {
                "target_source": target_source,
                "query_aware": query,
                "first_detection": first,
                "delta": query - first,
            }
        )
    data = pd.DataFrame(rows)
    if data.empty:
        return data
    data.to_csv(out_dir / f"selector_effect_{label}.csv", index=False)

    x = range(len(data))
    width = 0.36
    fig, ax = plt.subplots(figsize=(7.0, 3.2))
    ax.bar([i - width / 2 for i in x], data["query_aware"], width=width, label="Query-aware", color="#2f7d5b")
    ax.bar([i + width / 2 for i in x], data["first_detection"], width=width, label="First detection", color="#9a4a44")
    for i, delta in enumerate(data["delta"]):
        ax.text(i, max(data.loc[i, "query_aware"], data.loc[i, "first_detection"]) + 0.025, f"+{delta:.3f}", ha="center", fontsize=8)
    ax.set_xticks(list(x), [_clean_label(v) for v in data["target_source"]])
    ax.set_ylabel("Success rate")
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    _save_figure(fig, out_dir, f"fig_selector_effect_{label}")
    return data


def _plot_failure_distribution(label: str, root: Path, out_dir: Path) -> pd.DataFrame:
    counts: Counter[str] = Counter()
    for path in root.rglob("*.json"):
        if path.name == "experiment_config_snapshot.json":
            continue
        try:
            with open(path, encoding="utf-8") as f:
                rec = json.load(f)
        except Exception:
            continue
        if "task" not in rec or "baseline" not in rec:
            continue
        failure_type = rec.get("failure_type") or ("success" if rec.get("success") else "unknown")
        counts[failure_type] += 1
    data = pd.DataFrame(
        [{"failure_type": key, "count": value} for key, value in counts.most_common()]
    )
    if data.empty:
        return data
    data["fraction"] = data["count"] / data["count"].sum()
    data.to_csv(out_dir / f"failure_distribution_{label}.csv", index=False)

    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    ax.bar([_clean_label(x) for x in data["failure_type"]], data["fraction"], color="#665a8f")
    ax.set_ylabel("Fraction of episodes")
    ax.set_ylim(0, 1.0)
    ax.tick_params(axis="x", rotation=20)
    ax.grid(axis="y", alpha=0.25)
    _save_figure(fig, out_dir, f"fig_failure_distribution_{label}")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate paper figures from completed EmbodiedStressBench reports.")
    parser.add_argument("--run", action="append", type=_parse_run, required=True, metavar="LABEL=PATH")
    parser.add_argument("--semantic-run", type=_parse_run, default=None, metavar="LABEL=PATH")
    parser.add_argument("--hard-run", type=_parse_run, default=None, metavar="LABEL=PATH")
    parser.add_argument("--output-dir", default="paper/generated")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    _ensure_dir(out_dir)
    _plot_baseline_summary(args.run, out_dir)
    if args.hard_run is not None:
        _plot_hard_stressors(*args.hard_run, out_dir)
    if args.semantic_run is not None:
        _plot_selector_effect(*args.semantic_run, out_dir)
        _plot_failure_distribution(*args.semantic_run, out_dir)
    print(f"Wrote figures and CSV summaries under {out_dir}")


if __name__ == "__main__":
    main()
