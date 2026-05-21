#!/usr/bin/env bash
set -euo pipefail

cd /data/openMythosBench_project

PYTHON="${PYTHON:-/home/zetyun/q2g_venv/bin/python}"
DATE_TAG="${DATE_TAG:-20260520}"
POLL_SECONDS="${POLL_SECONDS:-300}"

BRIDGE_OUTPUT="${BRIDGE_OUTPUT:-/data/openMythosBench_project/outputs/open_vocab_bridge_v2_${DATE_TAG}}"
BRIDGE_LOG="${BRIDGE_LOG:-/data/openMythosBench_project/outputs/open_vocab_bridge_v2_queue_${DATE_TAG}.log}"
BRIDGE_EXPECTED="${BRIDGE_EXPECTED:-13500}"

CLOSED_SMOKE_OUTPUT="${CLOSED_SMOKE_OUTPUT:-/data/openMythosBench_project/outputs/closed_loop_sanity_smoke_${DATE_TAG}}"
CLOSED_FULL_OUTPUT="${CLOSED_FULL_OUTPUT:-/data/openMythosBench_project/outputs/closed_loop_sanity_subset_${DATE_TAG}}"
CLOSED_LOG="${CLOSED_LOG:-/data/openMythosBench_project/outputs/closed_loop_sanity_queue_${DATE_TAG}.log}"
CLOSED_EXPECTED="${CLOSED_EXPECTED:-4800}"

CALIB_OUTPUT="${CALIB_OUTPUT:-/data/openMythosBench_project/outputs/closed_loop_calibration_heldout_${DATE_TAG}}"
FALLBACK_OUTPUT="${FALLBACK_OUTPUT:-/data/openMythosBench_project/outputs/open_vocab_bridge_v2_ycb_clutter_heldout_${DATE_TAG}}"

ANALYSIS_ROOT="${ANALYSIS_ROOT:-/data/openMythosBench_project/outputs/scirep_overnight_${DATE_TAG}_analysis}"
REPORT_PATH="${REPORT_PATH:-/data/openMythosBench_project/outputs/overnight_${DATE_TAG}_experiment_report.md}"
STATUS_PATH="${STATUS_PATH:-/data/openMythosBench_project/docs/scientific_reports_experiment_status.md}"
CLAIM_PATH="${CLAIM_PATH:-/data/openMythosBench_project/docs/claim_evidence_table_scientific_reports.md}"

export EMBODIED_STRESSBENCH_GDINO_LOCAL_FILES_ONLY="${EMBODIED_STRESSBENCH_GDINO_LOCAL_FILES_ONLY:-1}"
export EMBODIED_STRESSBENCH_GDINO_MODEL="${EMBODIED_STRESSBENCH_GDINO_MODEL:-IDEA-Research/grounding-dino-tiny}"
export EMBODIED_STRESSBENCH_GDINO_INIT_RETRIES="${EMBODIED_STRESSBENCH_GDINO_INIT_RETRIES:-3}"

mkdir -p "$ANALYSIS_ROOT" "$(dirname "$REPORT_PATH")"

log() {
  echo "[scirep-overnight] $(date -Is) $*"
}

count_results() {
  find "$1" -name '*.json' ! -name 'experiment_config_snapshot.json' 2>/dev/null | wc -l
}

duplicate_count() {
  local root="$1"
  find "$root" -name '*.json' ! -name 'experiment_config_snapshot.json' -printf '%f\n' 2>/dev/null \
    | sort | uniq -d | wc -l
}

runner_exception_count() {
  "$PYTHON" - "$1" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
count = 0
for path in root.rglob("*.json"):
    if path.name == "experiment_config_snapshot.json":
        continue
    try:
        item = json.loads(path.read_text())
    except Exception:
        count += 1
        continue
    if item.get("failure_type") == "runner_exception" or item.get("status") == "error":
        count += 1
print(count)
PY
}

output_running() {
  local root="$1"
  local pid_file pid
  shopt -s nullglob
  for pid_file in "$root"/logs/shard_*.pid; do
    pid="$(cat "$pid_file" 2>/dev/null || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
  done
  return 1
}

append_report() {
  local section="$1"
  shift || true
  {
    echo
    echo "## $section"
    echo
    printf '%s\n' "$@"
  } >> "$REPORT_PATH"
}

