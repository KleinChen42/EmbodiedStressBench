#!/usr/bin/env bash
set -euo pipefail
IN=${1:-outputs/tiny_mock}
OUT=${2:-$IN/report.md}
python -m embodied_stressbench.reporting.make_report --input "$IN" --output "$OUT"
echo "Report: $OUT"
