#!/bin/bash
# sim_runner_v2_stub.sh — DRAFT / REFERENCE ONLY (not live, not executable)
#
# Replaces: system_v5/ops/sim_runner.sh
# Spec: system_v5/ops/SIM_RUNNER.md  (v1 live runner; update before promotion)
# Legacy harness anchors from the source draft; update to current wizard/wiki
# paths before promoting this stub into live runner code.
# Harness anchors:
#   ~/wiki/harness/28_bounded_work.md  lines 115-122  (admission-pool-not-pipeline)
#   ~/wiki/harness/31_admission_surface.md  II.2      (tool-manifest predicate)
#   feedback_tool_stage_admission_and_skip_ahead_contract.md  (this contract)
#
# Diff from v1 (sim_runner.sh):
#   1. QUEUES array reordered; queue_default.txt is REMOVED.
#   2. Adds queue_lego_backlog.txt + queue_offlane.txt.
#   3. Adds admission-gate preflight per row:
#      - T4-typed rows require an 8-field BOUND block.
#      - Every row requires: probe file exists, classification field present,
#        TOOL_MANIFEST with non-empty reasons, SIM_TEMPLATE lineage.
#      - Missing any of the above → mark INELIGIBLE, do not mark FAIL.
#      - INELIGIBLE ≠ FAIL so consecutive-failure circuit-breaker does not
#        trip on structural gating.
#   4. queue_offlane.txt is never auto-drained — surfaced in stats only.
#   5. Loopback writeback: on DONE of a T4-typed row, assert the ledger row
#      named in loopback_target was written in the last N seconds; if not,
#      mark LOOPBACK_MISSING and re-route to queue_disposal with a reason.
#   6. Drift alarm: if rate-of-DONE exceeds 10/hour without a paired ledger
#      writeback per DONE, pause and surface "admission drift detected."
#
# This stub shows the gating logic. Run loop + thermal handling + symlinks
# are elided (carry over from v1 verbatim where marked [[CARRY]]).

set -u

REPO="/Users/joshuaeisenhart/Desktop/Codex Ratchet"
OPS="$REPO/system_v5/ops"
LEDGER="$REPO/system_v5/docs/plans/plans/TOOL_CAPABILITY_AND_INTEGRATION_LEDGER.md"

# ---- NEW: queue ordering, no queue_default.txt ---------------------------
QUEUES=(
  "$OPS/queue_tier_a.txt"          # tool-stage; T4-typed; bound block required
  "$OPS/queue_tier_b.txt"          # shell-local legos
  "$OPS/queue_tier_d.txt"          # tier D work
  "$OPS/queue_lego_backlog.txt"    # bucket-4 lego-local work; no tool-integration claim
)
OFFLANE_QUEUE="$OPS/queue_offlane.txt"    # never auto-drain
DISPOSAL_QUEUE="$OPS/queue_disposal.txt"  # archive surface; never-run

# ---- NEW: 8-field BOUND block parser ------------------------------------
# A row in queue_tier_a may be preceded by a comment block of form:
#   # BOUND: {
#   #   "tool_target": "...",
#   #   "integration_question": "...",
#   #   "anchor_lego": "...",
#   #   "why_this_lego": "...",
#   #   "loopback_target": "...",
#   #   "expected_outcome_classification": "classical_baseline|canonical",
#   #   "bound_exit_condition": "...",
#   #   "out_of_scope": ["...", "..."]
#   # }
# All 8 fields required. Missing any → INELIGIBLE.
parse_bound_block() {
  local queue_file="$1" row="$2"
  # Extract contiguous "# BOUND:" block immediately preceding the row.
  # Implementation note: awk walks backward from the row match; emits JSON
  # to stdout or empty if no block. (Shown here as stub; real impl lives
  # in a sidecar python script probes/parse_bound_block.py to avoid awk
  # fragility on nested JSON.)
  :  # stub
}

validate_bound_block() {
  local json="$1"
  local required='tool_target integration_question anchor_lego why_this_lego loopback_target expected_outcome_classification bound_exit_condition out_of_scope'
  for field in $required; do
    echo "$json" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if '$field' in d and d['$field'] else 1)" \
      || { echo "MISSING:$field"; return 1; }
  done
  return 0
}

# ---- NEW: structural canonicality preflight (every row, every queue) ----
probe_is_structurally_admissible() {
  local probe="$1"
  [ -f "$probe" ] || { echo "probe_missing"; return 1; }
  grep -q 'classification[[:space:]]*=' "$probe" || { echo "no_classification_field"; return 1; }
  grep -q 'TOOL_MANIFEST' "$probe" || { echo "no_tool_manifest"; return 1; }
  grep -q 'SIM_TEMPLATE' "$probe" || { echo "no_sim_template_lineage"; return 1; }
  # Non-empty reason check deferred to probes/check_tool_manifest_reasons.py
  # (this is the II.2 z3 predicate — see drafts/z3_sim_tool_manifest_completeness.py)
  python3 "$OPS/check_tool_manifest_reasons.py" "$probe" || { echo "empty_tool_reason"; return 1; }
  return 0
}

