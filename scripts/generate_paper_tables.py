from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from embodied_stressbench.metrics.aggregation import aggregate_summary, load_results
from embodied_stressbench.utils.io import ensure_dir


def _escape_tex(value: object) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "_": r"\_",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
        "$": r"\$",
        "{": r"\{",
        "}": r"\}",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def _parse_run(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise argparse.ArgumentTypeError("Run must be LABEL=PATH")
    label, path = spec.split("=", 1)
    label = label.strip()
    if not label:
        raise argparse.ArgumentTypeError("Run label cannot be empty")
    return label, Path(path)


def _baseline_summary(label: str, df: pd.DataFrame) -> pd.DataFrame:
    summary = aggregate_summary(df, ["baseline"])
    if summary.empty:
        return summary
    oracle_rows = summary[summary["baseline"] == "oracle_target"]
    oracle_rate = float(oracle_rows["success_rate"].iloc[0]) if not oracle_rows.empty else float("nan")
    summary = summary.copy()
    summary.insert(0, "run", label)
    summary["oracle_gap"] = oracle_rate - summary["success_rate"]
    summary.loc[summary["baseline"] == "oracle_target", "oracle_gap"] = pd.NA
    return summary[["run", "baseline", "success_rate", "n", "mean_error", "oracle_gap"]]


def _selector_effect(df: pd.DataFrame) -> pd.DataFrame:
    summary = aggregate_summary(df, ["baseline"])
    if summary.empty:
        return pd.DataFrame()
    by_baseline = dict(zip(summary["baseline"], summary["success_rate"]))
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
    return pd.DataFrame(rows)


def _format_float(value: object, digits: int = 3, signed: bool = False) -> str:
    if pd.isna(value):
        return "--"
    number = float(value)
    fmt = f"{{:{'+' if signed else ''}.{digits}f}}"
    return fmt.format(number)


def _latex_table(headers: list[str], rows: Iterable[list[object]], caption: str, label: str) -> str:
    colspec = "l" + "r" * (len(headers) - 1)
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        rf"\begin{{tabular}}{{{colspec}}}",
        r"\hline",
        " & ".join(_escape_tex(h) for h in headers) + r" \\",
        r"\hline",
    ]
    for row in rows:
        lines.append(" & ".join(_escape_tex(cell) for cell in row) + r" \\")
    lines.extend([r"\hline", r"\end{tabular}", r"\end{table}", ""])
    return "\n".join(lines)


def _baseline_latex(df: pd.DataFrame) -> str:
    rows = []
    for _, row in df.iterrows():
        rows.append(
            [
                row["run"],
                row["baseline"],
                _format_float(row["success_rate"]),
                int(row["n"]),
                _format_float(row["oracle_gap"]),
            ]
        )
    return _latex_table(
        ["Run", "Baseline", "Success rate", "Episodes", "Oracle gap"],
        rows,
        "Generated baseline-level success and oracle gaps.",
        "tab:generated-baseline-summary",
    )


def _selector_latex(df: pd.DataFrame) -> str:
    rows = []
    for _, row in df.iterrows():
        rows.append(
            [
                row["target_source"],
                _format_float(row["query_aware"]),
                _format_float(row["first_detection"]),
                _format_float(row["delta"], signed=True),
            ]
        )
    return _latex_table(
        ["Target source", "Query-aware", "First detection", "Delta"],
        rows,
        "Generated selector effect for semantic distractor validity.",
        "tab:generated-selector-effect",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate paper-ready LaTeX tables from EmbodiedStressBench outputs.")
    parser.add_argument(
        "--run",
        action="append",
        type=_parse_run,
        required=True,
        metavar="LABEL=PATH",
        help="Result root to include. May be repeated.",
    )
    parser.add_argument("--output", default="paper/generated/results_tables.tex")
    parser.add_argument("--csv-dir", default="paper/generated")
    args = parser.parse_args()

    output_path = Path(args.output)
    csv_dir = Path(args.csv_dir)
    ensure_dir(output_path.parent)
    ensure_dir(csv_dir)

    baseline_tables = []
    selector_tables = []
    for label, path in args.run:
        df = load_results(path)
        if df.empty:
            raise SystemExit(f"No result records found for {label}: {path}")
        baseline = _baseline_summary(label, df)
        baseline_tables.append(baseline)
        selector = _selector_effect(df)
        if not selector.empty:
            selector.insert(0, "run", label)
            selector_tables.append(selector)

    baseline_all = pd.concat(baseline_tables, ignore_index=True)
    baseline_all.to_csv(csv_dir / "generated_baseline_summary.csv", index=False)

    tex_chunks = [
        "% Auto-generated by scripts/generate_paper_tables.py.",
        "% Do not edit numeric values by hand.",
        "",
        _baseline_latex(baseline_all),
    ]

    if selector_tables:
        selector_all = pd.concat(selector_tables, ignore_index=True)
        selector_all.to_csv(csv_dir / "generated_selector_effect.csv", index=False)
        for run_label, group in selector_all.groupby("run", sort=False):
            tex_chunks.append(f"% Selector effect for {run_label}")
            tex_chunks.append(_selector_latex(group.drop(columns=["run"])))

    output_path.write_text("\n".join(tex_chunks), encoding="utf-8")
    print(f"Wrote {output_path}")
    print(f"Wrote CSV summaries under {csv_dir}")


if __name__ == "__main__":
    main()
