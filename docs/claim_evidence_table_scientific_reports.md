# Scientific Reports Claim-Evidence Table

This file is a compact companion to `docs/SCIREP_CLAIM_EVIDENCE.md`.

| Claim | Verdict | Evidence source | Paper wording |
| --- | --- | --- | --- |
| Stressors expose target-generation failures | Supported | main diagnostic sweeps, held-out extension, hard-L3 confirmation | "parameterized stressors reveal target-source-dependent failures" |
| Target sources show a precision--robustness tradeoff | Supported | threshold sensitivity and target-error source data | "box-center is precise at strict thresholds; crop-median is robust at default/relaxed thresholds" |
| One learned detector plug-in can be audited | Supported with scope | detector-bridge source data and YCB/clutter query checks | "one GroundingDINO route plus controlled comparators" |
| External RGB-D probe reduces simulator-artifact risk | Supported with boundary | YCB-V/BOP source-data tables and figures | "static RGB-D target-generation validation, not real-robot execution" |
| Diagnostic target success predicts task success | Not supported | execution oracle-gate audit | "execution calibration remains unresolved" |

Unsupported claims are excluded from the manuscript: closed-loop policy
benchmarking, real-robot robustness, state-of-the-art VLA comparison, general
GroundingDINO performance claims, and a universal best target source.
