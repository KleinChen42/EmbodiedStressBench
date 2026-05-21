#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-/home/zetyun/q2g_venv/bin/python}"
export GPUS="${GPUS:-1 1 1 1 2 2 2 2 3 3 3 3 4 4 4 4 5 5 5 5 6 6 6 6 7 7 7 7}"
export POLL_SECONDS="${POLL_SECONDS:-180}"
export MAX_RESTARTS="${MAX_RESTARTS:-120}"

SMOKE_CONFIG="${SMOKE_CONFIG:-configs/experiments/semantic_distractor_validity_v1_smoke.yaml}"
SMOKE_OUTPUT="${SMOKE_OUTPUT:-/data/openMythosBench_project/outputs/semantic_distractor_validity_v1_smoke_20260518}"
SMOKE_EXPECTED="${SMOKE_EXPECTED:-300}"

MAIN_CONFIG="${MAIN_CONFIG:-configs/experiments/semantic_distractor_validity_v1.yaml}"
MAIN_OUTPUT="${MAIN_OUTPUT:-/data/openMythosBench_project/outputs/semantic_distractor_validity_v1_20260518}"
MAIN_EXPECTED="${MAIN_EXPECTED:-156800}"

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

echo "[queue] semantic distractor validity queue start"
echo "[queue] GPUS=$GPUS"
echo "[queue] POLL_SECONDS=$POLL_SECONDS MAX_RESTARTS=$MAX_RESTARTS"

run_stage "semantic_distractor_validity_v1_smoke" "$SMOKE_CONFIG" "$SMOKE_OUTPUT" "$SMOKE_EXPECTED"
run_stage "semantic_distractor_validity_v1" "$MAIN_CONFIG" "$MAIN_OUTPUT" "$MAIN_EXPECTED"

echo "[queue] semantic distractor validity queue complete"
