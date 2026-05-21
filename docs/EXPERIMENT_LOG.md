# Experiment Log

This file records result-producing runs that may be cited in the paper draft.
Only runs backed by JSON/JSONL artifacts should be added here.

## 2026-05-14 ManiSkill Smoke

- Config: `configs/experiments/exp_maniskill_smoke.yaml`
- Backend: `maniskill`
- Remote project: `/data/openMythosBench_project`
- Remote output: `/data/openMythosBench_outputs/maniskill_smoke_20260514`
- Python: `/home/zetyun/q2g_venv/bin/python`
- GPU: `CUDA_VISIBLE_DEVICES=1`
- Episodes: 160
- Report: `/data/openMythosBench_outputs/maniskill_smoke_20260514/report.md`

Summary generated from the report:

| Task | Baseline | Stressors | Levels | Seeds | Success rate |
| --- | --- | --- | --- | --- | --- |
| PickCube | oracle_target | none, depth_noise | 0, 1 | 0-4 | 1.00 |
| PickCube | box_center_depth | none, depth_noise | 0, 1 | 0-4 | 1.00 |
| PickCube | crop_median_depth | none, depth_noise | 0, 1 | 0-4 | 1.00 |
| PickCube | crop_top_surface | none, depth_noise | 0, 1 | 0-4 | 0.60 |
| StackCube | oracle_target | none, depth_noise | 0, 1 | 0-4 | 1.00 |
| StackCube | box_center_depth | none, depth_noise | 0, 1 | 0-4 | 1.00 |
| StackCube | crop_median_depth | none, depth_noise | 0, 1 | 0-4 | 0.85 |
| StackCube | crop_top_surface | none, depth_noise | 0, 1 | 0-4 | 0.20 |

Overall success rate: 0.831. Failure distribution: 133 successes and 27
`target_error_too_large` failures.

Interpretation for draft use: the real ManiSkill smoke confirms that the
framework can produce nontrivial target-source diagnostic gaps. The
`crop_top_surface` heuristic is fragile on StackCube, while oracle and
box-center depth are stable in this low-stress setting. These are pilot-scale
results, not final paper claims.

## 2026-05-14 ManiSkill Pilot Launch

- Config: `configs/experiments/exp_maniskill_pilot.yaml`
- Backend: `maniskill`
- Remote project: `/data/openMythosBench_project`
- Remote output: `/data/openMythosBench_outputs/maniskill_pilot_20260514`
- GPUs: 1, 2, 3, 4, 5, 6, 7
- Shards: 7
- Planned episodes: 3840
- Status command: `/data/openMythosBench_outputs/maniskill_pilot_20260514/check_status.sh`

This run was launched after the 160-episode smoke passed. It expands to six
stressor groups, four stress levels, and 20 seeds.

## 2026-05-14 ManiSkill Pilot Results

- Config: `configs/experiments/exp_maniskill_pilot.yaml`
- Backend: `maniskill`
- Remote project: `/data/openMythosBench_project`
- Remote output: `/data/openMythosBench_outputs/maniskill_pilot_20260514`
- Episodes: 3840
- Report: `/data/openMythosBench_outputs/maniskill_pilot_20260514/report.md`
- CSV: `/data/openMythosBench_outputs/maniskill_pilot_20260514/success_by_group.csv`

Overall success rate: 0.8544.

Baseline-level summary:

| Baseline | Success rate | Episodes | Mean target error |
| --- | ---: | ---: | ---: |
| oracle_target | 1.0000 | 960 | 0.0000 |
| box_center_depth | 0.9771 | 960 | 0.0263 |
| crop_median_depth | 0.9500 | 960 | 0.0471 |
| crop_top_surface | 0.4906 | 960 | 0.1360 |

Task-by-baseline summary:

| Task | Baseline | Success rate | Episodes | Mean target error |
| --- | --- | ---: | ---: | ---: |
| PickCube | oracle_target | 1.0000 | 480 | 0.0000 |
| PickCube | box_center_depth | 0.9729 | 480 | 0.0265 |
| PickCube | crop_median_depth | 0.9583 | 480 | 0.0457 |
| PickCube | crop_top_surface | 0.5354 | 480 | 0.1159 |
| StackCube | oracle_target | 1.0000 | 480 | 0.0000 |
| StackCube | box_center_depth | 0.9812 | 480 | 0.0262 |
| StackCube | crop_median_depth | 0.9417 | 480 | 0.0486 |
| StackCube | crop_top_surface | 0.4458 | 480 | 0.1561 |

