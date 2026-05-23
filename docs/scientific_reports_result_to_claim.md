# Scientific Reports Result-to-Claim Gate

Date: 2026-05-23
Release DOI: 10.5281/zenodo.20352155

## Verdict

The submitted Scientific Reports package supports a reproducible diagnostic
study of language-to-target generation. It does not support positive claims
about closed-loop manipulation, real-robot robustness, or detector leaderboard
performance.

## Evidence Summary

| Evidence set | Size | Integrity | Claim use |
| --- | ---: | --- | --- |
| Main diagnostic sweeps and held-out extension | 134,400 held-out episodes | duplicate count 0; generated source tables | target-source and stressor diagnosis |
| Hard-L3 confirmation | 14,400 episodes | duplicate count 0; generated source tables | failure diagnosis under hard stressors |
| Detector-bridge sweep | 13,500 episodes | duplicate count 0; runner exceptions 0 | one learned detector plug-in plus controlled comparators |
| YCB/clutter query checks | 960 episodes | debug fields present for learned-detector rows | query, domain, and adapter-label failure modes |
| External YCB-V/BOP RGB-D validation | 98,567 object instances | processed source tables and frame-block CIs | external static RGB-D scope check |
| Execution oracle-gate audit | 200 episodes | duplicate count 0; runner exceptions 0 | limitation; no positive execution-calibration claim |

## Claim Decisions

| Intended claim | Verdict | Supported wording |
| --- | --- | --- |
| Parameterized stressors expose target-generation failures | Supported | In the tested diagnostic sweeps, stressors reveal target-source-dependent failures. |
| Target sources show a precision--robustness tradeoff | Supported | Box-center is more precise at strict thresholds; crop-median is more robust at default/relaxed thresholds. |
| The protocol can audit a learned detector plug-in | Supported with scope | The protocol evaluates one GroundingDINO route plus metadata-assisted and first-detection comparators. |
| External real RGB-D data reduce simulator-artifact risk | Supported with boundary | The YCB-V/BOP probe validates static RGB-D target-generation decomposition, not robot execution. |
| Diagnostic target success predicts task success | Not supported | Scripted execution calibration remains unresolved. |

For the canonical release-facing claim map, use `docs/SCIREP_CLAIM_EVIDENCE.md`.
