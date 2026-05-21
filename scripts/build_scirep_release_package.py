from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
from pathlib import Path


REPO_URL = "https://github.com/KleinChen42/EmbodiedStressBench.git"
RELEASE_TAG = "v0.1.0-scirep"
ZENODO_PLACEHOLDER = "TO_BE_FILLED_AFTER_ZENODO_ARCHIVE"


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "UNKNOWN_COMMIT"


def _copy_file(src: Path, dst: Path, rows: list[dict[str, str]], role: str) -> None:
    if not src.exists():
        rows.append({"path": str(dst), "source": str(src), "role": role, "status": "missing"})
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    rows.append({"path": str(dst), "source": str(src), "role": role, "status": "included"})


def _copy_glob(src_dir: Path, pattern: str, dst_dir: Path, rows: list[dict[str, str]], role: str) -> None:
    for src in sorted(src_dir.glob(pattern)):
        if src.is_file():
            _copy_file(src, dst_dir / src.name, rows, role)


def build_package(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []

    _copy_file(Path("README_REPRODUCIBILITY.md"), out_dir / "README_REPRODUCIBILITY.md", rows, "reproducibility")
    _copy_file(Path("schemas/episode_result_schema.json"), out_dir / "schemas/episode_result_schema.json", rows, "schema")
    _copy_file(Path("docs/scientific_reports_result_to_claim.md"), out_dir / "docs/scientific_reports_result_to_claim.md", rows, "audit")
    _copy_file(Path("docs/claim_evidence_table_scientific_reports.md"), out_dir / "docs/claim_evidence_table_scientific_reports.md", rows, "audit")
    _copy_file(Path("docs/scientific_reports_experiment_status.md"), out_dir / "docs/scientific_reports_experiment_status.md", rows, "audit")
    _copy_file(Path("docs/scirep_data_code_release_checklist.md"), out_dir / "docs/scirep_data_code_release_checklist.md", rows, "metadata")
    _copy_file(Path("scientific_reports_revision_20260521/final_scirep_revision_report.md"), out_dir / "docs/final_scirep_revision_report.md", rows, "audit")
    _copy_file(Path("scientific_reports_revision_20260521/qualitative_case_manifest.csv"), out_dir / "source_data/qualitative_case_manifest.csv", rows, "source data")
    _copy_file(
        Path("scientific_reports_revision_20260521/scirep_open_vocab_detector_transfer_combined.csv"),
        out_dir / "source_data/scirep_open_vocab_detector_transfer_combined.csv",
        rows,
        "source data",
    )

    _copy_glob(Path("paper/scientific_reports/tables"), "*.csv", out_dir / "source_data/tables", rows, "source data")
    _copy_glob(Path("outputs/scirep_query_ablation_20260521"), "*.csv", out_dir / "source_data/query_ablation", rows, "source data")
    _copy_glob(Path("outputs/scirep_query_ablation_20260521"), "*.md", out_dir / "source_data/query_ablation", rows, "audit")
    _copy_glob(Path("outputs/ycb_true_name_probe_20260521"), "*.csv", out_dir / "source_data/target_name_probe", rows, "source data")
    _copy_glob(Path("outputs/ycb_true_name_probe_20260521"), "*.md", out_dir / "source_data/target_name_probe", rows, "audit")
    _copy_glob(Path("outputs/scirep_closed_loop_oracle_calibration_v2_20260521/smoke"), "*.csv", out_dir / "source_data/closed_loop_oracle_calibration_v2", rows, "source data")
    _copy_glob(Path("outputs/scirep_closed_loop_oracle_calibration_v2_20260521/smoke"), "*.md", out_dir / "source_data/closed_loop_oracle_calibration_v2", rows, "audit")
    _copy_glob(Path("outputs/scirep_oracle_failure_breakdown_20260521"), "*.csv", out_dir / "source_data/oracle_failure_breakdown", rows, "source data")
    _copy_glob(Path("outputs/scirep_oracle_failure_breakdown_20260521"), "*.md", out_dir / "source_data/oracle_failure_breakdown", rows, "audit")
    _copy_file(Path("outputs/closed_loop_oracle_calibration_v2_20260521_report.md"), out_dir / "source_data/closed_loop_oracle_calibration_v2/report.md", rows, "audit")
    _copy_file(Path("outputs/open_vocab_true_name_query_ablation_20260521_report.md"), out_dir / "source_data/target_name_probe/report.md", rows, "audit")
    _copy_glob(Path("paper/scientific_reports/tables"), "*.tex", out_dir / "paper_tables", rows, "paper table")
    _copy_glob(Path("paper/scientific_reports/figures"), "*.png", out_dir / "figures", rows, "figure")
    _copy_glob(Path("paper/scientific_reports/figures"), "*.pdf", out_dir / "figures", rows, "figure")
    _copy_glob(Path("paper/scientific_reports/figures"), "**/*.png", out_dir / "figures", rows, "figure")
    _copy_glob(Path("paper/scientific_reports/figures"), "**/*.pdf", out_dir / "figures", rows, "figure")
    _copy_file(Path("paper/scientific_reports/main.tex"), out_dir / "paper/scientific_reports/main.tex", rows, "manuscript")
    _copy_file(Path("paper/scientific_reports/references.bib"), out_dir / "paper/scientific_reports/references.bib", rows, "manuscript")
    _copy_glob(Path("paper/scientific_reports/sections"), "*.tex", out_dir / "paper/scientific_reports/sections", rows, "manuscript")

    for config in [
        "configs/experiments/main_v1_ieee_access.yaml",
        "configs/experiments/open_vocab_bridge_v2.yaml",
        "configs/experiments/open_vocab_bridge_v2_ycb_clutter_heldout.yaml",
        "configs/experiments/open_vocab_query_ablation_ycb_clutter.yaml",
        "configs/experiments/closed_loop_sanity_smoke.yaml",
        "configs/experiments/closed_loop_oracle_calibration_v2_smoke.yaml",
        "configs/experiments/closed_loop_oracle_calibration_v2.yaml",
        "configs/experiments/open_vocab_true_name_query_ablation_ycb_clutter.yaml",
    ]:
        _copy_file(Path(config), out_dir / config, rows, "experiment config")

    for script in [
        "scripts/generate_scirep_revision_assets.py",
        "scripts/analyze_open_vocab_bridge_v2.py",
        "scripts/analyze_ieee_access_statistics.py",
        "scripts/analyze_threshold_sensitivity.py",
        "scripts/generate_stressor_table.py",
        "scripts/export_maniskill_qualitative_renders.py",
        "scripts/run_h200_open_vocab_query_ablation_queue.sh",
        "scripts/probe_maniskill_target_names.py",
        "scripts/run_h200_closed_loop_oracle_calibration_v2.sh",
        "scripts/run_h200_true_name_probe_and_ablation.sh",
        "scripts/analyze_oracle_failure_breakdown.py",
    ]:
        _copy_file(Path(script), out_dir / script, rows, "script")

    metadata = f"""# EmbodiedStressBench Scientific Reports Release Metadata

Repository: {REPO_URL}
Release tag: {RELEASE_TAG}
Version identifier: GitHub release tag `{RELEASE_TAG}`. The tag resolves to the exact archived commit.
Zenodo DOI: {ZENODO_PLACEHOLDER}

## Contents

This package contains processed source data for paper tables and figures,
experiment configs, schemas, reproducibility notes, and scripts needed to
regenerate the Scientific Reports draft assets. Full large-scale per-episode
JSON archives should be deposited separately if their size exceeds the GitHub
release limit.

## Submission Gate

Before journal submission, create the public GitHub release `{RELEASE_TAG}`,
archive it with Zenodo, and replace `{ZENODO_PLACEHOLDER}` in release metadata
with the minted DOI.
"""
    (out_dir / "CODE_DATA_RELEASE_METADATA.md").write_text(metadata, encoding="utf-8")
    rows.append(
        {
            "path": str(out_dir / "CODE_DATA_RELEASE_METADATA.md"),
            "source": "generated",
            "role": "metadata",
            "status": "included",
        }
    )

    with (out_dir / "release_manifest.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "source", "role", "status"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="scientific_reports_revision_20260521/release_package")
    args = parser.parse_args()
    build_package(Path(args.output))
    print(f"Wrote release package to {args.output}")


if __name__ == "__main__":
    main()
