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

Release tag:

```text
v0.1.0-scirep
```

Zenodo DOI:

```text
10.5281/zenodo.20351628
```

## Canonical Manuscript Source

Compile the Scientific Reports draft from:

```text
paper/scientific_reports/main.tex
```

Use this source for the Scientific Reports submission. The repository root
`paper/main.tex` mirrors this entry point only to protect against automatic
main-file detection in Overleaf.

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
- JSON schema, checksums, license, citation metadata, and reproducibility notes.
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
| Detector-bridge sweep | `scientific_reports_revision_20260521/release_package/source_data/` | detector plug-in audit |
| YCB/clutter true-name query ablation | `query_ablation_summary.csv` and paired-effect summaries | detector-query and adapter-label failure modes |
| External YCB-V/BOP RGB-D validation | `external_rgbd_validation_summary.csv` | external RGB-D scope check |
| Detector threshold sweep | `external_rgbd_detector_threshold_sensitivity.csv` | GroundingDINO threshold robustness |
| Closed-loop oracle-gate audit | `closed_loop_oracle_calibration_v2_gate.csv` | execution-calibration claim boundary |
| Qualitative ManiSkill renders | qualitative figure files and manifest | visual failure examples |

## Figure/Table Source Mapping

| Manuscript item | Source CSV/table data | Generation script |
| --- | --- | --- |
| Figure 1 protocol schematic | generated from manuscript protocol labels | `scripts/generate_scirep_revision_assets.py` |
| Table 1 design summary | `paper/scientific_reports/tables/experiment_design_summary.tex` | `scripts/generate_scirep_revision_assets.py` |
| Table 2 diagnostic summary | `main_diagnostic_summary.csv` | `scripts/generate_scirep_revision_assets.py` |
| Figure 2 threshold tradeoff | `target_source_threshold_tradeoff_source.csv` | `scripts/generate_scirep_revision_assets.py` |
| Figure 3 detector bridge | `scirep_open_vocab_detector_transfer_combined.csv` | `scripts/generate_scirep_revision_assets.py` |
| Figure 4 external RGB-D validation | `external_rgbd_validation_source.csv` | `scripts/generate_scirep_external_rgbd_assets.py` |
| Figure 5 qualitative panels | `qualitative_case_manifest.csv` | `scripts/generate_scirep_revision_assets.py` |
| Table 3 execution audit | `closed_loop_oracle_calibration_v2_gate.csv` | `scripts/generate_scirep_revision_assets.py` |
| Supplementary tables | `paper/scientific_reports/tables/*.csv` | `scripts/generate_scirep_revision_assets.py` and external RGB-D scripts |

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

1. Confirm GitHub release tag `v0.1.0-scirep` resolves to the archived release.
2. Confirm Zenodo DOI `10.5281/zenodo.20351628` resolves to the release archive.
3. Compile and visually inspect the PDF.
4. Confirm the PDF has no old title, internal GPU/path wording, or unsupported
   execution/manipulation claims.
