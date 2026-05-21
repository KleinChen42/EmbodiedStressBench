#!/usr/bin/env bash
set -euo pipefail

CONFIG="${1:-configs/experiments/exp_maniskill_pilot.yaml}"
OUTPUT_ROOT="${2:-/data/openMythosBench_outputs/maniskill_pilot_$(date +%Y%m%d_%H%M%S)}"
PYTHON="${PYTHON:-/home/zetyun/q2g_venv/bin/python}"
GPUS="${GPUS:-1 2 3 4 5 6 7}"
RUNNER_MODULE="${RUNNER_MODULE:-embodied_stressbench.runners.run_matrix}"

mkdir -p "$OUTPUT_ROOT/logs"
read -r -a GPU_LIST <<< "$GPUS"
NUM_SHARDS="${#GPU_LIST[@]}"

echo "[launch] config=$CONFIG"
echo "[launch] output=$OUTPUT_ROOT"
echo "[launch] gpus=${GPU_LIST[*]}"
echo "[launch] runner=$RUNNER_MODULE"

for SHARD_INDEX in "${!GPU_LIST[@]}"; do
  GPU="${GPU_LIST[$SHARD_INDEX]}"
  SHARD_DIR="$OUTPUT_ROOT/shard_${SHARD_INDEX}"
  LOG="$OUTPUT_ROOT/logs/shard_${SHARD_INDEX}_gpu_${GPU}.log"
  (
    export CUDA_VISIBLE_DEVICES="$GPU"
    "$PYTHON" -m "$RUNNER_MODULE" \
      --config "$CONFIG" \
      --output "$SHARD_DIR" \
      --shard-index "$SHARD_INDEX" \
      --num-shards "$NUM_SHARDS"
  ) >"$LOG" 2>&1 &
  echo "$!" > "$OUTPUT_ROOT/logs/shard_${SHARD_INDEX}.pid"
  echo "[launch] shard=$SHARD_INDEX gpu=$GPU pid=$(cat "$OUTPUT_ROOT/logs/shard_${SHARD_INDEX}.pid") log=$LOG"
done

cat > "$OUTPUT_ROOT/check_status.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for pid_file in "$ROOT"/logs/shard_*.pid; do
  shard="$(basename "$pid_file" .pid)"
  pid="$(cat "$pid_file")"
  if kill -0 "$pid" 2>/dev/null; then
    state=running
  else
    state=done
  fi
  count="$(find "$ROOT/${shard}" -name '*.json' 2>/dev/null | wc -l || true)"
  echo -e "${shard}\tpid=${pid}\t${state}\tjson=${count}"
done
EOF
chmod +x "$OUTPUT_ROOT/check_status.sh"

echo "[launch] status: $OUTPUT_ROOT/check_status.sh"
