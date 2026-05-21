#!/usr/bin/env bash
set -euo pipefail
cd /data/openMythosBench_project
export PYTHON="${PYTHON:-/home/zetyun/q2g_venv/bin/python}"
export RUNNER_MODULE="embodied_stressbench.runners.run_matrix"
export GPUS="1 1 1 1 1 2 2 2 2 2 3 3 3 3 3"
export POLL_SECONDS="${POLL_SECONDS:-120}"
export MAX_RESTARTS="${MAX_RESTARTS:-120}"
export EMBODIED_STRESSBENCH_GDINO_LOCAL_FILES_ONLY="${EMBODIED_STRESSBENCH_GDINO_LOCAL_FILES_ONLY:-1}"
export EMBODIED_STRESSBENCH_GDINO_MODEL="${EMBODIED_STRESSBENCH_GDINO_MODEL:-IDEA-Research/grounding-dino-tiny}"
export EMBODIED_STRESSBENCH_GDINO_INIT_RETRIES="${EMBODIED_STRESSBENCH_GDINO_INIT_RETRIES:-3}"
CONFIG="configs/experiments/open_vocab_bridge_v2_ycb_clutter_heldout.yaml"
OUTPUT="/data/openMythosBench_project/outputs/open_vocab_bridge_v2_ycb_clutter_heldout_20260520"
EXPECTED=18000
ANALYSIS="/data/openMythosBench_project/outputs/scirep_overnight_20260520_analysis/open_vocab_bridge_v2_ycb_clutter_heldout"
echo "[fallback-resume] start $(date -Is) output=$OUTPUT expected=$EXPECTED"
bash scripts/watch_h200_matrix_until_complete.sh "$CONFIG" "$OUTPUT" "$EXPECTED"
"$PYTHON" -m embodied_stressbench.reporting.make_report --input "$OUTPUT" --output "$OUTPUT/report.md"
"$PYTHON" scripts/analyze_open_vocab_bridge_v2.py --input "$OUTPUT" --output-dir "$ANALYSIS" --expected "$EXPECTED"
echo "[fallback-resume] complete $(date -Is)"
