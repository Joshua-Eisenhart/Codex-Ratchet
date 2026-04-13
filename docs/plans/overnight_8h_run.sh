#!/bin/bash
set -uo pipefail

ROOT="/Users/joshuaeisenhart/Desktop/Codex Ratchet"
PY="/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
HERMES_ENV="/Users/joshuaeisenhart/.hermes/.env"
LOG_DIR="$ROOT/system_v4/probes/a2_state/sim_results/overnight_logs"
mkdir -p "$LOG_DIR"
STAMP=$(date +%Y%m%d_%H%M%S)
LOG="$LOG_DIR/overnight_8h_run_${STAMP}.log"
END_TS=$(( $(date +%s) + 8*60*60 ))

RUN_DURATION="8h"
PRIMARY_LANE="geometry spine"
MAINTENANCE_LANE="truth/maintenance closure"
CURRENT_TASK="boot"
HEALTH_STATE="healthy"
LAST_SUCCESS="none yet"
CHANGED_ITEMS="none yet"
NEXT_STEP="launch G1 geometry wave"
CLOSURE_STATE="truth/maintenance planned"
WORKER_STATE="runner booting"
TELEGRAM_MIN_INTERVAL=300
TELEGRAM_RATE_STATE="$LOG_DIR/overnight_8h_run_${STAMP}.telegram_ts"
LIVE_QUEUE_CONTROLLER="$ROOT/system_v4/probes/live_queue_controller.py"
LIVE_QUEUE_STATUS_FILE="/tmp/codex_live_queue_controller.status"
RUN_LOCK="/tmp/overnight_8h_run.lock"
RUN_HEADER="$LOG_DIR/overnight_8h_run_${STAMP}.run_header.json"
SUCCESS_EVAL="$LOG_DIR/overnight_8h_run_${STAMP}.success_eval.json"
REPORT_STATE="$LOG_DIR/overnight_8h_run_${STAMP}.report_state.json"
REPORT_QUEUE="$LOG_DIR/overnight_8h_run_${STAMP}.report_queue.tsv"
REPORTER_PID_FILE="$LOG_DIR/overnight_8h_run_${STAMP}.reporter.pid"
RESULTS_DIR="$ROOT/system_v4/probes/a2_state/sim_results"
TRUTH_AUDIT_DOC="$ROOT/system_v5/new docs/plans/sim_truth_audit.md"
START_EPOCH=$(date +%s)
REPORTER_PID=""

printf '0\n' > "$TELEGRAM_RATE_STATE"
: > "$REPORT_QUEUE"

exec > >(tee -a "$LOG") 2>&1

format_changed_items() {
  local raw="$1"
  if [ -z "$raw" ]; then
    printf 'none yet'
  else
    printf '%s' "$raw"
  fi
}

count_canonical_by_process() {
  TARGET_DOC="$TRUTH_AUDIT_DOC" "$PY" - <<'PY'
import os
from pathlib import Path

path = Path(os.environ["TARGET_DOC"])
text = path.read_text(encoding="utf-8") if path.exists() else ""
print(text.count("canonical by process"))
PY
}

INITIAL_CANONICAL_BY_PROCESS=$(count_canonical_by_process)

update_report_state() {
  REPORT_STATE_PATH="$REPORT_STATE" \
  REPORT_DURATION="$RUN_DURATION" \
  REPORT_PRIMARY_LANE="$PRIMARY_LANE" \
  REPORT_MAINTENANCE_LANE="$MAINTENANCE_LANE" \
  REPORT_CURRENT_TASK="$CURRENT_TASK" \
  REPORT_HEALTH="$HEALTH_STATE" \
  REPORT_LAST_SUCCESS="$LAST_SUCCESS" \
  REPORT_CHANGED_ITEMS="$CHANGED_ITEMS" \
  REPORT_NEXT_STEP="$NEXT_STEP" \
  REPORT_CLOSURE_STATE="$CLOSURE_STATE" \
  REPORT_WORKER_STATE="$WORKER_STATE" \
  REPORT_LOG_PATH="$LOG" \
  "$PY" - <<'PY'
import json
import os
from pathlib import Path

changed_raw = os.environ.get("REPORT_CHANGED_ITEMS", "").strip()
changed_items = [item.strip() for item in changed_raw.split("||") if item.strip()]
state = {
    "duration": os.environ.get("REPORT_DURATION", ""),
    "primary_lane": os.environ.get("REPORT_PRIMARY_LANE", ""),
    "maintenance_lane": os.environ.get("REPORT_MAINTENANCE_LANE", ""),
    "current_task": os.environ.get("REPORT_CURRENT_TASK", ""),
    "health": os.environ.get("REPORT_HEALTH", ""),
    "last_success": os.environ.get("REPORT_LAST_SUCCESS", ""),
    "changed_items": changed_items,
    "next_step": os.environ.get("REPORT_NEXT_STEP", ""),
    "closure_state": os.environ.get("REPORT_CLOSURE_STATE", ""),
    "worker_state": os.environ.get("REPORT_WORKER_STATE", ""),
    "log_path": os.environ.get("REPORT_LOG_PATH", ""),
}
Path(os.environ["REPORT_STATE_PATH"]).write_text(json.dumps(state, indent=2), encoding="utf-8")
PY
}

