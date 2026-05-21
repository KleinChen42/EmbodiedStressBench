# Open-Vocab Bridge v2 Audit

Input root: `/data/openMythosBench_project/outputs/open_vocab_query_ablation_ycb_clutter_20260521`

## Counts

- Expected episodes: 3840
- Completed episodes: 3840
- Duplicate result count: 0
- Runner exceptions: 0
- No-detection count: 0 (0.0000)
- Overall success rate: 0.3620

## Detector Debug

- GroundingDINO rows: 1920
- GroundingDINO rows with IoU/score debug: 1920

## YCB/Clutter Label Check

- Generic selected-label rows: 3120
- Example generic-label rows:
  - PickClutterYCB crop_trimmed_median_depth_grounding_dino same_shape_distractor L0 seed 91 label=target object
  - PickSingleYCB crop_trimmed_median_depth_grounding_dino same_color_distractor L0 seed 104 label=target object
  - PickClutterYCB crop_trimmed_median_depth_grounding_dino depth_sparsity L0 seed 96 label=object
  - PickSingleYCB crop_median_depth_query_aware depth_sparsity L0 seed 101 label=target object
  - PickClutterYCB crop_median_depth_query_aware depth_sparsity L0 seed 98 label=target object
  - PickClutterYCB crop_trimmed_median_depth_grounding_dino same_color_distractor L0 seed 103 label=target object
  - PickSingleYCB crop_trimmed_median_depth_grounding_dino partial_target_occlusion L3 seed 96 label=object
  - PickSingleYCB crop_median_depth_grounding_dino same_shape_distractor L3 seed 91 label=target object
  - PickClutterYCB crop_trimmed_median_depth_query_aware same_shape_distractor L3 seed 104 label=target object
  - PickSingleYCB crop_trimmed_median_depth_query_aware depth_sparsity L0 seed 91 label=target object

## Paper-Use Rule

Use this run for paper claims only if completed episodes reach the expected count, duplicate count is zero, runner exceptions are zero, and detector debug fields are present for GroundingDINO rows.