Stressor-level summary:

| Stressor | Success rate | Episodes | Mean target error |
| --- | ---: | ---: | ---: |
| none | 0.8688 | 640 | 0.0518 |
| semantic_variants | 0.8688 | 640 | 0.0518 |
| camera_pose_noise | 0.8641 | 640 | 0.0522 |
| depth_noise | 0.8547 | 640 | 0.0546 |
| execution_offset | 0.8359 | 640 | 0.0518 |
| visual_occlusion | 0.8344 | 640 | 0.0524 |

Level-3 stressors:

| Stressor | Success rate | Episodes | Mean target error |
| --- | ---: | ---: | ---: |
| none | 0.8688 | 160 | 0.0518 |
| semantic_variants | 0.8688 | 160 | 0.0518 |
| camera_pose_noise | 0.8562 | 160 | 0.0533 |
| depth_noise | 0.8250 | 160 | 0.0592 |
| execution_offset | 0.7625 | 160 | 0.0518 |
| visual_occlusion | 0.7500 | 160 | 0.0535 |

Failure distribution:

| Failure type | Count |
| --- | ---: |
| success | 3281 |
| target_error_too_large | 536 |
| depth_invalid | 23 |

Interpretation for draft use: the pilot supports a target-source hierarchy
under real ManiSkill observations. Oracle performance is perfect by
construction, box-center and crop-median depth remain strong, and
crop-top-surface is consistently fragile, especially on StackCube. At stress
level 3, execution offsets and visual occlusion are the most damaging stressor
families in this pilot. Semantic variants currently do not affect performance
because the implemented baselines use oracle detections rather than language
retrieval; this limitation should be stated explicitly.

## Main Experiment v1 Plan

- Config: `configs/experiments/main_v1_ieee_access.yaml`
- Smoke config: `configs/experiments/main_v1_ieee_access_smoke.yaml`
- Backend: `maniskill`
- Target submission route: IEEE Access first, with JINT-level rigor
- Full planned episodes: 44,800
- Smoke episodes: 120
- Full output root: `/data/openMythosBench_project/outputs/main_v1_ieee_access_YYYYMMDD`

Main v1 adds `PickSingleYCB` and `PickClutterYCB`, query-aware detection
selection, distractor stressors, partial target occlusion, depth sparsity, and
stronger execution offsets. It should not launch until the smoke config passes
with zero runner exceptions and a generated report.

## 2026-05-14 Main v1 Smoke Results

- Config: `configs/experiments/main_v1_ieee_access_smoke.yaml`
- Backend: `maniskill`
- Remote project: `/data/openMythosBench_project`
- Remote output: `/data/openMythosBench_project/outputs/main_v1_ieee_access_smoke_20260514_impl`
- Episodes: 120
- Report: `/data/openMythosBench_project/outputs/main_v1_ieee_access_smoke_20260514_impl/report.md`

Smoke acceptance status: passed. The run completed all 120 episodes with no
runner exceptions, generated a report, kept oracle success at 1.0, and produced
nontrivial oracle gaps.

Smoke summary:

| Group | Success rate | Episodes | Mean target error |
| --- | ---: | ---: | ---: |
| Overall | 0.8500 | 120 | - |
| oracle_target | 1.0000 | 40 | 0.0000 |
| box_center_depth | 0.7500 | 40 | 0.0303 |
| crop_median_depth | 0.8000 | 40 | 0.0629 |
| PickClutterYCB / crop_median_depth | 0.6000 | 20 | 0.0674 |
| partial_target_occlusion | 0.7667 | 60 | 0.0317 |
| nearby_distractor | 0.9333 | 60 | 0.0307 |

Failure distribution:

| Failure type | Count |
| --- | ---: |
| success | 102 |
| depth_invalid | 10 |
| target_error_too_large | 8 |

Interpretation for draft use: the smoke validates the two harder YCB tasks and
the fixed `PickClutterYCB` adapter. Partial target occlusion already creates a
strong oracle gap for box-center depth, while PickClutterYCB exposes crop-median
fragility even at the smoke scale.

## 2026-05-15 Main Experiment v1 Results

