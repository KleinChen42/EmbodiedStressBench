#!/usr/bin/env bash
set -euo pipefail

cd /data/openMythosBench_project

PYTHON="${PYTHON:-/home/zetyun/q2g_venv/bin/python}"
DATE_TAG="${DATE_TAG:-20260521}"
GPUS=(${GPUS:-1 2 3})
export PYTHONPATH="/data/openMythosBench_project:${PYTHONPATH:-}"

SMOKE_CONFIG="configs/experiments/closed_loop_oracle_calibration_v2_smoke.yaml"
FULL_CONFIG="configs/experiments/closed_loop_oracle_calibration_v2.yaml"
SMOKE_OUTPUT="/data/openMythosBench_project/outputs/closed_loop_oracle_calibration_v2_smoke_${DATE_TAG}"
FULL_OUTPUT="/data/openMythosBench_project/outputs/closed_loop_oracle_calibration_v2_${DATE_TAG}"
ANALYSIS_ROOT="/data/openMythosBench_project/outputs/scirep_closed_loop_oracle_calibration_v2_${DATE_TAG}"
LOG_DIR="/data/openMythosBench_project/outputs/closed_loop_oracle_calibration_v2_${DATE_TAG}_logs"
REPORT="/data/openMythosBench_project/outputs/closed_loop_oracle_calibration_v2_${DATE_TAG}_report.md"

mkdir -p "$SMOKE_OUTPUT" "$FULL_OUTPUT" "$ANALYSIS_ROOT" "$LOG_DIR"

count_results() {
  find "$1" -name '*.json' ! -name 'experiment_config_snapshot.json' 2>/dev/null | wc -l
}

duplicate_count() {
  find "$1" -name '*.json' ! -name 'experiment_config_snapshot.json' -printf '%f\n' 2>/dev/null | sort | uniq -d | wc -l
}

run_sharded() {
  local config="$1"
  local output="$2"
  local shards="$3"
  local prefix="$4"
  local pids=()
  for idx in $(seq 0 $((shards - 1))); do
    local gpu="${GPUS[$((idx % ${#GPUS[@]}))]}"
    CUDA_VISIBLE_DEVICES="$gpu" "$PYTHON" -m embodied_stressbench.runners.run_closed_loop_sanity \
      --config "$config" \
      --output "$output/shard_${idx}" \
      --shard-index "$idx" \
      --num-shards "$shards" \
      >"$LOG_DIR/${prefix}_shard_${idx}.log" 2>&1 &
    pids+=("$!")
  done
  local failed=0
  for pid in "${pids[@]}"; do
    if ! wait "$pid"; then
      failed=1
    fi
  done
  return "$failed"
}

analyze() {
  local input="$1"
  local expected="$2"
  local name="$3"
  "$PYTHON" scripts/analyze_closed_loop_sanity.py \
    --input "$input" \
    --output-dir "$ANALYSIS_ROOT/$name" \
    --expected "$expected"
}

gate_passes() {
  "$PYTHON" - "$ANALYSIS_ROOT/smoke/closed_loop_oracle_gate_by_task.csv" <<'PY'
import pandas as pd, sys
path = sys.argv[1]
df = pd.read_csv(path)
def rate(task):
    row = df[df["task"] == task]
    return float(row["oracle_task_success_rate"].iloc[0]) if len(row) else 0.0
pick = rate("PickCube")
ycb = rate("PickSingleYCB")
print(f"PickCube={pick:.3f} PickSingleYCB={ycb:.3f}")
raise SystemExit(0 if pick >= 0.80 and ycb >= 0.70 else 1)
PY
}

{
  echo "# Closed-loop Oracle Calibration v2 Report"
  echo
  echo "- Date tag: ${DATE_TAG}"
  echo "- Smoke output: \`${SMOKE_OUTPUT}\`"
  echo "- Full output: \`${FULL_OUTPUT}\`"
  echo "- Analysis root: \`${ANALYSIS_ROOT}\`"
  echo
} >"$REPORT"

run_sharded "$SMOKE_CONFIG" "$SMOKE_OUTPUT" 3 "smoke"
analyze "$SMOKE_OUTPUT" 20 "smoke"
smoke_count="$(count_results "$SMOKE_OUTPUT")"
smoke_dup="$(duplicate_count "$SMOKE_OUTPUT")"
{
  echo "## Smoke"
  echo
  echo "- Count: ${smoke_count}/20"
  echo "- Duplicate filenames: ${smoke_dup}"
} >>"$REPORT"

if gate_line="$(gate_passes)"; then
  echo "- Oracle gate: PASS (${gate_line})" >>"$REPORT"
  run_sharded "$FULL_CONFIG" "$FULL_OUTPUT" 6 "full"
  analyze "$FULL_OUTPUT" 1200 "full"
  full_count="$(count_results "$FULL_OUTPUT")"
  full_dup="$(duplicate_count "$FULL_OUTPUT")"
  {
    echo
    echo "## Full calibration"
    echo
    echo "- Count: ${full_count}/1200"
    echo "- Duplicate filenames: ${full_dup}"
    echo "- Analysis: \`${ANALYSIS_ROOT}/full\`"
  } >>"$REPORT"
else
  echo "- Oracle gate: FAIL (${gate_line:-no gate output})" >>"$REPORT"
  {
    echo
    echo "## Full calibration"
    echo
    echo "Skipped because the oracle smoke gate failed. Manuscript execution claims must remain downgraded."
  } >>"$REPORT"
fi

echo "Wrote $REPORT"
