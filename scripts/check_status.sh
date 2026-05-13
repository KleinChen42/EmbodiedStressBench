#!/usr/bin/env bash
set -euo pipefail
OUT=${1:-outputs/tiny_mock}
echo "== status =="
cat "$OUT/status.tsv" 2>/dev/null || true
echo "== pid =="
cat "$OUT/pidfile" 2>/dev/null || true
echo "== results =="
find "$OUT" -name '*.json' | wc -l
echo "== latest log =="
tail -n 80 "$OUT/logs/main.log" 2>/dev/null || true
