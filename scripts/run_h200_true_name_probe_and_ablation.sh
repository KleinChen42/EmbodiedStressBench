#!/usr/bin/env bash
set -euo pipefail

cd /data/openMythosBench_project

PYTHON="${PYTHON:-/home/zetyun/q2g_venv/bin/python}"
DATE_TAG="${DATE_TAG:-20260521}"
GPUS=(${GPUS:-1 2 3})
export PYTHONPATH="/data/openMythosBench_project:${PYTHONPATH:-}"

PROBE_OUT="/data/openMythosBench_project/outputs/ycb_true_name_probe_${DATE_TAG}"
ABLATION_OUT="/data/openMythosBench_project/outputs/open_vocab_true_name_query_ablation_ycb_clutter_${DATE_TAG}"
ANALYSIS_OUT="/data/openMythosBench_project/outputs/scirep_true_name_query_ablation_${DATE_TAG}"
LOG_DIR="/data/openMythosBench_project/outputs/open_vocab_true_name_query_ablation_${DATE_TAG}_logs"
REPORT="/data/openMythosBench_project/outputs/open_vocab_true_name_query_ablation_${DATE_TAG}_report.md"
CONFIG="configs/experiments/open_vocab_true_name_query_ablation_ycb_clutter.yaml"

mkdir -p "$PROBE_OUT" "$ABLATION_OUT" "$ANALYSIS_OUT" "$LOG_DIR"

count_results() {
  find "$1" -name '*.json' ! -name 'experiment_config_snapshot.json' 2>/dev/null | wc -l
}

duplicate_count() {
  find "$1" -name '*.json' ! -name 'experiment_config_snapshot.json' -printf '%f\n' 2>/dev/null | sort | uniq -d | wc -l
}

run_query_ablation() {
  local shards=6
  local pids=()
  for idx in $(seq 0 $((shards - 1))); do
    local gpu="${GPUS[$((idx % ${#GPUS[@]}))]}"
    CUDA_VISIBLE_DEVICES="$gpu" "$PYTHON" -m embodied_stressbench.runners.run_matrix \
      --config "$CONFIG" \
      --output "$ABLATION_OUT/shard_${idx}" \
      --shard-index "$idx" \
      --num-shards "$shards" \
      >"$LOG_DIR/ablation_shard_${idx}.log" 2>&1 &
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
  echo "# YCB True-Name Probe and Query Ablation"
  echo
  echo "- Date tag: ${DATE_TAG}"
  echo "- Probe output: \`${PROBE_OUT}\`"
  echo "- Conditional ablation output: \`${ABLATION_OUT}\`"
  echo
} >"$REPORT"

"$PYTHON" scripts/probe_maniskill_target_names.py \
  --tasks PickSingleYCB PickClutterYCB \
  --seeds 0 1 2 3 4 5 6 7 8 9 \
  --output-dir "$PROBE_OUT"

allowed="$("$PYTHON" - "$PROBE_OUT/target_name_probe_summary.csv" <<'PY'
import pandas as pd, sys
df = pd.read_csv(sys.argv[1])
print(int(bool(df["true_name_ablation_allowed"].iloc[0])))
PY
)"
cat "$PROBE_OUT/target_name_probe_audit.md" >>"$REPORT"

if [[ "$allowed" == "1" ]]; then
  echo >>"$REPORT"
  echo "## Conditional ablation" >>"$REPORT"
  echo >>"$REPORT"
  echo "Probe found non-generic target labels; running true-name query ablation." >>"$REPORT"
  run_query_ablation
  "$PYTHON" scripts/analyze_open_vocab_bridge_v2.py \
    --input "$ABLATION_OUT" \
    --output-dir "$ANALYSIS_OUT" \
    --expected 5120
  count="$(count_results "$ABLATION_OUT")"
  dup="$(duplicate_count "$ABLATION_OUT")"
  {
    echo "- Count: ${count}/5120"
    echo "- Duplicate filenames: ${dup}"
    echo "- Analysis: \`${ANALYSIS_OUT}\`"
  } >>"$REPORT"
else
  echo >>"$REPORT"
  echo "## Conditional ablation" >>"$REPORT"
  echo >>"$REPORT"
  echo "Skipped. Probe did not expose non-generic YCB target labels, so a true-name ablation would be misleading." >>"$REPORT"
fi

echo "Wrote $REPORT"