write_header() {
  cat > "$REPORT_PATH" <<EOF
# Overnight Scientific Reports Experiment Report

Date tag: ${DATE_TAG}

This live report is written by \`scripts/run_h200_scirep_overnight_20260520.sh\`.
It uses GPU1--3 only and does not launch Octo/OpenVLA/VLA or new external-model dependencies.

EOF
}

write_scirep_docs() {
  cat > "$STATUS_PATH" <<EOF
# Scientific Reports Experiment Status

Last updated: $(date -Is)

## Overnight queue

- Orchestrator: \`scripts/run_h200_scirep_overnight_20260520.sh\`
- Live report: \`$REPORT_PATH\`
- Analysis root: \`$ANALYSIS_ROOT\`
- GPU allocation: GPU1--3

## Priority rule

1. Wait for Open-Vocab Bridge v2; do not duplicate it.
2. Audit Bridge v2 once complete.
3. Let or launch the closed-loop sanity subset.
4. If closed-loop gates pass, launch closed-loop calibration held-out.
5. If closed-loop gates fail, launch YCB/clutter Open-Vocab Bridge fallback.

EOF

  cat > "$CLAIM_PATH" <<EOF
# Scientific Reports Claim-Evidence Table

| Claim | Evidence source | Current status | Claim control |
| --- | --- | --- | --- |
| Parameterized simulation stressors expose target-generation failures | Main v1, held-out, hard L3, semantic distractor reports | Supported by completed diagnostic JSON/CSV | No real-robot robustness claim |
| Target sources show a precision-vs-robustness tradeoff | Threshold sensitivity CSV/table and target-error CDF | Supported by completed analysis | Do not claim crop-median is universally strongest |
| Open-vocabulary detectors can be evaluated through the same protocol | GroundingDINO bridge and Bridge v2 audit | Bridge v2 pending/audited by this queue | Do not claim GroundingDINO solves semantic grounding |
| Diagnostic target success is informative for scripted execution success | Closed-loop sanity and calibration held-out | Pending tonight's gate and extension | Not a closed-loop policy benchmark |
| Failure taxonomy separates wrong detection, invalid depth, target displacement, and execution sensitivity | Failure-distribution CSVs and qualitative manifest | Supported for diagnostic runs; closed-loop extension pending | Use taxonomy as diagnosis, not causal proof beyond logged artifacts |

EOF
}

audit_bridge() {
  local out_dir="$ANALYSIS_ROOT/open_vocab_bridge_v2"
  mkdir -p "$out_dir"
  "$PYTHON" scripts/analyze_open_vocab_bridge_v2.py \
    --input "$BRIDGE_OUTPUT" \
    --output-dir "$out_dir" \
    --expected "$BRIDGE_EXPECTED"
  "$PYTHON" -m embodied_stressbench.reporting.make_report \
    --input "$BRIDGE_OUTPUT" \
    --output "$BRIDGE_OUTPUT/report.md"
}

analyze_closed_loop() {
  local input="$1"
  local expected="$2"
  local name="$3"
  local out_dir="$ANALYSIS_ROOT/$name"
  mkdir -p "$out_dir"
  "$PYTHON" scripts/analyze_closed_loop_sanity.py \
    --input "$input" \
    --output-dir "$out_dir" \
    --expected "$expected"
}

wait_for_bridge() {
  log "checking Bridge v2"
  local current
  current="$(count_results "$BRIDGE_OUTPUT")"
  append_report "Initial state" \
    "- Bridge v2 output: \`$BRIDGE_OUTPUT\`" \
    "- Initial Bridge v2 count: $current/$BRIDGE_EXPECTED" \
    "- Existing follow-up log: \`$CLOSED_LOG\`"
  while [[ "$current" -lt "$BRIDGE_EXPECTED" ]]; do
    log "Bridge v2 incomplete: $current/$BRIDGE_EXPECTED; sleeping ${POLL_SECONDS}s"
    sleep "$POLL_SECONDS"
    current="$(count_results "$BRIDGE_OUTPUT")"
  done
  log "Bridge v2 reached $current/$BRIDGE_EXPECTED"
  audit_bridge
  local dup fail
  dup="$(duplicate_count "$BRIDGE_OUTPUT")"
  fail="$(runner_exception_count "$BRIDGE_OUTPUT")"
  append_report "Bridge v2 audit" \
    "- Count: $current/$BRIDGE_EXPECTED" \
    "- Duplicate filenames: $dup" \
    "- Runner exceptions: $fail" \
    "- Audit directory: \`$ANALYSIS_ROOT/open_vocab_bridge_v2\`" \
    "- Report: \`$BRIDGE_OUTPUT/report.md\`"
}

wait_or_run_closed_loop() {
  local current
  current="$(count_results "$CLOSED_FULL_OUTPUT")"
  if [[ "$current" -ge "$CLOSED_EXPECTED" ]]; then
    log "closed-loop sanity already complete"
    return 0
  fi

  if pgrep -af "run_h200_followup_after_bridge_v2.sh|run_h200_closed_loop_sanity_queue.sh" >/dev/null 2>&1 || output_running "$CLOSED_SMOKE_OUTPUT" || output_running "$CLOSED_FULL_OUTPUT"; then
    log "closed-loop follow-up or queue already running; waiting"
  else
    log "closed-loop queue not running; launching it once"
    DATE_TAG="$DATE_TAG" bash scripts/run_h200_closed_loop_sanity_queue.sh >"$CLOSED_LOG" 2>&1 &
  fi

  while pgrep -af "run_h200_followup_after_bridge_v2.sh|run_h200_closed_loop_sanity_queue.sh" >/dev/null 2>&1 || output_running "$CLOSED_SMOKE_OUTPUT" || output_running "$CLOSED_FULL_OUTPUT"; do
    current="$(count_results "$CLOSED_FULL_OUTPUT")"
    log "closed-loop sanity progress full=$current/$CLOSED_EXPECTED"
    sleep "$POLL_SECONDS"
  done
}

closed_loop_gate() {
  local full_count smoke_count
  full_count="$(count_results "$CLOSED_FULL_OUTPUT")"
  smoke_count="$(count_results "$CLOSED_SMOKE_OUTPUT")"
  if [[ "$full_count" -ge "$CLOSED_EXPECTED" ]]; then
    analyze_closed_loop "$CLOSED_FULL_OUTPUT" "$CLOSED_EXPECTED" "closed_loop_sanity"
  elif [[ "$smoke_count" -gt 0 ]]; then
    analyze_closed_loop "$CLOSED_SMOKE_OUTPUT" 80 "closed_loop_sanity_smoke"
    append_report "Closed-loop sanity incomplete" \
      "- Full count: $full_count/$CLOSED_EXPECTED" \
      "- Smoke count: $smoke_count/80" \
      "- Closed-loop full did not complete; using fallback path."
    return 1
  else
    append_report "Closed-loop sanity missing" \
      "- Full count: $full_count/$CLOSED_EXPECTED" \
      "- Smoke count: $smoke_count/80" \
      "- No usable closed-loop outputs; using fallback path."
    return 1
  fi

  "$PYTHON" - "$ANALYSIS_ROOT/closed_loop_sanity/closed_loop_sanity_summary.csv" "$ANALYSIS_ROOT/closed_loop_sanity/closed_loop_oracle_gate_by_task.csv" <<'PY'
import pandas as pd, sys
summary = pd.read_csv(sys.argv[1]).iloc[0]
gates = pd.read_csv(sys.argv[2])
def rate(task):
    row = gates[gates["task"] == task]
    return float(row["oracle_task_success_rate"].iloc[0]) if len(row) else 0.0
runner_ok = int(summary["runner_exception_count"]) == 0
dup_ok = int(summary["duplicate_result_count"]) == 0
pick_ok = rate("PickCube") >= 0.80
ycb_ok = rate("PickSingleYCB") >= 0.70
stack_ok = rate("StackCube") >= 0.80
stable = runner_ok and dup_ok and pick_ok and ycb_ok
print(f"stable={int(stable)} include_stack={int(stack_ok)} pick={rate('PickCube'):.3f} ycb={rate('PickSingleYCB'):.3f} stack={rate('StackCube'):.3f}")
raise SystemExit(0 if stable else 1)
PY
}

launch_calibration() {
  local gate_line="$1"
  local include_stack expected config
  include_stack="$(echo "$gate_line" | sed -n 's/.*include_stack=\([01]\).*/\1/p')"
  if [[ "$include_stack" == "1" ]]; then
    config="configs/experiments/closed_loop_calibration_heldout_with_stackcube.yaml"
    expected=9600
  else
    config="configs/experiments/closed_loop_calibration_heldout_no_stackcube.yaml"
    expected=6400
  fi
  local current
  current="$(count_results "$CALIB_OUTPUT")"
  append_report "Closed-loop calibration launch" \
    "- Gate: $gate_line" \
    "- Config: \`$config\`" \
    "- Output: \`$CALIB_OUTPUT\`" \
    "- Expected: $expected" \
    "- Existing count: $current/$expected"
  if [[ "$current" -lt "$expected" ]]; then
    export RUNNER_MODULE="embodied_stressbench.runners.run_closed_loop_sanity"
    export GPUS="1 1 1 2 2 2 3 3 3"
    export POLL_SECONDS=120
    export MAX_RESTARTS=120
    bash scripts/watch_h200_matrix_until_complete.sh "$config" "$CALIB_OUTPUT" "$expected"
  fi
  analyze_closed_loop "$CALIB_OUTPUT" "$expected" "closed_loop_calibration_heldout"
  append_report "Closed-loop calibration complete" \
    "- Count: $(count_results "$CALIB_OUTPUT")/$expected" \
    "- Duplicate filenames: $(duplicate_count "$CALIB_OUTPUT")" \
    "- Runner exceptions: $(runner_exception_count "$CALIB_OUTPUT")" \
    "- Analysis directory: \`$ANALYSIS_ROOT/closed_loop_calibration_heldout\`"
}

launch_fallback() {
  local config="configs/experiments/open_vocab_bridge_v2_ycb_clutter_heldout.yaml"
  local expected=18000
  local current
  current="$(count_results "$FALLBACK_OUTPUT")"
  append_report "Fallback Bridge launch" \
    "- Reason: closed-loop sanity gate failed or did not complete cleanly" \
    "- Config: \`$config\`" \
    "- Output: \`$FALLBACK_OUTPUT\`" \
    "- Expected: $expected" \
    "- Existing count: $current/$expected"
  if [[ "$current" -lt "$expected" ]]; then
    export RUNNER_MODULE="embodied_stressbench.runners.run_matrix"
    export GPUS="1 1 1 1 1 2 2 2 2 2 3 3 3 3 3"
    export POLL_SECONDS=120
    export MAX_RESTARTS=120
    bash scripts/watch_h200_matrix_until_complete.sh "$config" "$FALLBACK_OUTPUT" "$expected"
  fi
  "$PYTHON" -m embodied_stressbench.reporting.make_report \
    --input "$FALLBACK_OUTPUT" \
    --output "$FALLBACK_OUTPUT/report.md"
  "$PYTHON" scripts/analyze_open_vocab_bridge_v2.py \
    --input "$FALLBACK_OUTPUT" \
    --output-dir "$ANALYSIS_ROOT/open_vocab_bridge_v2_ycb_clutter_heldout" \
    --expected "$expected"
  append_report "Fallback Bridge complete" \
    "- Count: $(count_results "$FALLBACK_OUTPUT")/$expected" \
    "- Duplicate filenames: $(duplicate_count "$FALLBACK_OUTPUT")" \
    "- Runner exceptions: $(runner_exception_count "$FALLBACK_OUTPUT")" \
    "- Analysis directory: \`$ANALYSIS_ROOT/open_vocab_bridge_v2_ycb_clutter_heldout\`"
}

main() {
  write_header
  write_scirep_docs
  wait_for_bridge
  wait_or_run_closed_loop
  set +e
  gate_output="$(closed_loop_gate 2>&1)"
  gate_status=$?
  set -e
  append_report "Closed-loop sanity gate" \
    "- Gate output: \`$gate_output\`" \
    "- Full count: $(count_results "$CLOSED_FULL_OUTPUT")/$CLOSED_EXPECTED" \
    "- Duplicate filenames: $(duplicate_count "$CLOSED_FULL_OUTPUT")" \
    "- Runner exceptions: $(runner_exception_count "$CLOSED_FULL_OUTPUT")" \
    "- Analysis root: \`$ANALYSIS_ROOT\`"
  if [[ "$gate_status" -eq 0 ]]; then
    launch_calibration "$gate_output"
  else
    launch_fallback
  fi
  append_report "Final status" \
    "- Completed at: $(date -Is)" \
    "- Bridge v2 report: \`$BRIDGE_OUTPUT/report.md\`" \
    "- Closed-loop sanity log: \`$CLOSED_LOG\`" \
    "- Overnight analysis root: \`$ANALYSIS_ROOT\`" \
    "- Honest blocker: final paper claims should be added only after inspecting the generated CSVs."
  log "overnight queue complete; report=$REPORT_PATH"
}

main "$@"
