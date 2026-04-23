#!/bin/bash
# Throttle: kill youngest runner if load > THRESHOLD or thermal warning.
ROOT="/Users/joshuaeisenhart/Desktop/Codex Ratchet"
LOG="$ROOT/overnight_logs/thermal_guard.log"
THRESHOLD=${THRESHOLD:-12}
while :; do
  load=$(uptime | awk -F'load averages?:' '{print $2}' | awk '{print int($1)}')
  therm=$(pmset -g therm 2>/dev/null | grep -i "CPU_Speed_Limit" | awk '{print $NF}')
  if [ "$load" -gt "$THRESHOLD" ] || [ -n "$therm" ] && [ "${therm:-100}" -lt 100 ] 2>/dev/null; then
    youngest=$(pgrep -f overnight_two_runner.sh | tail -1)
    [ -n "$youngest" ] && kill "$youngest" && echo "[$(date)] killed pid=$youngest (load=$load therm=$therm)" >> "$LOG"
  fi
  sleep 60
done
