# Scientific Reports Query-Ablation Summary

Input root: `outputs\scirep_query_ablation_20260521`

- Expected episodes: 3840
- Completed episodes: 3840
- Duplicate result count: 0
- Runner exceptions: 0
- GroundingDINO rows with debug fields: 1920/1920
- Overall success rate: 0.3620

## Interpretation

The ablation removes the previous no-detection artifact but GroundingDINO remains
dominated by wrong-detection failures on YCB/clutter. Template variants do not
recover object-specific prompting because the current ManiSkill adapter exposes
generic labels (`target object` / `object`) for these tasks. The paper should
therefore claim detector-query sensitivity and adapter-metadata limitations, not
full object-name prompt recovery.
