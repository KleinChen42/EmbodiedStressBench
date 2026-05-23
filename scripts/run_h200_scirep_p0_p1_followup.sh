#!/usr/bin/env bash
set -euo pipefail

cd /data/openMythosBench_project

PYTHON="${PYTHON:-/home/zetyun/q2g_venv/bin/python}"
DATE_TAG="${DATE_TAG:-20260521}"
GPUS=(${GPUS:-1 2 3})
export PYTHONPATH="/data/openMythosBench_project:${PYTHONPATH:-}"
if [[ -z "${LD_PRELOAD:-}" && -e /usr/lib/x86_64-linux-gnu/libgomp.so.1 ]]; then
  export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libgomp.so.1
fi

CLOSED_CONFIG="configs/experiments/closed_loop_oracle_gate_audit_200.yaml"
CLOSED_OUTPUT="/data/openMythosBench_project/outputs/closed_loop_oracle_gate_audit_200_${DATE_TAG}"
CLOSED_ANALYSIS="/data/openMythosBench_project/outputs/scirep_closed_loop_oracle_gate_audit_200_${DATE_TAG}"
PROBE_OUTPUT="/data/openMythosBench_project/outputs/ycb_target_identity_deep_probe_${DATE_TAG}"
ABLATION_CONFIG="configs/experiments/open_vocab_true_name_ablation_small.yaml"
ABLATION_OUTPUT="/data/openMythosBench_project/outputs/open_vocab_true_name_ablation_small_${DATE_TAG}"
ABLATION_ANALYSIS="/data/openMythosBench_project/outputs/scirep_true_name_ablation_small_${DATE_TAG}"
LOG_DIR="/data/openMythosBench_project/outputs/scirep_p0_p1_followup_${DATE_TAG}_logs"
REPORT="/data/openMythosBench_project/outputs/scirep_p0_p1_followup_${DATE_TAG}_report.md"

mkdir -p "$CLOSED_OUTPUT" "$CLOSED_ANALYSIS" "$PROBE_OUTPUT" "$ABLATION_OUTPUT" "$ABLATION_ANALYSIS" "$LOG_DIR"

count_results() {
  find "$1" -name '*.json' ! -name 'experiment_config_snapshot.json' 2>/dev/null | wc -l
}

duplicate_count() {
  find "$1" -name '*.json' ! -name 'experiment_config_snapshot.json' -printf '%f\n' 2>/dev/null | sort | uniq -d | wc -l
}

run_closed_loop_audit() {
  local shards=6
  local pids=()
  for idx in $(seq 0 $((shards - 1))); do
    local gpu="${GPUS[$((idx % ${#GPUS[@]}))]}"
    env LD_PRELOAD="${LD_PRELOAD:-}" CUDA_VISIBLE_DEVICES="$gpu" "$PYTHON" -m embodied_stressbench.runners.run_closed_loop_sanity \
      --config "$CLOSED_CONFIG" \
      --output "$CLOSED_OUTPUT/shard_${idx}" \
      --shard-index "$idx" \
      --num-shards "$shards" \
      >"$LOG_DIR/closed_loop_audit_shard_${idx}.log" 2>&1 &
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

run_true_name_ablation() {
  local shards=6
  local pids=()
  for idx in $(seq 0 $((shards - 1))); do
    local gpu="${GPUS[$((idx % ${#GPUS[@]}))]}"
    env LD_PRELOAD="${LD_PRELOAD:-}" CUDA_VISIBLE_DEVICES="$gpu" "$PYTHON" -m embodied_stressbench.runners.run_matrix \
      --config "$ABLATION_CONFIG" \
      --output "$ABLATION_OUTPUT/shard_${idx}" \
      --shard-index "$idx" \
      --num-shards "$shards" \
      >"$LOG_DIR/true_name_ablation_shard_${idx}.log" 2>&1 &
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

{
  echo "# Scientific Reports P0/P1 Follow-up Report"
  echo
  echo "- Date tag: ${DATE_TAG}"
  echo "- GPUs: ${GPUS[*]}"
  echo "- LD_PRELOAD: ${LD_PRELOAD:-unset}"
  echo "- Closed-loop output: \`${CLOSED_OUTPUT}\`"
  echo "- Deep identity probe: \`${PROBE_OUTPUT}\`"
  echo "- Conditional true-name ablation: \`${ABLATION_OUTPUT}\`"
  echo
} >"$REPORT"

run_closed_loop_audit
env LD_PRELOAD="${LD_PRELOAD:-}" "$PYTHON" scripts/analyze_closed_loop_sanity.py \
  --input "$CLOSED_OUTPUT" \
  --output-dir "$CLOSED_ANALYSIS" \
  --expected 200

closed_count="$(count_results "$CLOSED_OUTPUT")"
closed_dup="$(duplicate_count "$CLOSED_OUTPUT")"
{
  echo "## Closed-loop oracle-gate audit"
  echo
  echo "- Count: ${closed_count}/200"
  echo "- Duplicate filenames: ${closed_dup}"
  echo "- Analysis: \`${CLOSED_ANALYSIS}\`"
} >>"$REPORT"

env LD_PRELOAD="${LD_PRELOAD:-}" "$PYTHON" scripts/probe_maniskill_target_identity_deep.py \
  --tasks PickSingleYCB PickClutterYCB \
  --seeds 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 \
  --output-dir "$PROBE_OUTPUT"

cat "$PROBE_OUTPUT/target_identity_deep_probe_audit.md" >>"$REPORT"

allowed="$("$PYTHON" - "$PROBE_OUTPUT/target_identity_deep_probe_summary.csv" <<'PY'
import pandas as pd, sys
df = pd.read_csv(sys.argv[1])
resolved = pd.to_numeric(df["resolved_object_name_rows"], errors="coerce").fillna(0)
print(int(len(resolved) > 0 and bool((resolved > 0).all())))
PY
)"

if [[ "$allowed" == "1" ]]; then
  {
    echo
    echo "## Conditional true-name ablation"
    echo
    echo "Deep probe resolved non-generic object names; running 960-episode ablation."
  } >>"$REPORT"
  run_true_name_ablation
  env LD_PRELOAD="${LD_PRELOAD:-}" "$PYTHON" scripts/analyze_open_vocab_bridge_v2.py \
    --input "$ABLATION_OUTPUT" \
    --output-dir "$ABLATION_ANALYSIS" \
    --expected 960
  ablation_count="$(count_results "$ABLATION_OUTPUT")"
  ablation_dup="$(duplicate_count "$ABLATION_OUTPUT")"
  {
    echo "- Count: ${ablation_count}/960"
    echo "- Duplicate filenames: ${ablation_dup}"
    echo "- Analysis: \`${ABLATION_ANALYSIS}\`"
  } >>"$REPORT"
else
  {
    echo
    echo "## Conditional true-name ablation"
    echo
    echo "Skipped. Deep probe did not resolve non-generic YCB object names, so a true-name ablation would be misleading."
  } >>"$REPORT"
fi

echo "Wrote $REPORT"
