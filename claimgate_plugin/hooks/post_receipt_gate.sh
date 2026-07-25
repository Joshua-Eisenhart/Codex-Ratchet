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

# ------------------------------------------------------------ DURABLE LEDGER
# Every run of this chain appends ONE hash-chained line to
# claimgate_plugin/results/gate_ledger.jsonl — PASS, BLOCKED, PARKED and
# infra-error runs alike. Before this, the gate left nothing behind: 2876/2876
# claim-bearing receipts were orphans (claimgate_plugin/orphan_receipt_detector.py)
# because a receipt that had been gated was indistinguishable from one that never
# had been. A gate that recorded only its passes would keep that hole open, since
# "never ran" and "ran and refused" would still look identical.
#
# Written from an EXIT trap so an early `exit` at ANY stage below still records.
# disposition is set explicitly per stage, never derived from the exit code:
# intake exit 3 is PARK (blocks) while claim_verify exit 3 is admitted-pending.
gate_stages=""
gate_disposition="INCOMPLETE"
gate_blocking_stage=""
gate_admits=0   # 1 once the chain is on a path that ADMITS the receipt

stage_done() {  # stage_done <stage> <exit>
  gate_stages="${gate_stages}${gate_stages:+,}$1=$2"
}

_ledger_write() {
  rc=$1
  python3 "$script_dir/../gate_ledger.py" append "$receipt" \
    --exit "$rc" \
    --disposition "$gate_disposition" \
    --blocking-stage "$gate_blocking_stage" \
    --stages "$gate_stages"
  ledger_rc=$?
  if [ "$ledger_rc" -ne 0 ]; then
    echo "post_receipt_gate: DURABLE LEDGER WRITE FAILED (exit $ledger_rc)" >&2
    # An ADMITTING verdict with no durable record IS the orphan condition this
    # ledger exists to close, so it must not be reported as a clean admission.
    # A blocking verdict is preserved as-is: the block stands on its own.
    if [ "$gate_admits" -eq 1 ]; then
      echo "post_receipt_gate: an admission with no durable record is exactly the orphan condition — escalating to exit 2 (infra)" >&2
      return 2
    fi
  fi
  return "$rc"
}

classify_block() {  # classify_block <stage> <stage_exit>
  gate_blocking_stage=$1
  case "$2" in
    2) gate_disposition=INFRA_ERROR ;;
    3) gate_disposition=PARKED ;;
    *) gate_disposition=BLOCKED ;;
  esac
}

trap 'rc=$?; _ledger_write "$rc"; rc=$?; trap - EXIT; exit "$rc"' EXIT

# INTAKE SUPERVISOR (strict parse boundary — fires BEFORE every other tier).
# Poisoned bytes must never reach a checker that can normalize them into a
# convenient claim. Closes the three standing hostile GAPs:
#   duplicate_json_key  last-wins would silently pick a value before validation
#   nan_values          NaN/null evidence made every recompute "match"
#   renamed_metric      a locked floor metric vanished via rename
# Exit 1 REJECT, 3 PARK — both block admission. See claimgate_plugin/intake_supervisor.py.
python3 "$script_dir/../intake_supervisor.py" "$receipt"
intake_exit=$?
stage_done intake "$intake_exit"
if [ "$intake_exit" -ne 0 ]; then
  classify_block intake "$intake_exit"
  echo "post_receipt_gate: intake supervisor blocked at the parse boundary (exit $intake_exit)" >&2
  advise
  exit "$intake_exit"
fi

# RECOMPUTE VETO (lean gate tier: numpy + numba, no Julia/PyTorch/JAX).
# Re-derives claimed aggregates from the raw arrays in the same receipt instead of
# trusting the producer's number, and vetoes when summation ORDER is load-bearing
# (ordered vs compensated disagree) because a bare "sum" claim is then ambiguous.
# numpy is ALLOWED in the ClaimGate lane by owner rule — the gate's job is veto.
python3 "$script_dir/../recompute_veto.py" "$receipt"
recompute_exit=$?
stage_done recompute_veto "$recompute_exit"
if [ "$recompute_exit" -ne 0 ]; then
  classify_block recompute_veto "$recompute_exit"
  echo "post_receipt_gate: recompute veto (exit $recompute_exit) — a claimed number did not re-derive" >&2
  advise
  exit "$recompute_exit"
fi

node "$script_dir/../claimgate.mjs" lint-receipt "$receipt" \
  --rules "$script_dir/../rules_ratchet.json"
tier0_exit=$?
stage_done tier0 "$tier0_exit"
if [ "$tier0_exit" -ne 0 ]; then
  classify_block tier0 "$tier0_exit"
  echo "post_receipt_gate: tier0 rejected or errored (exit $tier0_exit)" >&2
  advise
  exit "$tier0_exit"
