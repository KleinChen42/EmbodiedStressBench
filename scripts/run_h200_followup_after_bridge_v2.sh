#!/usr/bin/env bash
set -euo pipefail

cd /data/openMythosBench_project

BRIDGE_LOG="${BRIDGE_LOG:-outputs/open_vocab_bridge_v2_queue_20260520.log}"
FOLLOWUP_LOG="${FOLLOWUP_LOG:-outputs/closed_loop_sanity_queue_20260520.log}"
POLL_SECONDS="${POLL_SECONDS:-300}"

echo "[followup] waiting_for_bridge $(date -Is) bridge_log=$BRIDGE_LOG"
while pgrep -af "run_h200_open_vocab_bridge_v2_queue.sh" >/dev/null 2>&1; do
  sleep "$POLL_SECONDS"
done

if grep -q "\[bridge-v2\] queue_complete" "$BRIDGE_LOG"; then
  echo "[followup] bridge_complete $(date -Is); launching closed-loop sanity"
  DATE_TAG="${DATE_TAG:-20260520}" bash scripts/run_h200_closed_loop_sanity_queue.sh >"$FOLLOWUP_LOG" 2>&1
  echo "[followup] closed_loop_done $(date -Is) log=$FOLLOWUP_LOG"
else
  echo "[followup] bridge queue did not complete cleanly; closed-loop sanity skipped" >&2
  exit 2
fi