# ---- NEW: row type classification (T1/T2/T3/T4) -------------------------
# Determined by queue file + probe filename pattern + TOOL_INTEGRATION_DEPTH.
# T4 is the only type that requires a BOUND block.
row_type() {
  local queue_file="$1" basename="$2" probe="$3"
  case "${queue_file##*/}" in
    queue_tier_a.txt)
      if grep -Eq 'TOOL_INTEGRATION_DEPTH.*load_bearing' "$probe"; then
        echo "T4"
      else
        case "$basename" in
          sim_capability_*) echo "T2" ;;
          sim_integration_*) echo "T3" ;;
          *) echo "T1" ;;
        esac
      fi
      ;;
    queue_lego_backlog.txt) echo "T2_or_lego_local" ;;
    *) echo "unclassified" ;;
  esac
}

# ---- NEW: admission gate (replaces default_queue_forbidden) -------------
admit_row() {
  local queue_file="$1" basename="$2" probe="$3"

  # Structural preflight — applies to every row everywhere
  local struct_err
  if ! struct_err=$(probe_is_structurally_admissible "$probe"); then
    echo "INELIGIBLE:$struct_err"
    return 1
  fi

  local rtype
  rtype=$(row_type "$queue_file" "$basename" "$probe")

  # T4 rows need a valid 8-field BOUND block
  if [ "$rtype" = "T4" ]; then
    local json
    json=$(parse_bound_block "$queue_file" "$basename")
    if [ -z "$json" ]; then
      echo "INELIGIBLE:t4_missing_bound_block"
      return 1
    fi
    local bfail
    if ! bfail=$(validate_bound_block "$json"); then
      echo "INELIGIBLE:t4_bound_block_$bfail"
      return 1
    fi
  fi

  # lego_backlog refuses load_bearing rows — they belong in tier_a with a bound block
  if [ "${queue_file##*/}" = "queue_lego_backlog.txt" ]; then
    if grep -Eq 'TOOL_INTEGRATION_DEPTH.*load_bearing' "$probe"; then
      echo "INELIGIBLE:load_bearing_row_in_lego_backlog_use_tier_a"
      return 1
    fi
  fi

  echo "ADMITTED:$rtype"
  return 0
}

# ---- NEW: loopback writeback assertion on T4 DONE -----------------------
assert_loopback_writeback() {
  local probe="$1" loopback_target="$2"
  # Expect ledger row named $loopback_target to have been touched since
  # run start. Git diff check or mtime check on LEDGER file suffices.
  local since="$3"  # unix epoch of run start
  [ -f "$LEDGER" ] || return 1
  local mtime
  mtime=$(stat -f %m "$LEDGER" 2>/dev/null || stat -c %Y "$LEDGER")
  [ "$mtime" -ge "$since" ] && grep -q "$loopback_target" "$LEDGER"
}

# ---- NEW: drift alarm ---------------------------------------------------
# If done_rate_per_hour > THRESHOLD and ledger_write_rate_per_hour is
# materially lower, pause and surface. Prevents silent queue drain
# without integration loopback.
DONE_RATE_THRESHOLD=10
check_drift_alarm() {
  local done_count="$1" ledger_touches="$2"
  if [ "$done_count" -ge "$DONE_RATE_THRESHOLD" ] && [ "$ledger_touches" -lt $((done_count / 2)) ]; then
    echo "DRIFT: $done_count DONE in window but only $ledger_touches ledger touches — admission-pool-as-pipeline suspected"
    return 1
  fi
  return 0
}

# ---- [[CARRY]] from v1: thermal, stop-file, mark_line, pick_next, ... ---
# Omitted here for brevity. The only behavioral changes are the
# admission-gate insertion between pick_next and the run call, and the
# loopback assertion after a successful run.

# ---- Main loop sketch ---------------------------------------------------
#
# while :; do
#   check_stop
#   pick=$(pick_next) || { sleep 600; continue; }
#   queue_file="${pick%%|*}"
#   basename="${pick##*|}"
#   probe="system_v4/probes/${basename}.py"
#
#   adm=$(admit_row "$queue_file" "$basename" "$probe")
#   if [[ "$adm" == INELIGIBLE:* ]]; then
#     reason="${adm#INELIGIBLE:}"
#     log "INELIGIBLE $basename ($reason)"
#     mark_line "$queue_file" "$basename" "INELIGIBLE" "$reason"
#     # INELIGIBLE does NOT increment consecutive_failures — structural
#     # gating is expected, not a runtime fault.
#     continue
#   fi
#
#   rtype="${adm#ADMITTED:}"
#   run_start=$(date +%s)
#   # [[CARRY]] execute probe with timeout + nice
#   # [[CARRY]] record dur, OK/FAIL
#
#   if [ "$rtype" = "T4" ] && [ "$run_outcome" = "OK" ]; then
#     loopback=$(parse_bound_block "$queue_file" "$basename" | python3 -c "import sys,json; print(json.load(sys.stdin)['loopback_target'])")
#     if ! assert_loopback_writeback "$probe" "$loopback" "$run_start"; then
#       log "LOOPBACK_MISSING $basename (target=$loopback)"
#       mark_line "$queue_file" "$basename" "LOOPBACK_MISSING" "$dur"
#       # Re-route to queue_disposal with reason
#       echo "# loopback_missing: target=$loopback on $(date +%F) run_start=$run_start" >> "$DISPOSAL_QUEUE"
#       echo "$basename" >> "$DISPOSAL_QUEUE"
#       continue
#     fi
#   fi
#
#   check_drift_alarm "$done_count_window" "$ledger_touches_window"
# done

echo "This is a stub. Not executable."
exit 2
