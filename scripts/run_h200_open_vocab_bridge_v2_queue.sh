#!/usr/bin/env bash
set -euo pipefail

cd /data/openMythosBench_project

PYTHON="${PYTHON:-/home/zetyun/q2g_venv/bin/python}"
DATE_TAG="${DATE_TAG:-$(date +%Y%m%d)}"
SMOKE_CONFIG="${SMOKE_CONFIG:-configs/experiments/open_vocab_bridge_v2_smoke.yaml}"
FULL_CONFIG="${FULL_CONFIG:-configs/experiments/open_vocab_bridge_v2.yaml}"
SMOKE_OUTPUT="${SMOKE_OUTPUT:-/data/openMythosBench_project/outputs/open_vocab_bridge_v2_smoke_${DATE_TAG}}"
FULL_OUTPUT="${FULL_OUTPUT:-/data/openMythosBench_project/outputs/open_vocab_bridge_v2_${DATE_TAG}}"
SMOKE_EXPECTED="${SMOKE_EXPECTED:-144}"
FULL_EXPECTED="${FULL_EXPECTED:-13500}"

export EMBODIED_STRESSBENCH_GDINO_LOCAL_FILES_ONLY="${EMBODIED_STRESSBENCH_GDINO_LOCAL_FILES_ONLY:-1}"
export EMBODIED_STRESSBENCH_GDINO_MODEL="${EMBODIED_STRESSBENCH_GDINO_MODEL:-IDEA-Research/grounding-dino-tiny}"
export EMBODIED_STRESSBENCH_GDINO_INIT_RETRIES="${EMBODIED_STRESSBENCH_GDINO_INIT_RETRIES:-3}"
export POLL_SECONDS="${POLL_SECONDS:-90}"
export MAX_RESTARTS="${MAX_RESTARTS:-80}"

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
  local name="$1"
  local config="$2"
  local output="$3"
  local expected="$4"
  local gpus="$5"
  echo "[bridge-v2] stage=$name config=$config output=$output expected=$expected"
  export GPUS="$gpus"
  bash scripts/watch_h200_matrix_until_complete.sh "$config" "$output" "$expected"
  "$PYTHON" -m embodied_stressbench.reporting.make_report \
    --input "$output" \
    --output "$output/report.md"
  local current
  current="$(count_results "$output")"
  local failures
  failures="$(count_failures "$output")"
  echo "[bridge-v2] stage=$name results=$current/$expected runner_failures=$failures"
  if [[ "$current" -lt "$expected" ]]; then
    echo "[bridge-v2] ERROR incomplete stage $name" >&2
    exit 2
  fi
  if [[ "$failures" -ne 0 ]]; then
    echo "[bridge-v2] ERROR runner failures in stage $name: $failures" >&2
    exit 3
  fi
}

echo "[bridge-v2] queue_start $(date -Is)"
run_stage "smoke" "$SMOKE_CONFIG" "$SMOKE_OUTPUT" "$SMOKE_EXPECTED" "1 1 1 2 2 2 3 3 3"
run_stage "full" "$FULL_CONFIG" "$FULL_OUTPUT" "$FULL_EXPECTED" "1 1 1 1 1 2 2 2 2 2 3 3 3 3 3"
echo "[bridge-v2] queue_complete $(date -Is)"
