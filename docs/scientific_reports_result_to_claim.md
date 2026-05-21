# Scientific Reports Result-to-Claim Gate

Date: 2026-05-21

## Verdict

The new results support a Scientific Reports manuscript centered on reproducible
simulation diagnosis of language-to-target generation failures. They do **not**
support a positive claim about scripted execution success calibration.

## Evidence Summary

| Evidence set | Episodes | Complete | Duplicate count | Runner exceptions | Key finding |
| --- | ---: | --- | ---: | ---: | --- |
| Open-Vocab Bridge v2 | 13500/13500 | True | 0 | 0 | Learned detector plug-in is runnable and produces detector-specific target-generation failures |
| YCB/clutter held-out bridge | 18000/18000 | True | 0 | 0 | Generic open-vocabulary detector transfer fails through no-detection on YCB/clutter |
| Closed-loop smoke | 80/80 | True | 0 | 0 | Scripted executor gate failed; do not use for positive task-success claims |
| Closed-loop oracle calibration v2 | 20/20 | True | 0 | 0 | Oracle task success remained below gate (0.100); execution calibration remains unresolved |


## Claim Decisions

| Intended claim | Verdict | Supported wording |
| --- | --- | --- |
| Parameterized simulation stressors expose target-generation failures | Supported | The benchmark exposes target-source and detector failure modes through controlled stressor sweeps and per-episode artifacts. |
| Target sources show a precision-vs-robustness tradeoff | Supported | Threshold sensitivity supports a precision--robustness tradeoff; crop-median is not universally strongest under strict thresholds. |
| Open-vocabulary detectors can be evaluated through the same protocol | Supported with scope | GroundingDINO can be evaluated through the protocol, and the YCB/clutter held-out plus query checks expose detector-query and adapter-label limitations. |
| Diagnostic target success is informative for scripted execution success | Not supported yet | The current scripted executor smoke failed the oracle task-success gate, so execution calibration remains unresolved. |
| Failure taxonomy separates wrong detection, invalid depth, target displacement, and execution sensitivity | Supported for diagnostic runs | Failure labels are useful for diagnosis; execution claims require a calibrated executor. |

## Important Negative Result

In the YCB/clutter held-out bridge, GroundingDINO rows have an average
no-detection rate of 1.000. This should be written as a limitation of
the generic target-object query and current adapter labels, not as a general
statement that GroundingDINO cannot work on YCB or clutter.

## Query-Ablation Update

The follow-up query ablation completes the prompt-sensitivity check. It removes
the no-detection artifact but GroundingDINO remains dominated by wrong-detection
failures on YCB/clutter. A target-name probe found no non-generic target_label
rows, so a true object-name prompt ablation is not claimable from the current
adapter. This supports detector-query sensitivity and adapter-metadata
limitations rather than full object-name prompt recovery.

## Manuscript Routing

1. Move closed-loop execution from a positive result to a limitation and sanity
   audit.
2. Promote detector-transfer diagnosis to a main Scientific Reports finding.
3. Keep all claims simulation-only and target-generation-specific.
4. Do not add SOTA VLA, real-robot, or policy-benchmark claims.
