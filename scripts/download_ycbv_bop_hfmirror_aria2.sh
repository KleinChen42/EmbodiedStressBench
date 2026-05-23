#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-/data/openMythosBench_project/external_data/ycbv_bop}"
LOG="${2:-/data/openMythosBench_project/outputs/download_ycbv_bop_hfmirror_aria2_20260522.log}"
BASE_URL="${YCBV_MIRROR_BASE_URL:-https://hf-mirror.com/datasets/bop-benchmark/ycbv/resolve/main}"

mkdir -p "$OUT" "$(dirname "$LOG")"
cd "$OUT"

echo "[start] $(date -Is)" | tee -a "$LOG"
for f in ycbv_base.zip ycbv_models.zip ycbv_test_all.zip; do
  url="${BASE_URL}/${f}"
  echo "[download] $f $(date -Is)" | tee -a "$LOG"
  aria2c \
    -c \
    -x 8 \
    -s 8 \
    -k 1M \
    --retry-wait=10 \
    --max-tries=0 \
    --timeout=60 \
    --connect-timeout=20 \
    --summary-interval=60 \
    -d "$OUT" \
    -o "$f" \
    "$url" 2>&1 | tee -a "$LOG"
  echo "[downloaded] $f $(stat -c%s "$OUT/$f") bytes" | tee -a "$LOG"
done

echo "[extract] $(date -Is)" | tee -a "$LOG"
for f in ycbv_base.zip ycbv_models.zip ycbv_test_all.zip; do
  unzip -n "$OUT/$f" -d "$OUT" 2>&1 | tee -a "$LOG"
done

cat > "$OUT/download_manifest.csv" <<EOF
file,bytes
ycbv_base.zip,$(stat -c%s "$OUT/ycbv_base.zip")
ycbv_models.zip,$(stat -c%s "$OUT/ycbv_models.zip")
ycbv_test_all.zip,$(stat -c%s "$OUT/ycbv_test_all.zip")
EOF

echo "[done] $(date -Is)" | tee -a "$LOG"
