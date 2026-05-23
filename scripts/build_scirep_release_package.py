from __future__ import annotations

import argparse
import csv
import hashlib
import os
import shutil
import subprocess
from pathlib import Path


REPO_URL = "https://github.com/KleinChen42/EmbodiedStressBench.git"
RELEASE_TAG = "v0.1.0-scirep"
ZENODO_VERSION_DOI = "10.5281/zenodo.20352155"
ZENODO_CONCEPT_DOI = "10.5281/zenodo.20351620"
LICENSE_NAME = "MIT"


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "UNKNOWN_COMMIT"


def _safe_clean_dir(out_dir: Path) -> None:
    repo = Path.cwd().resolve()
    allowed_root = (repo / "scientific_reports_revision_20260521").resolve()
    target = out_dir.resolve()
    target.relative_to(allowed_root)
    if not target.name.startswith("release_package"):
        raise ValueError(f"Refusing to clean unexpected output directory: {target}")
    if target.exists():
        def _make_writable_then_retry(function, path, _excinfo):
            os.chmod(path, 0o700)
            function(path)

        shutil.rmtree(target, onexc=_make_writable_then_retry)
    target.mkdir(parents=True, exist_ok=True)


def _copy_file(src: Path, dst: Path, rows: list[dict[str, str]], role: str) -> None:
    if not src.exists():
        rows.append({"path": str(dst), "source": str(src), "role": role, "status": "missing"})
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(src, dst)
        status = "included"
    except OSError as exc:
        status = f"copy_error: {exc.__class__.__name__}: {exc}"
    rows.append({"path": str(dst), "source": str(src), "role": role, "status": status})


def _copy_csv_sanitized_paths(src: Path, dst: Path, rows: list[dict[str, str]], role: str) -> None:
    if not src.exists():
        rows.append({"path": str(dst), "source": str(src), "role": role, "status": "missing"})
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    with src.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        out_rows = []
        for row in reader:
            for key, value in list(row.items()):
                text = str(value)
                if key == "source_file" or "/data/" in text:
                    row[key] = Path(text.replace("\\", "/")).name
            out_rows.append(row)
    with dst.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)
    rows.append({"path": str(dst), "source": str(src), "role": role, "status": "included"})


def _copy_glob(
    src_dir: Path,
    pattern: str,
    dst_dir: Path,
    rows: list[dict[str, str]],
    role: str,
    skip_names: tuple[str, ...] = (),
) -> None:
    for src in sorted(src_dir.glob(pattern)):
        if src.is_file() and not any(src.match(skip) or src.name == skip for skip in skip_names):
            if src.suffix.lower() == ".csv":
                _copy_csv_sanitized_paths(src, dst_dir / src.name, rows, role)
            else:
                _copy_file(src, dst_dir / src.name, rows, role)


def _copy_recursive(
    src_dir: Path,
    patterns: tuple[str, ...],
    dst_dir: Path,
    rows: list[dict[str, str]],
    role: str,
) -> None:
    if not src_dir.exists():
        rows.append({"path": str(dst_dir), "source": str(src_dir), "role": role, "status": "missing"})
        return
    seen: set[Path] = set()
    for pattern in patterns:
        for src in sorted(src_dir.rglob(pattern)):
            if src.is_file() and src not in seen:
                seen.add(src)
                _copy_file(src, dst_dir / src.relative_to(src_dir), rows, role)


def _write_checksums(out_dir: Path, rows: list[dict[str, str]]) -> None:
    checksum_path = out_dir / "checksums_sha256.csv"
    checksum_rows = []
    for path in sorted(p for p in out_dir.rglob("*") if p.is_file()):
        if path.name in {"checksums_sha256.csv", "release_manifest.csv"}:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        checksum_rows.append({"sha256": digest, "path": str(path.relative_to(out_dir)).replace("\\", "/")})
    with checksum_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["sha256", "path"])
        writer.writeheader()
        writer.writerows(checksum_rows)
    rows.append({"path": str(checksum_path), "source": "generated", "role": "checksum manifest", "status": "included"})


