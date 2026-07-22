#!/bin/bash
# Deterministic runner for the cr-serialized-physics flow — same node sequence,
# no agent in the loop (gates ARE code). Mirrors .lev/flows/cr-serialized-physics.flow.yaml.
#
# Usage: run_spine.sh <run_id>
#   FORCE_FAIL_Z3=1  — Phase 1 acceptance test: z3 stage fails closed.
#
# Exit: 0 admitted, 3 parked, 1 rejected/halted.
set -u
cd "$(dirname "$0")/../.."   # repo root

RUN_ID="${1:?usage: run_spine.sh <run_id>}"
STATE_DB=".lev/physics/agentfs/physics.db"
PYTHON="${PYTHON:-/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3}"
STAGE="sim_engines/serialized/serialized_stage.py"

halted() {
  echo "[flow] node '$1' FAILED -> halted. Classifying via ClaimGate:"
  node --experimental-sqlite claimgate_plugin/claim_admission.mjs "$RUN_ID" "$STATE_DB"
  exit $?
}

echo "[flow] cr-serialized-physics run_id=$RUN_ID"
"$PYTHON" "$STAGE" --stage julia   --run-id "$RUN_ID" --state-db "$STATE_DB" || halted julia_canon
"$PYTHON" "$STAGE" --stage jax     --run-id "$RUN_ID" --state-db "$STATE_DB" || halted jax_relax
"$PYTHON" "$STAGE" --stage pysindy --run-id "$RUN_ID" --state-db "$STATE_DB" || halted pysindy_discovery

# bash 3.2 (macOS): empty-array expansion breaks under set -u — use a plain string
Z3_ARGS=""
[ "${FORCE_FAIL_Z3:-0}" = "1" ] && Z3_ARGS="--force-fail"
"$PYTHON" "$STAGE" --stage z3 --run-id "$RUN_ID" --state-db "$STATE_DB" $Z3_ARGS || halted z3_verify

echo "[flow] all stages bound -> claim_admission:"
node --experimental-sqlite claimgate_plugin/claim_admission.mjs "$RUN_ID" "$STATE_DB"
rc=$?
[ $rc -eq 0 ] && echo "[flow] terminal: done (admitted)" || echo "[flow] terminal: halted (rc=$rc)"
exit $rc
