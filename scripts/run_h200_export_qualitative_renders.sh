#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=${PROJECT_DIR:-/data/openMythosBench_project}
PYTHON_BIN=${PYTHON_BIN:-/home/zetyun/q2g_venv/bin/python}
MANIFEST=${MANIFEST:-scientific_reports_revision_20260521/qualitative_case_manifest.csv}
OUTPUT_DIR=${OUTPUT_DIR:-paper/scientific_reports/figures/maniskill_qualitative}

cd "$PROJECT_DIR"
"$PYTHON_BIN" scripts/export_maniskill_qualitative_renders.py \
  --manifest "$MANIFEST" \
  --output-dir "$OUTPUT_DIR" \
  --backend maniskill

echo "[qualitative] wrote render panels to $OUTPUT_DIR"
