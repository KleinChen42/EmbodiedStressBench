from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
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


def _effective_error(row: pd.Series) -> float | None:
    debug = row.get("execution_debug")
    if isinstance(debug, dict) and debug.get("target_error_l2") is not None:
        return float(debug["target_error_l2"])
    value = row.get("target_error_l2")
    if pd.isna(value):
        return None
    return float(value)


def _load_json_with_execution_debug(root: Path) -> pd.DataFrame:
    records = []
    for path in root.rglob("*.json"):
        if path.name == "experiment_config_snapshot.json":
            continue
        try:
            with open(path, encoding="utf-8") as f:
                rec = json.load(f)
        except Exception:
            continue
        if "task" in rec and "baseline" in rec:
            records.append(rec)
    return pd.DataFrame(records)


def _escape_tex(value: object) -> str:
    text = str(value)
    return text.replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")


def _write_tex(df: pd.DataFrame, path: Path) -> None:
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Threshold sensitivity of diagnostic target success. Success is recomputed from stored target-error values at each threshold.}",
        r"\label{tab:threshold-sensitivity}",
        r"\begin{tabular}{llrr}",
        r"\hline",
        r"Run & Baseline & Threshold (m) & Success rate \\",
        r"\hline",
    ]
    for _, row in df.iterrows():
        lines.append(
            f"{_escape_tex(row['run'])} & {_escape_tex(row['baseline'])} & {float(row['threshold_m']):.2f} & {float(row['success_rate']):.3f} \\\\"
        )
    lines.extend([r"\hline", r"\end{tabular}", r"\end{table}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="append", type=_parse_run, required=True, metavar="LABEL=PATH")
    parser.add_argument("--thresholds", nargs="*", type=float, default=[0.04, 0.06, 0.08, 0.10])
    parser.add_argument("--output-dir", default="ieee_access_revision_20260520")
    parser.add_argument("--tables-dir", default="paper/ieee_access/tables")
    parser.add_argument("--figures-dir", default="paper/ieee_access/figures")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    tables_dir = Path(args.tables_dir)
    figures_dir = Path(args.figures_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for label, root in args.run:
        df = _load_json_with_execution_debug(root)
        if df.empty:
            # Fall back to aggregation loader if JSON schema lacks debug fields.
            df = load_results(root)
        if df.empty:
            raise SystemExit(f"No records found for {label}: {root}")
        errors = df.apply(_effective_error, axis=1)
        tmp = df.copy()
        tmp["effective_target_error_l2"] = errors
        for threshold in args.thresholds:
            valid = tmp["effective_target_error_l2"].notna()
            recomputed = valid & (tmp["effective_target_error_l2"] <= threshold)
            grouped = tmp.assign(recomputed_success=recomputed).groupby("baseline", dropna=False)
            for baseline, group in grouped:
                rows.append(
                    {
                        "run": label,
                        "baseline": baseline,
                        "threshold_m": threshold,
                        "success_rate": float(group["recomputed_success"].mean()),
                        "n": int(len(group)),
                    }
                )
    result = pd.DataFrame(rows)
    csv_path = out_dir / "threshold_sensitivity.csv"
    tex_path = tables_dir / "threshold_sensitivity.tex"
    result.to_csv(csv_path, index=False)
    _write_tex(result, tex_path)

    main_baselines = ["oracle_target", "box_center_depth", "crop_median_depth", "crop_top_surface"]
    plot_data = result[result["baseline"].isin(main_baselines)].copy()
    if "Heldout" in set(plot_data["run"]):
        plot_data = plot_data[plot_data["run"] == "Heldout"].copy()
    if not plot_data.empty:
        fig, ax = plt.subplots(figsize=(7.2, 3.2))
        order = {name: idx for idx, name in enumerate(main_baselines)}
        plot_data["baseline_order"] = plot_data["baseline"].map(order)
        for baseline, group in plot_data.sort_values("baseline_order").groupby("baseline"):
            group = group.sort_values("threshold_m")
            ax.plot(group["threshold_m"], group["success_rate"], marker="o", label=baseline.replace("_", " "))
        ax.set_xlabel("Success threshold (m)")
        ax.set_ylabel("Recomputed success rate")
        ax.set_ylim(0, 1.05)
        ax.grid(alpha=0.25)
        ax.legend(frameon=False, fontsize=8, ncols=2)
        fig.tight_layout()
        fig.savefig(figures_dir / "threshold_sensitivity.pdf", bbox_inches="tight")
        fig.savefig(figures_dir / "threshold_sensitivity.png", dpi=240, bbox_inches="tight")
        plt.close(fig)

    print(f"Wrote {csv_path}")
    print(f"Wrote {tex_path}")


if __name__ == "__main__":
    main()
