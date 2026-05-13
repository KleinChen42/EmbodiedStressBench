#!/usr/bin/env bash
set -euo pipefail
python -m embodied_stressbench.runners.run_single \
  --task PickCube \
  --baseline oracle_target \
  --seed 0 \
  --output outputs/smoke_pickcube_oracle
python -m embodied_stressbench.runners.run_matrix \
  --config configs/experiments/exp_tiny_mock.yaml \
  --output outputs/tiny_mock
python -m embodied_stressbench.reporting.make_report \
  --input outputs/tiny_mock \
  --output outputs/tiny_mock/report.md
