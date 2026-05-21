#!/usr/bin/env bash
set -euo pipefail

CONFIG=${1:-configs/experiments/exp_mvp_main.yaml}
OUT=${2:-outputs/exp_mvp_main_$(date +%Y%m%d_%H%M%S)}
mkdir -p "$OUT/logs"

cat > "$OUT/run.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$(pwd)"
python -m embodied_stressbench.runners.run_matrix --config "$CONFIG" --output "$OUT" \
  > "$OUT/logs/main.log" 2>&1
EOF
chmod +x "$OUT/run.sh"

setsid bash "$OUT/run.sh" >/dev/null 2>&1 < /dev/null &
echo $! > "$OUT/pidfile"
echo -e "timestamp\tstatus\tconfig\toutput" > "$OUT/status.tsv"
echo -e "$(date -Iseconds)\tlaunched\t$CONFIG\t$OUT" >> "$OUT/status.tsv"
echo "Launched. Output: $OUT"
echo "PID file: $OUT/pidfile"
