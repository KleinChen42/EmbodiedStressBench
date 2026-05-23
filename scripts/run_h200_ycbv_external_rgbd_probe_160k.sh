#!/usr/bin/env bash
set -euo pipefail

export PROJECT_DIR="${PROJECT_DIR:-/data/openMythosBench_project}"
export DATA_ROOT="${DATA_ROOT:-/data/openMythosBench_project/external_data/ycbv_bop}"
export OUT_ROOT="${OUT_ROOT:-/data/openMythosBench_project/outputs/ycbv_external_rgbd_probe_160k_20260522}"
export SMOKE_ROOT="${SMOKE_ROOT:-/data/openMythosBench_project/outputs/ycbv_external_rgbd_probe_160k_20260522_smoke}"
export ANALYSIS_ROOT="${ANALYSIS_ROOT:-/data/openMythosBench_project/outputs/ycbv_external_rgbd_probe_160k_20260522_analysis}"
export LOG_PATH="${LOG_PATH:-/data/openMythosBench_project/outputs/ycbv_external_rgbd_probe_160k_20260522_queue.log}"
export MAX_TARGETS="${MAX_TARGETS:-160000}"
export FRAME_STRIDE="${FRAME_STRIDE:-1}"
export GPUS="${GPUS:-1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3}"

cd "$PROJECT_DIR"
exec bash scripts/run_h200_ycbv_external_rgbd_probe.sh
