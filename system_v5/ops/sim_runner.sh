#!/bin/bash
# 24/7 thermal-safe sim runner. Drains tier queues in priority order.
# Spec: system_v5/ops/SIM_RUNNER.md

set -u

REPO="/Users/joshuaeisenhart/Desktop/Codex Ratchet"
OPS="$REPO/system_v5/ops"
STOP="$OPS/.stop_sim_runner"
LOCK_DIR="$OPS/.sim_runner.lock"
STAGE_GATE="$OPS/stage_gate.json"
LOG_DIR="$REPO/overnight_logs"
RESULT_DIR="$REPO/system_v4/probes/a2_state/sim_results"
PYTHON="$(awk -F':=' '/^PYTHON[[:space:]]*:=/ {gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2); print $2; exit}' "$REPO/Makefile")"
[ -n "$PYTHON" ] || PYTHON="$(which python3)"

QUEUES=(
  "$OPS/queue_tier_a.txt"
  "$OPS/queue_tier_b.txt"
  "$OPS/queue_tier_d.txt"
  "$OPS/queue_default.txt"
)

LATE_STAGE_PATTERN='pairwise|couple|coupling|crosscouple|coexistence|triple|bridge|axis|phi0|rho_ab|kernel|emergence|stacking|carnot|szilard|jarzynski|landauer|engine|ladder|bakeoff|cascade|pipeline|integrated|integration|compound|composition|global|companion|overlay|alignment|meta_|deep_quantum|full_|mega_|substrate_|topology_entropy|topology_boundary|topology_compatibility|topology_pauli|carrier_array|cross_layer|crosscheck|geom_layer_|layered_|minimal_surviving_set|g_structure_tower|gtower_chain|tower_chain|layer4_5_6|layer7_12|layer13_19|layer0_1|l4_l6|l6_l7|l5_l6|l0_l1'

# Apple Silicon thermal: CPU_Speed_Limit from `pmset -g therm`.
# 100 = no throttle; drops below when hot.
THERMAL_PAUSE_BELOW=85     # pause if speed limit drops below this
THERMAL_RESUME_ABOVE=95    # resume when speed limit back above this
COOLDOWN_SECS=120
INTER_SIM_SLEEP=5
CONSECUTIVE_FAIL_LIMIT=5
POST_FAIL_PAUSE=1800
PER_SIM_TIMEOUT=300  # kill any single sim after 5 min — protects against hangs
STRICT_RECEIPT_ADMISSION="${STRICT_RECEIPT_ADMISSION:-1}"
STRICT_WIZARD_QUEUE_ADMISSION="${STRICT_WIZARD_QUEUE_ADMISSION:-1}"
ALLOW_HELPER_PROCESSES="${ALLOW_HELPER_PROCESSES:-0}"
ADMISSION_BYPASS_SENTINEL="${ADMISSION_BYPASS_SENTINEL:-$OPS/.allow_admission_bypass_recovery}"
# macOS ships without `timeout`; fall back to portable perl-alarm wrapper.
TIMEOUT_BIN="$(command -v gtimeout || command -v timeout || echo '')"
PERL_BIN="$(command -v perl)"

mkdir -p "$LOG_DIR"
cd "$REPO" || exit 1

# Keep a 'current' symlink to this run's log so Hermes can tail it
THIS_LOG="$LOG_DIR/sim_runner_$(date +%Y%m%d_%H%M%S).log"

log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"; }

release_lock() {
  if [ -d "$LOCK_DIR" ] && [ "$(cat "$LOCK_DIR/pid" 2>/dev/null || true)" = "$$" ]; then
    rm -f "$LOCK_DIR/pid" "$LOCK_DIR/started_at"
    rmdir "$LOCK_DIR" 2>/dev/null || true
  fi
}

