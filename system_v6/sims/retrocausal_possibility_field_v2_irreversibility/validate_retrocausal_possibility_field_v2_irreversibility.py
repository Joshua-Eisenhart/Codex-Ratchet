#!/usr/bin/env python3
"""
Validator for retrocausal_possibility_field_v2_irreversibility.

Written to the v2 HARD ACCEPTANCE bar (the controller re-runs it fresh). It
asserts (and reports):

  1. ALL first-class object keys present in the result JSON and genuinely shaped.
  2. ALL required invariants hold on the canonical instance (incl. the v2
     orientation-derivation invariants and the v1 SHELL_REASSIGNMENT_MOVES_SURVIVOR).
  3. The HARD-STOP holds: future_continuations != present_survivor.

  THE v2 HARD ACCEPTANCE (orientation EMERGENT from compression irreversibility):
  4. The result JSON contains a COMPUTED quantity (per-stratum fan_in/fan_out and
     injective/many_to_one) from which the INWARD/OUTWARD orientation is DERIVED --
     NOT read from a constant. The validator re-derives the orientation from those
     measured quantities and asserts it MATCHES the stored shell_orientation.
  5. NO shell dict in the result carries a stipulated "shell_orientation" string.
  6. THE EMERGENCE DISCRIMINATING CONTROL: reversing the measured asymmetry FLIPS
     the derived orientation, in BOTH directions:
       (i)  an inward (many-to-one) stratum made injective derives OUTWARD instead
            of INWARD;
       (ii) the record (injective) stratum made many-to-one derives INWARD instead
            of OUTWARD (end-to-end: a full rebuild flips the instance label).
     The validator independently re-derives both flips from measure_irreversibility,
     proving the orientation is not stipulated.

  THE v1 WINS (must STILL hold):
  7. shell-reassignment (union identical) MOVES the present_survivor.
  8. trap #1 (weight permutation) and trap #4 (state mutation) move the survivor.
  9. NEGATIVE CONTROLS: (a) flat-union collapse inert; (b) scramble breaks;
     (c) uniform weights break + kill the shell effect.
 10. hard-stop fc != survivor.

Exits 0 (green) only if ALL of the above hold.

Run:  <sim-stack python3> validate_retrocausal_possibility_field_v2_irreversibility.py
"""

from __future__ import annotations

import json
import os
import sys

SIM_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SIM_DIR)

import retrocausal_possibility_field_v2_irreversibility as rpf  # noqa: E402


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
    rec = result.get("outward_record", {})
    checks["outward_record_is_outward_hash_chain"] = (
        isinstance(rec, dict)
        and rec.get("record_orientation") == "OUTWARD"
        and bool(rec.get("append_only_recomputed"))
        and bool(rec.get("reflects_per_shell_compression_steps"))
    )
    return checks


def check_orientation_is_derived_not_stored(result: dict) -> dict:
    """
    THE v2 CORE CHECK. Independently re-derive the orientation from the COMPUTED
    irreversibility quantities in the result JSON and assert it matches the stored
    shell_orientation. Also assert NO shell carries a stipulated orientation string.
    """
    checks: dict[str, bool] = {}

    shells = result.get("shells", [])
    checks["no_shell_carries_stipulated_orientation_string"] = all(
        "shell_orientation" not in s for s in shells
    )

    shell_orientation = result.get("shell_orientation", {})
    cm = result.get("compression_map", {})
    rec = result.get("outward_record", {})

    # Re-derive each inward stratum's orientation from its stored fan_in/fan_out and
    # assert it equals the recorded derived orientation AND the instance label.
    inward_ok = True
    nonempty = [s for s in cm.get("traversal_steps", []) if s.get("branches_on_shell")]
    if len(nonempty) < 2:
        inward_ok = False
    for s in nonempty:
        irr = s.get("irreversibility", {})
        rederived = rpf.derive_orientation(irr)
        # the measured asymmetry must actually be many-to-one for the canonical run
        if not (irr.get("fan_in", 0) > irr.get("fan_out", 0)):
            inward_ok = False
        if rederived != "INWARD":
            inward_ok = False
        if rederived != s.get("derived_orientation"):
            inward_ok = False
        if rederived != shell_orientation.get(s["shell_id"]):
            inward_ok = False
    checks["inward_orientation_rederived_from_fan_in_fan_out_matches"] = inward_ok

    # Re-derive the record stratum orientation from its measured injectivity.
    rec_irr = rec.get("record_irreversibility", {})
    rec_rederived = rpf.derive_orientation(rec_irr)
    record_ok = (
        rec_irr.get("fan_in") == rec_irr.get("fan_out")
        and bool(rec_irr.get("injective"))
        and rec_rederived == "OUTWARD"
        and rec_rederived == rec.get("record_orientation")
        and rec_rederived == shell_orientation.get(rec.get("record_shell_id"))
    )
    checks["record_orientation_rederived_from_injectivity_matches"] = record_ok

    # The result must explicitly flag the derivation provenance.
    checks["compression_flags_direction_is_derived"] = bool(
        cm.get("direction_is_derived_from_irreversibility")
    )
    checks["record_flags_orientation_is_derived"] = bool(
        rec.get("record_orientation_is_derived_from_irreversibility")
    )
    return checks


