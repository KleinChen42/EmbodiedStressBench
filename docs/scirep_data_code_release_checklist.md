# Scientific Reports Data and Code Release Checklist

Repository: https://github.com/KleinChen42/EmbodiedStressBench.git
Release commit: resolved by GitHub tag `v0.1.0-scirep`
Release tag: `v0.1.0-scirep`
Zenodo version DOI: `10.5281/zenodo.20352155`
Zenodo concept DOI: `10.5281/zenodo.20351620`

## Submission Gate

- The manuscript Data Availability and Code Availability sections cite the version DOI above.
- The release package includes license, citation metadata, processed source data, schemas, scripts, figures, tables, and checksum metadata.
- Supplementary Tables S1--S14 are included as `supplementary_tables.tex`, `supplementary_tables_S1_S14.xlsx`, and a manifest; submit these with the manuscript so every supplementary-table citation resolves.
- The GitHub release notes and release-package metadata record the exact target commit after the final cleanup commit is created.

## Included In The Staged Release Package

- Processed CSV source data for paper tables.
- Figure files and qualitative render panels.
- Scientific Reports manuscript source and references.
- Supplementary Tables S1--S14 LaTeX source, editable workbook, and manifest.
- Experiment configs, including the query-ablation config.
- JSON schema and reproducibility README.
- Result-to-claim audit and experiment status documents.
- Scripts for analysis, table generation, qualitative render export, and external RGB-D source-data regeneration.
- MIT license, `CITATION.cff`, release metadata, and SHA256 checksums.

## Not Included By Default

- The complete 400k+ per-episode JSON archive, due size.
- Internal system logs and private scheduler logs.
- Secrets, SSH keys, local paths, or private environment files.
- Remote queue wrappers and operational scheduler notes.

## Data Availability Wording

`The archived release is available at https://doi.org/10.5281/zenodo.20352155. The GitHub repository is available at https://github.com/KleinChen42/EmbodiedStressBench.git under release tag v0.1.0-scirep.`
