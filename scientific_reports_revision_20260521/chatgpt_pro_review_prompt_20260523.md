# ChatGPT Pro Review Prompt

You are acting as a Scientific Reports editor, a robotics/manipulation methods reviewer, an open-vocabulary perception reviewer, a statistics/reproducibility reviewer, and a devil's advocate reviewer.

Please review the attached manuscript PDF as a near-submission Scientific Reports paper. The goal is not only to find fatal flaws, but to identify concrete changes that would most improve acceptance probability.

## Target journal

Scientific Reports, Nature Portfolio.

## Intended positioning

The paper should be evaluated as a reproducible diagnostic study/benchmark for query-conditioned 3D target localization and language-to-target generation in robotic manipulation. It should not be interpreted as claiming:

- a closed-loop policy benchmark,
- a real-robot manipulation system,
- state-of-the-art VLA performance,
- real-robot robustness,
- or that GroundingDINO generally fails beyond the tested query/adaptor setting.

## Evidence currently in the manuscript

- Large-scale ManiSkill diagnostic sweeps with oracle-gap and failure taxonomy.
- Threshold sensitivity showing a precision--robustness tradeoff: box-center is more precise at strict thresholds; crop-median is stronger at default/relaxed thresholds.
- Open-vocabulary detector bridge using metadata-assisted selector, first detection, and GroundingDINO.
- YCB/clutter true-name query check showing detector-query/domain and adapter-label failure modes.
- External YCB-V/BOP real RGB-D validation probe:
  - oracle-mask lifting: 99.97% success at 8 cm,
  - oracle 2D boxes + crop-trimmed median: 79.9%,
  - GroundingDINO generic prompts: 23.8%,
  - GroundingDINO true object-name prompts: 61.4%.
- Scripted closed-loop oracle-gate audit fails; it is framed only as a claim boundary/limitation.
- Data/code are intended for GitHub release and Zenodo DOI before final submission.

## What I want you to check

1. Is the title appropriately conservative for Scientific Reports?
2. Does the abstract accurately reflect the strongest evidence without overclaiming?
3. Does the introduction make a clear gap and contribution, or is it still too engineering-report-like?
4. Are the Results organized around scientific questions rather than run logs?
5. Is the external YCB-V/BOP RGB-D validation enough to reduce the "simulation-only artifact" criticism?
6. Is the GroundingDINO interpretation safe, especially around generic prompts, true-name prompts, no-detection, low IoU but valid 3D target success, and YCB/clutter transfer?
7. Is the failed closed-loop oracle audit correctly framed, or should execution be further de-emphasized?
8. Are the statistical methods sufficient: confidence intervals, seed/frame-block bootstrap, threshold sensitivity, and claim boundaries?
9. Are any major claims unsupported or too strong?
10. Are Data Availability and Code Availability ready for Scientific Reports once the Zenodo DOI is inserted?
11. Are required declarations complete: Author Contributions, Competing Interests, Funding, Acknowledgements, Data Availability, Code Availability?
12. Are figures and tables readable enough for Scientific Reports, especially Figure 1, Figure 2, Figure 5, Table 8, Table 10, and the claim-support matrix?
13. Should any main-text table/figure move to Supplementary?
14. Are references broad and credible enough, or should key works be added/replaced?
15. What small or medium experiment, if any, would most improve acceptance probability?

## Output requested

Please provide:

1. Editorial decision: Accept / Minor Revision / Major Revision / Reject and Resubmit.
2. Submission-readiness percentage and what would raise it.
3. Top 5 blocking issues, ordered by severity.
4. Top 10 concrete fixes before submission.
5. Page-by-page readability/layout audit.
6. Claim-evidence audit table with: Claim | Evidence | Supported? | Risk | Safer wording.
7. "Dangerous sentence" list: quote risky sentences and rewrite them safely.
8. Experiment recommendation list:
   - must-run before submission,
   - high-value but optional,
   - not worth doing now.
9. Data/code/reproducibility audit for Scientific Reports.
10. Final go/no-go recommendation.

Please prioritize changes that improve acceptance probability without requiring large new experiments. If you recommend a new experiment, explain exactly what reviewer concern it resolves and the smallest credible version of the experiment.