- Primary config: `configs/experiments/main_v1_ieee_access.yaml`
- Confirmatory config: `configs/experiments/main_v1_ieee_access_confirmatory.yaml`
- Hard level-3 config: `configs/experiments/main_v1_ieee_access_hard_l3_extension.yaml`
- Backend: `maniskill`
- Remote project: `/data/openMythosBench_project`
- Primary output: `/data/openMythosBench_project/outputs/main_v1_ieee_access_20260514_full`
- Confirmatory output: `/data/openMythosBench_project/outputs/main_v1_ieee_access_confirmatory_20260514`
- Hard level-3 output: `/data/openMythosBench_project/outputs/main_v1_ieee_access_hard_l3_extension_20260514`

All queued H200 runs completed successfully. The primary run contains 44,800
episodes, the confirmatory run contains 22,400 episodes, and the hard level-3
extension contains 19,200 episodes. Each output root has a generated `report.md`,
and the hard level-3 extension completed with zero duplicate JSON result files.

Primary Main v1 baseline summary:

| Baseline | Success rate | Episodes | Mean target error | Oracle gap |
| --- | ---: | ---: | ---: | ---: |
| oracle_target | 0.9718 | 11200 | 0.0000 | - |
| crop_median_depth | 0.8104 | 11200 | 0.0640 | 0.1614 |
| box_center_depth | 0.7639 | 11200 | 0.0373 | 0.2079 |
| crop_top_surface | 0.4210 | 11200 | 0.1291 | 0.5508 |

Confirmatory Main v1 baseline summary:

| Baseline | Success rate | Episodes | Mean target error | Oracle gap |
| --- | ---: | ---: | ---: | ---: |
| oracle_target | 0.9707 | 5600 | 0.0000 | - |
| crop_median_depth | 0.8114 | 5600 | 0.0644 | 0.1593 |
| box_center_depth | 0.7434 | 5600 | 0.0424 | 0.2273 |
| crop_top_surface | 0.3805 | 5600 | 0.1376 | 0.5902 |

Hard level-3 extension baseline summary:

| Baseline | Success rate | Episodes | Mean target error | Oracle gap |
| --- | ---: | ---: | ---: | ---: |
| oracle_target | 0.9050 | 4800 | 0.0000 | - |
| crop_median_depth | 0.7442 | 4800 | 0.0651 | 0.1608 |
| box_center_depth | 0.5621 | 4800 | 0.0402 | 0.3429 |
| crop_top_surface | 0.3254 | 4800 | 0.1370 | 0.5796 |

Hard level-3 stressor summary:

| Stressor | Success rate | Episodes | Mean target error |
| --- | ---: | ---: | ---: |
| nearby_distractor | 0.8053 | 3200 | 0.0594 |
| same_color_distractor | 0.8053 | 3200 | 0.0594 |
| same_shape_distractor | 0.8053 | 3200 | 0.0594 |
| depth_sparsity | 0.6306 | 3200 | 0.0618 |
| partial_target_occlusion | 0.4450 | 3200 | 0.0777 |
| execution_offset_strong | 0.3134 | 3200 | 0.0594 |

Hard level-3 failure distribution:

| Failure type | Count |
| --- | ---: |
| success | 12176 |
| target_error_too_large | 5616 |
| depth_invalid | 1408 |

Interpretation for draft use: Main v1 now supports the paper's central claim.
Clean and distractor-only settings can make target-source methods look robust,
but stronger diagnostic perturbations reveal large oracle gaps. The full and
confirmatory runs agree on the ordering `oracle_target > crop_median_depth >
box_center_depth > crop_top_surface`, while the hard level-3 extension shows
that `execution_offset_strong`, `partial_target_occlusion`, and
`depth_sparsity` are the most discriminative stressors. The oracle remains high
under all hard level-3 stressors except strong execution offset, which should be
framed as a deliberately execution-limited regime rather than pure target-source
failure.

## 2026-05-18 Weekend H200 Extension Results

- Weekend queue log: `/data/openMythosBench_project/outputs/weekend_queue_20260516.log`
- Held-out Main v1 output: `/data/openMythosBench_project/outputs/weekend_main_v1_seed350_650_20260516`
- Visual/sensor bridge output: `/data/openMythosBench_project/outputs/weekend_visual_sensor_bridge_seed350_500_20260516`
- Hard level-3 confirmation output: `/data/openMythosBench_project/outputs/weekend_hard_l3_seed650_800_20260516`