fi

# CLAIM POLICY GATE — the EVALUATOR decides what this receipt must satisfy.
# Fires BEFORE the seal, because the seal honours producer-declared exemptions.
# Measured on the reviewed branch: a receipt declaring claim_kind=field_only with
# engine_contract.numeric_engine_required=false returned exit 0 / VERIFIED / ledger
# PASS, and so did one that simply omitted engine metadata and asserted a number.
# Numeric-ness is now derived from CONTENT and the requirement comes from
# claimgate_plugin/claim_policy.json, so neither a boolean nor silence is an
# exemption. Exit 1 BLOCK, 3 PARK — both block admission.
python3 "$script_dir/../claim_policy_gate.py" "$receipt"
policy_exit=$?
stage_done claim_policy "$policy_exit"
if [ "$policy_exit" -ne 0 ]; then
  classify_block claim_policy "$policy_exit"
  echo "post_receipt_gate: claim policy gate blocked (exit $policy_exit — 1=BLOCK, 3=PARK/pending evidence)" >&2
  advise
  exit "$policy_exit"
fi

# THREE-ENGINE SEAL (hard, structural): numpy/scipy/mpmath are CONTROL-ONLY; an
# authoritative engine (Julia/JAX/PyTorch) must carry the numeric work. Fired here
# so a contract-violating receipt cannot be admitted. Closes the systemic
# 2026-07-22 breaking (10 arrows ran on numpy with no engine). Pure symbolic/SMT/
# finite receipts are exempt. See claimgate_plugin/three_engine_seal.py.
python3 "$script_dir/../three_engine_seal.py" "$receipt"
seal_exit=$?
stage_done seal "$seal_exit"
if [ "$seal_exit" -ne 0 ]; then
  # FAIL-CLOSED on ANY nonzero (audit 2026-07-22): exit 1 = rejected; exit 2 =
  # the seal's own tooling/usage broke — a broken gate must BLOCK, not wave through.
  # The ledger keeps both facts: stages records the seal's RAW exit, gate_exit the
  # chain's fail-closed 1.
  gate_blocking_stage=seal
  gate_disposition=BLOCKED
  echo "post_receipt_gate: THREE-ENGINE SEAL blocked (exit $seal_exit — 1=rejected, 2=seal tooling error; both fail closed)" >&2
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
stage_done claim_verify "$claim_exit"
if [ "$claim_exit" -ne 0 ] && [ "$claim_exit" -ne 3 ]; then
  classify_block claim_verify "$claim_exit"
  echo "post_receipt_gate: claim_verify REJECTED or errored (exit $claim_exit)" >&2
  advise
  exit "$claim_exit"
fi
gate_admits=1   # claim_verify returned 0 or 3 — both admit; only floor can revoke it
if [ "$claim_exit" -eq 3 ]; then
  gate_disposition=ADMITTED_PENDING_DEPTH
  echo "post_receipt_gate: admitted at tier0, pending deeper audit (INSUFFICIENT_DEPTH, exit 3) — not a rejection; floor stage runs" >&2
  advise
else
  gate_disposition=PASS
fi
if python3 -c "import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d.get('floor_claims') else 1)" "$receipt"; then
  python3 "$script_dir/../ratchet_floor.py" admit "$receipt" --store "${RF_STORE:-$script_dir/../ratchet_floor.json}"
  floor_exit=$?
  stage_done floor "$floor_exit"
  # ratchet_floor: 0=admitted, 1=REJECTED (regression/direction tamper), 2=IO,
  # 3=PARKED (unknown key, needs --allow-new-keys). A regression/IO error is a real
  # gate failure and overrides; PARK/ADMIT are benign and preserve the claim signal.
  if [ "$floor_exit" -eq 1 ] || [ "$floor_exit" -eq 2 ]; then
    classify_block floor "$floor_exit"
    gate_admits=0   # the floor revoked the admission claim_verify had granted
    echo "post_receipt_gate: floor stage FAILED (exit $floor_exit — floor regression or IO)" >&2
    advise
    exit "$floor_exit"
  fi
  if [ "$floor_exit" -eq 3 ]; then
    # Benign PARK: the claim verdict stands, so this is NOT the blocking PARKED
    # state. Its own label keeps the two apart instead of collapsing them.
    gate_disposition=ADMITTED_FLOOR_PARKED
    gate_blocking_stage=floor
    echo "post_receipt_gate: floor stage PARKED (unknown floor key) — benign, preserving claim verdict" >&2
    advise
  fi
fi
exit "$claim_exit"
