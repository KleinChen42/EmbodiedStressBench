# Scientific Reports Experiment Status

Date: 2026-05-23
Release DOI: 10.5281/zenodo.20351628

## Submitted Evidence Sets

| Evidence set | Status | Size | Paper use |
| --- | --- | ---: | --- |
| Main diagnostic sweeps and held-out extension | complete | 134,400 held-out episodes | target-source and stressor diagnosis |
| Hard-L3 confirmation | complete | 14,400 episodes | hard-stressor failure diagnosis |
| Detector-bridge sweep | complete | 13,500 episodes | one learned detector plug-in plus controlled comparators |
| YCB/clutter query checks | complete | 960 episodes | query, domain, and adapter-label failure modes |
| External YCB-V/BOP RGB-D validation | complete | 98,567 object instances | external static RGB-D target-generation validation |
| Detector-threshold sweep | complete | two additional full external runs | detector-query threshold sensitivity |
| Execution oracle-gate audit | complete | 200 episodes | limitation; no positive execution-calibration claim |

## Submitted Claim Decision

The Scientific Reports manuscript supports detector-pluggable target-generation
diagnosis with one learned GroundingDINO route and controlled comparators. It
does not support a positive claim that diagnostic target success predicts
closed-loop task success. The YCB-V/BOP probe provides external static RGB-D
support for the lifting/detector decomposition: oracle-mask lifting reaches
99.97% success at 8 cm, oracle 2D boxes with crop-trimmed median reach 79.9%,
GroundingDINO generic prompts reach 23.8%, and true-name prompts reach 61.4%.

## Generated Local Artifacts

- `docs/SCIREP_CLAIM_EVIDENCE.md`
- `paper/scientific_reports/main.tex`
- `paper/scientific_reports/supplementary_tables.tex`
- `paper/scientific_reports/tables/*.csv`
- `paper/scientific_reports/tables/*.tex`
- `paper/scientific_reports/figures/*.png`
- `paper/scientific_reports/figures/*.pdf`
- `scientific_reports_revision_20260521/release_package/`
- `scientific_reports_revision_20260521/release_package/checksums_sha256.csv`

## Next Actions

1. Compile and visually inspect `paper/scientific_reports/main.tex`.
2. Confirm the GitHub release and Zenodo DOI resolve to the final package.
3. Do not add closed-loop execution claims unless a future calibrated executor
   passes a separate oracle-gate protocol.
