#!/usr/bin/env python3
"""
Validator for retrocausal_possibility_field_v2_contraction.

Written to the v2 HARD ACCEPTANCE bar (the controller re-runs it fresh). It
RE-DERIVES the emergence claim from the module's functions (it does not merely
read result-JSON booleans), then asserts:

  1. ALL first-class object keys are present in the result JSON and genuinely shaped
     (incl. the new derived_orientation + contraction_ratio fields).
  2. ALL required invariants hold on the canonical instance.
  3. The HARD-STOP holds: future_continuations != present_survivor.

  THE v2 ACCEPTANCE (orientation EMERGENT, not stipulated):
  4. The result JSON contains a COMPUTED quantity (contraction_ratio, a real
     number) from which the INWARD/OUTWARD orientation is DERIVED -- and the
     validator re-derives derive_orientation(contraction_ratio) == direction
     (i.e. the direction is a FUNCTION of the computed scalar, not a constant).
  5. EMERGENCE DISCRIMINATING CONTROL -- re-derived fresh:
       (a) REVERSE the asymmetry (reverse the shell traversal order, x* held
           fixed): the contraction ratio crosses 1 and the DERIVED orientation
           FLIPS INWARD -> OUTWARD.
       (b) REMOVE the asymmetry (radially symmetric field, shells equidistant
           from x*): the contraction ratio == 1 so the DERIVED orientation FAILS
           to UNDEFINED.
     The orientation is genuinely emergent iff (forward INWARD) AND (reversed
     OUTWARD) AND (symmetric UNDEFINED).

  v1 WINS RETAINED (must still pass):
  6. shell-reassignment (union identical) MOVES the present_survivor.
  7. trap #1 (weight permutation) and trap #4 (state mutation) move the survivor.

  NEGATIVE CONTROLS:
  8. (a) flat-union collapse -> shell-reassignment becomes INERT;
     (b) scramble futures -> build breaks;
     (c) uniform weights -> build breaks and shell effect dies;
     (d) remove the OUTWARD record-sink tag -> build breaks.

Exits 0 (green) only if ALL of the above hold.

Run:  <sim-stack python3> validate_retrocausal_possibility_field_v2_contraction.py
"""

from __future__ import annotations

import json
import math
import os
import sys

SIM_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SIM_DIR)

import retrocausal_possibility_field_v2_contraction as rpf  # noqa: E402


FIRST_CLASS_KEYS = rpf.FIRST_CLASS_KEYS


def check_keys_present(result: dict) -> dict:
    """Each first-class key present AND genuinely shaped (not a degenerate proxy)."""
    checks = {}
    for k in FIRST_CLASS_KEYS:
        checks[f"key_present:{k}"] = k in result

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
    # v2: orientation is DERIVED -- the direction_source must say so, and the
    # contraction is a real-number sequence (NOT a hardcoded literal label).
    checks["orientation_source_is_derived"] = (
        cm.get("direction_source") == "DERIVED_FROM_CONTRACTION_RATIO"
        and result.get("orientation_source") == "DERIVED_FROM_CONTRACTION_RATIO"
    )
    cr = result.get("contraction_ratio")
    checks["contraction_ratio_is_real_number"] = isinstance(cr, float) and math.isfinite(cr)
    contraction = cm.get("contraction", {})
    checks["contraction_has_distance_sequence"] = (
        isinstance(contraction, dict)
        and isinstance(contraction.get("mean_distance_sequence"), list)
        and len(contraction.get("mean_distance_sequence", [])) >= 2
    )
    rec = result.get("outward_record", {})
    checks["outward_record_is_outward_hash_chain"] = (
        isinstance(rec, dict)
        and rec.get("record_orientation") == "OUTWARD"
        and bool(rec.get("append_only_recomputed"))
        and bool(rec.get("reflects_per_shell_compression_steps"))
        and bool(rec.get("binds_contraction_trace"))
    )
    return checks


def rederive_orientation_is_a_function_of_the_scalar(result: dict) -> bool:
    """The CORE v2 check: prove the direction is a FUNCTION of the computed
    contraction_ratio, not a constant. We feed the result's own contraction_ratio
    through derive_orientation and require it to reproduce the reported direction;
    and we independently confirm that a ratio>1 fed to the SAME function yields
    OUTWARD (so the function genuinely discriminates, it is not a constant
    returning INWARD)."""
    cr = result["contraction_ratio"]
    reported = result["compression_map"]["direction"]
    rederived = rpf.derive_orientation(cr)
    function_reproduces = (rederived == reported)
    # the function is not a constant: a synthetic ratio > 1 must give OUTWARD,
    # a synthetic ratio == 1 must give UNDEFINED.
    function_discriminates = (
        rpf.derive_orientation(2.0) == "OUTWARD"
        and rpf.derive_orientation(1.0) == "UNDEFINED"
        and rpf.derive_orientation(0.5) == "INWARD"
    )
    return function_reproduces and function_discriminates


