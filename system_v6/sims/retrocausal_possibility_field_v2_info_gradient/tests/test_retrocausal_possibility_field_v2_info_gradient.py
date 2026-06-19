#!/usr/bin/env python3
"""
Tests for retrocausal_possibility_field_v2_info_gradient -- positive + negative
+ boundary.

Focus of v2 (the audited gap): the SHELL ORIENTATION (INWARD/OUTWARD) is now
EMERGENT from a MEASURED per-shell possibility-entropy gradient, not a stipulated
string constant. The discriminating test is the reverse-gradient emergence
control (invert the possibility profile -> the derived orientation FLIPS and the
build refuses), plus the flat-gradient control (zero gradient -> no inward
direction emerges). v1's wins (shell-reassignment moves survivor; traps #1/#4;
hard-stop) must STILL pass.

Run:  <sim-stack python3> tests/test_retrocausal_possibility_field_v2_info_gradient.py
Exits 0 only if every test passes.
"""

from __future__ import annotations

import json
import math
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.dirname(TESTS_DIR)
sys.path.insert(0, SIM_DIR)

import retrocausal_possibility_field_v2_info_gradient as rpf  # noqa: E402


FAILURES: list[str] = []


def check(name: str, cond: bool) -> None:
    status = "PASS" if cond else "FAIL"
    if not cond:
        FAILURES.append(name)
    print(f"[{status}] {name}")


# =====================================================================
# POSITIVE tests -- object instantiates; orientation is EMERGENT
# =====================================================================

def positive_tests() -> None:
    print("\n=== POSITIVE (object field instantiation + EMERGENT orientation) ===")
    result = rpf.build_result()

    for k in rpf.FIRST_CLASS_KEYS:
        check(f"positive: first-class key present -> {k}", k in result)

    fc = result["future_continuations"]
    check("positive: future_continuations is a dict", isinstance(fc, dict))
    check(
        "positive: each shell carries a LIST of >=2 distinct branches",
        all(isinstance(v, list) and len(set(v)) >= 2 for v in fc.values()),
    )

    cw = result["compatibility_weights"]
    check("positive: compatibility_weights over PAIRS (keys 'bi|bj')", all("|" in k for k in cw))
    check("positive: compatibility_weights non-uniform", len(set(round(v, 12) for v in cw.values())) >= 2)

    # ---- THE v2 CORE: orientation is COMPUTED, not stipulated ----
    si = result["shell_information"]
    check("positive: per-shell possibility-entropy is computed (floats)",
          all(isinstance(d["info_entropy"], float) for d in si.values()))
    # the outer future stratum has MORE possibility than the inner (decreasing profile)
    check("positive: outer future stratum has higher info than inner (decreasing profile)",
          si["Sigma_2"]["info_entropy"] > si["Sigma_1"]["info_entropy"])
    # entropy equals log2(count)
    check("positive: info_entropy == log2(branch_count) for Sigma_2",
          abs(si["Sigma_2"]["info_entropy"] - math.log2(si["Sigma_2"]["branch_count"])) < 1e-12)

    od = result["orientation_derivation"]
    check("positive: measured net_dI_future_stack is negative (possibilities collapse inward)",
          od["net_dI_future_stack"] < -1e-12)
    check("positive: field_collapses_inward is True (by the measured gradient)",
          od["field_collapses_inward"] is True)

    so = result["shell_orientation_derived"]
    check("positive: Sigma_2 derived INWARD", so.get("Sigma_2") == "INWARD")
    check("positive: Sigma_1 derived INWARD", so.get("Sigma_1") == "INWARD")
    check("positive: Sigma_record derived OUTWARD", so.get("Sigma_record") == "OUTWARD")

    # NO shell carries a stipulated shell_orientation constant
    check("positive: NO shell carries a stipulated shell_orientation string constant",
          all("shell_orientation" not in s for s in result["shells"]))

    cm = result["compression_map"]
    check("positive: compression_map direction INWARD", cm["direction"] == "INWARD")
    check("positive: compression_map marks direction emergent", cm.get("direction_is_emergent") is True)
    nonempty = [s for s in cm["traversal_steps"] if s["branches_on_shell"]]
    check("positive: compression_map is a MULTI-STEP traversal (>=2 non-empty shells)", len(nonempty) >= 2)

    ps = result["present_survivor"]
    check("positive: present_survivor is a single branch id", isinstance(ps, str) and ps in rpf.BRANCH_STATES)
    check("positive: present_survivor derived (final selected anchor of the traversal)",
          ps == cm["present_survivor"] and ps == nonempty[-1]["selected_anchor"])

    rec = result["outward_record"]
    check("positive: outward_record orientation OUTWARD (derived)", rec["record_orientation"] == "OUTWARD")
    check("positive: outward_record orientation marked derived", rec.get("record_orientation_is_derived") is True)
    check("positive: outward_record hash-chain recomputes", rec["append_only_recomputed"] is True)
    check("positive: outward_record binds the present survivor", rec["binds_present_survivor"] == ps)
    check("positive: outward_record has one entry per traversal step",
          len(rec["record_entries"]) == len(cm["traversal_steps"]))

    # v1 win kept: shell-reassignment moves the survivor
    check("positive: shell_reassignment_moves_survivor (v1 win kept)",
          result["shell_reassignment_moves_survivor"] is True)

    # the v2 acceptance flag
    check("positive: orientation_emergence_passes (the v2 fix)",
          result["orientation_emergence_passes"] is True)

    check("positive: all invariants hold", result["all_invariants_hold"] is True)
    check("positive: classification scratch_diagnostic", result["classification"] == "scratch_diagnostic")
    check("positive: promotion_allowed false", result["promotion_allowed"] is False)
    check("positive: formal_admission_allowed false", result["formal_admission_allowed"] is False)


