#!/bin/bash
# Probe lane 2 — run independently-computed engine legs, then interpret their
# receipts under one explicit mode. The comparator is the only multi-receipt
# reader; the carrier evaluator is a separate post-comparison control surface.
set -u

PY="${SIM_PY:-/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3}"
JL="${JULIA_BIN:-/opt/homebrew/bin/julia}"
D="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$D/../../.." && pwd)"
JULIA_CARRIER="${JULIA_CARRIER:-$REPO_ROOT/system_v5/julia_carrier}"
MAN="$D/results/run_manifest.txt"

usage() {
  echo "usage: $0 [--acceptance|--diagnostic]" >&2
  echo "  --acceptance: compare only float64 engine receipts; expects exit 0" >&2
  echo "  --diagnostic: compare float32 + float64 receipts; expects exit 3" >&2
}

MODE="${1:---diagnostic}"
case "$MODE" in
  --acceptance)
    export ROOT_STRATA_PRECISIONS=float64
    EXPECTED_COMPARE=0
    ;;
  --diagnostic)
    export ROOT_STRATA_PRECISIONS=float32,float64
    EXPECTED_COMPARE=3
    ;;
  *)
    usage
    exit 2
    ;;
esac

if [[ ! -x "$PY" ]]; then
  echo "missing canonical Python runtime: $PY" >&2
  exit 2
fi
if [[ ! -x "$JL" ]]; then
  echo "missing Julia runtime: $JL" >&2
  exit 2
fi
if [[ ! -f "$JULIA_CARRIER/Project.toml" ]]; then
  echo "missing Julia carrier project: $JULIA_CARRIER/Project.toml" >&2
  exit 2
fi

mkdir -p "$D/results"
: > "$MAN"
FAILURES=()
LAST_RC=0

run_expected() {            # run_expected <label> <expected-exit> <cmd...>
  local label="$1"
  local expected="$2"
  shift 2
  "$@" > "$D/results/$label.stdout.txt" 2> "$D/results/$label.stderr.txt"
  LAST_RC=$?
  printf '%-34s exit=%s expected=%s cmd=%s\n' "$label" "$LAST_RC" "$expected" "$*" | tee -a "$MAN"
  if [[ "$LAST_RC" -ne "$expected" ]]; then
    FAILURES+=("$label: expected $expected, got $LAST_RC")
  fi
}

run_expected enum_reference        0 "$PY" "$D/enum_reference.py"
run_expected closed_form_reference 0 "$PY" "$D/closed_form_reference.py"
run_expected lane_jax_float32      0 "$PY" "$D/lane_jax.py" float32
run_expected lane_jax_float64      0 "$PY" "$D/lane_jax.py" float64
run_expected lane_torch_float32    0 "$PY" "$D/lane_torch.py" float32
run_expected lane_torch_float64    0 "$PY" "$D/lane_torch.py" float64
run_expected lane_julia_float32    0 env JULIA_LOAD_PATH=@:@stdlib "$JL" --startup-file=no "--project=$JULIA_CARRIER" "$D/lane_julia.jl" float32
run_expected lane_julia_float64    0 env JULIA_LOAD_PATH=@:@stdlib "$JL" --startup-file=no "--project=$JULIA_CARRIER" "$D/lane_julia.jl" float64
run_expected compare_lanes         "$EXPECTED_COMPARE" "$PY" "$D/compare_lanes.py"
run_expected emit_typed_receipts   0 "$PY" "$D/emit_typed_receipts.py"

echo "--- manifest: $MAN"
cat "$MAN"
if (( ${#FAILURES[@]} )); then
  printf '%s\n' "root-strata $MODE FAILED:" >&2
  printf '  %s\n' "${FAILURES[@]}" >&2
  exit 1
fi
echo "root-strata $MODE passed"
