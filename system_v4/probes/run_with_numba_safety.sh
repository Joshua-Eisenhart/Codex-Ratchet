#!/usr/bin/env bash
set -euo pipefail

# Repo-local wrapper for probe execution.
# Keeps NumPy/Numba/Matplotlib cache noise from breaking repeated sim runs.

export NUMBA_DISABLE_JIT="${NUMBA_DISABLE_JIT:-1}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/codex-mplconfig}"
export NUMBA_CACHE_DIR="${NUMBA_CACHE_DIR:-/tmp/codex-numba-cache}"

mkdir -p "$MPLCONFIGDIR" "$NUMBA_CACHE_DIR"

exec "$@"
