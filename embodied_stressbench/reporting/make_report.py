from __future__ import annotations

import argparse
from pathlib import Path

from embodied_stressbench.metrics.aggregation import aggregate_success, load_results
from embodied_stressbench.utils.io import ensure_dir


def _to_markdown_fallback(df) -> str:
    """Render a compact markdown table without requiring pandas' tabulate extra."""
    try:
        return df.to_markdown(index=False)
    except ImportError:
        if df.empty:
            return "_No rows._"
        headers = [str(col) for col in df.columns]
        rows = [[str(value) for value in row] for row in df.to_numpy()]
        widths = [
            max(len(headers[idx]), *(len(row[idx]) for row in rows))
            for idx in range(len(headers))
        ]
        header = "| " + " | ".join(text.ljust(widths[idx]) for idx, text in enumerate(headers)) + " |"
        sep = "| " + " | ".join("-" * widths[idx] for idx in range(len(headers))) + " |"
        body = [
            "| " + " | ".join(text.ljust(widths[idx]) for idx, text in enumerate(row)) + " |"
            for row in rows
        ]
        return "\n".join([header, sep, *body])


def make_report(input_dir: str | Path, output_path: str | Path) -> None:
    df = load_results(input_dir)
    out_path = Path(output_path)
    ensure_dir(out_path.parent)

    if df.empty:
        out_path.write_text("# EmbodiedStressBench Report\n\nNo results found.\n", encoding="utf-8")
        return

    agg = aggregate_success(df)
    csv_path = out_path.parent / "success_by_group.csv"
    agg.to_csv(csv_path, index=False)

    lines = []
    lines.append("# EmbodiedStressBench Report")
    lines.append("")
    lines.append(f"Input directory: `{input_dir}`")
    lines.append(f"Number of runs: **{len(df)}**")
    lines.append("")
    lines.append("## Overall success")
    lines.append("")
    lines.append(f"Mean success rate: **{df['success'].mean():.3f}**")
    lines.append("")
    lines.append("## Success by task / baseline / stressor / level")
    lines.append("")
    lines.append(_to_markdown_fallback(agg))
    lines.append("")
    lines.append("## Failure distribution")
    lines.append("")
    if "failure_type" in df.columns:
        failure_counts = df["failure_type"].fillna("success").value_counts().reset_index()
        failure_counts.columns = ["failure_type", "count"]
        lines.append(_to_markdown_fallback(failure_counts))
    lines.append("")
    lines.append(f"CSV table saved to `{csv_path}`.")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    make_report(args.input, args.output)


if __name__ == "__main__":
    main()
