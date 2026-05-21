#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-/home/zetyun/q2g_venv/bin/python}"
export GPUS="${GPUS:-1 1 1 1 2 2 2 2 3 3 3 3 4 4 4 4 5 5 5 5 6 6 6 6 7 7 7 7}"
export POLL_SECONDS="${POLL_SECONDS:-180}"
export MAX_RESTARTS="${MAX_RESTARTS:-120}"

MAIN_EXT_CONFIG="${MAIN_EXT_CONFIG:-configs/experiments/weekend_main_v1_seed350_650.yaml}"
MAIN_EXT_OUTPUT="${MAIN_EXT_OUTPUT:-/data/openMythosBench_project/outputs/weekend_main_v1_seed350_650_20260516}"
MAIN_EXT_EXPECTED="${MAIN_EXT_EXPECTED:-134400}"

VISUAL_BRIDGE_CONFIG="${VISUAL_BRIDGE_CONFIG:-configs/experiments/weekend_visual_sensor_bridge_seed350_500.yaml}"
VISUAL_BRIDGE_OUTPUT="${VISUAL_BRIDGE_OUTPUT:-/data/openMythosBench_project/outputs/weekend_visual_sensor_bridge_seed350_500_20260516}"
VISUAL_BRIDGE_EXPECTED="${VISUAL_BRIDGE_EXPECTED:-38400}"

HARD_L3_CONFIG="${HARD_L3_CONFIG:-configs/experiments/weekend_hard_l3_seed650_800.yaml}"
HARD_L3_OUTPUT="${HARD_L3_OUTPUT:-/data/openMythosBench_project/outputs/weekend_hard_l3_seed650_800_20260516}"
HARD_L3_EXPECTED="${HARD_L3_EXPECTED:-14400}"

report_stage() {
  local output="$1"
  "$PYTHON" -m embodied_stressbench.reporting.make_report \
    --input "$output" \
    --output "$output/report.md"
  local duplicates
  duplicates="$(find "$output" -name '*.json' ! -name 'experiment_config_snapshot.json' -printf '%f\n' 2>/dev/null | sort | uniq -d | wc -l)"
  echo "[queue] duplicate_result_filenames=$duplicates output=$output"
}

run_stage() {
  local name="$1"
  local config="$2"
  local output="$3"
  local expected="$4"
  echo "[queue] $name start"
  echo "[queue] config=$config"
  echo "[queue] output=$output"
  echo "[queue] expected=$expected"
  bash scripts/watch_h200_matrix_until_complete.sh "$config" "$output" "$expected"
  report_stage "$output"
  echo "[queue] $name complete"
}

echo "[queue] weekend queue start"
echo "[queue] GPUS=$GPUS"
echo "[queue] POLL_SECONDS=$POLL_SECONDS MAX_RESTARTS=$MAX_RESTARTS"

run_stage "weekend_main_v1_seed350_650" "$MAIN_EXT_CONFIG" "$MAIN_EXT_OUTPUT" "$MAIN_EXT_EXPECTED"
run_stage "weekend_visual_sensor_bridge_seed350_500" "$VISUAL_BRIDGE_CONFIG" "$VISUAL_BRIDGE_OUTPUT" "$VISUAL_BRIDGE_EXPECTED"
run_stage "weekend_hard_l3_seed650_800" "$HARD_L3_CONFIG" "$HARD_L3_OUTPUT" "$HARD_L3_EXPECTED"

echo "[queue] weekend queue complete"
