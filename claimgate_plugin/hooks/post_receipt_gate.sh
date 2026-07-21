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
exit $?
