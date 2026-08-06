#!/bin/bash
# Runs every discriminator and records the REAL exit code of each process.
# No step's status is written by hand.
set -u
PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
JL=/opt/homebrew/bin/julia
HERE="$(cd "$(dirname "$0")" && pwd)"
MAN="$HERE/results/run_manifest.txt"
: > "$MAN"

run() {
  local name="$1"; shift
  "$@" > "$HERE/results/${name}.stdout.txt" 2> "$HERE/results/${name}.stderr.txt"
  local code=$?
  printf '%-28s exit=%s  cmd=%s\n' "$name" "$code" "$*" >> "$MAN"
  echo "$name exit=$code"
}

run d1_root_support   "$PY" "$HERE/d1_root_support.py"
run d2_root_geometry  "$PY" "$HERE/d2_root_geometry.py"
run d3_quotient_order "$PY" "$HERE/d3_quotient_order.py"
run d4_presentations  "$PY" "$HERE/d4_presentations.py"
run d5_algebra        "$PY" "$HERE/d5_algebra.py"
run lane_julia        "$JL" --startup-file=no "$HERE/lane_julia.jl"
run compare_lanes     "$PY" "$HERE/compare_lanes.py"

echo "--- manifest ---"
cat "$MAN"
