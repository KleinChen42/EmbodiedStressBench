# Closed-Loop Sanity Report

Input root: `/data/openMythosBench_project/outputs/closed_loop_oracle_calibration_v2_smoke_20260521`

## Counts

- Expected episodes: 20
- Completed episodes: 20
- Duplicate result count: 0
- Runner exceptions: 0

## Diagnostic Calibration

- Diagnostic success rate: 1.0000
- Task success rate: 0.1000
- Agreement rate: 0.1000
- Oracle task success rate: 0.1000
- Correlation(target error, task success): nan
- AUROC(target error predicts task failure): 0.5000

## Paper-Use Rule

Use closed-loop results as Scientific Reports calibration evidence only if duplicate count is zero, runner exceptions are zero, and oracle task success passes the configured task gates.