acquire_lock() {
  for _ in 1 2; do
    if mkdir "$LOCK_DIR" 2>/dev/null; then
      printf '%s\n' "$$" > "$LOCK_DIR/pid"
      date +%Y-%m-%d_%H:%M:%S > "$LOCK_DIR/started_at"
      trap release_lock EXIT
      trap 'release_lock; exit 130' INT TERM
      return 0
    fi
    local owner
    owner=$(cat "$LOCK_DIR/pid" 2>/dev/null || true)
    if [ -z "$owner" ] || ! kill -0 "$owner" 2>/dev/null; then
      log "Removing stale sim runner lock at $LOCK_DIR (owner=${owner:-unknown})"
      rm -f "$LOCK_DIR/pid" "$LOCK_DIR/started_at"
      rmdir "$LOCK_DIR" 2>/dev/null || true
      continue
    fi
    break
  done
  log "Another sim runner appears active; lock exists at $LOCK_DIR"
  log "Lock owner pid=$(cat "$LOCK_DIR/pid" 2>/dev/null || echo unknown) started_at=$(cat "$LOCK_DIR/started_at" 2>/dev/null || echo unknown)"
  exit 1
}

helper_process_preflight() {
  if [ "$ALLOW_HELPER_PROCESSES" = "1" ]; then
    log "Helper process preflight bypassed by ALLOW_HELPER_PROCESSES=1"
    return 0
  fi
  if ! "$PYTHON" scripts/helper_process_audit.py --strict >/dev/null; then
    log "Helper process preflight failed; stop stale Computer Use helpers before non-browser sim runs."
    log "Set ALLOW_HELPER_PROCESSES=1 only when an active browser/computer-use task intentionally owns them."
    exit 1
  fi
}

admission_bypass_preflight() {
  if [ "$STRICT_RECEIPT_ADMISSION" = "1" ] && [ "$STRICT_WIZARD_QUEUE_ADMISSION" = "1" ]; then
    return 0
  fi
  if [ -f "$ADMISSION_BYPASS_SENTINEL" ]; then
    log "Admission bypass recovery sentinel present: $ADMISSION_BYPASS_SENTINEL"
    return 0
  fi
  log "Admission bypass refused: strict receipt and Wizard queue admission must stay enabled for normal sim runs."
  log "Create $ADMISSION_BYPASS_SENTINEL only for a bounded manual recovery run, then remove it immediately."
  exit 1
}

check_stop() {
  [ -f "$STOP" ] && { log "Stop file present. Exiting."; exit 0; }
}

stage_gate_bool() {
  local key="$1" default="$2"
  [ -f "$STAGE_GATE" ] || { echo "$default"; return 0; }
  "$PYTHON" - "$STAGE_GATE" "$key" "$default" <<'PY' 2>/dev/null || echo "$default"
import json
import sys

path, key, default = sys.argv[1:]
default_bool = default.lower() == "true"
try:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    value = default_bool if key not in data else data.get(key) is True
except Exception:
    value = default_bool
print("true" if bool(value) else "false")
PY
}

tier_d_allowed() {
  [ "$(stage_gate_bool allow_tier_d_launch false)" = "true" ]
}

default_queue_late_stage_allowed() {
  [ "$(stage_gate_bool allow_default_queue_late_stage false)" = "true" ]
}

# Returns CPU_Speed_Limit (1-100). 100 = no throttle.
check_thermal() {
  pmset -g therm 2>/dev/null | awk -F'=' '/CPU_Speed_Limit/ {gsub(/ /,"",$2); print $2; exit}' || echo 100
}

wait_until_cool() {
  while :; do
    check_stop
    local t
    t=$(check_thermal)
    [ -z "$t" ] && t=100
    if [ "$t" -ge "$THERMAL_RESUME_ABOVE" ]; then
      return 0
    fi
    log "Cooldown: cpu_speed_limit=$t (resume at $THERMAL_RESUME_ABOVE), waiting ${COOLDOWN_SECS}s"
    sleep "$COOLDOWN_SECS"
  done
}

pick_next() {
  # Print: "<queue_file>|<basename>" for first runnable line across priority queues
  for q in "${QUEUES[@]}"; do
    [ -f "$q" ] || continue
    if [ "$q" = "$OPS/queue_tier_d.txt" ] && ! tier_d_allowed; then
      continue
    fi
    local line
    line=$(grep -v '^#' "$q" | grep -v '^[[:space:]]*$' | head -1)
    if [ -n "$line" ]; then
      echo "${q}|${line}"
      return 0
    fi
  done
  return 1
}

default_queue_forbidden() {
  local basename="$1"
  echo "$basename" | grep -Eiq "$LATE_STAGE_PATTERN"
}

