#!/bin/sh

# Harness-fireable entry point: Lev (or another harness) calls THIS script,
# not claimgate.mjs or claim_verify.py directly, so the receipt-producing agent
# cannot choose to skip verification.

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 2
receipt=${1-}

node "$script_dir/../claimgate.mjs" lint-receipt "$receipt" \
  --rules "$script_dir/../rules_ratchet.json"
tier0_exit=$?
if [ "$tier0_exit" -ne 0 ]; then
  echo "post_receipt_gate: tier0 rejected or errored (exit $tier0_exit)" >&2
  exit "$tier0_exit"
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
  exit "$claim_exit"
fi
if [ "$claim_exit" -eq 3 ]; then
  echo "post_receipt_gate: admitted at tier0, pending deeper audit (INSUFFICIENT_DEPTH, exit 3) — not a rejection; floor stage runs" >&2
fi
if python3 -c "import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d.get('floor_claims') else 1)" "$receipt"; then
  python3 "$script_dir/../ratchet_floor.py" admit "$receipt" --store "${RF_STORE:-$script_dir/../ratchet_floor.json}"
  floor_exit=$?
  # ratchet_floor: 0=admitted, 1=REJECTED (regression/direction tamper), 2=IO,
  # 3=PARKED (unknown key, needs --allow-new-keys). A regression/IO error is a real
  # gate failure and overrides; PARK/ADMIT are benign and preserve the claim signal.
  if [ "$floor_exit" -eq 1 ] || [ "$floor_exit" -eq 2 ]; then
    echo "post_receipt_gate: floor stage FAILED (exit $floor_exit — floor regression or IO)" >&2
    exit "$floor_exit"
  fi
  if [ "$floor_exit" -eq 3 ]; then
    echo "post_receipt_gate: floor stage PARKED (unknown floor key) — benign, preserving claim verdict" >&2
  fi
fi
exit "$claim_exit"
