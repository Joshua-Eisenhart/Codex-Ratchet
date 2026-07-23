#!/bin/bash
# Codex-Ratchet session boot — delegates to Lev OS (owner instruction 2026-07-19).
set -uo pipefail
input=$(cat); source=$(echo "$input" | jq -r '.source // "startup"' 2>/dev/null || echo startup)
[[ "$source" != "startup" ]] && exit 0
echo "[CODEX-RATCHET BOOT — LEV OS GOVERNED]"
echo "Lev front door: /Users/joshuaeisenhart/lev-main (AGENTS.md iron-clad laws; dna/graph.yaml C1/C2; .lev/validation-gates.yaml)"
( cd /Users/joshuaeisenhart/lev-main && echo '{"source":"startup"}' | bash .claude/hooks/session-start.sh ) 2>/dev/null || true
echo "READ-FIRST (binding): CLAUDE.md BINDING STATE; three-engine contract (Julia Canon authoritative, JAX workhorse, PyTorch graph lane, numpy=CONTROL-ONLY); gates ARE code; inventory before generation — check owner packs/repos BEFORE building anything new."
exit 0
