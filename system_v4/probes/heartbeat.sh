#!/bin/bash
# Codex Ratchet Heartbeat — Autopoietic Self-Reflecting Daemon
# JP's bootstrap chain: dna.yaml → DAG walker → telemetry → self-reflection → versioned seeds
#
# Two phases per tick:
#   1. Deterministic system tick (SIMs → evidence → triage → graph)
#   2. Codex headless learning tick (codex exec → tick_prompt.md → repo outputs)
#
# Run modes:
#   heartbeat.sh           → full tick (deterministic + codex learning)
#   heartbeat.sh --no-codex → deterministic only (for debugging)

REPO="/Users/joshuaeisenhart/Desktop/Codex Ratchet"
LOG_DIR="$REPO/system_v4/probes/a2_state/sim_results"
DAEMON="$REPO/system_v4/skills/intent-compiler/heartbeat_daemon.py"

cd "$REPO"

echo "" >> "$LOG_DIR/heartbeat.log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$LOG_DIR/heartbeat.log"
echo "LAUNCHD TRIGGER: $(date -u '+%Y-%m-%dT%H:%M:%SZ')" >> "$LOG_DIR/heartbeat.log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$LOG_DIR/heartbeat.log"

PYTHON_BIN="${PYTHON_BIN:-$(awk -F':=' '/^PYTHON[[:space:]]*:=[[:space:]]*/{print $2; exit}' "$REPO/Makefile" | xargs)}"
"$PYTHON_BIN" "$DAEMON" "$@" >> "$LOG_DIR/heartbeat.log" 2>> "$LOG_DIR/heartbeat_error.log"

echo "EXIT: $? at $(date -u '+%Y-%m-%dT%H:%M:%SZ')" >> "$LOG_DIR/heartbeat.log"
