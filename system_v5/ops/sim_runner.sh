#!/bin/bash
# 24/7 thermal-safe sim runner. Drains tier queues in priority order.
# Spec: system_v5/ops/SIM_RUNNER.md

set -u

REPO="/Users/joshuaeisenhart/Desktop/Codex Ratchet"
OPS="$REPO/system_v5/ops"
STOP="$OPS/.stop_sim_runner"
STAGE_GATE="$OPS/stage_gate.json"
LOG_DIR="$REPO/overnight_logs"
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
# macOS ships without `timeout`; fall back to portable perl-alarm wrapper.
TIMEOUT_BIN="$(command -v gtimeout || command -v timeout || echo '')"
PERL_BIN="$(command -v perl)"

mkdir -p "$LOG_DIR"
cd "$REPO" || exit 1

# Keep a 'current' symlink to this run's log so Hermes can tail it
THIS_LOG="$LOG_DIR/sim_runner_$(date +%Y%m%d_%H%M%S).log"
ln -sf "$THIS_LOG" "$LOG_DIR/sim_runner_current.log"

log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"; }

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
try:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    value = data.get(key, default.lower() == "true")
except Exception:
    value = default.lower() == "true"
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

log "Runner started. Priority: A > B > D(if stage gate permits) > default."
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
    log "OK   $basename (${dur}s)"
    consecutive_failures=0
    mark_line "$queue_file" "$basename" "DONE" "$dur"
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
