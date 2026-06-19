#!/usr/bin/env python3
"""
Validator for retrocausal_possibility_field_v0.

Asserts (and reports):
  1. ALL first-class object keys are present in the result JSON and genuinely shaped.
  2. ALL required invariants hold on the canonical instance.
  3. The HARD-STOP holds: future_continuations != present_survivor.
  4. Each of the four NEGATIVE CONTROLS BREAKS the result (must NOT pass):
       (a) scramble future_continuations
       (b) remove shell_orientation
       (c) replace compatibility_weights with uniform-and-then-claim-structure
       (d) collapse future_continuations to a scalar count (the proxy shape)

Exits 0 (green) only if: keys present + invariants hold + hard-stop holds + all
four negative controls break.

Run:  <sim-stack python3> validate_retrocausal_possibility_field_v0.py
"""

from __future__ import annotations

import json
import os
import sys

SIM_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SIM_DIR)

import retrocausal_possibility_field_v0 as rpf  # noqa: E402


FIRST_CLASS_KEYS = rpf.FIRST_CLASS_KEYS


def check_keys_present(result: dict) -> dict:
    """Each first-class key present AND genuinely shaped (not a degenerate proxy)."""
    checks = {}
    for k in FIRST_CLASS_KEYS:
        checks[f"key_present:{k}"] = k in result
    # shape gates on the hardest-to-fake fields
    fc = result.get("future_continuations", {})
    checks["future_continuations_is_shell_keyed_dict_of_lists"] = (
        isinstance(fc, dict)
        and len(fc) >= 1
        and all(isinstance(v, list) and len(set(v)) >= 2 for v in fc.values())
    )
    cw = result.get("compatibility_weights", {})
    checks["compatibility_weights_is_pair_real_structure"] = (
        isinstance(cw, dict)
        and len(cw) >= 1
        and all("|" in k for k in cw.keys())
        and all(isinstance(v, float) for v in cw.values())
    )
    cm = result.get("compression_map", {})
    checks["compression_map_is_inward_trace"] = (
        isinstance(cm, dict)
        and cm.get("direction") == "INWARD"
        and "candidate_inward_mass" in cm
    )
    rec = result.get("outward_record", {})
    checks["outward_record_is_outward_hash_chain"] = (
        isinstance(rec, dict)
        and rec.get("record_orientation") == "OUTWARD"
        and bool(rec.get("append_only_recomputed"))
    )
    return checks


def negative_control_a_scramble_futures() -> bool:
    """
    (a) Scramble future_continuations: replace each shell's branch LIST with the
    SAME single repeated branch (destroys the >=2-distinct structure). The
    invariant future_continuations_lists_of_distinct_ge2 MUST fail -> build breaks.
    Returns True iff the control BREAKS the result (all_invariants_hold == False).
    """
    scrambled = {sid: [branches[0], branches[0]] for sid, branches in rpf.FUTURE_CONTINUATIONS_BY_SHELL.items()}
    inst = rpf.build_object_instance(future_continuations=scrambled)
    inv = rpf.check_invariants(inst)
    return not all(inv.values())


def negative_control_b_remove_orientation() -> bool:
    """
    (b) Remove shell_orientation: strip the orientation labels from all shells.
    record_outward / future_flow_inward / has_outward_shell MUST fail.
    Returns True iff the control BREAKS the result.
    """
    shells_no_orient = [
        {k: v for k, v in s.items() if k != "shell_orientation"} for s in rpf.SHELLS
    ]
    # the record builder selects the OUTWARD shell by orientation; with none, it
    # cannot build -> that is itself a break. Catch and treat as broken.
    try:
        inst = rpf.build_object_instance(shells=shells_no_orient)
    except StopIteration:
        return True  # no OUTWARD shell to anchor the record -> broken as required
    inv = rpf.check_invariants(inst)
    return not all(inv.values())


def negative_control_c_uniform_weights() -> bool:
    """
    (c) Replace compatibility_weights with uniform-and-then-claim-structure:
    same pair keys but a CONSTANT value. compatibility_weights_non_uniform MUST
    fail (the structure is decorative). Returns True iff control BREAKS the result.
    """
    real_weights = rpf.compute_compatibility_weights(rpf.FUTURE_CONTINUATIONS_BY_SHELL)
    uniform = {k: 0.5 for k in real_weights}  # claims pair structure but is flat
    inst = rpf.build_object_instance(weights_override=uniform)
    inv = rpf.check_invariants(inst)
    return not all(inv.values())


def negative_control_d_scalar_count_proxy() -> bool:
    """
    (d) Collapse future_continuations to a scalar count (THE proxy shape).
    Build a proxy result where future_continuations is an int (a survivor count)
    and re-run the key/shape gate. The shape gate MUST reject it.
    Returns True iff the proxy shape is REJECTED.
    """
    proxy_result = dict(rpf.build_result())
    proxy_result["future_continuations"] = 6  # scalar count -> proxy attractor
    key_checks = check_keys_present(proxy_result)
    # the proxy must FAIL the shell-keyed-dict-of-lists gate
    return key_checks["future_continuations_is_shell_keyed_dict_of_lists"] is False


def main() -> int:
    # Build canonical result fresh.
    result = rpf.build_result()

    key_checks = check_keys_present(result)
    invariants = result["invariants"]
    hard_stop = invariants["HARD_STOP_future_continuations_ne_present_survivor"]

    neg = {
        "a_scramble_future_continuations_breaks": negative_control_a_scramble_futures(),
        "b_remove_shell_orientation_breaks": negative_control_b_remove_orientation(),
        "c_uniform_weights_claim_structure_breaks": negative_control_c_uniform_weights(),
        "d_scalar_count_proxy_rejected": negative_control_d_scalar_count_proxy(),
    }

    keys_ok = all(key_checks.values())
    invariants_ok = all(invariants.values())
    negatives_ok = all(neg.values())

    green = keys_ok and invariants_ok and hard_stop and negatives_ok

    report = {
        "validator": "validate_retrocausal_possibility_field_v0",
        "first_class_keys_present_in_result": [k for k in FIRST_CLASS_KEYS if k in result],
        "key_shape_checks": key_checks,
        "all_keys_present_and_shaped": keys_ok,
        "invariants": invariants,
        "all_invariants_hold": invariants_ok,
        "HARD_STOP_future_continuations_ne_present_survivor": hard_stop,
        "future_continuations_keys": sorted(result["future_continuations"].keys()),
        "present_survivor": result["present_survivor"],
        "negative_controls": neg,
        "all_negative_controls_break": negatives_ok,
        "GREEN": green,
        "classification": result["classification"],
        "promotion_allowed": result["promotion_allowed"],
        "formal_admission_allowed": result["formal_admission_allowed"],
        "claim_ceiling": result["claim_ceiling"],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if green else 1


if __name__ == "__main__":
    raise SystemExit(main())
