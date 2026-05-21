#!/usr/bin/env bash
set -euo pipefail

CONFIG="${1:-configs/experiments/main_v1_ieee_access.yaml}"
OUTPUT_ROOT="${2:-/data/openMythosBench_project/outputs/main_v1_ieee_access_$(date +%Y%m%d)}"

bash scripts/launch_h200_maniskill_pilot.sh "$CONFIG" "$OUTPUT_ROOT"
