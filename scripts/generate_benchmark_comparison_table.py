from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROWS = [
    {
        "benchmark": "EmbodiedStressBench (ours)",
        "primary_focus": "Language-to-3D-target diagnosis",
        "language_tasks": "Yes",
        "stressors": "Parameterized semantic, visual, geometric, execution",
        "oracle_gap": "Yes",
        "failure_taxonomy": "Yes",
        "detector_plugins": "Metadata, first detection, CLIP interface, GroundingDINO",
        "artifact_style": "JSON episodes, YAML configs, generated tables",
        "citation": "",
    },
    {
        "benchmark": "ManiSkill",
        "primary_focus": "Simulation tasks and policy evaluation",
        "language_tasks": "Limited / task-dependent",
        "stressors": "Not the main abstraction",
        "oracle_gap": "No",
        "failure_taxonomy": "No",
        "detector_plugins": "Not central",
        "artifact_style": "Environments, assets, demonstrations",
        "citation": r"\cite{gu2021maniskill,gu2023maniskill2}",
    },
    {
        "benchmark": "CALVIN",
        "primary_focus": "Long-horizon language-conditioned manipulation",
        "language_tasks": "Yes",
        "stressors": "Not parameterized for target-generation diagnosis",
        "oracle_gap": "No",
        "failure_taxonomy": "No",
        "detector_plugins": "Policy-level perception",
        "artifact_style": "Tasks, language annotations, evaluation protocol",
        "citation": r"\cite{mees2022calvin}",
    },
    {
        "benchmark": "SIMPLER",
        "primary_focus": "Sim-to-real policy evaluation",
        "language_tasks": "Yes / policy-dependent",
        "stressors": "Evaluation realism rather than controlled target stressors",
        "oracle_gap": "No",
        "failure_taxonomy": "No",
        "detector_plugins": "Policy-level perception",
        "artifact_style": "Simulation evaluation suite",
        "citation": r"\cite{li2024simpler}",
    },
    {
        "benchmark": "VLABench",
        "primary_focus": "Vision-language-agent task evaluation",
        "language_tasks": "Yes",
        "stressors": "Broad task variation, not target-source oracle-gap sweeps",
        "oracle_gap": "No",
        "failure_taxonomy": "Limited",
        "detector_plugins": "Agent-level perception",
        "artifact_style": "Benchmark tasks and evaluation",
        "citation": r"\cite{zhang2024vlabench}",
    },
]


def _tex_escape(text: str) -> str:
    if "\\" in text:
        return text
    return (
        text.replace("&", r"\&")
        .replace("%", r"\%")
        .replace("_", r"\_")
        .replace("#", r"\#")
    )


def _write_tex(df: pd.DataFrame, path: Path) -> None:
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{Comparison with representative manipulation and embodied-AI benchmarks. EmbodiedStressBench is complementary: it diagnoses the language-to-target stage rather than replacing policy-level benchmarks.}",
        r"\label{tab:benchmark-comparison}",
        r"\scriptsize",
        r"\begin{tabular}{p{0.15\textwidth}p{0.18\textwidth}p{0.10\textwidth}p{0.19\textwidth}p{0.09\textwidth}p{0.10\textwidth}p{0.13\textwidth}}",
        r"\toprule",
        r"Benchmark & Primary focus & Language tasks & Controlled stressors & Oracle gap & Failure taxonomy & Detector plug-ins \\",
        r"\midrule",
    ]
    for row in df.to_dict("records"):
        name = _tex_escape(row["benchmark"])
        citation = row["citation"]
        if citation:
            name = f"{name} {citation}"
        lines.append(
            " & ".join(
                [
                    name,
                    _tex_escape(row["primary_focus"]),
                    _tex_escape(row["language_tasks"]),
                    _tex_escape(row["stressors"]),
                    _tex_escape(row["oracle_gap"]),
                    _tex_escape(row["failure_taxonomy"]),
                    _tex_escape(row["detector_plugins"]),
                ]
            )
            + r" \\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="ieee_access_revision_20260520")
    parser.add_argument("--tables-dir", default="paper/ieee_access/tables")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    tables_dir = Path(args.tables_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(ROWS)
    df.to_csv(out_dir / "benchmark_comparison_table.csv", index=False)
    _write_tex(df, tables_dir / "benchmark_comparison_table.tex")
    print(f"Wrote {out_dir / 'benchmark_comparison_table.csv'}")
    print(f"Wrote {tables_dir / 'benchmark_comparison_table.tex'}")


if __name__ == "__main__":
    main()
