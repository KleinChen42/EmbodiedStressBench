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

The starter does not implement GPU pinning. Add it only after the CPU/mock and ManiSkill smoke tests pass.