queue_report_event() {
  local phase="$1"
  local summary="$2"
  local safe_summary
  safe_summary=$(printf '%s' "$summary" | tr '\t\n' '  ')
  update_report_state
  printf '%s\t%s\n' "$phase" "$safe_summary" >> "$REPORT_QUEUE"
}

write_run_header() {
  RUN_HEADER_PATH="$RUN_HEADER" \
  START_EPOCH_VALUE="$START_EPOCH" \
  LOG_PATH_VALUE="$LOG" \
  RESULTS_DIR_VALUE="$RESULTS_DIR" \
  TRUTH_AUDIT_DOC_VALUE="$TRUTH_AUDIT_DOC" \
  INITIAL_CANONICAL_VALUE="$INITIAL_CANONICAL_BY_PROCESS" \
  "$PY" - <<'PY'
import json
import os
import time
from pathlib import Path

header = {
    "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(os.environ["START_EPOCH_VALUE"]))),
    "start_epoch": int(os.environ["START_EPOCH_VALUE"]),
    "log_path": os.environ["LOG_PATH_VALUE"],
    "results_dir": os.environ["RESULTS_DIR_VALUE"],
    "truth_audit_doc": os.environ["TRUTH_AUDIT_DOC_VALUE"],
    "criteria": {
        "live_queue_batches_min": 3,
        "audits_green_final": True,
        "new_result_jsons_min": 10,
        "canonical_by_process_count_delta": 0,
    },
    "baselines": {
        "canonical_by_process_count": int(os.environ["INITIAL_CANONICAL_VALUE"]),
    },
}
Path(os.environ["RUN_HEADER_PATH"]).write_text(json.dumps(header, indent=2), encoding="utf-8")
PY
}

cleanup_other_runner_processes() {
  local pid
  for pid in $(pgrep -f 'overnight_8h_run.sh' || true); do
    if [ "$pid" != "$$" ] && [ "$pid" != "$PPID" ]; then
      kill "$pid" 2>/dev/null || true
    fi
  done
  for pid in $(pgrep -f 'live_queue_controller.py' || true); do
    kill "$pid" 2>/dev/null || true
  done
}

acquire_run_lock() {
  cleanup_other_runner_processes
  sleep 1
  local pid
  for pid in $(pgrep -f 'overnight_8h_run.sh' || true); do
    if [ "$pid" != "$$" ] && [ "$pid" != "$PPID" ]; then
      echo "LOCK FAILURE: live overnight_8h_run.sh pid remains: $pid"
      return 1
    fi
  done
  if [ -f "$RUN_LOCK" ]; then
    local existing_pid
    existing_pid=$(tr -d '[:space:]' < "$RUN_LOCK")
    if [ -n "$existing_pid" ] && kill -0 "$existing_pid" 2>/dev/null; then
      echo "LOCK FAILURE: run lock already held by pid=$existing_pid"
      return 1
    fi
    rm -f "$RUN_LOCK"
  fi
  printf '%s\n' "$$" > "$RUN_LOCK"
}

release_run_lock() {
  local existing_pid=""
  if [ -f "$RUN_LOCK" ]; then
    existing_pid=$(tr -d '[:space:]' < "$RUN_LOCK")
  fi
  if [ -z "$existing_pid" ] || [ "$existing_pid" = "$$" ]; then
    rm -f "$RUN_LOCK"
  fi
}

