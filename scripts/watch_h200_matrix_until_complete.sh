#!/usr/bin/env bash
set -euo pipefail

CONFIG="${1:?config yaml required}"
OUTPUT_ROOT="${2:?output root required}"
EXPECTED_EPISODES="${3:?expected episode count required}"
POLL_SECONDS="${POLL_SECONDS:-300}"
MAX_RESTARTS="${MAX_RESTARTS:-80}"

mkdir -p "$OUTPUT_ROOT/logs"

count_results() {
  find "$OUTPUT_ROOT" -name '*.json' ! -name 'experiment_config_snapshot.json' 2>/dev/null | wc -l
}

any_running() {
  local pid_file pid
  shopt -s nullglob
  for pid_file in "$OUTPUT_ROOT"/logs/shard_*.pid; do
    pid="$(cat "$pid_file" 2>/dev/null || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
  done
  return 1
}

archive_logs() {
  local round="$1"
  local archive_dir="$OUTPUT_ROOT/logs/restart_round_${round}"
  mkdir -p "$archive_dir"
  shopt -s nullglob
  cp "$OUTPUT_ROOT"/logs/shard_*_gpu_*.log "$archive_dir"/ 2>/dev/null || true
}

restart_round=0
echo "[watch] config=$CONFIG"
echo "[watch] output=$OUTPUT_ROOT"
echo "[watch] expected_episodes=$EXPECTED_EPISODES"

while true; do
  current="$(count_results)"
  echo "[watch] $(date -Is) results=$current/$EXPECTED_EPISODES restarts=$restart_round"
  if [[ "$current" -ge "$EXPECTED_EPISODES" ]]; then
    echo "[watch] complete"
    exit 0
  fi

  if any_running; then
    sleep "$POLL_SECONDS"
    continue
  fi

  if [[ "$restart_round" -ge "$MAX_RESTARTS" ]]; then
    echo "[watch] ERROR: max restarts reached" >&2
    exit 2
  fi

  restart_round=$((restart_round + 1))
  archive_logs "$restart_round"
  echo "[watch] restarting round $restart_round"
  bash scripts/launch_h200_main_v1.sh "$CONFIG" "$OUTPUT_ROOT"
  sleep "$POLL_SECONDS"
done
