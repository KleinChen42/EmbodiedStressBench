#!/usr/bin/env bash
set -euo pipefail

PRIMARY_CONFIG="${PRIMARY_CONFIG:-configs/experiments/main_v1_ieee_access.yaml}"
PRIMARY_OUTPUT="${PRIMARY_OUTPUT:-/data/openMythosBench_project/outputs/main_v1_ieee_access_20260514_full}"
PRIMARY_EXPECTED="${PRIMARY_EXPECTED:-44800}"

CONFIRM_CONFIG="${CONFIRM_CONFIG:-configs/experiments/main_v1_ieee_access_confirmatory.yaml}"
CONFIRM_OUTPUT="${CONFIRM_OUTPUT:-/data/openMythosBench_project/outputs/main_v1_ieee_access_confirmatory_20260514}"
CONFIRM_EXPECTED="${CONFIRM_EXPECTED:-22400}"

HARD_L3_CONFIG="${HARD_L3_CONFIG:-configs/experiments/main_v1_ieee_access_hard_l3_extension.yaml}"
HARD_L3_OUTPUT="${HARD_L3_OUTPUT:-/data/openMythosBench_project/outputs/main_v1_ieee_access_hard_l3_extension_20260514}"
HARD_L3_EXPECTED="${HARD_L3_EXPECTED:-19200}"

PYTHON="${PYTHON:-/home/zetyun/q2g_venv/bin/python}"

echo "[queue] primary start"
bash scripts/watch_h200_matrix_until_complete.sh "$PRIMARY_CONFIG" "$PRIMARY_OUTPUT" "$PRIMARY_EXPECTED"
"$PYTHON" -m embodied_stressbench.reporting.make_report \
  --input "$PRIMARY_OUTPUT" \
  --output "$PRIMARY_OUTPUT/report.md"

echo "[queue] confirmatory start"
bash scripts/watch_h200_matrix_until_complete.sh "$CONFIRM_CONFIG" "$CONFIRM_OUTPUT" "$CONFIRM_EXPECTED"
"$PYTHON" -m embodied_stressbench.reporting.make_report \
  --input "$CONFIRM_OUTPUT" \
  --output "$CONFIRM_OUTPUT/report.md"

echo "[queue] hard level-3 extension start"
bash scripts/watch_h200_matrix_until_complete.sh "$HARD_L3_CONFIG" "$HARD_L3_OUTPUT" "$HARD_L3_EXPECTED"
"$PYTHON" -m embodied_stressbench.reporting.make_report \
  --input "$HARD_L3_OUTPUT" \
  --output "$HARD_L3_OUTPUT/report.md"

echo "[queue] complete"