All three weekend H200 runs completed successfully. The held-out Main v1
extension contains 134,400 episodes, the visual/sensor bridge contains 38,400
episodes, and the hard level-3 confirmation contains 14,400 episodes. All three
output roots have generated `report.md` files and zero duplicate JSON result
filenames. GPU 1-7 workers exited after completion.

Weekend held-out Main v1 baseline summary:

| Baseline | Success rate | Episodes | Mean target error | Oracle gap |
| --- | ---: | ---: | ---: | ---: |
| oracle_target | 0.9710 | 33600 | 0.0000 | - |
| crop_median_depth | 0.8166 | 33600 | 0.0624 | 0.1543 |
| box_center_depth | 0.7621 | 33600 | 0.0384 | 0.2088 |
| crop_top_surface | 0.4028 | 33600 | 0.1372 | 0.5682 |

Visual/sensor bridge baseline summary:

| Baseline | Success rate | Episodes | Mean target error | Oracle gap |
| --- | ---: | ---: | ---: | ---: |
| oracle_target | 0.9958 | 9600 | 0.0000 | - |
| box_center_depth | 0.8984 | 9600 | 0.0404 | 0.0974 |
| crop_median_depth | 0.8243 | 9600 | 0.0629 | 0.1716 |
| crop_top_surface | 0.4357 | 9600 | 0.1378 | 0.5601 |

Visual/sensor bridge stressor summary:

| Stressor | Success rate | Episodes | Mean target error |
| --- | ---: | ---: | ---: |
| camera_pose_noise | 0.8075 | 9600 | 0.0602 |
| depth_noise | 0.7877 | 9600 | 0.0619 |
| visual_occlusion | 0.7871 | 9600 | 0.0594 |
| execution_offset | 0.7720 | 9600 | 0.0596 |

Weekend hard level-3 confirmation summary:

| Baseline | Success rate | Episodes | Mean target error | Oracle gap |
| --- | ---: | ---: | ---: | ---: |
| oracle_target | 0.8967 | 3600 | 0.0000 | - |
| crop_median_depth | 0.7400 | 3600 | 0.0663 | 0.1567 |
| box_center_depth | 0.5619 | 3600 | 0.0406 | 0.3347 |
| crop_top_surface | 0.3300 | 3600 | 0.1357 | 0.5667 |

Weekend hard level-3 stressor summary:

| Stressor | Success rate | Episodes | Mean target error |
| --- | ---: | ---: | ---: |
| nearby_distractor | 0.8100 | 2400 | 0.0593 |
| same_color_distractor | 0.8100 | 2400 | 0.0593 |
| same_shape_distractor | 0.8100 | 2400 | 0.0593 |
| depth_sparsity | 0.6258 | 2400 | 0.0626 |
| partial_target_occlusion | 0.4504 | 2400 | 0.0775 |
| execution_offset_strong | 0.2867 | 2400 | 0.0593 |

Interpretation for draft use: the weekend extension strongly validates the
Main v1 story with a much larger held-out seed block. The baseline ordering is
stable, the large crop-top-surface oracle gap persists, and the hard level-3
confirmation reproduces the stressor ordering from the earlier hard extension.
The visual/sensor bridge restores the pilot perturbation families and shows
that execution, visual occlusion, and depth/camera noise all remain meaningful
diagnostic axes rather than one-off pilot artifacts.

## 2026-05-20 Semantic Distractor Validity Results

- Smoke output: `/data/openMythosBench_project/outputs/semantic_distractor_validity_v1_smoke_20260518`
- Main output: `/data/openMythosBench_project/outputs/semantic_distractor_validity_v1_20260518`
- Resume log: `/data/openMythosBench_project/outputs/semantic_distractor_validity_v1_21way_20260519.log`

The semantic distractor validity run completed successfully with 156,800
episodes, zero duplicate JSON result filenames, and a generated `report.md`.
The 300-episode smoke stage also has a generated report. The run used the
21-way GPU1-3 resume plan after GPU4-7 were freed for other work.

Semantic selector baseline summary:

| Baseline | Success rate | Episodes | Oracle gap |
| --- | ---: | ---: | ---: |
| oracle_target | 1.0000 | 22400 | - |
| crop_median_depth_query_aware | 0.8508 | 22400 | 0.1492 |
| box_center_depth_query_aware | 0.6446 | 22400 | 0.3554 |
| crop_median_depth_first_detection | 0.5379 | 22400 | 0.4621 |
| box_center_depth_first_detection | 0.4790 | 22400 | 0.5210 |
| crop_top_surface_query_aware | 0.3810 | 22400 | 0.6190 |
| crop_top_surface_first_detection | 0.3622 | 22400 | 0.6378 |

Selector effect:

| Target source | Query-aware | First detection | Delta |
| --- | ---: | ---: | ---: |
| box_center_depth | 0.6446 | 0.4790 | +0.1656 |
| crop_median_depth | 0.8508 | 0.5379 | +0.3129 |
| crop_top_surface | 0.3810 | 0.3622 | +0.0188 |

Level-3 semantic stressor findings:

| Stressor | Key result |
| --- | --- |
| nearby_distractor | query-aware box center stays at 0.9500; all first-detection target sources drop to 0.0000 |
| same_color_distractor | query-aware box center stays at 0.9500; all first-detection target sources drop to 0.0000 |
| same_shape_distractor | query-aware box center stays at 0.9500; all first-detection target sources drop to 0.0000 |
| partial_target_occlusion | crop median remains 0.7375, while box center drops to 0.0000 and crop top surface to 0.0762 |
| same_color_partial_occlusion | query-aware crop median remains 0.7375; first-detection target sources drop to 0.0000 |
| same_shape_nearby_occlusion | query-aware crop median remains 0.7375; first-detection target sources drop to 0.0000 |

Failure distribution:

| Failure type | Count |
| --- | ---: |
| success | 95323 |
| wrong_detection_selected | 28677 |
| target_error_too_large | 23200 |
| depth_invalid | 9600 |

Interpretation for draft use: this run resolves the main semantic-stressor
validity risk. Distractor stressors are no longer merely perturbation labels:
they produce a large, measurable separation between deterministic query-aware
selection and first-detection selection. The strongest selector effect appears
for `crop_median_depth` (+31.29 points) and `box_center_depth` (+16.56 points),
while `crop_top_surface` remains dominated by geometric fragility. The
`wrong_detection_selected` failure category gives the paper a direct failure
diagnosis channel for semantic/distractor stressors.

## 2026-05-20 Open-Vocab Bridge v2 Launch

- Smoke config: `configs/experiments/open_vocab_bridge_v2_smoke.yaml`
- Full config: `configs/experiments/open_vocab_bridge_v2.yaml`
- Queue log: `/data/openMythosBench_project/outputs/open_vocab_bridge_v2_queue_20260520.log`
- Smoke output: `/data/openMythosBench_project/outputs/open_vocab_bridge_v2_smoke_20260520`
- Full output after smoke gate: `/data/openMythosBench_project/outputs/open_vocab_bridge_v2_20260520`
- Follow-up launcher log: `/data/openMythosBench_project/outputs/followup_after_bridge_v2_20260520.log`
- Closed-loop queue log after Bridge v2 success: `/data/openMythosBench_project/outputs/closed_loop_sanity_queue_20260520.log`

Purpose: address the remaining reviewer concern that the learned-detector
bridge was too small and PickCube-only. The v2 bridge adds PickSingleYCB and
PickClutterYCB, first-detection lower comparators, metadata query-aware upper
comparators, GroundingDINO target sources, and the new `crop_trimmed_median_depth`
baseline family.

Local and remote dry-runs confirmed:

| Config | Expected episodes |
| --- | ---: |
| `open_vocab_bridge_v2_smoke.yaml` | 144 |
| `open_vocab_bridge_v2.yaml` | 13,500 |
| `closed_loop_sanity_smoke.yaml` | 80 |
| `closed_loop_sanity_subset.yaml` | 4,800 |

Initial remote status after launch: smoke passed with 144/144 JSON files and
zero runner failures, then the full 13,500-episode bridge launched with 15
workers on GPU1--3. A follow-up script is waiting for Bridge v2 to complete
cleanly before launching the closed-loop sanity queue. Do not claim v2 or
closed-loop results until the queues complete, duplicate checks pass, and
generated CSV tables are produced from JSON artifacts.
