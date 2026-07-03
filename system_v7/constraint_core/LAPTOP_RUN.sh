#!/usr/bin/env bash
# LAPTOP_RUN.sh -- one command to set up and verify the whole constraint-core
# bundle on a local laptop (macOS/Linux). Safe to re-run.
#
#   bash LAPTOP_RUN.sh          full run (installs deps, runs everything incl. engines)
#   bash LAPTOP_RUN.sh --fast   skip jax/long sims and the engines cross-substrate lane
#
# Exit 0 = GREEN (every check passed). Exit 1 = a finding to report (do NOT
# edit expected values to force green -- a mismatch is a result).
set -euo pipefail
cd "$(dirname "$0")"
FAST="${1:-}"

echo "== constraint-core laptop runner =="
PY="${PYTHON:-python3}"
echo "python: $($PY --version 2>&1)"

# 1. isolated venv (kept in .venv next to this script)
if [ ! -d .venv ]; then
  echo "== creating .venv =="
  $PY -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --quiet --upgrade pip

# 2. dependencies. numpy/scipy/sympy are REQUIRED; jax/torch enable the
#    substrate engines. matplotlib is intentionally NOT required (harness is headless).
echo "== installing deps (numpy scipy sympy) =="
pip install --quiet numpy scipy sympy
if [ "$FAST" != "--fast" ]; then
  echo "== installing substrate engines (jax, torch) -- optional, may take a few min =="
  pip install --quiet "jax[cpu]" || echo "   (jax install skipped/failed -- engines jax route will SKIP)"
  pip install --quiet torch || echo "   (torch install skipped/failed -- engines torch route will SKIP)"
fi

# 3. the sim harness (23 sims + engines cross-substrate lane)
echo "== run_all.py $FAST =="
python run_all.py $FAST

# 4. Julia route (3rd independent substrate) -- only if julia is on PATH
if [ "$FAST" != "--fast" ] && command -v julia >/dev/null 2>&1; then
  echo "== Julia substrate (engines/julia_engine.jl) =="
  ( cd engines
    julia -e 'using Pkg; try; using JSON; catch; Pkg.add("JSON"); end'
    julia julia_engine.jl
    python validate_engines.py )
else
  echo "== Julia: not on PATH (or --fast) -- skipping 3rd substrate."
  echo "   to run it: install Julia, then  cd engines && julia julia_engine.jl && python validate_engines.py"
fi

echo
echo "== DONE. See run_all_report.json for the machine-readable result. =="