load_hermes_telegram_env() {
  if [ ! -f "$HERMES_ENV" ]; then
    return 0
  fi
  if [ -z "${TELEGRAM_BOT_TOKEN:-}" ]; then
    TELEGRAM_BOT_TOKEN=$(grep '^TELEGRAM_BOT_TOKEN=' "$HERMES_ENV" | head -n 1 | cut -d= -f2-)
    export TELEGRAM_BOT_TOKEN
  fi
  if [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
    TELEGRAM_CHAT_ID=$(grep '^TELEGRAM_CHAT_ID=' "$HERMES_ENV" | head -n 1 | cut -d= -f2-)
    export TELEGRAM_CHAT_ID
  fi
  if [ -z "${TELEGRAM_HOME_CHANNEL:-}" ]; then
    TELEGRAM_HOME_CHANNEL=$(grep '^TELEGRAM_HOME_CHANNEL=' "$HERMES_ENV" | head -n 1 | cut -d= -f2-)
    export TELEGRAM_HOME_CHANNEL
  fi
  if [ -z "${TELEGRAM_HOME_CHANNEL_NAME:-}" ]; then
    TELEGRAM_HOME_CHANNEL_NAME=$(grep '^TELEGRAM_HOME_CHANNEL_NAME=' "$HERMES_ENV" | head -n 1 | cut -d= -f2-)
    export TELEGRAM_HOME_CHANNEL_NAME
  fi
}

result_name_from_script() {
  local script="$1"
  local base
  base=$(basename "$script")
  base="${base%.py}"
  if [[ "$base" == sim_* ]]; then
    base="${base#sim_}"
  fi
  printf '%s_results.json' "$base"
}

send_telegram_status() {
  local phase="$1"
  local summary="$2"
  load_hermes_telegram_env
  REPORT_PHASE="$phase" \
  REPORT_SUMMARY="$summary" \
  REPORT_STATE_PATH="$REPORT_STATE" \
  REPORT_ROOT="$ROOT" \
  "$PY" - <<'PY' || true
import json
import os
import sys
from pathlib import Path

root = os.environ["REPORT_ROOT"]
sys.path.insert(0, root)
import telegram_bot as tb  # noqa: E402

state_path = Path(os.environ["REPORT_STATE_PATH"])
state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
message = tb.format_run_status_report(
    phase=os.environ.get("REPORT_PHASE", "status"),
    summary=os.environ.get("REPORT_SUMMARY", "status update"),
    duration_bound=state.get("duration") or None,
    primary_lane=state.get("primary_lane") or None,
    maintenance_lane=state.get("maintenance_lane") or None,
    current_task=state.get("current_task") or None,
    health=state.get("health") or None,
    last_success=state.get("last_success") or None,
    changed_items=state.get("changed_items") or None,
    next_step=state.get("next_step") or None,
    closure_state=state.get("closure_state") or None,
    worker_state=state.get("worker_state") or None,
    log_path=state.get("log_path") or None,
)
result = tb.send_message(message)
print(f"TELEGRAM REPORT phase={os.environ.get('REPORT_PHASE')} ok={result.get('ok')} sent={result.get('sent_count')} attempted={result.get('attempted_count')}")
PY
}

periodic_report_summary() {
  if [ -f "$LIVE_QUEUE_STATUS_FILE" ]; then
    printf 'live queue controller active: %s' "$(read_live_queue_status)"
  else
    printf 'overnight runner status checkpoint'
  fi
}

process_report_queue() {
  if [ ! -s "$REPORT_QUEUE" ]; then
    return 0
  fi
  local queue_batch="${REPORT_QUEUE}.processing"
  mv "$REPORT_QUEUE" "$queue_batch" 2>/dev/null || return 0
  : > "$REPORT_QUEUE"
  local phase
  local summary
  local exit_requested=0
  while IFS=$'\t' read -r phase summary; do
    [ -z "$phase" ] && continue
    if [ "$phase" = "__REPORTER_EXIT__" ]; then
      exit_requested=1
      continue
    fi
    send_telegram_status "$phase" "$summary"
  done < "$queue_batch"
  rm -f "$queue_batch"
  if [ $exit_requested -eq 1 ]; then
    return 111
  fi
  return 0
}

reporter_loop() {
  local last_periodic="$START_EPOCH"
  while true; do
    process_report_queue
    local queue_rc=$?
    if [ $queue_rc -eq 111 ]; then
      break
    fi
    local now
    now=$(date +%s)
    if [ $(( now - last_periodic )) -ge $TELEGRAM_MIN_INTERVAL ]; then
      send_telegram_status "heartbeat" "$(periodic_report_summary)"
      last_periodic=$now
    fi
    sleep 5
  done
}

start_reporter() {
  reporter_loop &
  REPORTER_PID=$!
  printf '%s\n' "$REPORTER_PID" > "$REPORTER_PID_FILE"
}

stop_reporter() {
  if [ -n "$REPORTER_PID" ] && kill -0 "$REPORTER_PID" 2>/dev/null; then
    queue_report_event "__REPORTER_EXIT__" "shutdown"
    wait "$REPORTER_PID" || true
  fi
  rm -f "$REPORTER_PID_FILE"
}

cleanup_exit() {
  stop_reporter
  release_run_lock
}

trap cleanup_exit EXIT

heartbeat() {
  local message="$1"
  local force="${2:-0}"
  echo "HEARTBEAT $(date -Iseconds) | $message"
  update_report_state
  if [ "$force" = "1" ]; then
    queue_report_event "heartbeat" "$message"
  fi
}

run_task() {
  local label="$1"
  local script="$2"
  local result_json
  result_json=$(result_name_from_script "$script")

  CURRENT_TASK="$label"
  NEXT_STEP="run $label via $script"
  WORKER_STATE="main runner active"
  heartbeat "starting $label"

  MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba "$PY" "$ROOT/system_v4/probes/cleanup_first_guard.py" --context sim
  local guard_code=$?
  if [ $guard_code -ne 0 ]; then
    HEALTH_STATE="blocked"
    CLOSURE_STATE="cleanup guard blocked new sim execution"
    CHANGED_ITEMS="none yet"
    WORKER_STATE="main runner blocked"
    heartbeat "blocked $label because cleanup guard failed (exit=$guard_code)" 1
    return $guard_code
  fi

  MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba "$PY" "$ROOT/$script"
  local code=$?
  CHANGED_ITEMS="${result_json}"
  if [ $code -eq 0 ]; then
    LAST_SUCCESS="$script"
    HEALTH_STATE="healthy"
    CLOSURE_STATE="packet complete; audits next"
    WORKER_STATE="main runner active"
    NEXT_STEP="audit packet outputs"
    heartbeat "completed $label cleanly"
  else
    HEALTH_STATE="degraded"
    CLOSURE_STATE="packet failed before audit closure"
    WORKER_STATE="main runner active"
    NEXT_STEP="audit failure and decide bounded next move"
    heartbeat "failed $label (exit=$code)"
  fi
  return $code
}

run_wave_parallel() {
  local wave="$1"
  shift
  CURRENT_TASK="wave $wave"
  NEXT_STEP="run queued packets for $wave"
  WORKER_STATE="parallel packet workers running"
  heartbeat "wave $wave started"

  local pids=()
  local labels=()
  while [ "$#" -gt 0 ]; do
    local label="$1"; shift
    local script="$1"; shift
    (
      run_task "$label" "$script"
    ) &
    pids+=("$!")
    labels+=("$label")
  done
  local any_fail=0
  for i in "${!pids[@]}"; do
    if ! wait "${pids[$i]}"; then
      any_fail=1
      HEALTH_STATE="degraded"
      CLOSURE_STATE="one or more packet workers failed"
      NEXT_STEP="finish waits then audit the wave"
      heartbeat "wave $wave worker ${labels[$i]} failed"
    fi
  done
  if [ $any_fail -eq 0 ]; then
    HEALTH_STATE="healthy"
    CLOSURE_STATE="wave packets complete; audits next"
    NEXT_STEP="run truth/controller audits for $wave"
    heartbeat "wave $wave completed cleanly"
  fi
  return $any_fail
}

audits() {
  CURRENT_TASK="audits"
  NEXT_STEP="decide next bounded wave"
  WORKER_STATE="audit pass running"
  heartbeat "running truth/controller audits"
  "$PY" "$ROOT/system_v4/probes/probe_truth_audit.py"
  local a=$?
  "$PY" "$ROOT/system_v4/probes/controller_alignment_audit.py"
  local b=$?
  CHANGED_ITEMS="probe_truth_audit_results.json||controller_alignment_audit_results.json||live_anchor_spine.json"
  if [ $a -eq 0 ] && [ $b -eq 0 ]; then
    HEALTH_STATE="healthy"
    CLOSURE_STATE="truth/maintenance on track"
    LAST_SUCCESS="probe_truth_audit.py + controller_alignment_audit.py"
    WORKER_STATE="audits complete"
    heartbeat "audits passed"
  else
    HEALTH_STATE="degraded"
    CLOSURE_STATE="audit blocker detected"
    WORKER_STATE="audits complete with blocker"
    heartbeat "audits returned truth=$a controller=$b" 1
  fi
  return $(( a || b ))
}

sleep_heartbeat_loop() {
  local minutes="$1"
  local start=$(date +%s)
  local dur=$(( minutes*60 ))
  while [ $(( $(date +%s) - start )) -lt $dur ] && [ $(date +%s) -lt $END_TS ]; do
    CURRENT_TASK="idle maintenance window"
    NEXT_STEP="next checkpoint heartbeat"
    WORKER_STATE="overnight runner waiting between waves"
    heartbeat "idle maintenance window active"
    sleep 300
  done
}

read_live_queue_status() {
  if [ -f "$LIVE_QUEUE_STATUS_FILE" ]; then
    tr '\n' ' ' < "$LIVE_QUEUE_STATUS_FILE" | cut -c1-200
  else
    printf 'status unavailable'
  fi
}

run_live_queue_for_remaining_budget() {
  if [ ! -f "$LIVE_QUEUE_CONTROLLER" ]; then
    HEALTH_STATE="blocked"
    CLOSURE_STATE="live queue controller missing"
    WORKER_STATE="main runner blocked"
    NEXT_STEP="restore live queue controller before relaunch"
    heartbeat "blocked because live queue controller is missing" 1
    return 1
  fi

  local remaining_seconds=$(( END_TS - $(date +%s) ))
  local remaining_minutes=$(( remaining_seconds / 60 ))
  if [ $remaining_minutes -le 0 ]; then
    return 0
  fi

  CURRENT_TASK="live queue controller"
  NEXT_STEP="continuous bounded batch queue for remaining overnight budget"
  WORKER_STATE="live queue controller active"
  CLOSURE_STATE="continuous queue phase active"
  heartbeat "handing remaining budget to live queue controller (${remaining_minutes}m)"

  "$PY" "$LIVE_QUEUE_CONTROLLER" --minutes "$remaining_minutes" &
  local controller_pid=$!
  local controller_rc=0

  while kill -0 "$controller_pid" 2>/dev/null; do
    sleep "$TELEGRAM_MIN_INTERVAL"
    if ! kill -0 "$controller_pid" 2>/dev/null; then
      break
    fi
    CURRENT_TASK="live queue controller"
    NEXT_STEP="continue bounded batch queue"
    WORKER_STATE="live queue controller active"
    CHANGED_ITEMS="live_queue_controller.status"
    heartbeat "live queue controller active: $(read_live_queue_status)"
  done

  wait "$controller_pid"
  controller_rc=$?
  CHANGED_ITEMS="live_queue_controller.status||probe_truth_audit_results.json||controller_alignment_audit_results.json"
  if [ $controller_rc -eq 0 ]; then
    HEALTH_STATE="healthy"
    LAST_SUCCESS="live_queue_controller.py"
    CLOSURE_STATE="continuous queue completed inside overnight budget"
    WORKER_STATE="live queue controller complete"
    NEXT_STEP="final overnight closeout"
    heartbeat "live queue controller completed cleanly"
  else
    HEALTH_STATE="degraded"
    CLOSURE_STATE="continuous queue controller exited nonzero"
    WORKER_STATE="live queue controller failed"
    NEXT_STEP="close out with controller failure"
    heartbeat "live queue controller failed (exit=$controller_rc)" 1
  fi
  return $controller_rc
}

evaluate_success_criteria() {
  RUN_HEADER_PATH="$RUN_HEADER" \
  SUCCESS_EVAL_PATH="$SUCCESS_EVAL" \
  RESULTS_DIR_VALUE="$RESULTS_DIR" \
  "$PY" - <<'PY'
import json
import os
import re
from pathlib import Path

header = json.loads(Path(os.environ["RUN_HEADER_PATH"]).read_text(encoding="utf-8"))
results_dir = Path(os.environ["RESULTS_DIR_VALUE"])
log_text = Path(header["log_path"]).read_text(encoding="utf-8", errors="replace")
truth_path = results_dir / "probe_truth_audit_results.json"
controller_path = results_dir / "controller_alignment_audit_results.json"
truth_doc = Path(header["truth_audit_doc"])
truth_json = json.loads(truth_path.read_text(encoding="utf-8")) if truth_path.exists() else {}
controller_json = json.loads(controller_path.read_text(encoding="utf-8")) if controller_path.exists() else {}
truth_doc_text = truth_doc.read_text(encoding="utf-8") if truth_doc.exists() else ""

live_queue_batches = re.findall(r"RUN-PLAN .* selected=(batch\d+)", log_text)
new_result_jsons = [
    path.name
    for path in results_dir.glob("*_results.json")
    if path.stat().st_mtime >= header["start_epoch"]
]
final_canonical_count = truth_doc_text.count("canonical by process")
canonical_delta = final_canonical_count - header["baselines"]["canonical_by_process_count"]
audits_green_final = bool(truth_json.get("summary", {}).get("ok")) and bool(controller_json.get("probe_truth_audit", {}).get("ok")) and bool(controller_json.get("controller_contract_current"))

criteria = header["criteria"]
checks = {
    "live_queue_batches_min": {
        "expected": criteria["live_queue_batches_min"],
        "actual": len(live_queue_batches),
        "pass": len(live_queue_batches) >= criteria["live_queue_batches_min"],
        "detail": live_queue_batches,
    },
    "audits_green_final": {
        "expected": criteria["audits_green_final"],
        "actual": audits_green_final,
        "pass": audits_green_final is criteria["audits_green_final"],
    },
    "new_result_jsons_min": {
        "expected": criteria["new_result_jsons_min"],
        "actual": len(new_result_jsons),
        "pass": len(new_result_jsons) >= criteria["new_result_jsons_min"],
        "detail": new_result_jsons,
    },
    "canonical_by_process_count_delta": {
        "expected": criteria["canonical_by_process_count_delta"],
        "actual": canonical_delta,
        "pass": canonical_delta >= criteria["canonical_by_process_count_delta"],
        "detail": {
            "initial": header["baselines"]["canonical_by_process_count"],
            "final": final_canonical_count,
        },
    },
}
failed = [name for name, payload in checks.items() if not payload["pass"]]
report = {
    "status": "success" if not failed else "failure",
    "failed_criteria": failed,
    "checks": checks,
}
Path(os.environ["SUCCESS_EVAL_PATH"]).write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
raise SystemExit(0 if not failed else 1)
PY
}

failed_success_criteria() {
  SUCCESS_EVAL_PATH="$SUCCESS_EVAL" "$PY" - <<'PY'
import json
import os
from pathlib import Path

path = Path(os.environ["SUCCESS_EVAL_PATH"])
if not path.exists():
    print("success_eval_missing")
else:
    report = json.loads(path.read_text(encoding="utf-8"))
    failed = report.get("failed_criteria", [])
    print(", ".join(failed) if failed else "none")
PY
}

initialize_run_contract() {
  acquire_run_lock || return 1
  write_run_header
  update_report_state
  start_reporter
}

CURRENT_TASK="launch"
NEXT_STEP="start G1 geometry wave"
WORKER_STATE="main runner active"
if ! initialize_run_contract; then
  exit 1
fi
heartbeat "overnight 8h run launched" 1

# Wave 1: already-known missing/central geometry packets via closest existing probes
run_wave_parallel "G1" \
  "hopf-map" "system_v4/probes/sim_density_hopf_geometry.py" \
  "fiber-equivalence" "system_v4/probes/sim_hopf_torus_lego.py" \
  "chiral-bookkeeping" "system_v4/probes/sim_weyl_nested_shell.py" \
  "weyl-pair" "system_v4/probes/sim_weyl_spinor_hopf.py"
audits

# Wave 2: operator and connection packet
run_wave_parallel "G2" \
  "pauli-basis" "system_v4/probes/sim_lego_pauli_algebra.py" \
  "hopf-connection" "system_v4/probes/sim_torch_hopf_connection.py" \
  "channel-order" "system_v4/probes/sim_torch_channel_composition.py" \
  "partial-trace" "system_v4/probes/sim_partial_trace_audit.py"
audits

# Wave 3: clean math-named geometry packet
run_wave_parallel "G3" \
  "sphere-geometry" "system_v4/probes/sim_sphere_geometry.py" \
  "nested-torus" "system_v4/probes/sim_nested_torus_geometry.py" \
  "fubini-study" "system_v4/probes/sim_fubini_study_geometry.py" \
  "bures-geometry" "system_v4/probes/sim_bures_geometry.py"
audits

# Wave 4: graph/topology geometry packet
run_wave_parallel "G4" \
  "graph-shell" "system_v4/probes/sim_graph_shell_geometry.py" \
  "cell-complex" "system_v4/probes/sim_cell_complex_geometry.py" \
  "persistence" "system_v4/probes/sim_persistence_geometry.py" \
  "state-class-binding" "system_v4/probes/sim_toponetx_state_class_binding.py"
audits

# Wave 5: local witness/graph side packet
run_wave_parallel "G5" \
  "pyg-werner" "system_v4/probes/sim_pyg_dynamic_edge_werner.py" \
  "fiber-base-transport" "system_v4/probes/sim_fiber_base_transport_test.py" \
  "xgi-family" "system_v4/probes/sim_xgi_family_hypergraph.py" \
  "xgi-shell" "system_v4/probes/sim_xgi_shell_hypergraph.py"
audits

# Wave 6: classical/QIT-aligned lego lane (separate)
PRIMARY_LANE="classical/QIT side lane"
NEXT_STEP="start C1 side-lane wave"
run_wave_parallel "C1" \
  "carnot-core" "system_v4/probes/sim_qit_carnot_two_bath_cycle.py" \
  "carnot-finite-time" "system_v4/probes/sim_qit_carnot_finite_time_companion.py" \
  "carnot-hold-policy" "system_v4/probes/sim_qit_carnot_hold_policy_companion.py" \
  "szilard-core" "system_v4/probes/sim_qit_szilard_landauer_cycle.py"
audits

# Wave 7: more classical/QIT-aligned lego lane
run_wave_parallel "C2" \
  "szilard-record" "system_v4/probes/sim_qit_szilard_record_companion.py" \
  "szilard-substep" "system_v4/probes/sim_qit_szilard_substep_companion.py" \
  "szilard-bidirectional" "system_v4/probes/sim_qit_szilard_bidirectional_protocol.py" \
  "engine-lab-matrix" "system_v4/probes/sim_engine_lab_matrix.py"
audits

# Hand the remaining budget to the live queue controller so the run keeps executing bounded work.
PRIMARY_LANE="geometry spine"
run_live_queue_for_remaining_budget
LIVE_QUEUE_EXIT=$?

CURRENT_TASK="closeout"
NEXT_STEP="none"
CHANGED_ITEMS="probe_truth_audit_results.json||controller_alignment_audit_results.json||$(basename "$SUCCESS_EVAL")"
if [ $LIVE_QUEUE_EXIT -ne 0 ]; then
  HEALTH_STATE="degraded"
  CLOSURE_STATE="live queue controller exited nonzero before closeout"
  WORKER_STATE="main runner complete with failure"
fi

if evaluate_success_criteria && [ $LIVE_QUEUE_EXIT -eq 0 ]; then
  HEALTH_STATE="healthy"
  LAST_SUCCESS="overnight success contract"
  CLOSURE_STATE="success criteria satisfied"
  WORKER_STATE="main runner complete"
  update_report_state
  queue_report_event "closeout" "overnight 8h run finished"
  queue_report_event "__REPORTER_EXIT__" "shutdown"
  if [ -n "$REPORTER_PID" ]; then
    wait "$REPORTER_PID" || true
    REPORTER_PID=""
  fi
  echo "FINAL LOG PATH: $LOG"
  exit 0
else
  failed_criteria=$(failed_success_criteria)
  if [ $LIVE_QUEUE_EXIT -ne 0 ]; then
    if [ "$failed_criteria" = "none" ]; then
      failed_criteria="live_queue_controller_exit"
    else
      failed_criteria="$failed_criteria, live_queue_controller_exit"
    fi
  fi
  HEALTH_STATE="degraded"
  CLOSURE_STATE="success criteria failed: $failed_criteria"
  NEXT_STEP="inspect $(basename "$SUCCESS_EVAL")"
  WORKER_STATE="main runner complete with failure"
  update_report_state
  queue_report_event "FAILURE" "overnight success criteria failed: $failed_criteria"
  queue_report_event "__REPORTER_EXIT__" "shutdown"
  if [ -n "$REPORTER_PID" ]; then
    wait "$REPORTER_PID" || true
    REPORTER_PID=""
  fi
  echo "FINAL LOG PATH: $LOG"
  echo "SUCCESS EVAL: $SUCCESS_EVAL"
  exit 1
fi
