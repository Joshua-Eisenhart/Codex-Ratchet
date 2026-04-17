#!/bin/bash
# Fleet health check. Reports state of runner + caffeinate + Hermes terminals + crons.
# Usage: bash system_v5/ops/fleet_health.sh
# Zero-cost; can be run from any shell or by the wiki steward each tick.

set -u
REPO="/Users/joshuaeisenhart/Desktop/Codex Ratchet"
cd "$REPO" || exit 1

echo "=== Fleet Health — $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo ""

echo "## Runner"
RUNNER_PID=$(pgrep -f system_v5/ops/sim_runner.sh | head -1)
if [ -n "$RUNNER_PID" ]; then
  echo "- PID: $RUNNER_PID (alive)"
  # last activity timestamp from current log
  LOG=$(readlink overnight_logs/sim_runner_current.log 2>/dev/null || ls -t overnight_logs/sim_runner_*.log 2>/dev/null | head -1)
  if [ -n "$LOG" ]; then
    LAST=$(tail -1 "$LOG" | awk '{print $1, $2}' | tr -d '[]')
    echo "- last log line: $LAST"
  fi
else
  echo "- PID: (stopped) 🔴"
fi
echo ""

echo "## Caffeinate"
if pgrep -x caffeinate >/dev/null; then
  echo "- running"
else
  echo "- NOT running 🟡 (laptop may sleep)"
fi
echo ""

echo "## Hermes processes"
HERMES_COUNT=$(pgrep -f '/.local/bin/hermes' | wc -l | tr -d ' ')
echo "- live terminals: $HERMES_COUNT"
echo ""

echo "## Queues"
for q in system_v5/ops/queue_tier_a.txt system_v5/ops/queue_tier_b.txt system_v5/ops/queue_tier_d.txt system_v5/ops/queue_default.txt; do
  if [ -f "$q" ]; then
    p=$(grep -cvE '^#|^$' "$q" 2>/dev/null | tr -d '\n')
    d=$(grep -cE '^# DONE' "$q" 2>/dev/null | tr -d '\n')
    f=$(grep -cE '^# FAIL' "$q" 2>/dev/null | tr -d '\n')
    s=$(grep -cE '^# SKIPPED' "$q" 2>/dev/null | tr -d '\n')
    printf "  %-22s %sp/%sd/%sf/%ss\n" "${q##*/}" "${p:-0}" "${d:-0}" "${f:-0}" "${s:-0}"
  fi
done
echo ""

echo "## Tier gate status (from wiki)"
for tier in tier_a tier_b tier_d; do
  f="/Users/joshuaeisenhart/wiki/projects/codex-ratchet/${tier}.md"
  if [ -f "$f" ]; then
    STATUS=$(grep -iE "(^|## )(Status|Gate):" "$f" | head -2 | tr '\n' ' ')
    printf "  %-8s %s\n" "$tier" "$STATUS"
  else
    printf "  %-8s (no report yet)\n" "$tier"
  fi
done
echo ""

echo "## Recent commits (last 5)"
git log --oneline -5
echo ""

echo "## Active scopes (Hermes terminal registrations)"
if [ -f /tmp/hermes_active_scopes.txt ]; then
  grep -v '^#' /tmp/hermes_active_scopes.txt | wc -l | awk '{print "  entries:", $1}'
fi
echo ""

echo "## Thermal"
THERM=$(pmset -g therm 2>/dev/null | awk -F'=' '/CPU_Speed_Limit/ {gsub(/ /,"",$2); print $2}')
echo "- CPU_Speed_Limit: ${THERM:-100 (no throttle data)}"
echo ""

echo "## Blocking questions count"
Q_FILE="/Users/joshuaeisenhart/wiki/projects/codex-ratchet/_steward_questions.md"
if [ -f "$Q_FILE" ]; then
  BLOCKING=$(grep -cE "^## Q[0-9]+" "$Q_FILE" 2>/dev/null | tr -d '\n')
  echo "- $BLOCKING"
fi
echo ""

echo "=== End ==="
