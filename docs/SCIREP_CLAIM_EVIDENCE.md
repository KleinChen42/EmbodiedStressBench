# Scientific Reports Claim-Evidence Map

This document is the canonical claim-evidence audit for the submitted
Scientific Reports package. Older submission-format and operational experiment logs
are historical notes and are not part of the submitted claim wording.

Release DOI: 10.5281/zenodo.20352155
Release tag: v0.1.0-scirep  
Release commit: resolved by GitHub tag `v0.1.0-scirep`

## Supported Claims

| Claim | Evidence | Manuscript use |
| --- | --- | --- |
| The benchmark isolates query-conditioned 3D target generation before policy execution. | Protocol schematic, episode definition, target-error metric, oracle gap, and failure taxonomy. | Main framing claim. |
| Parameterized stressors expose target-generation failures. | Main diagnostic sweeps, held-out seed extension, hard-L3 confirmation, and failure breakdowns. | Supported for the tested ManiSkill tasks and stressors. |
| Target sources show a precision--robustness tradeoff. | Threshold sensitivity: box-center is stronger at strict 4--6 cm thresholds; crop-median is stronger at 8--10 cm thresholds. | Supported; no universal-best target-source claim. |
| One learned detector plug-in can be audited through the same protocol. | Detector-bridge sweep with metadata-assisted selector, first detection, and GroundingDINO. | Supported as detector-pluggable evidence, not a detector leaderboard. |
| External RGB-D data support the target-generation decomposition outside ManiSkill rendering. | YCB-V/BOP probe: oracle-mask 99.97%, oracle 2D box plus trimmed median 79.9%, GroundingDINO generic 23.8%, true-name 61.4%. | Supported as static RGB-D target-generation validation, not real-robot execution. |
| Low 2D IoU can still preserve useful 3D crop evidence in some cases. | Low-IoU valid-3D summary and qualitative panels. | Supported as a bounded diagnostic observation. |
| Scripted execution calibration remains unresolved. | 200-episode oracle-gate audit: PickCube and PickSingleYCB each 2/100 task success. | Limitation and claim boundary. |

## Claims Not Made

- No closed-loop policy benchmark claim.
- No real-robot robustness claim.
- No state-of-the-art VLA comparison claim.
- No claim that GroundingDINO generally succeeds or fails outside the tested route.
- No claim that crop-median depth is universally strongest.
- No claim that diagnostic target success predicts task success before executor calibration.

## Submitted Display Items

| Main item | Role | Source data |
| --- | --- | --- |
| Figure 1 | Protocol schematic | generated from protocol labels |
| Table 1 | Experimental design summary | generated table source |
| Table 2 | Diagnostic success and oracle gap | `main_diagnostic_summary.csv` |
| Figure 2 | Target-source threshold tradeoff | `target_source_threshold_tradeoff_source.csv` |
| Figure 3 | Detector-bridge outcomes | `scirep_open_vocab_detector_transfer_combined.csv` |
| Figure 4 | External RGB-D validation | `external_rgbd_validation_source.csv` |
| Figure 5 | Qualitative cases | `qualitative_case_manifest.csv` |
| Table 3 | Execution oracle-gate audit | `closed_loop_oracle_calibration_v2_gate.csv` |
