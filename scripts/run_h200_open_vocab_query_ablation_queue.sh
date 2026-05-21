#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=${PROJECT_DIR:-/data/openMythosBench_project}
PYTHON_BIN=${PYTHON_BIN:-/home/zetyun/q2g_venv/bin/python}
CONFIG=${CONFIG:-configs/experiments/open_vocab_query_ablation_ycb_clutter.yaml}
OUTPUT_ROOT=${OUTPUT_ROOT:-/data/openMythosBench_project/outputs/open_vocab_query_ablation_ycb_clutter_20260521}
ANALYSIS_ROOT=${ANALYSIS_ROOT:-/data/openMythosBench_project/outputs/scirep_query_ablation_20260521}
GPUS=(${GPUS:-1 1 1 2 2 2 3 3 3})
POLL_SECONDS=${POLL_SECONDS:-120}

cd "$PROJECT_DIR"
mkdir -p "$OUTPUT_ROOT" "$ANALYSIS_ROOT"

echo "[query-ablation] dry run"
"$PYTHON_BIN" -m embodied_stressbench.runners.run_matrix \
  --config "$CONFIG" \
  --output "$OUTPUT_ROOT" \
  --dry-run

num_shards=${#GPUS[@]}
for idx in "${!GPUS[@]}"; do
  shard_dir="$OUTPUT_ROOT/shard_$idx"
  mkdir -p "$shard_dir"
  (
    export CUDA_VISIBLE_DEVICES="${GPUS[$idx]}"
    "$PYTHON_BIN" -m embodied_stressbench.runners.run_matrix \
      --config "$CONFIG" \
      --output "$shard_dir" \
      --shard-index "$idx" \
      --num-shards "$num_shards"
  ) > "$OUTPUT_ROOT/shard_$idx.log" 2>&1 &
  echo "[query-ablation] shard $idx/$num_shards gpu=${GPUS[$idx]} pid=$!"
done

while true; do
  running=0
  for job in $(jobs -p); do
    if kill -0 "$job" 2>/dev/null; then
      running=$((running + 1))
    fi
  done
  count=$(find "$OUTPUT_ROOT" -name '*.json' ! -name experiment_config_snapshot.json | wc -l)
  echo "[query-ablation] $(date -Iseconds) json=$count running=$running"
  if [[ "$running" -eq 0 ]]; then
    break
  fi
  sleep "$POLL_SECONDS"
done

"$PYTHON_BIN" scripts/analyze_open_vocab_bridge_v2.py \
  --input "$OUTPUT_ROOT" \
  --output-dir "$ANALYSIS_ROOT" \
  --expected 3840

echo "[query-ablation] analysis written to $ANALYSIS_ROOT"
