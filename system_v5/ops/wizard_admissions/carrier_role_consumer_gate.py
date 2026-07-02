#!/usr/bin/env python3
"""carrier_role consumer gate (Wizard-council-selected move, 2026-06-01).

The 11 shared _tn_carrier legos each carry a `carrier_role`:
  - object_load_bearing      : the CLAIM flips on carrier-erase (entanglement is object-necessary)
  - operator_readout_on_carrier : an operator/connection fact read on the carrier; entanglement is
                                  SUPPORTIVE (gate-bearing), NOT object-necessary

The labels existed but nothing enforced them at consume-time, so a downstream consumer could confuse an
operator_readout row, an object_load_bearing residual row, and a vacuous cvc5_required boolean. This gate
validates label<->evidence for every lego and fences promotion, so only honestly-object-load-bearing rows
can feed a tier-2/object consumer. It does NOT rerun sims; it audits the emitted result JSONs.

Pass per row requires:
  (A) carrier_role present and one of the two allowed values;
  (B) object_load_bearing  => at least one CLAIM-FLIP witness is True (the entanglement-necessary claim
      genuinely flips on erase): tier2_residual_flips_pass, OR a product-goes-to-zero control
      (product_no_entanglement_pass / cut_entanglement_pass), OR the object-field survivor carrier-erase
      flip (carrier_load_bearing_pass AND object first-class fields present);
  (C) operator_readout_on_carrier => carrier_role_note present AND it does NOT assert a tier-2 object
      (no tier2_residual_flips_pass:True) -- if an operator row secretly flips, it is MISLABELED;
  (D) promotion_allowed is False and blocked_consumers fences the downstream set;
  (E) the proof is not cvc5-only: a real midpoint_proof verdict-flip (differ:True) must back the row.
"""
from __future__ import annotations
import json, glob, os, sys, pathlib

RESULTS = pathlib.Path(__file__).resolve().parents[3] / "system_v5/legos/results"
OUT = pathlib.Path(__file__).resolve().parent / "carrier_role_consumer_gate_ledger.json"
ALLOWED_ROLES = {"object_load_bearing", "operator_readout_on_carrier"}
OBJECT_FIELD_KEYS = {"shells", "future_continuations", "compatibility_weights", "compression_map", "present_survivor", "outward_record"}
MUST_FENCE = {"layer_stacking", "flux", "Xi/Phi0", "Axis0"}
FLIP_WITNESS_KEYS = ["tier2_residual_flips_pass", "product_no_entanglement_pass", "cut_entanglement_pass"]


def has_object_fields(r):
    rows = r.get("rows") or []
    blob = json.dumps(r)
    return sum(1 for k in OBJECT_FIELD_KEYS if k in blob) >= 4


def real_proof_backs_row(r):
    """A real load-bearing proof = midpoint_proof verdict-flip (differ True bound to measured values),
    NOT the vacuous cvc5_required boolean-consistency check."""
    for key in ("proof_gate", "structural_proof", "tier1_order_gate_proof", "tier1_cocycle_gate_proof"):
        p = r.get(key)
        if isinstance(p, dict) and p.get("differ") is True and ("measured_real" in p or "real_claim_verdict" in p):
            return True
    return False


def audit_row(r):
    name = r.get("name", "?")
    req = r.get("required", {})
    role = r.get("carrier_role")
    findings = []
    # (A)
    if role not in ALLOWED_ROLES:
        findings.append(f"carrier_role missing/invalid: {role!r}")
    # (B)/(C)
    flip_true = bool(req.get("tier2_residual_flips_pass") is True)
    if role == "object_load_bearing":
        witnesses = [k for k in FLIP_WITNESS_KEYS if req.get(k) is True]
        survivor_flip = bool(req.get("carrier_load_bearing_pass") is True) and has_object_fields(r)
        if not witnesses and not survivor_flip:
            findings.append("object_load_bearing but NO claim-flip witness (no residual flip, no product->0 control, no survivor field-flip) => label not earned")
        claim_flip = bool(witnesses) or survivor_flip
    elif role == "operator_readout_on_carrier":
        if not r.get("carrier_role_note"):
            findings.append("operator_readout_on_carrier missing carrier_role_note (must state entanglement is supportive, not object-necessary)")
        if flip_true:
            findings.append("operator_readout row asserts tier2_residual_flips_pass=True => MISLABELED, should be object_load_bearing")
        claim_flip = False
    else:
        claim_flip = False
    # (D)
    if r.get("promotion_allowed") is not False:
        findings.append(f"promotion_allowed must be False, got {r.get('promotion_allowed')!r}")
    fenced = set(r.get("blocked_consumers") or [])
    missing_fence = MUST_FENCE - fenced
    if missing_fence:
        findings.append(f"blocked_consumers does not fence: {sorted(missing_fence)}")
    # (E)
    if not real_proof_backs_row(r):
        findings.append("no real midpoint_proof verdict-flip backs the row (cvc5_required alone is vacuous)")
    return {
        "name": name, "carrier_role": role, "claim_flips_on_erase": claim_flip,
        "tier2_consumer_eligible": role == "object_load_bearing" and claim_flip and not findings,
        "findings": findings, "pass": not findings,
    }


def main():
    files = sorted(glob.glob(str(RESULTS / "*_results.json")))
    rows = []
    for f in files:
        try:
            r = json.load(open(f))
        except Exception:
            continue
        if "carrier_role" not in r:
            continue
        rows.append(audit_row(r))
    n = len(rows)
    obj = [x for x in rows if x["carrier_role"] == "object_load_bearing"]
    opr = [x for x in rows if x["carrier_role"] == "operator_readout_on_carrier"]
    tier2_eligible = [x["name"] for x in rows if x["tier2_consumer_eligible"]]
    failed = [x for x in rows if not x["pass"]]
    ledger = {
        "gate": "carrier_role_consumer_gate", "n_legos": n,
        "object_load_bearing": len(obj), "operator_readout_on_carrier": len(opr),
        "tier2_consumer_eligible": sorted(tier2_eligible),
        "operator_readout_fenced_from_tier2": sorted(x["name"] for x in opr),
        "all_pass": len(failed) == 0 and n == 11,
        "n_failed": len(failed),
        "rows": rows,
    }
    OUT.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in ledger.items() if k != "rows"}, indent=2, sort_keys=True))
    for x in failed:
        print(f"  FAIL {x['name']} [{x['carrier_role']}]: {x['findings']}")
    return ledger


if __name__ == "__main__":
    res = main()
    raise SystemExit(0 if res["all_pass"] else 1)
