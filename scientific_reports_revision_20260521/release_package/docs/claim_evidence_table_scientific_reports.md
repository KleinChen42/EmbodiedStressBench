# Scientific Reports Claim-Evidence Table

| Claim | Verdict | Evidence source | Paper wording |
| --- | --- | --- | --- |
| Parameterized simulation stressors expose target-generation failures | Supported | Main v1, held-out, hard L3, detection-list ambiguity, and Bridge v2 artifacts | "stressors expose target-generation and detector failure modes" |
| Target sources show a precision-vs-robustness tradeoff | Supported | Threshold sensitivity and target-error analyses | "crop-median is robust at default/relaxed thresholds; box-center is more precise under strict thresholds" |
| Open-vocabulary detectors can be evaluated through the same protocol | Supported with scope | `outputs/scirep_overnight_20260520_analysis/open_vocab_bridge_v2*`; `outputs/scirep_query_ablation_20260521`; `outputs/ycb_true_name_probe_20260521` | "GroundingDINO can be plugged in, and YCB/clutter exposes detector-query sensitivity and adapter-label limitations" |
| Diagnostic target success predicts scripted execution success | Not supported | `outputs/scirep_overnight_20260520_analysis/closed_loop_sanity_smoke`; `outputs/scirep_closed_loop_oracle_calibration_v2_20260521` | "scripted execution calibration remains unresolved" |
| Failure taxonomy separates wrong detection, invalid depth, displacement, and execution sensitivity | Supported for diagnostic runs | failure-distribution tables and qualitative case manifest | "failure taxonomy supports diagnostic triage, not causal proof beyond logged artifacts" |

## Claim Boundaries

- No real-robot robustness claim.
- No closed-loop policy benchmark claim.
- No SOTA VLA comparison claim.
- No claim that GroundingDINO solves semantic grounding.
- No claim that crop-median depth is universally strongest across all thresholds.
