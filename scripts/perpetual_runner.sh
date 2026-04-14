#!/bin/bash
# Perpetual wrapper: respawns reseeder + runners whenever they exit.
# Local compute only, zero tokens. Stop with: pkill -f perpetual_runner.sh
set -u
ROOT="/Users/joshuaeisenhart/Desktop/Codex Ratchet"
cd "$ROOT"
LOG="$ROOT/overnight_logs/perpetual_$(date +%Y%m%d_%H%M%S).log"
echo "[$(date)] perpetual runner started, pid=$$" >> "$LOG"

while :; do
  if ! pgrep -f autonomous_reseed_loop.sh >/dev/null; then
    echo "[$(date)] respawning reseeder (MAX_HOURS=99999)" >> "$LOG"
    MAX_HOURS=99999 IDLE_CYCLES=999999 nohup bash scripts/autonomous_reseed_loop.sh >> "$LOG" 2>&1 &
  fi
  sleep 120
done
