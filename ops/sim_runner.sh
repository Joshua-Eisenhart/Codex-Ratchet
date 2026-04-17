#!/bin/bash
# 24/7 thermal-safe sim runner. Drains tier queues in priority order.
# Spec: ops/SIM_RUNNER.md

set -u

REPO="/Users/joshuaeisenhart/Desktop/Codex Ratchet"
OPS="$REPO/ops"
STOP="$OPS/.stop_sim_runner"
LOG_DIR="$REPO/overnight_logs"
PYTHON="$(which python3)"

QUEUES=(
  "$OPS/queue_tier_a.txt"
  "$OPS/queue_tier_b.txt"
  "$OPS/queue_tier_d.txt"
  "$OPS/queue_default.txt"
)

THERMAL_PAUSE_LEVEL=60
THERMAL_RESUME_LEVEL=40
LOAD_PAUSE_FACTOR=0.75
COOLDOWN_SECS=120
INTER_SIM_SLEEP=5
CONSECUTIVE_FAIL_LIMIT=5
POST_FAIL_PAUSE=1800

mkdir -p "$LOG_DIR"
cd "$REPO" || exit 1

# Keep a 'current' symlink to this run's log so Hermes can tail it
THIS_LOG="$LOG_DIR/sim_runner_$(date +%Y%m%d_%H%M%S).log"
ln -sf "$THIS_LOG" "$LOG_DIR/sim_runner_current.log"

log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"; }

check_stop() {
  [ -f "$STOP" ] && { log "Stop file present. Exiting."; exit 0; }
}

check_thermal() {
  sysctl -n machdep.xcpm.cpu_thermal_level 2>/dev/null || echo 0
}

check_load_ok() {
  local ncpus load1
  ncpus=$(sysctl -n hw.ncpu)
  load1=$(sysctl -n vm.loadavg | awk '{print $2}')
  awk -v l="$load1" -v n="$ncpus" -v f="$LOAD_PAUSE_FACTOR" \
      'BEGIN { exit !(l < n * f) }'
}

wait_until_cool() {
  while :; do
    check_stop
    local t
    t=$(check_thermal)
    if [ "$t" -lt "$THERMAL_RESUME_LEVEL" ] && check_load_ok; then
      return 0
    fi
    log "Cooldown: thermal_level=$t, waiting ${COOLDOWN_SECS}s"
    sleep "$COOLDOWN_SECS"
  done
}

pick_next() {
  # Print: "<queue_file>|<basename>" for first runnable line across priority queues
  for q in "${QUEUES[@]}"; do
    [ -f "$q" ] || continue
    local line
    line=$(grep -v '^#' "$q" | grep -v '^[[:space:]]*$' | head -1)
    if [ -n "$line" ]; then
      echo "${q}|${line}"
      return 0
    fi
  done
  return 1
}

regen_default_queue() {
  local q="${QUEUES[3]}"
  log "Regenerating default queue from canonical-missing-depth list"
  "$PYTHON" - <<'PY' > "$q"
import json, glob, os
for p in sorted(glob.glob('system_v4/probes/a2_state/sim_results/*.json')):
    try: d = json.load(open(p))
    except Exception: continue
    if d.get('classification') == 'canonical' and 'tool_integration_depth' not in d:
        base = os.path.basename(p).replace('_results.json', '')
        py_path = f'system_v4/probes/{base}.py'
        if os.path.exists(py_path):
            print(base)
PY
}

mark_line() {
  local q="$1" basename="$2" status="$3" dur="$4"
  sed -i '' "0,/^${basename}$/s//# ${status} $(date +%Y-%m-%d_%H:%M:%S) ${basename} (${dur}s)/" "$q"
}

consecutive_failures=0

log "Runner started. Priority: A > B > D > default."

while :; do
  check_stop

  pick=$(pick_next || echo "")
  if [ -z "$pick" ]; then
    regen_default_queue
    if ! pick=$(pick_next); then
      log "All queues empty. Sleeping 600s."
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

  t=$(check_thermal)
  if [ "$t" -ge "$THERMAL_PAUSE_LEVEL" ] || ! check_load_ok; then
    log "Thermal/load high (thermal=$t). Cooling down."
    wait_until_cool
  fi

  log "Running [${queue_file##*/}]: $basename"
  start=$(date +%s)
  if nice -n 19 "$PYTHON" "$probe" >/dev/null 2>&1; then
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

  sleep "$INTER_SIM_SLEEP"
done