# =====================================================================
# NEGATIVE / EMERGENCE-DISCRIMINATING tests
# =====================================================================

def negative_tests() -> None:
    print("\n=== NEGATIVE / EMERGENCE-DISCRIMINATING controls ===")

    # HARD-STOP
    inst = rpf.build_object_instance()
    inv = rpf.check_invariants(inst)
    check("hard-stop holds (future_continuations != present_survivor)",
          inv["HARD_STOP_future_continuations_ne_present_survivor"] is True)

    # ---- THE PRIMARY EMERGENCE DISCRIMINATING CONTROL: reverse the gradient ----
    rev = rpf.emergence_reverse_gradient_control()
    check("emergence (reverse): base field collapses inward",
          rev["base_field_collapses_inward"] is True)
    check("emergence (reverse): REVERSED field does NOT collapse inward",
          rev["reversed_field_collapses_inward"] is False)
    check("emergence (reverse): derived orientation FLIPS under reversal (INWARD -> UNDIRECTED)",
          rev["orientation_flipped_under_reversal"] is True
          and rev["reversed_future_orientation_labels"] != rev["base_future_orientation_labels"])
    check("emergence (reverse): reversed-profile build REFUSES (no valid emergent inward field)",
          rev["reversed_build_refused"] is True)
    check("emergence (reverse): the discriminating control PASSES (orientation is emergent)",
          rev["emergence_control_passes"] is True)

    # ---- SECONDARY EMERGENCE CONTROL: flat gradient ----
    flat = rpf.emergence_flat_gradient_control()
    check("emergence (flat): zero-gradient field does NOT collapse inward",
          flat["flat_field_collapses_inward"] is False)
    check("emergence (flat): flat-profile build REFUSES",
          flat["flat_build_refused"] is True)
    check("emergence (flat): the flat control PASSES", flat["flat_control_passes"] is True)

    # ---- v1 negative controls (must still behave) ----
    fl = rpf.flat_union_negative_control()
    check("negative (a): flat-union collapse is INERT (does NOT move survivor)",
          fl["flat_union_control_correctly_inert"] is True)
    scr = rpf.scramble_futures_negative_control()
    check("negative (b): scramble future_continuations breaks", scr["control_breaks"] is True)
    uni = rpf.uniform_weights_negative_control()
    check("negative (c): uniform weights break the build", uni["control_breaks"] is True)
    check("negative (c): uniform weights KILL the shell-reassignment effect",
          uni["uniform_correctly_kills_shell_effect"] is True)


