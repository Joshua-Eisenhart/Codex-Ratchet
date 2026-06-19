#!/bin/bash
# Perpetual wrapper: respawns reseeder + runners whenever they exit.
# Local compute only, zero tokens. Stop with: kill "$(cat /tmp/codex_ratchet_perpetual_runner.pid)"
set -u
ROOT="${CODEX_RATCHET_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)}"
PY="${CODEX_RATCHET_PYTHON:-${SIM_PY:-/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3}}"
PERPETUAL_PIDFILE="/tmp/codex_ratchet_perpetual_runner.pid"
CONTROLLER_PIDFILE="/tmp/codex_ratchet_adaptive_controller.pid"
RESEED_PIDFILE="/tmp/codex_ratchet_autonomous_reseed.pid"
cd "$ROOT"
LOG="$ROOT/overnight_logs/perpetual_$(date +%Y%m%d_%H%M%S).log"
echo "[$(date)] perpetual runner started, pid=$$" >> "$LOG"

clear_perpetual_pidfile() {
  if [ -f "$PERPETUAL_PIDFILE" ] && [ "$(cat "$PERPETUAL_PIDFILE" 2>/dev/null)" = "$$" ]; then
    rm -f "$PERPETUAL_PIDFILE"
  fi
}

stop_pidfile_process() {
  local pidfile="$1" label="$2"
  [ -f "$pidfile" ] || return 0
  local pid
  pid=$(cat "$pidfile" 2>/dev/null || true)
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    echo "[$(date)] stopping $label pid=$pid" >> "$LOG"
    kill "$pid" 2>/dev/null || true
  fi
}

cleanup_perpetual() {
  stop_pidfile_process "$CONTROLLER_PIDFILE" "adaptive_controller"
  stop_pidfile_process "$RESEED_PIDFILE" "autonomous_reseed_loop"
  clear_perpetual_pidfile
}

acquire_perpetual_pidfile() {
  if [ ! -f "$PERPETUAL_PIDFILE" ]; then
    echo "$$" > "$PERPETUAL_PIDFILE"
    trap cleanup_perpetual EXIT
    trap 'trap - EXIT; cleanup_perpetual; exit 130' INT TERM
    return 0
  fi
  pid=$(cat "$PERPETUAL_PIDFILE" 2>/dev/null || true)
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    echo "[$(date)] existing perpetual pidfile is alive; exiting duplicate" >> "$LOG"
    return 1
  fi
  echo "$$" > "$PERPETUAL_PIDFILE"
  trap cleanup_perpetual EXIT
  trap 'trap - EXIT; cleanup_perpetual; exit 130' INT TERM
  return 0
}

if ! acquire_perpetual_pidfile; then
  exit 0
fi

controller_running() {
  "$PY" - "$CONTROLLER_PIDFILE" <<'PY'
import os
import sys

pidfile = sys.argv[1]
try:
    with open(pidfile, "r", encoding="utf-8") as handle:
        pid = int(handle.read().strip())
    os.kill(pid, 0)
except Exception:
    raise SystemExit(1)
raise SystemExit(0)
PY
}

reseed_running() {
  if [ ! -f "$RESEED_PIDFILE" ]; then
    return 1
  fi
  pid=$(cat "$RESEED_PIDFILE" 2>/dev/null || true)
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

while :; do
  # Adaptive controller: triage, schema repair, integration pass, priority queueing
  if ! controller_running; then
    echo "[$(date)] respawning adaptive_controller" >> "$LOG"
    nohup "$PY" \
      scripts/adaptive_controller.py >> "$ROOT/overnight_logs/adaptive_controller_perpetual.log" 2>&1 &
  fi
  # Legacy reseeder still runs as fallback
  if ! reseed_running; then
    echo "[$(date)] respawning legacy reseeder" >> "$LOG"
    MAX_HOURS=99999 IDLE_CYCLES=999999 nohup bash scripts/autonomous_reseed_loop.sh >> "$LOG" 2>&1 &
    echo "$!" > "$RESEED_PIDFILE"
  fi
  sleep 120
done
