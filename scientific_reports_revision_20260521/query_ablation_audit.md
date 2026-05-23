# Scientific Reports Query-Ablation Summary

Input root: `outputs\scirep_true_name_ablation_small_20260521_r7`

- Expected episodes: 960
- Completed episodes: 960
- Duplicate result count: 0
- Runner exceptions: 0
- GroundingDINO rows with debug fields: 468/480
- Overall success rate: 0.3396

## Interpretation

The ablation audits whether generic prompts, resolved true names, or true-name
phrases change the YCB/clutter detector bridge. If GroundingDINO remains at
high no-detection or wrong-detection rates, the paper should describe this as a
detector-query/domain and adapter-label limitation, not as a detector leaderboard
or a broad claim about all YCB recognition.