regen_default_queue() {
  local q="${QUEUES[3]}"
  log "Default queue is fail-closed. Leaving queue_default.txt empty until controller writes allowed stage-gated entries."
  cat > "$q" <<'EOF'
# Default queue — fail-closed placeholder.
# This file is not a generic never-run pile.
# It may only hold controller-approved tool sims or local lego-stage work.
# Stage-heavier tool-integration rows belong in Tier A or explicit review.
# Do not place pairwise/coexistence/bridge/axis/engine-style probes here.
# If the tier queues are empty and no controller-supplied safe default queue exists,
# the runner should stay idle rather than widen scope.
EOF
}

mark_line() {
  local q="$1" basename="$2" status="$3" dur="$4"
  local ts; ts=$(date +%Y-%m-%d_%H:%M:%S)
  local tmp; tmp=$(mktemp)
  awk -v bn="$basename" -v st="$status" -v ts="$ts" -v dur="$dur" '
    !done_flag && $0 == bn { print "# " st " " ts " " bn " (" dur "s)"; done_flag=1; next }
    { print }
  ' "$q" > "$tmp" && mv "$tmp" "$q"
}

receipt_admitted() {
  local basename="$1"
  local run_start="$2"
  if [ "$STRICT_RECEIPT_ADMISSION" != "1" ]; then
    ADMITTED_RESULT="not_required"
    return 0
  fi
  local admitted
  if ! admitted=$("$PYTHON" scripts/find_admitted_result.py \
    --basename "$basename" \
    --probe "system_v4/probes/${basename}.py" \
    --result-dir "$RESULT_DIR" \
    --run-start "$run_start" \
    --path-only); then
    log "ADMISSION FAIL $basename: no strict executable run-boundary result JSON was admitted"
    return 1
  fi
  ADMITTED_RESULT="$admitted"
  return 0
}

wizard_queue_admitted() {
  local basename="$1"
  local probe="$2"
  if [ "$STRICT_WIZARD_QUEUE_ADMISSION" != "1" ]; then
    return 0
  fi
  "$PYTHON" scripts/wizard_sim_admission.py \
    --basename "$basename" \
    --sim-path "$probe" \
    --path-only >/dev/null
}

consecutive_failures=0
sim_count=0
STATS_EVERY=10

queue_stats() {
  for q in "${QUEUES[@]}"; do
    [ -f "$q" ] || continue
    local pending done_count fail_count
    pending=$(grep -cvE '^#|^$' "$q" 2>/dev/null | tr -d '\n')
    done_count=$(grep -cE '^# DONE' "$q" 2>/dev/null | tr -d '\n')
    fail_count=$(grep -cE '^# FAIL' "$q" 2>/dev/null | tr -d '\n')
    printf "  %s: %sp/%sd/%sf\n" "${q##*/}" "${pending:-0}" "${done_count:-0}" "${fail_count:-0}"
  done
}

acquire_lock
ln -sf "$THIS_LOG" "$LOG_DIR/sim_runner_current.log"
helper_process_preflight
admission_bypass_preflight

log "Runner started. Priority: A > B > D(if stage gate permits) > default."
log "Single-runner lock: $LOCK_DIR"
if [ "$STRICT_RECEIPT_ADMISSION" = "1" ]; then
  log "Strict receipt admission is enabled; DONE requires executable run-boundary validation."
else
  log "Strict receipt admission is bypassed by STRICT_RECEIPT_ADMISSION=0; DONE means process exit only."
fi
if [ "$STRICT_WIZARD_QUEUE_ADMISSION" = "1" ]; then
  log "Strict Wizard queue admission is enabled; queued rows require v4.1 admission artifacts before execution."
else
  log "Strict Wizard queue admission is bypassed by STRICT_WIZARD_QUEUE_ADMISSION=0; rows may run without v4.1 queue admission."
fi
log "Initial queue state:"
queue_stats | while read line; do log "$line"; done
if ! tier_d_allowed; then
  log "Stage gate: Tier D launch is blocked by stage_gate.json; queue_tier_d.txt will not drain."
fi

