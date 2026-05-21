#!/usr/bin/env bash
set -euo pipefail

cd /data/openMythosBench_project

export GPUS="${GPUS:-1 1 1 1 1 1 1 2 2 2 2 2 2 2 3 3 3 3 3 3 3}"
export POLL_SECONDS="${POLL_SECONDS:-180}"
export MAX_RESTARTS="${MAX_RESTARTS:-120}"

CONFIG="${CONFIG:-configs/experiments/semantic_distractor_validity_v1.yaml}"
OUTPUT="${OUTPUT:-/data/openMythosBench_project/outputs/semantic_distractor_validity_v1_20260518}"
EXPECTED="${EXPECTED:-156800}"
PYTHON="${PYTHON:-/home/zetyun/q2g_venv/bin/python}"

echo "[resume21] config=$CONFIG"
echo "[resume21] output=$OUTPUT"
echo "[resume21] expected=$EXPECTED"
echo "[resume21] GPUS=$GPUS"

bash scripts/watch_h200_matrix_until_complete.sh "$CONFIG" "$OUTPUT" "$EXPECTED"
"$PYTHON" -m embodied_stressbench.reporting.make_report \
  --input "$OUTPUT" \
  --output "$OUTPUT/report.md"

duplicates="$(find "$OUTPUT" -name '*.json' ! -name 'experiment_config_snapshot.json' -printf '%f\n' 2>/dev/null | sort | uniq -d | wc -l)"
echo "[resume21] duplicate_result_filenames=$duplicates"
echo "[resume21] complete"
