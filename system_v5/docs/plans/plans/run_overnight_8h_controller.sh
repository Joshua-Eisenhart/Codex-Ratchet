#!/bin/bash
set -euo pipefail

ROOT="/Users/joshuaeisenhart/Desktop/Codex Ratchet"
CANONICAL_RUNNER="$ROOT/system_v5/docs/plans/overnight_8h_run.sh"

if [ ! -x "$CANONICAL_RUNNER" ]; then
  chmod +x "$CANONICAL_RUNNER"
fi

exec "$CANONICAL_RUNNER" "$@"