while :; do
  check_stop

  pick=$(pick_next || echo "")
  if [ -z "$pick" ]; then
    regen_default_queue
    if ! pick=$(pick_next); then
      log "All queues empty after fail-closed default queue check. Sleeping 600s."
      sleep 600
      continue
    fi
  fi

  queue_file="${pick%%|*}"
  basename="${pick##*|}"
  probe="system_v4/probes/${basename}.py"

  if [ ! -f "$probe" ]; then
    log "Missing probe: $probe — marking SKIPPED"
    mark_line "$queue_file" "$basename" "SKIPPED" "0"
    continue
  fi

  if ! wizard_queue_admitted "$basename" "$probe"; then
    log "INELIGIBLE (wizard admission): $basename lacks v4.1 queue-ready admission"
    mark_line "$queue_file" "$basename" "INELIGIBLE" "0"
    continue
  fi

  if [ "$queue_file" = "$OPS/queue_default.txt" ] && ! default_queue_late_stage_allowed && default_queue_forbidden "$basename"; then
    log "SKIP (hard stage gate): $basename is late-stage and cannot run from queue_default.txt"
    mark_line "$queue_file" "$basename" "SKIPPED" "0"
    continue
  fi

  t=$(check_thermal)
  [ -z "$t" ] && t=100
  if [ "$t" -lt "$THERMAL_PAUSE_BELOW" ]; then
    log "Thermal throttle detected: cpu_speed_limit=$t (pause<$THERMAL_PAUSE_BELOW). Cooling down."
    wait_until_cool
  fi

  # Skip known hang-prone probes
  # Extended 2026-04-17 after deep log audit found: live_queue_controller (3602s),
  # autoresearch_sim_harness (126s), multi_seed_stability_test (86s),
  # followup_anomaly_investigation (461s), various *_substep_*_sweep (70-171s)
  case "$basename" in
    *benchmark*|*_stress*|*stress_test*|*infinite*|*long_exact*|*80shell*|*prolongation*\
    |*sweep_runner*|*_runner|*_runner_*|classical_sweep_*|autonomous_*|overnight_*\
    |*_sweep|*variant_sweep*|*substep_*_sweep|*substep_*sweep|live_queue_*|autoresearch_*\
    |followup_*|multi_seed_*|cross_*_analyzer|*_normalizer|*_enforce|*_checker\
    |*_legality|thread_sim_*|phase*_first_*|graph_policy_*|smt_graph_*|egglog_*)
      log "SKIP (hang-prone pattern): $basename"
      mark_line "$queue_file" "$basename" "SKIPPED" "0"
      continue
      ;;
  esac

  log "Running [${queue_file##*/}]: $basename"
  start=$(date +%s)
  ADMITTED_RESULT=""
  if [ -n "$TIMEOUT_BIN" ]; then
    RUN_CMD=("$TIMEOUT_BIN" "${PER_SIM_TIMEOUT}s" nice -n 19 "$PYTHON" "$probe")
  elif [ -n "$PERL_BIN" ]; then
    # Portable perl-alarm fallback for macOS without GNU timeout
    RUN_CMD=("$PERL_BIN" -e 'alarm shift; exec @ARGV or die "exec: $!"' "$PER_SIM_TIMEOUT" nice -n 19 "$PYTHON" "$probe")
  else
    RUN_CMD=(nice -n 19 "$PYTHON" "$probe")
  fi
  if "${RUN_CMD[@]}" >/dev/null 2>&1; then
    dur=$(( $(date +%s) - start ))
    if receipt_admitted "$basename" "$start"; then
      log "OK   $basename (${dur}s, result=${ADMITTED_RESULT})"
      consecutive_failures=0
      mark_line "$queue_file" "$basename" "DONE" "$dur"
    else
      log "FAIL $basename (${dur}s, admission)"
      consecutive_failures=$((consecutive_failures + 1))
      mark_line "$queue_file" "$basename" "FAIL" "$dur"
    fi
  else
    dur=$(( $(date +%s) - start ))
    log "FAIL $basename (${dur}s)"
    consecutive_failures=$((consecutive_failures + 1))
    mark_line "$queue_file" "$basename" "FAIL" "$dur"
    if [ "$consecutive_failures" -ge "$CONSECUTIVE_FAIL_LIMIT" ]; then
      log "Hit ${CONSECUTIVE_FAIL_LIMIT} consecutive failures. Pausing ${POST_FAIL_PAUSE}s."
      sleep "$POST_FAIL_PAUSE"
      consecutive_failures=0
    fi
  fi

  sim_count=$((sim_count + 1))
  if [ $((sim_count % STATS_EVERY)) -eq 0 ]; then
    log "Progress after $sim_count sims:"
    queue_stats | while read line; do log "$line"; done
  fi

  sleep "$INTER_SIM_SLEEP"
done
