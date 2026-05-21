# H200 Workflow

## Principle

Never launch full-scale experiments before small smoke tests pass.

## Scaling ladder

1. Single run.
2. Tiny matrix: 2 tasks × 2 baselines × 2 stressors × 2 levels × 3 seeds.
3. Small matrix: 3 tasks × 3 baselines × 3 stressors × 4 levels × 20 seeds.
4. Main matrix: 3–4 tasks × 5 baselines × 5–6 stressors × 4 levels × 100–300 seeds.

## SSH-safe launch

Use:

```bash
bash scripts/launch_h200_matrix.sh configs/experiments/exp_mvp_main.yaml outputs/exp_mvp_main_001
```

The script uses `setsid -f` and writes a PID file to avoid hanging SSH sessions.

## Status check

```bash
bash scripts/check_status.sh outputs/exp_mvp_main_001
```

## Experiment provenance

Each output directory should contain:

- `experiment_config_snapshot.json`
- `summary.jsonl`
- per-run JSON files
- logs
- generated reports

## GPU allocation TODO

The starter now supports sharded matrix launches for the ManiSkill pilot.
Use GPUs 1-7 and write outputs to `/data`, because the H200 root filesystem is
full.

```bash
cd /data/openMythosBench_project
bash scripts/launch_h200_maniskill_pilot.sh \
  configs/experiments/exp_maniskill_pilot.yaml \
  /data/openMythosBench_outputs/maniskill_pilot_20260514

/data/openMythosBench_outputs/maniskill_pilot_20260514/check_status.sh
```

After all shards finish:

```bash
/home/zetyun/q2g_venv/bin/python -m embodied_stressbench.reporting.make_report \
  --input /data/openMythosBench_outputs/maniskill_pilot_20260514 \
  --output /data/openMythosBench_outputs/maniskill_pilot_20260514/report.md
```

## Main v1 IEEE Access run

The Main v1 run should use the `/data` project mirror and write new outputs
under `/data/openMythosBench_project/outputs/`. Do not overwrite pilot outputs.

Dry-run the episode count:

```bash
cd /data/openMythosBench_project
/home/zetyun/q2g_venv/bin/python -m embodied_stressbench.runners.run_matrix \
  --config configs/experiments/main_v1_ieee_access.yaml \
  --output /data/openMythosBench_project/outputs/main_v1_ieee_access_dryrun \
  --dry-run
```

Smoke gate:

```bash
CUDA_VISIBLE_DEVICES=1 /home/zetyun/q2g_venv/bin/python -m embodied_stressbench.runners.run_matrix \
  --config configs/experiments/main_v1_ieee_access_smoke.yaml \
  --output /data/openMythosBench_project/outputs/main_v1_ieee_access_smoke_$(date +%Y%m%d)
```

Full sharded launch after the smoke passes:

```bash
cd /data/openMythosBench_project
bash scripts/launch_h200_main_v1.sh \
  configs/experiments/main_v1_ieee_access.yaml \
  /data/openMythosBench_project/outputs/main_v1_ieee_access_$(date +%Y%m%d)
```
