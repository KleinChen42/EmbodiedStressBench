# Scientific Reports Data and Code Release Checklist

Repository: https://github.com/KleinChen42/EmbodiedStressBench.git
Release commit: record after final release commit
Planned release tag: `v0.1.0-scirep`

## Submission-Blocking Actions

- Create the public GitHub release `v0.1.0-scirep`.
- Upload or attach `scientific_reports_revision_20260521/release_package/`.
- Archive the GitHub release with Zenodo.
- Replace the release-package DOI field `TO_BE_FILLED_AFTER_ZENODO_ARCHIVE` with the minted DOI.
- Update the manuscript Data Availability statement with the Zenodo DOI.

## Included In The Staged Release Package

- Processed CSV source data for paper tables.
- Figure files and qualitative render panels.
- Scientific Reports manuscript source and references.
- Experiment configs, including the query-ablation config.
- JSON schema and reproducibility README.
- Result-to-claim audit and experiment status documents.
- Scripts for analysis, table generation, qualitative render export, and H200 follow-up.

## Not Included By Default

- The complete 400k+ per-episode JSON archive, due size.
- H200 system logs and internal GPU scheduling logs.
- Secrets, SSH keys, local paths, or private environment files.

## Recommended Data Availability Wording After DOI Minting

Replace the draft DOI sentence with:

`The archived release is available at [Zenodo DOI]. The GitHub repository is available at https://github.com/KleinChen42/EmbodiedStressBench.git under release tag v0.1.0-scirep.`
