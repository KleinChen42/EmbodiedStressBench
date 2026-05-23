#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/data/openMythosBench_project}"
CURRENT_LOG="${CURRENT_LOG:-/data/openMythosBench_project/outputs/ycbv_external_rgbd_probe_160k_20260522_queue.log}"
CURRENT_ANALYSIS="${CURRENT_ANALYSIS:-/data/openMythosBench_project/outputs/ycbv_external_rgbd_probe_160k_20260522_analysis}"
CHAIN_LOG="${CHAIN_LOG:-/data/openMythosBench_project/outputs/ycbv_external_rgbd_threshold_sweep_after_160k_20260522.log}"
export DATA_ROOT="${DATA_ROOT:-/data/openMythosBench_project/external_data/ycbv_bop}"
export MAX_TARGETS="${MAX_TARGETS:-160000}"
export FRAME_STRIDE="${FRAME_STRIDE:-1}"
export GPUS="${GPUS:-1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3}"

cd "$PROJECT_DIR"
mkdir -p "$(dirname "$CHAIN_LOG")"

log() {
  echo "[ycbv-threshold-sweep] $(date -Is) $*" | tee -a "$CHAIN_LOG"
}

wait_for_current() {
  log "waiting_for_current current_log=$CURRENT_LOG current_analysis=$CURRENT_ANALYSIS"
  while true; do
    if [[ -f "$CURRENT_ANALYSIS/report.md" ]] && grep -q "queue_complete" "$CURRENT_LOG" 2>/dev/null; then
      log "current_complete"
      return 0
    fi
    local records=0
    if [[ -d /data/openMythosBench_project/outputs/ycbv_external_rgbd_probe_160k_20260522 ]]; then
      records=$(find /data/openMythosBench_project/outputs/ycbv_external_rgbd_probe_160k_20260522 -name records.jsonl -type f -print0 2>/dev/null | xargs -0 -r cat | wc -l)
    fi
    log "current_not_done records=$records"
    sleep 300
  done
}

run_threshold() {
  local tag="$1"
  local box_threshold="$2"
  local text_threshold="$3"
  export OUT_ROOT="/data/openMythosBench_project/outputs/ycbv_external_rgbd_probe_${tag}_20260522"
  export SMOKE_ROOT="/data/openMythosBench_project/outputs/ycbv_external_rgbd_probe_${tag}_20260522_smoke"
  export ANALYSIS_ROOT="/data/openMythosBench_project/outputs/ycbv_external_rgbd_probe_${tag}_20260522_analysis"
  export LOG_PATH="/data/openMythosBench_project/outputs/ycbv_external_rgbd_probe_${tag}_20260522_queue.log"
  export EMBODIED_STRESSBENCH_GDINO_BOX_THRESHOLD="$box_threshold"
  export EMBODIED_STRESSBENCH_GDINO_TEXT_THRESHOLD="$text_threshold"
  export EMBODIED_STRESSBENCH_GDINO_LOCAL_FILES_ONLY="${EMBODIED_STRESSBENCH_GDINO_LOCAL_FILES_ONLY:-1}"
  log "start_threshold tag=$tag box=$box_threshold text=$text_threshold out=$OUT_ROOT"
  bash scripts/run_h200_ycbv_external_rgbd_probe.sh
  log "done_threshold tag=$tag analysis=$ANALYSIS_ROOT"
}

wait_for_current
run_threshold "thr010" "0.10" "0.10"
run_threshold "thr030" "0.30" "0.25"
log "queue_complete"
