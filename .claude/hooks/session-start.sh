#!/bin/bash
# Codex-Ratchet session boot — delegates to Lev OS (owner instruction 2026-07-19).
set -uo pipefail
input=$(cat); source=$(echo "$input" | jq -r '.source // "startup"' 2>/dev/null || echo startup)
case "$source" in
  startup|resume|clear|compact) ;;
  *) source=startup ;;
esac
repo=$(cd "$(dirname "$0")/../.." && pwd)
cd "$repo" || exit 2
python="$repo/constraint_box/.venv/bin/python"
if [[ ! -x "$python" ]]; then
  printf 'CB Light contained interpreter missing: %s\n' "$python" >&2
  exit 2
fi
echo "[CODEX-RATCHET BOOT — LEV OS GOVERNED]"
echo "Lev front door: /Users/joshuaeisenhart/lev-main (AGENTS.md iron-clad laws; dna/graph.yaml C1/C2; .lev/validation-gates.yaml)"
( cd /Users/joshuaeisenhart/lev-main && printf '{"source":"%s"}\n' "$source" | bash .claude/hooks/session-start.sh ) 2>/dev/null || true
echo "CB LIGHT (active default): Python/stdlib plus constrained Light libraries. Installed, candidate, selected, probed, and adopted are separate facts. Heavy sim engines cannot enter Light by being installed."
echo "CB HEAVY (explicit lanes only): Julia/JAX/PyTorch and simulation engines remain a separate profile and evidence ceiling."
gate_output=$(cd "$repo/constraint_box" && "$python" -I \
  -m hookkernel.cb_light_gate session-start \
  --payload-json "$input" 2>&1)
gate_status=$?
if [[ $gate_status -ne 0 ]]; then
  printf '%s\n' "$gate_output" >&2
  exit 2
fi
gate_disposition=$(printf '%s' "$gate_output" | jq -r '.disposition')
gate_reason=$(printf '%s' "$gate_output" | jq -r '.reason_code')
printf 'CB LIGHT SESSION GATE: %s %s\n' "$gate_disposition" "$gate_reason"
exit 0
