#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/data/openMythosBench_project}"
DATA_ROOT="${DATA_ROOT:-/data/openMythosBench_project/external_data/ycbv_bop}"
OUT_ROOT="${OUT_ROOT:-/data/openMythosBench_project/outputs/ycbv_external_rgbd_probe_20260522}"
SMOKE_ROOT="${SMOKE_ROOT:-/data/openMythosBench_project/outputs/ycbv_external_rgbd_probe_smoke_20260522}"
ANALYSIS_ROOT="${ANALYSIS_ROOT:-/data/openMythosBench_project/outputs/ycbv_external_rgbd_probe_20260522_analysis}"
LOG_PATH="${LOG_PATH:-/data/openMythosBench_project/outputs/ycbv_external_rgbd_probe_20260522_queue.log}"
PYTHON_BIN="${PYTHON_BIN:-/home/zetyun/q2g_venv/bin/python}"
GPUS=(${GPUS:-1 1 1 1 1 1 1 1 1 1 1 1 1 1 2 2 2 2 2 2 2 2 2 2 2 2 2 2 3 3 3 3 3 3 3 3 3 3 3 3 3 3})
MAX_TARGETS="${MAX_TARGETS:-6000}"
FRAME_STRIDE="${FRAME_STRIDE:-10}"

cd "$PROJECT_DIR"
mkdir -p "$(dirname "$LOG_PATH")" "$OUT_ROOT" "$SMOKE_ROOT" "$ANALYSIS_ROOT"

log() {
  echo "[ycbv-external] $(date -Is) $*" | tee -a "$LOG_PATH"
}

count_records() {
  find "$1" -name records.jsonl -type f -print0 2>/dev/null | xargs -0 -r cat | wc -l
}

launch_stage() {
  local root="$1"
  local num_shards="$2"
  local max_targets="$3"
  local frame_stride="$4"
  local include_gdino="$5"
  local pids=()
  rm -rf "$root"
  mkdir -p "$root"
  for ((i=0; i<num_shards; i++)); do
    local gpu="${GPUS[$((i % ${#GPUS[@]}))]}"
    local shard="$root/shard_${i}"
    mkdir -p "$shard"
    (
      export CUDA_VISIBLE_DEVICES="$gpu"
      export PYTHONPATH="$PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}"
      export EMBODIED_STRESSBENCH_GDINO_LOCAL_FILES_ONLY="${EMBODIED_STRESSBENCH_GDINO_LOCAL_FILES_ONLY:-1}"
      "$PYTHON_BIN" scripts/run_ycbv_external_rgbd_probe.py \
        --data-root "$DATA_ROOT" \
        --output "$shard" \
        --max-targets "$max_targets" \
        --frame-stride "$frame_stride" \
        --shard-index "$i" \
        --num-shards "$num_shards" \
        --query-variants generic true_name photo_true_name \
        $include_gdino \
        > "$shard/stdout.log" 2> "$shard/stderr.log"
    ) &
    pids+=("$!")
    log "launched shard=$i gpu=$gpu pid=${pids[-1]} root=$root"
    sleep 0.25
  done

  local failed=0
  while true; do
    local alive=0
    for pid in "${pids[@]}"; do
      if kill -0 "$pid" 2>/dev/null; then
        alive=$((alive + 1))
      fi
    done
    log "stage=$root records=$(count_records "$root") alive=$alive"
    if [[ "$alive" -eq 0 ]]; then
      break
    fi
    sleep 60
  done

  for pid in "${pids[@]}"; do
    if ! wait "$pid"; then
      failed=$((failed + 1))
    fi
  done
  log "stage=$root finished records=$(count_records "$root") failed_shards=$failed"
  return "$failed"
}

log "start data_root=$DATA_ROOT out=$OUT_ROOT gpus=${GPUS[*]}"
if [[ ! -d "$DATA_ROOT/test" ]]; then
  log "missing YCB-V data root: $DATA_ROOT"
  exit 2
fi

log "smoke start"
launch_stage "$SMOKE_ROOT" 3 24 20 "--include-grounding-dino"
"$PYTHON_BIN" scripts/analyze_ycbv_external_rgbd_probe.py --input "$SMOKE_ROOT" --output-dir "${SMOKE_ROOT}_analysis" | tee -a "$LOG_PATH"
if grep -R "frame_load_error\\|grounding_dino_exception" -n "$SMOKE_ROOT" >/tmp/ycbv_external_smoke_errors.txt 2>/dev/null; then
  log "smoke found hard errors; see /tmp/ycbv_external_smoke_errors.txt"
  cat /tmp/ycbv_external_smoke_errors.txt | tee -a "$LOG_PATH"
  exit 3
fi

log "full start shards=${#GPUS[@]} max_targets=$MAX_TARGETS frame_stride=$FRAME_STRIDE"
launch_stage "$OUT_ROOT" "${#GPUS[@]}" "$MAX_TARGETS" "$FRAME_STRIDE" "--include-grounding-dino"
"$PYTHON_BIN" scripts/analyze_ycbv_external_rgbd_probe.py --input "$OUT_ROOT" --output-dir "$ANALYSIS_ROOT" | tee -a "$LOG_PATH"
log "queue_complete analysis=$ANALYSIS_ROOT"
