# EmbodiedStressBench Scientific Reports Release Reproducibility Notes

This package stages the processed source data, manuscript source, scripts, and
generated assets for the Scientific Reports submission of EmbodiedStressBench.

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

Zenodo DOI:

```text
Pending until the author archives the final GitHub release.
```

## Package Contents

- `paper/scientific_reports/`: manuscript source.
- `paper_tables/`: generated LaTeX tables used by the manuscript.
- `figures/`: generated manuscript figures and qualitative panels.
- `source_data/`: processed CSV files and compact source-data artifacts.
- `configs/`: experiment configs needed to rerun or inspect evidence-producing
  runs.
- `scripts/`: analysis, plotting, probe, and queue scripts.
- `docs/`: claim-evidence, experiment-status, and result-to-claim documents.
- `CODE_DATA_RELEASE_METADATA.md`: release metadata and DOI insertion reminder.

## Canonical Manuscript

Compile:

```text
paper/scientific_reports/main.tex
```

Do not compile the IEEE Access draft when preparing the Scientific Reports
submission.

## Main Evidence Tables

The manuscript draws from processed CSVs under `source_data/tables/`, including:

- `external_rgbd_validation_summary.csv`
- `external_rgbd_detector_threshold_sensitivity.csv`
- `open_vocab_detector_transfer_summary.csv`
- `query_ablation_summary.csv`
- `closed_loop_oracle_calibration_v2_gate.csv`
- `target_name_probe_summary.csv`

## Reproduction Commands

Install lightweight analysis dependencies:

```bash
python -m pip install pandas numpy matplotlib pyyaml pytest
```

Regenerate Scientific Reports assets:

```bash
python scripts/generate_scirep_revision_assets.py
python scripts/generate_scirep_external_rgbd_assets.py
python scripts/generate_scirep_ycbv_threshold_sweep_assets.py
```

Run smoke tests from the repository root:

```bash
python -m pytest -q tests
```

## Submission Gate

Before journal submission:

1. Commit the final package to GitHub.
2. Create the `v0.1.0-scirep` GitHub release.
3. Archive the release with Zenodo.
4. Insert the Zenodo DOI into the manuscript and this metadata package.
