#!/bin/bash
# Perpetual wrapper: respawns reseeder + runners whenever they exit.
# Local compute only, zero tokens. Stop with: pkill -f perpetual_runner.sh
set -u
ROOT="/Users/joshuaeisenhart/Desktop/Codex Ratchet"
cd "$ROOT"
LOG="$ROOT/overnight_logs/perpetual_$(date +%Y%m%d_%H%M%S).log"
echo "[$(date)] perpetual runner started, pid=$$" >> "$LOG"

while :; do
  # Adaptive controller: triage, schema repair, integration pass, priority queueing
  if ! pgrep -f adaptive_controller.py >/dev/null; then
    echo "[$(date)] respawning adaptive_controller" >> "$LOG"
    nohup /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 \
      scripts/adaptive_controller.py >> "$ROOT/overnight_logs/adaptive_controller_perpetual.log" 2>&1 &
  fi
  # Legacy reseeder still runs as fallback
  if ! pgrep -f autonomous_reseed_loop.sh >/dev/null; then
    echo "[$(date)] respawning legacy reseeder" >> "$LOG"
    MAX_HOURS=99999 IDLE_CYCLES=999999 nohup bash scripts/autonomous_reseed_loop.sh >> "$LOG" 2>&1 &
  fi
  sleep 120
done
