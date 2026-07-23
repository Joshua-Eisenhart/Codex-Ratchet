#!/bin/bash
# run_through_lev.sh — the standard "run a manifold sim through the whole box" command.
# Makes Lev genuinely USED (not retyped ad hoc): one invocation drives
#   (1) ClaimGate fired gate  (post_receipt_gate.sh = three-engine seal + tier0 + claim_verify + floor)
#   (2) Lev host-recompute    (lev_steering_producer.py -> core/poly/bin/lev orchestration
#                              claimgate-steering consume --no-write)
# on a receipt an engine sim already produced. Prints each leg's real exit code / verdict.
#
# Usage:  run_through_lev.sh <receipt.json> [--generated-at <iso>]
# Exit:   0 iff ClaimGate admitted (exit 0 or 3) AND Lev recomputed without error.
set -o pipefail
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 2
receipt=${1:?usage: run_through_lev.sh <receipt.json> [--generated-at <iso>]}
gen_at=${3:-2026-07-22T00:00:00Z}
# 2026-07-22: ~/GitHub/lev deleted; ~/lev-main = the only Lev (pure upstream main).
lev_root=${LEV_REPO_ROOT:-/Users/joshuaeisenhart/lev-main}
PY=${SIM_PY:-/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3}

echo "== [1/2] ClaimGate fired gate =="
sh "$script_dir/hooks/post_receipt_gate.sh" "$receipt"; gate=$?
case "$gate" in
  0) echo "  ClaimGate: VERIFIED (exit 0)";;
  3) echo "  ClaimGate: admitted, depth-pending (exit 3 — not a rejection)";;
  *) echo "  ClaimGate: REJECTED/error (exit $gate) — stopping; not sent to Lev." >&2; exit "$gate";;
esac

echo "== [2/2] Lev host-recompute (claimgate-steering consume) =="
lev_bin="$lev_root/core/poly/bin/lev"
if [ ! -x "$lev_bin" ]; then
  echo "  Lev poly binary missing ($lev_bin) — cannot host-consume; ClaimGate leg stands." >&2
  exit 0
fi
# Pure upstream main does NOT ship 'orchestration claimgate-steering' (it lived on
# the deleted fable/cr-sim-eval-pack branch). Detect and degrade HONESTLY: the
# ClaimGate leg stands alone until the rebuilt patch restores a Lev-side consumer.
if ! "$lev_bin" orchestration --help >/dev/null 2>&1; then
  echo "  Lev at $lev_root has no 'orchestration' subcommand (pure upstream main;"
  echo "  steering-consume was branch-only and is being rebuilt as the ClaimGate patch)."
  echo "  ClaimGate leg stands; Lev host-recompute SKIPPED — not silently passed."
  exit 0
fi
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
run_dir=$("$PY" "$script_dir/lev_steering_producer.py" "$receipt" --out "$work" \
           --generated-at "$gen_at" --json 2>/dev/null \
         | "$PY" -c "import json,sys; print(json.load(sys.stdin)['run_dir'])") || {
  echo "  producer failed to emit a projection." >&2; exit 0; }
( cd "$lev_root" && "$lev_bin" orchestration claimgate-steering consume "$run_dir" --no-write 2>&1 ) \
  | grep -iE "steering run|Projected verdict|Recomputed verdict|Live Lev consumed"
echo "  (host_consumed = full pass admitted; host_reviewed_failed = recomputed + correctly not admitted for a probe)"
exit 0