def build_package(out_dir: Path) -> None:
    _safe_clean_dir(out_dir)
    rows: list[dict[str, str]] = []
    commit = _git_commit()

    for path, role in [
        ("README.md", "overview"),
        ("README_REPRODUCIBILITY.md", "reproducibility"),
        ("LICENSE", "license"),
        ("CITATION.cff", "citation metadata"),
        ("schemas/episode_result_schema.json", "schema"),
        ("docs/SCIREP_CLAIM_EVIDENCE.md", "audit"),
        ("docs/scientific_reports_result_to_claim.md", "audit"),
        ("docs/claim_evidence_table_scientific_reports.md", "audit"),
        ("docs/scientific_reports_experiment_status.md", "audit"),
        ("docs/scirep_data_code_release_checklist.md", "metadata"),
    ]:
        _copy_file(Path(path), out_dir / path, rows, role)
    _copy_file(
        Path("scientific_reports_revision_20260521/final_scirep_revision_report.md"),
        out_dir / "docs/final_scirep_revision_report.md",
        rows,
        "release report",
    )

    _copy_csv_sanitized_paths(
        Path("scientific_reports_revision_20260521/qualitative_case_manifest.csv"),
        out_dir / "source_data/qualitative_case_manifest.csv",
        rows,
        "source data",
    )
    _copy_file(
        Path("scientific_reports_revision_20260521/scirep_open_vocab_detector_transfer_combined.csv"),
        out_dir / "source_data/scirep_open_vocab_detector_transfer_combined.csv",
        rows,
        "source data",
    )

    _copy_glob(Path("paper/scientific_reports/tables"), "*.csv", out_dir / "source_data/tables", rows, "source data")
    for src_dir, dst_name in [
        ("outputs/scirep_query_ablation_20260521", "query_ablation"),
        ("outputs/ycb_true_name_probe_20260521", "target_name_probe"),
        ("outputs/scirep_closed_loop_oracle_calibration_v2_20260521/smoke", "closed_loop_oracle_calibration_v2"),
        ("outputs/scirep_closed_loop_oracle_gate_audit_200_20260521", "closed_loop_oracle_gate_audit_200"),
        ("outputs/scirep_oracle_failure_breakdown_20260521", "oracle_failure_breakdown"),
        ("outputs/ycb_target_identity_deep_probe_20260521", "target_identity_probe"),
        ("outputs/scirep_true_name_ablation_small_20260521", "true_name_ablation_small"),
    ]:
        _copy_glob(
            Path(src_dir),
            "*.csv",
            out_dir / "source_data" / dst_name,
            rows,
            "source data",
            skip_names=("*episode_index.csv",),
        )
    for ycbv_root in [
        "outputs/ycbv_external_rgbd_probe_160k_20260522_analysis",
        "outputs/ycbv_external_rgbd_probe_thr010_20260522_analysis",
        "outputs/ycbv_external_rgbd_probe_thr030_20260522_analysis",
    ]:
        _copy_glob(
            Path(ycbv_root),
            "*.csv",
            out_dir / "source_data/ycbv_external_rgbd" / Path(ycbv_root).name,
            rows,
            "source data",
            skip_names=("*episode_index.csv",),
        )

    for ext in ("*.png", "*.pdf", "*.svg"):
        _copy_glob(Path("paper/scientific_reports/figures"), ext, out_dir / "figures", rows, "figure")
    _copy_glob(Path("paper/scientific_reports/figures"), "*.csv", out_dir / "source_data/figures", rows, "figure source data")
    _copy_glob(
        Path("paper/scientific_reports/tables"),
        "*.tex",
        out_dir / "paper_tables",
        rows,
        "paper table",
        skip_names=("closed_loop_smoke_outcome.tex",),
    )
    for path in [
        "paper/scientific_reports/main.tex",
        "paper/scientific_reports/supplementary_tables.tex",
        "paper/scientific_reports/supplementary_tables_S1_S14.xlsx",
        "paper/scientific_reports/supplementary_tables_manifest.csv",
        "paper/scientific_reports/supplementary_tables_manifest.md",
        "paper/scientific_reports/references.bib",
    ]:
        _copy_file(Path(path), out_dir / path, rows, "manuscript")
    _copy_glob(Path("paper/scientific_reports/sections"), "*.tex", out_dir / "paper/scientific_reports/sections", rows, "manuscript")

    for config in [
        "configs/experiments/main_v1_ieee_access.yaml",
        "configs/experiments/open_vocab_bridge_v2.yaml",
        "configs/experiments/open_vocab_query_ablation_ycb_clutter.yaml",
        "configs/experiments/closed_loop_oracle_gate_audit_200.yaml",
        "configs/experiments/open_vocab_true_name_ablation_small.yaml",
        "configs/experiments/scirep_oracle_2d_box_control.yaml",
        "configs/experiments/scirep_oracle_2d_box_control_smoke.yaml",
    ]:
        _copy_file(Path(config), out_dir / config, rows, "experiment config")

    for script in [
        "scripts/generate_scirep_revision_assets.py",
        "scripts/generate_scirep_external_rgbd_assets.py",
        "scripts/generate_scirep_ycbv_threshold_sweep_assets.py",
        "scripts/analyze_threshold_sensitivity.py",
        "scripts/generate_stressor_table.py",
        "scripts/export_maniskill_qualitative_renders.py",
        "scripts/analyze_oracle_failure_breakdown.py",
        "scripts/analyze_ycbv_external_rgbd_probe.py",
        "scripts/run_ycbv_external_rgbd_probe.py",
        "scripts/build_scirep_supplementary_tables_workbook.py",
    ]:
        _copy_file(Path(script), out_dir / script, rows, "script")

    metadata = f"""# EmbodiedStressBench Scientific Reports Release Metadata

Repository: {REPO_URL}
Release tag: {RELEASE_TAG}
Archived commit: {commit}
Zenodo version DOI: https://doi.org/{ZENODO_VERSION_DOI}
Zenodo concept DOI: https://doi.org/{ZENODO_CONCEPT_DOI}
License: {LICENSE_NAME}

## Contents

This package contains processed source data for all manuscript figures and
tables, Supplementary Tables S1--S14 as LaTeX source plus an editable workbook,
figure files, manuscript source, selected experiment configs, schemas,
reproducibility instructions, final claim-evidence audit documents, scripts for
source-data regeneration, and SHA256 checksums. Large raw per-episode JSON
archives and operational scheduler logs are intentionally outside this
lightweight submission package.
"""
    metadata_path = out_dir / "CODE_DATA_RELEASE_METADATA.md"
    metadata_path.write_text(metadata, encoding="utf-8")
    rows.append({"path": str(metadata_path), "source": "generated", "role": "metadata", "status": "included"})

    _write_checksums(out_dir, rows)
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
