#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# run_all_checks.sh  --  Full manifest check for CI / manual runs
#
# Runs check_manifest.py against ALL sim-result JSON files.
# Exit code mirrors the checker: 0 = pass, 1 = canonical violations.
# ──────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECKER="${SCRIPT_DIR}/check_manifest.py"

echo "======================================================================"
echo "  Codex Ratchet -- Full Manifest Check"
echo "======================================================================"
echo ""

python3 "$CHECKER"
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "ALL CHECKS PASSED"
else
    echo "CHECKS FAILED -- see violations above"
fi

exit $EXIT_CODE
