#!/usr/bin/env bash
set -euo pipefail

cd /data/openMythosBench_project

PYTHON="${PYTHON:-/home/zetyun/q2g_venv/bin/python}"
DATE_TAG="${DATE_TAG:-$(date +%Y%m%d)}"
SMOKE_CONFIG="${SMOKE_CONFIG:-configs/experiments/closed_loop_sanity_smoke.yaml}"
FULL_CONFIG="${FULL_CONFIG:-configs/experiments/closed_loop_sanity_subset.yaml}"
SMOKE_OUTPUT="${SMOKE_OUTPUT:-/data/openMythosBench_project/outputs/closed_loop_sanity_smoke_${DATE_TAG}}"
FULL_OUTPUT="${FULL_OUTPUT:-/data/openMythosBench_project/outputs/closed_loop_sanity_subset_${DATE_TAG}}"
SMOKE_EXPECTED="${SMOKE_EXPECTED:-80}"
FULL_EXPECTED="${FULL_EXPECTED:-4800}"

export RUNNER_MODULE="embodied_stressbench.runners.run_closed_loop_sanity"
export POLL_SECONDS="${POLL_SECONDS:-120}"
export MAX_RESTARTS="${MAX_RESTARTS:-60}"

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
unsupported = 0
oracle_total = 0
oracle_success = 0
for path in root.rglob("*.json"):
    if path.name == "experiment_config_snapshot.json":
        continue
    try:
        item = json.loads(path.read_text())
    except Exception:
        continue
    if item.get("failure_type") == "runner_exception" or item.get("status") == "error":
        count += 1
    if item.get("failure_type") == "scripted_executor_unsupported":
        unsupported += 1
    if item.get("baseline") == "oracle_target":
        oracle_total += 1
        oracle_success += int(bool(item.get("task_success")))
print(f"{count} {unsupported} {oracle_success} {oracle_total}")
PY
}

run_stage() {
  local name="$1"
  local config="$2"
  local output="$3"
  local expected="$4"
  local gpus="$5"
  echo "[closed-loop] stage=$name config=$config output=$output expected=$expected"
  export GPUS="$gpus"
  bash scripts/watch_h200_matrix_until_complete.sh "$config" "$output" "$expected"
  local current
  current="$(count_results "$output")"
  read -r failures unsupported oracle_success oracle_total <<< "$(count_runner_failures "$output")"
  echo "[closed-loop] stage=$name results=$current/$expected runner_failures=$failures unsupported=$unsupported oracle=$oracle_success/$oracle_total"
  if [[ "$current" -lt "$expected" ]]; then
    echo "[closed-loop] ERROR incomplete stage $name" >&2
    exit 2
  fi
  if [[ "$failures" -ne 0 || "$unsupported" -ne 0 ]]; then
    echo "[closed-loop] ERROR runner/unsupported failures in stage $name" >&2
    exit 3
  fi
  if [[ "$name" == "smoke" && "$oracle_total" -gt 0 ]]; then
    "$PYTHON" - "$oracle_success" "$oracle_total" <<'PY'
import sys
success = int(sys.argv[1])
total = int(sys.argv[2])
rate = success / total if total else 0.0
print(f"[closed-loop] oracle_smoke_rate={rate:.3f}")
raise SystemExit(0 if rate >= 0.80 else 4)
PY
  fi
}

echo "[closed-loop] queue_start $(date -Is)"
run_stage "smoke" "$SMOKE_CONFIG" "$SMOKE_OUTPUT" "$SMOKE_EXPECTED" "1 1 2 2 3 3"
run_stage "full" "$FULL_CONFIG" "$FULL_OUTPUT" "$FULL_EXPECTED" "1 1 1 2 2 2 3 3 3"
echo "[closed-loop] queue_complete $(date -Is)"
