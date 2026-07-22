#!/bin/sh

# Harness-fireable entry point: Lev (or another harness) calls THIS script,
# not claimgate.mjs or claim_verify.py directly, so the receipt-producing agent
# cannot choose to skip verification.

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 2
receipt=${1-}

# OPTIONAL advisory step (never gates, never touched by any tier's exit code):
# turn a rejection or an INSUFFICIENT_DEPTH admission into a concrete HOW.
# Best-effort — a suggest.mjs failure/absence must never mask or alter the
# real gate outcome, so it always runs after the real exit is already decided
# and its own output/exit status is discarded.
advise() {
  node "$script_dir/../suggest.mjs" "$receipt" >&2 2>/dev/null || true
}

node "$script_dir/../claimgate.mjs" lint-receipt "$receipt" \
  --rules "$script_dir/../rules_ratchet.json"
tier0_exit=$?
if [ "$tier0_exit" -ne 0 ]; then
  echo "post_receipt_gate: tier0 rejected or errored (exit $tier0_exit)" >&2
  advise
  exit "$tier0_exit"
fi

# THREE-ENGINE SEAL (hard, structural): numpy/scipy/mpmath are CONTROL-ONLY; an
# authoritative engine (Julia/JAX/PyTorch) must carry the numeric work. Fired here
# so a contract-violating receipt cannot be admitted. Closes the systemic
# 2026-07-22 breaking (10 arrows ran on numpy with no engine). Pure symbolic/SMT/
# finite receipts are exempt. See claimgate_plugin/three_engine_seal.py.
python3 "$script_dir/../three_engine_seal.py" "$receipt"
seal_exit=$?
if [ "$seal_exit" -eq 1 ]; then
  echo "post_receipt_gate: THREE-ENGINE SEAL rejected (numpy control-only / no authoritative engine)" >&2
  advise
  exit 1
fi

python3 "$script_dir/../claim_verify.py" "$receipt"
claim_exit=$?
# claim_verify exit codes: 0=VERIFIED, 1=REJECTED, 2=usage/IO, 3=INSUFFICIENT_DEPTH.
# Exit 3 is the HONEST verdict for un-audited probe work: tier0 admitted the
# receipt, the deeper required tiers are simply not met yet. It is NOT a rejection
# and must not collapse into exit 1. Propagate it distinctly and still run the
# floor stage, so a probe receipt reads "admitted at tier0, pending deeper audit".
if [ "$claim_exit" -ne 0 ] && [ "$claim_exit" -ne 3 ]; then
  echo "post_receipt_gate: claim_verify REJECTED or errored (exit $claim_exit)" >&2
  advise
  exit "$claim_exit"
fi
if [ "$claim_exit" -eq 3 ]; then
  echo "post_receipt_gate: admitted at tier0, pending deeper audit (INSUFFICIENT_DEPTH, exit 3) — not a rejection; floor stage runs" >&2
  advise
fi
if python3 -c "import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d.get('floor_claims') else 1)" "$receipt"; then
  python3 "$script_dir/../ratchet_floor.py" admit "$receipt" --store "${RF_STORE:-$script_dir/../ratchet_floor.json}"
  floor_exit=$?
  # ratchet_floor: 0=admitted, 1=REJECTED (regression/direction tamper), 2=IO,
  # 3=PARKED (unknown key, needs --allow-new-keys). A regression/IO error is a real
  # gate failure and overrides; PARK/ADMIT are benign and preserve the claim signal.
  if [ "$floor_exit" -eq 1 ] || [ "$floor_exit" -eq 2 ]; then
    echo "post_receipt_gate: floor stage FAILED (exit $floor_exit — floor regression or IO)" >&2
    advise
    exit "$floor_exit"
  fi
  if [ "$floor_exit" -eq 3 ]; then
    echo "post_receipt_gate: floor stage PARKED (unknown floor key) — benign, preserving claim verdict" >&2
    advise
  fi
fi
exit "$claim_exit"
