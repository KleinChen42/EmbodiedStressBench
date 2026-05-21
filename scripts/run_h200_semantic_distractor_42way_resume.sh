#!/usr/bin/env bash
set -euo pipefail

cd /data/openMythosBench_project

export GPUS="${GPUS:-1 1 1 1 1 1 2 2 2 2 2 2 3 3 3 3 3 3 4 4 4 4 4 4 5 5 5 5 5 5 6 6 6 6 6 6 7 7 7 7 7 7}"
export POLL_SECONDS="${POLL_SECONDS:-180}"
export MAX_RESTARTS="${MAX_RESTARTS:-120}"

CONFIG="${CONFIG:-configs/experiments/semantic_distractor_validity_v1.yaml}"
OUTPUT="${OUTPUT:-/data/openMythosBench_project/outputs/semantic_distractor_validity_v1_20260518}"
EXPECTED="${EXPECTED:-156800}"
PYTHON="${PYTHON:-/home/zetyun/q2g_venv/bin/python}"

echo "[resume42] config=$CONFIG"
echo "[resume42] output=$OUTPUT"
echo "[resume42] expected=$EXPECTED"
echo "[resume42] GPUS=$GPUS"

bash scripts/watch_h200_matrix_until_complete.sh "$CONFIG" "$OUTPUT" "$EXPECTED"
"$PYTHON" -m embodied_stressbench.reporting.make_report \
  --input "$OUTPUT" \
  --output "$OUTPUT/report.md"

duplicates="$(find "$OUTPUT" -name '*.json' ! -name 'experiment_config_snapshot.json' -printf '%f\n' 2>/dev/null | sort | uniq -d | wc -l)"
echo "[resume42] duplicate_result_filenames=$duplicates"
echo "[resume42] complete"
