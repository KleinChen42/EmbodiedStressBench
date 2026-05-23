#!/usr/bin/env bash
set -euo pipefail

cd /data/openMythosBench_project

PYTHON="${PYTHON:-/home/zetyun/q2g_venv/bin/python}"
DATE_TAG="${DATE_TAG:-$(date +%Y%m%d)}"
SMOKE_CONFIG="${SMOKE_CONFIG:-configs/experiments/scirep_oracle_2d_box_control_smoke.yaml}"
FULL_CONFIG="${FULL_CONFIG:-configs/experiments/scirep_oracle_2d_box_control.yaml}"
SMOKE_OUTPUT="${SMOKE_OUTPUT:-/data/openMythosBench_project/outputs/scirep_oracle_2d_box_control_smoke_${DATE_TAG}}"
FULL_OUTPUT="${FULL_OUTPUT:-/data/openMythosBench_project/outputs/scirep_oracle_2d_box_control_${DATE_TAG}}"
SMOKE_EXPECTED="${SMOKE_EXPECTED:-72}"
FULL_EXPECTED="${FULL_EXPECTED:-37440}"

export LD_PRELOAD="${LD_PRELOAD:-/usr/lib/x86_64-linux-gnu/libgomp.so.1}"
export EMBODIED_STRESSBENCH_GDINO_LOCAL_FILES_ONLY="${EMBODIED_STRESSBENCH_GDINO_LOCAL_FILES_ONLY:-1}"
export EMBODIED_STRESSBENCH_GDINO_MODEL="${EMBODIED_STRESSBENCH_GDINO_MODEL:-IDEA-Research/grounding-dino-tiny}"
export EMBODIED_STRESSBENCH_GDINO_INIT_RETRIES="${EMBODIED_STRESSBENCH_GDINO_INIT_RETRIES:-3}"
export POLL_SECONDS="${POLL_SECONDS:-90}"
export MAX_RESTARTS="${MAX_RESTARTS:-100}"

count_results() {
  find "$1" -name '*.json' ! -name 'experiment_config_snapshot.json' 2>/dev/null | wc -l
}

count_runner_failures() {
  "$PYTHON" - "$1" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
count = 0
for path in root.rglob("*.json"):
    if path.name == "experiment_config_snapshot.json":
        continue
    try:
        item = json.loads(path.read_text())
    except Exception:
        continue
    if item.get("failure_type") == "runner_exception" or item.get("status") == "error":
        count += 1
print(count)
PY
}

count_duplicates() {
  find "$1" -name '*.json' ! -name 'experiment_config_snapshot.json' -printf '%f\n' 2>/dev/null \
    | sort | uniq -d | wc -l
}

run_stage() {
  local name="$1"
  local config="$2"
  local output="$3"
  local expected="$4"
  local gpus="$5"
  echo "[oracle-2d-control] stage=$name config=$config output=$output expected=$expected"
  export GPUS="$gpus"
  bash scripts/watch_h200_matrix_until_complete.sh "$config" "$output" "$expected"
  "$PYTHON" -m embodied_stressbench.reporting.make_report \
    --input "$output" \
    --output "$output/report.md"
  local current failures duplicates
  current="$(count_results "$output")"
  failures="$(count_runner_failures "$output")"
  duplicates="$(count_duplicates "$output")"
  echo "[oracle-2d-control] stage=$name results=$current/$expected runner_failures=$failures duplicates=$duplicates"
  if [[ "$current" -lt "$expected" ]]; then
    echo "[oracle-2d-control] ERROR incomplete stage $name" >&2
    exit 2
  fi
  if [[ "$failures" -ne 0 ]]; then
    echo "[oracle-2d-control] ERROR runner failures in stage $name: $failures" >&2
    exit 3
  fi
  if [[ "$duplicates" -ne 0 ]]; then
    echo "[oracle-2d-control] ERROR duplicate result names in stage $name: $duplicates" >&2
    exit 4
  fi
}

echo "[oracle-2d-control] queue_start $(date -Is)"
run_stage "smoke" "$SMOKE_CONFIG" "$SMOKE_OUTPUT" "$SMOKE_EXPECTED" "${SMOKE_GPUS:-1 1 1 2 2 2 3 3 3}"
run_stage "full" "$FULL_CONFIG" "$FULL_OUTPUT" "$FULL_EXPECTED" "${FULL_GPUS:-1 1 1 1 1 1 1 2 2 2 2 2 2 2 3 3 3 3 3 3 3}"
echo "[oracle-2d-control] queue_complete $(date -Is)"