def check_emergence_control_independently() -> dict:
    """
    Independently RE-RUN the emergence discriminating control via the sim's
    derive_orientation, NOT just read the stored boolean. Reverse the measured
    asymmetry in both directions and assert the derived label flips.
    """
    checks: dict[str, bool] = {}

    base = rpf.build_object_instance()

    # (i) inward stratum: actual many-to-one derives INWARD; injective derives OUTWARD
    sample = [s for s in base["compression_map"]["traversal_steps"] if s["branches_on_shell"]][0]
    actual_inward = rpf.derive_orientation(rpf.measure_irreversibility(sample["stratum_map"]))
    injective_map = {b: f"img_{b}" for b in sample["branches_on_shell"]}
    reversed_inward = rpf.derive_orientation(rpf.measure_irreversibility(injective_map))
    checks["inward_actual_derives_INWARD"] = actual_inward == "INWARD"
    checks["inward_reversed_injective_derives_OUTWARD"] = reversed_inward == "OUTWARD"
    checks["inward_orientation_flips_under_reversal"] = (
        actual_inward == "INWARD" and reversed_inward == "OUTWARD"
    )

    # (ii) record stratum: actual injective derives OUTWARD; collapsed derives INWARD
    actual_record = rpf.derive_orientation(
        rpf.measure_irreversibility(base["outward_record"]["record_map"])
    )
    domain = sorted(base["outward_record"]["record_map"].keys())
    collapsed = {ev: "one_image" for ev in domain}
    reversed_record = rpf.derive_orientation(rpf.measure_irreversibility(collapsed))
    checks["record_actual_derives_OUTWARD"] = actual_record == "OUTWARD"
    checks["record_reversed_collapsed_derives_INWARD"] = reversed_record == "INWARD"
    checks["record_orientation_flips_under_reversal"] = (
        actual_record == "OUTWARD" and reversed_record == "INWARD"
    )

    # (iii) end-to-end: rebuild the whole instance with the collapsed record map and
    # confirm the instance-level record orientation flips OUTWARD -> INWARD.
    record_shell_id = base["outward_record"]["record_shell_id"]
    reversed_instance = rpf.build_object_instance(record_map_override=collapsed)
    checks["record_flips_end_to_end_full_rebuild"] = (
        base["shell_orientation"][record_shell_id] == "OUTWARD"
        and reversed_instance["shell_orientation"][record_shell_id] == "INWARD"
    )
    return checks


def negative_control_a_flat_union_inert() -> bool:
    flat = rpf.flat_union_negative_control()
    return flat["flat_union_control_correctly_inert"] is True


def negative_control_b_scramble_futures() -> bool:
    return rpf.scramble_futures_negative_control()["control_breaks"] is True


def negative_control_c_uniform_weights() -> bool:
    u = rpf.uniform_weights_negative_control()
    return (u["control_breaks"] is True) and (u["uniform_correctly_kills_shell_effect"] is True)


def main() -> int:
    result = rpf.build_result()

    key_checks = check_keys_present(result)
    derivation_checks = check_orientation_is_derived_not_stored(result)
    emergence_checks = check_emergence_control_independently()

    invariants = result["invariants"]
    hard_stop = invariants["HARD_STOP_future_continuations_ne_present_survivor"]

    # v1 wins, re-derived fresh
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
    derivation_ok = all(derivation_checks.values())
    emergence_ok = all(emergence_checks.values())
    invariants_ok = all(invariants.values())
    negatives_ok = all(neg.values())

    green = (
        keys_ok
        and derivation_ok
        and emergence_ok
        and invariants_ok
        and hard_stop
        and shell_reassignment_moves
        and trap1
        and trap4
        and negatives_ok
    )

    report = {
        "validator": "validate_retrocausal_possibility_field_v2_irreversibility",
        "first_class_keys_present_in_result": [k for k in FIRST_CLASS_KEYS if k in result],
        "key_shape_checks": key_checks,
        "all_keys_present_and_shaped": keys_ok,

        # --- THE v2 CORE: orientation derived, not stored ---
        "orientation_derivation_checks": derivation_checks,
        "orientation_is_derived_not_stored": derivation_ok,
        "computed_irreversibility": result["computed_irreversibility"],

        # --- THE v2 EMERGENCE DISCRIMINATING CONTROL (re-derived fresh) ---
        "emergence_control_checks": emergence_checks,
        "orientation_is_emergent_reversal_flips_label": emergence_ok,

        "invariants": invariants,
        "all_invariants_hold": invariants_ok,
        "HARD_STOP_future_continuations_ne_present_survivor": hard_stop,

        # --- v1 wins retained ---
        "shell_reassignment_moves_survivor": shell_reassignment_moves,
        "shell_reassignment_base_survivor": reassignment["base_present_survivor"],
        "shell_reassignment_reassigned_survivor": reassignment["reassigned_present_survivor"],
        "shell_reassignment_union_identical": reassignment["union_identical"],
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