# =====================================================================
# TRAP tests -- v0/v1 traps must STILL pass (no regression)
# =====================================================================

def trap_tests() -> None:
    print("\n=== TRAPS retained from v0/v1 (must still pass) ===")
    t1 = rpf.weight_permutation_trap()
    check("trap #1: weight permutation moves the survivor", t1["weight_permutation_moves_survivor"] is True)
    print(f"     (weight perm: {t1['base_survivor']} -> {t1['permuted_survivor']})")
    t4 = rpf.state_mutation_trap()
    check("trap #4: state mutation moves the survivor", t4["state_mutation_moves_survivor"] is True)
    print(f"     (state mut: {t4['base_survivor']} -> {t4['mutated_survivor']})")
    # the carrier was restored cleanly (no leak from the trap)
    check("trap #4: carrier restored after mutation (no leak)",
          rpf.BRANCH_STATES["b3"] == {"a": 1, "b": 1})


# =====================================================================
# BOUNDARY tests -- thin edges of the gradient / orientation derivation
# =====================================================================

def boundary_tests() -> None:
    print("\n=== BOUNDARY (thin edges of the gradient) ===")

    # Boundary: minimal NON-trivial gradient -- outer 3 vs inner 2 is the
    # canonical decreasing profile; a 2-vs-1 profile would break the >=2-distinct
    # invariant, so the minimal emergent-inward field needs outer>=3, inner>=2.
    # Confirm a 3-vs-2 field is the boundary that just collapses inward.
    minimal = {"Sigma_2": ["b0", "b1", "b5"], "Sigma_1": ["b2", "b3"]}
    inst_min = rpf.build_object_instance(future_continuations=minimal)
    od = inst_min["orientation_derivation"]
    check("boundary: minimal 3-vs-2 decreasing profile collapses inward",
          od["field_collapses_inward"] is True)
    check("boundary: minimal profile net_dI == log2(2) - log2(3) (the measured step)",
          abs(od["net_dI_future_stack"] - (math.log2(2) - math.log2(3))) < 1e-12)

    # Boundary: a STRICTLY-INCREASING profile (inner > outer) must NOT collapse
    # inward (orientation cannot emerge) -- the build must refuse.
    increasing = {"Sigma_2": ["b0", "b1"], "Sigma_1": ["b2", "b3", "b4"]}
    refused = False
    try:
        rpf.build_object_instance(future_continuations=increasing)
    except StopIteration:
        refused = True
    inc_orient = rpf.derive_orientation_from_gradient(
        rpf.compute_shell_information(rpf.SHELLS, increasing, present_survivor=None)
    )
    check("boundary: strictly-increasing profile does NOT collapse inward",
          inc_orient["field_collapses_inward"] is False)
    check("boundary: strictly-increasing profile build refuses", refused is True)

    # Boundary: possibility_entropy of a single branch is 0.0 (a committed survivor)
    check("boundary: possibility_entropy(['bX']) == 0.0 (committed, no possibility)",
          abs(rpf.possibility_entropy(["b0"]) - 0.0) < 1e-12)
    check("boundary: possibility_entropy of 4 distinct branches == 2.0",
          abs(rpf.possibility_entropy(["b0", "b1", "b2", "b3"]) - 2.0) < 1e-12)
    # duplicates do not inflate the count
    check("boundary: possibility_entropy counts DISTINCT branches only",
          abs(rpf.possibility_entropy(["b0", "b0", "b1"]) - 1.0) < 1e-12)

    # Boundary: present_survivor is always a scalar id, never a list/count
    check("boundary: present_survivor is a scalar id", isinstance(inst_min["present_survivor"], str))


def main() -> int:
    positive_tests()
    negative_tests()
    trap_tests()
    boundary_tests()
    print("\n=== SUMMARY ===")
    if FAILURES:
        print(json.dumps({"green": False, "failures": FAILURES}, indent=2))
        return 1
    print(json.dumps({"green": True, "failures": []}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
