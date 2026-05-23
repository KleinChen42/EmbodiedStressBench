#!/usr/bin/env bash
set -euo pipefail

cd /data/openMythosBench_project

PYTHON="${PYTHON:-/home/zetyun/q2g_venv/bin/python}"
DATE_TAG="${DATE_TAG:-20260521_r4}"
GPUS=(${GPUS:-1 2 3})
export PYTHONPATH="/data/openMythosBench_project:${PYTHONPATH:-}"
if [[ -z "${LD_PRELOAD:-}" && -e /usr/lib/x86_64-linux-gnu/libgomp.so.1 ]]; then
  export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libgomp.so.1
fi

CONFIG="${CONFIG:-configs/experiments/open_vocab_true_name_ablation_small.yaml}"
OUTPUT="/data/openMythosBench_project/outputs/open_vocab_true_name_ablation_small_${DATE_TAG}"
ANALYSIS="/data/openMythosBench_project/outputs/scirep_true_name_ablation_small_${DATE_TAG}"
LOG_DIR="/data/openMythosBench_project/outputs/true_name_ablation_${DATE_TAG}_logs"
REPORT="/data/openMythosBench_project/outputs/true_name_ablation_${DATE_TAG}_report.md"

mkdir -p "$OUTPUT" "$ANALYSIS" "$LOG_DIR"

count_results() {
  find "$1" -name '*.json' ! -name 'experiment_config_snapshot.json' 2>/dev/null | wc -l
}

duplicate_count() {
  find "$1" -name '*.json' ! -name 'experiment_config_snapshot.json' -printf '%f\n' 2>/dev/null | sort | uniq -d | wc -l
}

shards=6
pids=()
for idx in $(seq 0 $((shards - 1))); do
  gpu="${GPUS[$((idx % ${#GPUS[@]}))]}"
  env LD_PRELOAD="${LD_PRELOAD:-}" CUDA_VISIBLE_DEVICES="$gpu" "$PYTHON" -m embodied_stressbench.runners.run_matrix \
    --config "$CONFIG" \
    --output "$OUTPUT/shard_${idx}" \
    --shard-index "$idx" \
    --num-shards "$shards" \
    >"$LOG_DIR/shard_${idx}.log" 2>&1 &
  pids+=("$!")
done

failed=0
for pid in "${pids[@]}"; do
  if ! wait "$pid"; then
    failed=1
  fi
done

env LD_PRELOAD="${LD_PRELOAD:-}" "$PYTHON" scripts/analyze_open_vocab_bridge_v2.py \
  --input "$OUTPUT" \
  --output-dir "$ANALYSIS" \
  --expected 960

count="$(count_results "$OUTPUT")"
dups="$(duplicate_count "$OUTPUT")"
{
  echo "# True-name YCB Query Ablation"
  echo
  echo "- Date tag: ${DATE_TAG}"
  echo "- Config: \`${CONFIG}\`"
  echo "- Output: \`${OUTPUT}\`"
  echo "- Analysis: \`${ANALYSIS}\`"
  echo "- Count: ${count}/960"
  echo "- Duplicate filenames: ${dups}"
  echo "- Runner exit failure flag: ${failed}"
  echo "- LD_PRELOAD: ${LD_PRELOAD:-unset}"
} >"$REPORT"

if [[ "$failed" != "0" ]]; then
  exit 1
fi

echo "Wrote $REPORT"
