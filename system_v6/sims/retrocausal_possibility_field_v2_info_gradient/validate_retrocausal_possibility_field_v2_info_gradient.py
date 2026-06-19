#!/usr/bin/env python3
"""
Validator for retrocausal_possibility_field_v2_info_gradient.

This validator is written to the v2 HARD ACCEPTANCE bar (the controller will
re-run it fresh). It asserts (and reports):

  1. ALL first-class object keys present in the result JSON and genuinely shaped.
  2. ALL required invariants hold on the canonical instance (incl. the v2
     orientation-emergence invariants and the v1 SHELL_REASSIGNMENT invariant).
  3. The HARD-STOP holds: future_continuations != present_survivor.

  THE v2 ACCEPTANCE -- orientation is EMERGENT, not stipulated:
  4. ORIENTATION IS DERIVED FROM A COMPUTED QUANTITY: the result contains a
     measured per-shell possibility-entropy gradient (net_dI_future_stack) and
     the INWARD/OUTWARD orientation is read off its SIGN, NOT from a constant.
     We assert NO shell carries a shell_orientation string constant.
  5. EMERGENCE DISCRIMINATING CONTROL (reverse): inverting the measured
     information asymmetry FLIPS the derived orientation (future strata go
     INWARD -> UNDIRECTED) and the build REFUSES (no valid emergent inward field).
     If orientation were stipulated this would be unchanged. PASS proves emergent.
  6. EMERGENCE CONTROL (flat): a zero-gradient (equal-count) field shows NO inward
     collapse and the build REFUSES -- orientation needs a measured asymmetry.

  v1 WINS KEPT:
  7. SHELL-REASSIGNMENT MOVES THE SURVIVOR (union identical, branch moved shells).
  8. TRAP#1 (weight permutation) stays PASS.
  9. TRAP#4 (state mutation) stays PASS.
 10. NEGATIVE CONTROLS (v1): (a) flat-union collapse inert; (b) scramble breaks;
     (c) uniform weights break and kill the shell effect.

Exits 0 (green) only if ALL of the above hold.

Run:  <sim-stack python3> validate_retrocausal_possibility_field_v2_info_gradient.py
"""

from __future__ import annotations

import json
import os
import sys

SIM_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SIM_DIR)

