#!/bin/bash
# Perpetual wrapper: respawns reseeder + runners whenever they exit.
# Local compute only, zero tokens. Stop with: pkill -f perpetual_runner.sh
set -u
ROOT="/Users/joshuaeisenhart/Desktop/Codex Ratchet"
PY="/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
CONTROLLER_PIDFILE="/tmp/codex_ratchet_adaptive_controller.pid"
RESEED_PIDFILE="/tmp/codex_ratchet_autonomous_reseed.pid"
cd "$ROOT"
LOG="$ROOT/overnight_logs/perpetual_$(date +%Y%m%d_%H%M%S).log"
echo "[$(date)] perpetual runner started, pid=$$" >> "$LOG"

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
  fi
  sleep 120
done
