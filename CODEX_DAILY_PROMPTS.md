# Codex Daily Prompts

## Daily work template

```text
Today's goal:
[one concrete deliverable]

Constraints:
- Do not modify unrelated files.
- Run the smallest possible test after changes.
- Save outputs under outputs/date_task_name.
- If something fails, diagnose and propose the smallest fix.
- Do not start large-scale H200 jobs without passing smoke tests.

Deliverables:
1. Changed files summary.
2. Commands run.
3. Test results.
4. Next recommended step.
```

## Prompt 1: Read-only repository inspection

```text
Read the repository and summarize:
1. Existing structure.
2. Available simulation environments.
3. Existing Query-to-Grasp or RGB-D utilities that can be reused.
4. Missing dependencies.
5. The safest minimal path to run a smoke test.

Do not modify files yet.
Return a concrete implementation plan with file paths and commands.
```

## Prompt 2: Replace mock env with ManiSkill wrapper

```text
Implement the ManiSkill environment wrapper for EmbodiedStressBench.

Requirements:
- Support task names from config.
- Reset with a fixed seed.
- Return RGB-D observations if available.
- Return camera intrinsics/extrinsics if available.
- Provide object metadata when available.
- Provide a simple execute_pick or execute_pick_place interface.
- If some fields are unavailable, return None and log a warning instead of crashing.
- Keep the mock environment fallback working for CI or machines without ManiSkill.

Test:
Run PickCube for seeds 0, 1, 2 with oracle_target and save JSON metrics.
```

## Prompt 3: Implement depth baselines

```text
Implement the target-source baselines:

1. oracle_target
2. box_center_depth
3. crop_median_depth
4. crop_top_surface

Requirements:
- All baselines must share this interface:
  predict_target(observation, query, context) -> TargetPrediction
- TargetPrediction must include:
  target_3d, confidence, debug_info, failure_reason
- Save debug info to JSON.
- Add unit tests for depth back-projection.
- Add smoke command for each baseline.
```

## Prompt 4: Implement stressors

```text
Implement the first version of stressors:

1. depth_noise:
   Adds Gaussian noise and missing-depth masks to depth observations.

2. camera_pose_noise:
   Perturbs camera extrinsics by configurable translation/rotation noise if camera metadata is available.

3. visual_occlusion:
   Adds deterministic rectangular occluders or masks over RGB/depth regions.

4. execution_offset:
   Perturbs predicted 3D target before execution.

5. semantic_query_variants:
   Generates query variants from a config file.

Requirements:
- Each stressor must be deterministic with a seed.
- Each stressor must record its parameters in the output JSON.
- Stressors must be composable.
- Add configs/stressors/*.yaml.
- Add a stressor smoke test.
```

## Prompt 5: H200 runner

```text
Implement a robust H200 batch launcher.

Requirements:
- Read an experiment YAML.
- Iterate over tasks, baselines, stressor groups, levels, and seeds.
- Save one JSON file per run and one JSONL summary file.
- Support resume: skip runs whose output JSON already exists.
- Support parallel execution using subprocess workers.
- Add progress logging.
- Add failure-safe behavior: if one run crashes, record an error JSON and continue.
- Add scripts/launch_h200_matrix.sh for detached execution on a multi-GPU server.

Important:
Use clean process detachment suitable for SSH:
- Prefer setsid -f.
- Write PID files.
- Write status.tsv.
- Avoid hanging SSH sessions.

Test:
Run a tiny matrix:
2 tasks × 2 baselines × 2 stressors × 2 levels × 3 seeds.
```

## Prompt 6: Reporting and paper artifacts

```text
Implement reporting utilities.

Requirements:
- Read all JSON/JSONL results from an output directory.
- Aggregate success rate by task, baseline, stressor, and level.
- Compute oracle gap:
  oracle_success_rate - baseline_success_rate.
- Compute target error statistics.
- Compute failure type distribution.
- Generate:
  1. CSV tables
  2. LaTeX tables
  3. PNG figures
  4. Markdown report

Do not hardcode results.
Every table and figure must be generated from result files.
```
