#!/usr/bin/env bash
set -euo pipefail

cd /data/openMythosBench_project

PYTHON="${PYTHON:-/home/zetyun/q2g_venv/bin/python}"
DATE_TAG="${DATE_TAG:-20260520}"
SMOKE_CONFIG="${SMOKE_CONFIG:-configs/experiments/open_vocab_grounding_dino_smoke.yaml}"
SMALL_CONFIG="${SMALL_CONFIG:-configs/experiments/open_vocab_grounding_dino_ieee_access_small.yaml}"
SMOKE_OUTPUT="${SMOKE_OUTPUT:-/data/openMythosBench_project/outputs/open_vocab_grounding_dino_smoke_${DATE_TAG}}"
SMALL_OUTPUT="${SMALL_OUTPUT:-/data/openMythosBench_project/outputs/open_vocab_grounding_dino_ieee_access_small_${DATE_TAG}}"
SMOKE_EXPECTED="${SMOKE_EXPECTED:-100}"
SMALL_EXPECTED="${SMALL_EXPECTED:-1200}"

export EMBODIED_STRESSBENCH_GDINO_LOCAL_FILES_ONLY="${EMBODIED_STRESSBENCH_GDINO_LOCAL_FILES_ONLY:-1}"
export EMBODIED_STRESSBENCH_GDINO_MODEL="${EMBODIED_STRESSBENCH_GDINO_MODEL:-IDEA-Research/grounding-dino-tiny}"
export POLL_SECONDS="${POLL_SECONDS:-60}"
export MAX_RESTARTS="${MAX_RESTARTS:-30}"

count_results() {
  find "$1" -name '*.json' ! -name 'experiment_config_snapshot.json' 2>/dev/null | wc -l
}

count_failures() {
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

run_stage() {
  local config="$1"
  local output="$2"
  local expected="$3"
  local gpus="$4"
  echo "[open-vocab] stage config=$config"
  echo "[open-vocab] output=$output"
  echo "[open-vocab] expected=$expected"
  echo "[open-vocab] GPUS=$gpus"
  export GPUS="$gpus"
  bash scripts/watch_h200_matrix_until_complete.sh "$config" "$output" "$expected"
  "$PYTHON" -m embodied_stressbench.reporting.make_report \
    --input "$output" \
    --output "$output/report.md"
  local current
  current="$(count_results "$output")"
  local failures
  failures="$(count_failures "$output")"
  echo "[open-vocab] completed output=$output results=$current failures=$failures"
  if [[ "$current" -lt "$expected" ]]; then
    echo "[open-vocab] ERROR incomplete stage: $current/$expected" >&2
    exit 2
  fi
  if [[ "$failures" -ne 0 ]]; then
    echo "[open-vocab] ERROR runner failures detected: $failures" >&2
    exit 3
  fi
}

echo "[open-vocab] queue_start $(date -Is)"
run_stage "$SMOKE_CONFIG" "$SMOKE_OUTPUT" "$SMOKE_EXPECTED" "1 1 1 2 2 2 3 3 3"
run_stage "$SMALL_CONFIG" "$SMALL_OUTPUT" "$SMALL_EXPECTED" "1 1 1 1 1 2 2 2 2 2 3 3 3 3 3"
echo "[open-vocab] queue_complete $(date -Is)"