def rederive_emergence() -> dict:
    """Re-derive the emergence discriminating control from scratch (do not read the
    result JSON). Returns the three derived orientations and the verdict."""
    em = rpf.emergence_discriminating_control()
    return {
        "forward": em["forward_derived_orientation"],
        "reversed": em["reversed_derived_orientation"],
        "symmetric": em["symmetric_derived_orientation"],
        "forward_ratio": em["forward_contraction_ratio"],
        "reversed_ratio": em["reversed_contraction_ratio"],
        "symmetric_ratio": em["symmetric_contraction_ratio_to_b3"],
        "flips_under_reversal": em["orientation_flips_under_reversal"],
        "undefined_when_symmetric": em["orientation_undefined_when_symmetric"],
        "is_emergent": em["orientation_is_emergent"],
    }


def negative_control_a_flat_union_inert() -> bool:
    return rpf.flat_union_negative_control()["flat_union_control_correctly_inert"] is True


def negative_control_b_scramble_futures() -> bool:
    return rpf.scramble_futures_negative_control()["control_breaks"] is True


def negative_control_c_uniform_weights() -> bool:
    u = rpf.uniform_weights_negative_control()
    return (u["control_breaks"] is True) and (u["uniform_correctly_kills_shell_effect"] is True)


def negative_control_d_orientation_removal() -> bool:
    return rpf.orientation_removal_negative_control()["build_breaks"] is True


def main() -> int:
    result = rpf.build_result()

    key_checks = check_keys_present(result)
    invariants = result["invariants"]
    hard_stop = invariants["HARD_STOP_future_continuations_ne_present_survivor"]

    # v2 core: orientation is a function of the computed scalar
    orientation_is_function_of_scalar = rederive_orientation_is_a_function_of_the_scalar(result)

    # v2 emergence: re-derived fresh
    em = rederive_emergence()
    emergence_ok = (
        em["forward"] == "INWARD"
        and em["reversed"] == "OUTWARD"
        and em["symmetric"] == "UNDEFINED"
        and em["flips_under_reversal"]
        and em["undefined_when_symmetric"]
        and em["is_emergent"]
    )

    # v1 wins
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
        "d_orientation_removal_breaks_build": negative_control_d_orientation_removal(),
    }

    keys_ok = all(key_checks.values())
    invariants_ok = all(invariants.values())
    negatives_ok = all(neg.values())

    green = (
        keys_ok
        and invariants_ok
        and hard_stop
        and orientation_is_function_of_scalar
        and emergence_ok
        and shell_reassignment_moves
        and trap1
        and trap4
        and negatives_ok
    )

    report = {
        "validator": "validate_retrocausal_possibility_field_v2_contraction",
        "first_class_keys_present_in_result": [k for k in FIRST_CLASS_KEYS if k in result],
        "key_shape_checks": key_checks,
        "all_keys_present_and_shaped": keys_ok,
        "invariants": invariants,
        "all_invariants_hold": invariants_ok,
        "HARD_STOP_future_continuations_ne_present_survivor": hard_stop,

        # --- THE v2 AUDITED GAP, NOW FIXED: orientation EMERGENT ---
        "computed_quantity_contraction_ratio": result["contraction_ratio"],
        "derived_orientation": result["derived_orientation"],
        "orientation_is_a_function_of_the_computed_scalar": orientation_is_function_of_scalar,
        "emergence_forward_orientation": em["forward"],
        "emergence_reversed_orientation": em["reversed"],
        "emergence_symmetric_orientation": em["symmetric"],
        "emergence_forward_ratio": em["forward_ratio"],
        "emergence_reversed_ratio": em["reversed_ratio"],
        "emergence_symmetric_ratio": em["symmetric_ratio"],
        "ORIENTATION_FLIPS_UNDER_REVERSAL": em["flips_under_reversal"],
        "ORIENTATION_FAILS_WHEN_SYMMETRIC": em["undefined_when_symmetric"],
        "ORIENTATION_IS_EMERGENT": emergence_ok,

        # --- v1 wins retained ---
        "shell_reassignment_moves_survivor": shell_reassignment_moves,
        "shell_reassignment_base_survivor": reassignment["base_present_survivor"],
        "shell_reassignment_reassigned_survivor": reassignment["reassigned_present_survivor"],
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
