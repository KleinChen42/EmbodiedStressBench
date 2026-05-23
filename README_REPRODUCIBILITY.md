# EmbodiedStressBench Scientific Reports Reproducibility Pack

This document describes the artifacts needed to inspect and regenerate the
Scientific Reports manuscript results for EmbodiedStressBench.

Repository:

```text
https://github.com/KleinChen42/EmbodiedStressBench.git
```

Author and correspondence:

```text
Zhuo Chen, zhuoc@chalmers.se
```

Planned release tag:

```text
v0.1.0-scirep
```

Zenodo DOI status:

```text
Pending. The DOI should be minted from the GitHub release before journal
submission and then inserted into the manuscript Data Availability and Code
Availability statements.
```

## Canonical Manuscript Source

Compile the Scientific Reports draft from:

```text
paper/scientific_reports/main.tex
```

Do not use older IEEE Access or legacy `paper/main.tex` drafts for the
Scientific Reports submission.

## Staged Release Package

The staged source-data package is:

```text
scientific_reports_revision_20260521/release_package/
```

It contains:

- Scientific Reports manuscript source.
- Processed CSV files for manuscript tables.
- Figure source-data CSV files.
- Generated figures used by the manuscript.
- Configs for the completed evidence-producing runs.
- JSON schema and reproducibility notes.
- Claim-evidence and experiment-status documents.
- Scripts for analysis, table generation, plotting, and qualitative render
  extraction.

Full large-scale per-episode JSON outputs are not all committed to this local
package because of size. The manuscript claims are supported by the processed
CSV/source-data files, generated figure data, configs, reports, and release
metadata in the staged package. If the journal or reviewer requests raw JSON,
archive it as a separate large-artifact bundle and cite it alongside the main
Zenodo record.

## Environment

Local analysis requires:

```bash
python -m pip install pandas numpy matplotlib pyyaml pytest
```

ManiSkill reproduction requires a compatible CUDA/SAPIEN/ManiSkill
installation. The repository also includes mock-mode tests that run without
robot hardware.

## Smoke Test

```bash
python -m pytest -q tests
python scripts/generate_scirep_revision_assets.py --help
python scripts/analyze_ycbv_external_rgbd_probe.py --help
```

## Evidence Sets Used In The Scientific Reports Draft

| Evidence set | Local/source-data artifact | Manuscript role |
| --- | --- | --- |
| Main ManiSkill diagnostic sweeps | generated tables and claim-evidence docs | target-source and stressor diagnosis |
| Open-Vocab Bridge v2 | `scientific_reports_revision_20260521/release_package/source_data/` | detector plug-in audit |
| YCB/clutter true-name query ablation | `query_ablation_summary.csv` and episode index | detector-query and adapter-label failure modes |
| External YCB-V/BOP RGB-D validation | `external_rgbd_validation_summary.csv` | external RGB-D scope check |
| Detector threshold sweep | `external_rgbd_detector_threshold_sensitivity.csv` | GroundingDINO threshold robustness |
| Closed-loop oracle-gate audit | `closed_loop_oracle_calibration_v2_gate.csv` | execution-calibration claim boundary |
| Qualitative ManiSkill renders | qualitative figure files and manifest | visual failure examples |

## Regenerating Scientific Reports Tables And Figures

The main generated assets are produced by:

```bash
python scripts/generate_scirep_revision_assets.py
python scripts/generate_scirep_external_rgbd_assets.py
python scripts/generate_scirep_ycbv_threshold_sweep_assets.py
```

The external RGB-D probe summaries can be regenerated with:

```bash
python scripts/analyze_ycbv_external_rgbd_probe.py --help
```

The exact full-run commands are retained as scripts for provenance, but the
submitted manuscript should cite the processed source-data package rather than
internal scheduler paths.

## Claim-Evidence Audit

The current claim-evidence documents are:

```text
docs/claim_evidence_table_scientific_reports.md
docs/scientific_reports_result_to_claim.md
scientific_reports_revision_20260521/final_scirep_revision_report.md
```

Use these documents before changing the Abstract, Introduction, Results, or
Discussion. Any new claim should map to a generated CSV/table/figure or be
explicitly marked as a limitation.

## Submission Checklist

Before submitting to Scientific Reports:

1. Commit and push the final source package to GitHub.
2. Create release tag `v0.1.0-scirep`.
3. Archive the release on Zenodo.
4. Insert the minted Zenodo DOI into the manuscript Data Availability and Code
   Availability statements.
5. Compile and visually inspect the PDF.
6. Confirm the PDF has no old title, internal GPU/path wording, or unsupported
   execution/manipulation claims.