import retrocausal_possibility_field_v2_info_gradient as rpf  # noqa: E402


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

    # ---- v2 EMERGENCE shape gates (the orientation is a COMPUTED quantity) ----
    si = result.get("shell_information", {})
    checks["shell_information_is_computed_entropy_per_shell"] = (
        isinstance(si, dict)
        and len(si) >= 2
        and all(isinstance(d.get("info_entropy"), float) for d in si.values())
        and all("branch_count" in d for d in si.values())
    )
    od = result.get("orientation_derivation", {})
    checks["orientation_derivation_reads_a_measured_gradient"] = (
        isinstance(od, dict)
        and "net_dI_future_stack" in od
        and isinstance(od.get("net_dI_future_stack"), float)
        and "forward_steps_toward_present" in od
        and "field_collapses_inward" in od
    )
    so = result.get("shell_orientation_derived", {})
    checks["shell_orientation_is_a_derived_field_not_a_constant_on_shells"] = (
        isinstance(so, dict)
        and len(so) >= 1
        # AND no shell dict carries a hard-coded shell_orientation string
        and all("shell_orientation" not in s for s in result.get("shells", []))
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
    # Build canonical result fresh.
    result = rpf.build_result()

    key_checks = check_keys_present(result)
    invariants = result["invariants"]
    hard_stop = invariants["HARD_STOP_future_continuations_ne_present_survivor"]

    # --- the v1 win, re-derived fresh ---
    reassignment = rpf.shell_reassignment_control()
    shell_reassignment_moves = (
        reassignment["union_identical"] and reassignment["shell_reassignment_moves_survivor"]
    )
    trap1 = rpf.weight_permutation_trap()["weight_permutation_moves_survivor"]
    trap4 = rpf.state_mutation_trap()["state_mutation_moves_survivor"]

    # --- THE v2 ACCEPTANCE: orientation emergence, re-derived fresh ---
    reverse = rpf.emergence_reverse_gradient_control()
    flat_emc = rpf.emergence_flat_gradient_control()

    # the COMPUTED quantity from which orientation is derived
    net_dI = result["orientation_derivation"]["net_dI_future_stack"]
    orientation_from_computed_quantity = (
        isinstance(net_dI, float)
        and abs(net_dI) > 1e-12                      # a real measured asymmetry
        and result["orientation_derivation"]["field_collapses_inward"] is True
        and result["shell_orientation_derived"].get("Sigma_2") == "INWARD"
        and result["shell_orientation_derived"].get("Sigma_1") == "INWARD"
        and result["shell_orientation_derived"].get("Sigma_record") == "OUTWARD"
        # and NO stipulated orientation constant on any shell
        and all("shell_orientation" not in s for s in result["shells"])
    )

    neg = {
        "a_flat_union_collapse_inert": negative_control_a_flat_union_inert(),
        "b_scramble_future_continuations_breaks": negative_control_b_scramble_futures(),
        "c_uniform_weights_break_and_kill_shell_effect": negative_control_c_uniform_weights(),
    }

    keys_ok = all(key_checks.values())
    invariants_ok = all(invariants.values())
    negatives_ok = all(neg.values())
    emergence_ok = (
        orientation_from_computed_quantity
        and reverse["emergence_control_passes"] is True
        and flat_emc["flat_control_passes"] is True
    )

    green = (
        keys_ok
        and invariants_ok
        and hard_stop
        and emergence_ok
        and shell_reassignment_moves
        and trap1
        and trap4
        and negatives_ok
    )

    report = {
        "validator": "validate_retrocausal_possibility_field_v2_info_gradient",
        "first_class_keys_present_in_result": [k for k in FIRST_CLASS_KEYS if k in result],
        "key_shape_checks": key_checks,
        "all_keys_present_and_shaped": keys_ok,
        "invariants": invariants,
        "all_invariants_hold": invariants_ok,
        "HARD_STOP_future_continuations_ne_present_survivor": hard_stop,

        # --- THE v2 ACCEPTANCE: orientation derived from a COMPUTED quantity ---
        "orientation_derived_from_computed_quantity": orientation_from_computed_quantity,
        "computed_net_dI_future_stack": net_dI,
        "derived_orientation": result["shell_orientation_derived"],
        "no_stipulated_orientation_constant_on_any_shell": all(
            "shell_orientation" not in s for s in result["shells"]
        ),

        # --- THE EMERGENCE DISCRIMINATING CONTROLS ---
        "emergence_reverse_control": {
            "orientation_flipped_under_reversal": reverse["orientation_flipped_under_reversal"],
            "base_future_orientation_labels": reverse["base_future_orientation_labels"],
            "reversed_future_orientation_labels": reverse["reversed_future_orientation_labels"],
            "base_field_collapses_inward": reverse["base_field_collapses_inward"],
            "reversed_field_collapses_inward": reverse["reversed_field_collapses_inward"],
            "reversed_build_refused": reverse["reversed_build_refused"],
            "emergence_control_passes": reverse["emergence_control_passes"],
        },
        "emergence_flat_control": {
            "flat_field_collapses_inward": flat_emc["flat_field_collapses_inward"],
            "flat_build_refused": flat_emc["flat_build_refused"],
            "flat_control_passes": flat_emc["flat_control_passes"],
        },
        "orientation_emergence_passes": emergence_ok,

        # --- v1 win kept ---
        "shell_reassignment_moves_survivor": shell_reassignment_moves,
        "shell_reassignment_base_survivor": reassignment["base_present_survivor"],
        "shell_reassignment_reassigned_survivor": reassignment["reassigned_present_survivor"],
        "shell_reassignment_union_identical": reassignment["union_identical"],
        "shell_reassignment_base_inward_path": reassignment["base_inward_path"],
        "shell_reassignment_reassigned_inward_path": reassignment["reassigned_inward_path"],

        # --- traps retained from v0/v1 ---
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
