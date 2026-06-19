#!/usr/bin/env python3
"""
Validator for retrocausal_possibility_field_v1.

This validator is written to the v1 HARD ACCEPTANCE bar (the controller will
re-run it fresh). It asserts (and reports):

  1. ALL first-class object keys are present in the result JSON and genuinely shaped.
  2. ALL required invariants hold on the canonical instance (incl. the v1
     SHELL_REASSIGNMENT_MOVES_SURVIVOR invariant and compression_is_multi_step_traversal).
  3. The HARD-STOP holds: future_continuations != present_survivor.

  THE v1 ACCEPTANCE CONTROLS:
  4. TRAP#2/#5 FLIPS TO PASS: a shell-reassignment that keeps the union of
     branches identical but moves a branch to a different shell MOVES the
     present_survivor. Reported as shell_reassignment_moves_survivor=true with the
     two survivors shown.
  5. TRAP#1 (weight permutation) stays PASS: permuting compatibility_weights moves
     the survivor.
  6. TRAP#4 (state mutation) stays PASS: mutating a branch feature moves the survivor.
  7. NEGATIVE CONTROLS:
       (a) collapse the shell-traversal to a flat union argmax -> the
           shell-reassignment control then FAILS to move the survivor (proving the
           traversal is what carries the shell-ordering effect).
       (b) scramble future_continuations -> the build BREAKS.
       (c) uniform weights -> the build BREAKS and the shell effect dies.

Exits 0 (green) only if ALL of the above hold.

Run:  <sim-stack python3> validate_retrocausal_possibility_field_v1.py
"""

from __future__ import annotations

import json
import os
import sys

SIM_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SIM_DIR)

import retrocausal_possibility_field_v1 as rpf  # noqa: E402


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
    checks["compression_map_is_inward_shell_traversal"] = (
        isinstance(cm, dict)
        and cm.get("direction") == "INWARD"
        and "traversal_steps" in cm
        and isinstance(cm.get("shell_traversal_order"), list)
        and len([s for s in cm.get("traversal_steps", []) if s.get("branches_on_shell")]) >= 2
    )
    rec = result.get("outward_record", {})
    checks["outward_record_is_outward_hash_chain"] = (
        isinstance(rec, dict)
        and rec.get("record_orientation") == "OUTWARD"
        and bool(rec.get("append_only_recomputed"))
        and bool(rec.get("reflects_per_shell_compression_steps"))
    )
    return checks


def negative_control_a_flat_union_inert() -> bool:
    """
    (a) Collapse the shell-traversal to the flat union argmax (v0 mechanism).
    Under the flat mechanism the shell-reassignment (union identical) must FAIL
    to move the survivor. Returns True iff the flat control is correctly INERT
    (does NOT move the survivor) -- proving the traversal carries the effect.
    """
    flat = rpf.flat_union_negative_control()
    return flat["flat_union_control_correctly_inert"] is True


def negative_control_b_scramble_futures() -> bool:
    """
    (b) Scramble future_continuations: 1 distinct branch per shell -> build breaks.
    Returns True iff the control BREAKS the result.
    """
    return rpf.scramble_futures_negative_control()["control_breaks"] is True


def negative_control_c_uniform_weights() -> bool:
    """
    (c) Uniform weights: the build breaks (non-uniformity invariant fails) AND
    the shell effect dies. Returns True iff BOTH hold.
    """
    u = rpf.uniform_weights_negative_control()
    return (u["control_breaks"] is True) and (u["uniform_correctly_kills_shell_effect"] is True)


def main() -> int:
    # Build canonical result fresh.
    result = rpf.build_result()

    key_checks = check_keys_present(result)
    invariants = result["invariants"]
    hard_stop = invariants["HARD_STOP_future_continuations_ne_present_survivor"]

    # --- the v1 acceptance controls (re-derived fresh, not just read) ---
    reassignment = rpf.shell_reassignment_control()
    shell_reassignment_moves = (
        reassignment["union_identical"] and reassignment["shell_reassignment_moves_survivor"]
    )
    trap1 = rpf.weight_permutation_trap()["weight_permutation_moves_survivor"]
    trap4 = rpf.state_mutation_trap()["state_mutation_moves_survivor"]

    neg = {
        "a_flat_union_collapse_inert": negative_control_a_flat_union_inert(),
        "b_scramble_future_continuations_breaks": negative_control_b_scramble_futures(),
        "c_uniform_weights_break_and_kill_shell_effect": negative_control_c_uniform_weights(),
    }

    keys_ok = all(key_checks.values())
    invariants_ok = all(invariants.values())
    negatives_ok = all(neg.values())

    green = (
        keys_ok
        and invariants_ok
        and hard_stop
        and shell_reassignment_moves
        and trap1
        and trap4
        and negatives_ok
    )

    report = {
        "validator": "validate_retrocausal_possibility_field_v1",
        "first_class_keys_present_in_result": [k for k in FIRST_CLASS_KEYS if k in result],
        "key_shape_checks": key_checks,
        "all_keys_present_and_shaped": keys_ok,
        "invariants": invariants,
        "all_invariants_hold": invariants_ok,
        "HARD_STOP_future_continuations_ne_present_survivor": hard_stop,

        # --- THE AUDITED GAP, NOW FIXED ---
        "shell_reassignment_moves_survivor": shell_reassignment_moves,
        "shell_reassignment_base_survivor": reassignment["base_present_survivor"],
        "shell_reassignment_reassigned_survivor": reassignment["reassigned_present_survivor"],
        "shell_reassignment_union_identical": reassignment["union_identical"],
        "shell_reassignment_base_inward_path": reassignment["base_inward_path"],
        "shell_reassignment_reassigned_inward_path": reassignment["reassigned_inward_path"],

        # --- traps retained from v0 ---
        "trap_1_weight_permutation_moves_survivor": trap1,
        "trap_4_state_mutation_moves_survivor": trap4,

        "negative_controls": neg,
        "all_negative_controls_ok": negatives_ok,

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
