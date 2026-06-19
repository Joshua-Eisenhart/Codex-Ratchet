#!/usr/bin/env python3
"""
Tests for retrocausal_possibility_field_v2_contraction -- positive + negative +
boundary + traps.

Focus of v2 (the audited gap): the SHELL ORIENTATION (INWARD / OUTWARD) is now
EMERGENT from a computed contraction ratio, not a STIPULATED string label. The
discriminating tests are:
  - orientation is a FUNCTION of the computed contraction_ratio scalar;
  - REVERSING the traversal order FLIPS the derived orientation INWARD->OUTWARD;
  - REMOVING the asymmetry (symmetric field) FAILS the orientation to UNDEFINED;
  - the NON-TAUTOLOGY boundary: the forward (radius-descending) traversal can
    derive OUTWARD/UNDEFINED for other fields (so INWARD is not forced by code).
Plus all of v1's wins must still pass (shell-reassignment moves the survivor,
traps #1/#4, hard-stop).

Run:  <sim-stack python3> tests/test_retrocausal_possibility_field_v2_contraction.py
Exits 0 only if every test passes.
"""

from __future__ import annotations

import itertools
import json
import math
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.dirname(TESTS_DIR)
sys.path.insert(0, SIM_DIR)

import retrocausal_possibility_field_v2_contraction as rpf  # noqa: E402


FAILURES: list[str] = []


def check(name: str, cond: bool) -> None:
    status = "PASS" if cond else "FAIL"
    if not cond:
        FAILURES.append(name)
    print(f"[{status}] {name}")


# =====================================================================
# POSITIVE tests -- object instantiates; orientation is DERIVED and emergent
# =====================================================================

def positive_tests() -> None:
    print("\n=== POSITIVE (object field instantiation + emergent orientation) ===")
    result = rpf.build_result()

    for k in rpf.FIRST_CLASS_KEYS:
        check(f"positive: first-class key present -> {k}", k in result)

    fc = result["future_continuations"]
    check("positive: future_continuations is a dict", isinstance(fc, dict))
    check("positive: each shell carries a LIST of >=2 distinct branches",
          all(isinstance(v, list) and len(set(v)) >= 2 for v in fc.values()))

    cw = result["compatibility_weights"]
    check("positive: compatibility_weights over PAIRS (keys 'bi|bj')", all("|" in k for k in cw))
    check("positive: compatibility_weights non-uniform", len(set(round(v, 12) for v in cw.values())) >= 2)

    cm = result["compression_map"]
    # v2: the direction is DERIVED, not a constant.
    check("positive: direction_source is DERIVED_FROM_CONTRACTION_RATIO",
          cm["direction_source"] == "DERIVED_FROM_CONTRACTION_RATIO")
    check("positive: canonical derived direction is INWARD (field contracts)", cm["direction"] == "INWARD")
    cr = result["contraction_ratio"]
    check("positive: contraction_ratio is a real finite number", isinstance(cr, float) and math.isfinite(cr))
    check("positive: canonical contraction_ratio < 1 (genuine contraction)", cr < 1.0)
    check("positive: contraction has a >=2-length mean-distance sequence",
          len(cm["contraction"]["mean_distance_sequence"]) >= 2)

    # the CORE v2 property: orientation is derive_orientation(contraction_ratio)
    check("positive: orientation reproduced by derive_orientation(contraction_ratio)",
          rpf.derive_orientation(cr) == cm["direction"])
    # the function genuinely discriminates (it is not a constant)
    check("positive: derive_orientation discriminates (>1->OUTWARD, ==1->UNDEFINED, <1->INWARD)",
          rpf.derive_orientation(2.0) == "OUTWARD"
          and rpf.derive_orientation(1.0) == "UNDEFINED"
          and rpf.derive_orientation(0.5) == "INWARD")

    # the emergence discriminating control verdict
    em = result["emergence_discriminating_control"]
    check("positive: orientation FLIPS under traversal reversal (INWARD->OUTWARD)",
          em["forward_derived_orientation"] == "INWARD" and em["reversed_derived_orientation"] == "OUTWARD")
    check("positive: orientation FAILS to UNDEFINED when asymmetry removed",
          em["symmetric_derived_orientation"] == "UNDEFINED")
    check("positive: orientation_is_emergent verdict True", result["orientation_is_emergent"] is True)

    ps = result["present_survivor"]
    check("positive: present_survivor is a single branch id", isinstance(ps, str) and ps in rpf.BRANCH_STATES)
    nonempty = [s for s in cm["traversal_steps"] if s["branches_on_shell"]]
    check("positive: present_survivor is the final selected anchor of the traversal",
          ps == nonempty[-1]["selected_anchor"])

    rec = result["outward_record"]
    check("positive: outward_record orientation OUTWARD (record sink)", rec["record_orientation"] == "OUTWARD")
    check("positive: outward_record hash-chain recomputes", rec["append_only_recomputed"] is True)
    check("positive: outward_record binds the contraction trace", rec["binds_contraction_trace"] is True)
    check("positive: outward_record binds the present survivor", rec["binds_present_survivor"] == ps)

    # v1 win retained: shell-reassignment moves the survivor
    check("positive: shell_reassignment_moves_survivor (v1 win retained)",
          result["shell_reassignment_moves_survivor"] is True)

    check("positive: all invariants hold", result["all_invariants_hold"] is True)
    check("positive: classification scratch_diagnostic", result["classification"] == "scratch_diagnostic")
    check("positive: promotion_allowed false", result["promotion_allowed"] is False)
    check("positive: formal_admission_allowed false", result["formal_admission_allowed"] is False)


# =====================================================================
# NEGATIVE tests -- each control must BREAK / be inert / flip
# =====================================================================

def negative_tests() -> None:
    print("\n=== NEGATIVE (controls) ===")

    inst = rpf.build_object_instance()
    inv = rpf.check_invariants(inst)
    check("hard-stop holds (future_continuations != present_survivor)",
          inv["HARD_STOP_future_continuations_ne_present_survivor"] is True)

    # THE v2 EMERGENCE NEGATIVE CONTROLS -- re-derived fresh.
    em = rpf.emergence_discriminating_control()
    # (reverse) reversing the asymmetry flips orientation
    check("negative (reverse): reversing the traversal FLIPS orientation INWARD->OUTWARD",
          em["forward_derived_orientation"] == "INWARD"
          and em["reversed_derived_orientation"] == "OUTWARD")
    check("negative (reverse): the contraction ratio crosses 1 under reversal",
          em["forward_contraction_ratio"] < 1.0 and em["reversed_contraction_ratio"] > 1.0)
    # (remove) removing the asymmetry fails orientation
    check("negative (remove): symmetric field -> contraction ratio == 1.0 exactly",
          em["symmetric_contraction_ratio_to_b3"] == 1.0)
    check("negative (remove): symmetric field -> orientation UNDEFINED",
          em["symmetric_derived_orientation"] == "UNDEFINED")

    # (a) FLAT-UNION COLLAPSE must be INERT under shell-reassignment
    flat = rpf.flat_union_negative_control()
    check("negative (a): flat-union collapse is INERT (does NOT move survivor)",
          flat["flat_union_control_correctly_inert"] is True)

    # (b) scramble future_continuations -> break
    scr = rpf.scramble_futures_negative_control()
    check("negative (b): scramble future_continuations breaks", scr["control_breaks"] is True)

    # (c) uniform weights -> build breaks AND shell effect dies
    uni = rpf.uniform_weights_negative_control()
    check("negative (c): uniform weights break the build", uni["control_breaks"] is True)
    check("negative (c): uniform weights KILL the shell-reassignment effect",
          uni["uniform_correctly_kills_shell_effect"] is True)

    # (d) remove the OUTWARD record-sink tag -> build breaks
    rem = rpf.orientation_removal_negative_control()
    check("negative (d): removing the OUTWARD record-sink tag breaks the build",
          rem["build_breaks"] is True)


# =====================================================================
# TRAP tests -- the v0/v1 traps must STILL pass (no regression)
# =====================================================================

def trap_tests() -> None:
    print("\n=== TRAPS retained from v0/v1 (must still pass) ===")
    t1 = rpf.weight_permutation_trap()
    check("trap #1: weight permutation moves the survivor", t1["weight_permutation_moves_survivor"] is True)
    print(f"     (weight perm: {t1['base_survivor']} -> {t1['permuted_survivor']})")
    t4 = rpf.state_mutation_trap()
    check("trap #4: state mutation moves the survivor", t4["state_mutation_moves_survivor"] is True)
    print(f"     (state mut: {t4['base_survivor']} -> {t4['mutated_survivor']})")


# =====================================================================
# BOUNDARY tests -- the NON-TAUTOLOGY edge (the strongest emergence evidence)
# =====================================================================

def boundary_tests() -> None:
    print("\n=== BOUNDARY (non-tautology + thin edges) ===")

    # THE KEY NON-TAUTOLOGY TEST: the forward (radius-descending) traversal does
    # NOT always derive INWARD. If it did, INWARD would be forced by construction
    # (a disguised constant). Enumerate small 2+2 fields and require that SOME of
    # them derive OUTWARD and SOME derive UNDEFINED on the forward direction.
    branches = list(rpf.BRANCH_STATES.keys())
    forward_dirs = set()
    n_outward = n_undef = n_inward = 0
    for outer in itertools.combinations(branches, 2):
        for inner in itertools.combinations(branches, 2):
            fc = {"Sigma_2": list(outer), "Sigma_1": list(inner)}
            inst = rpf.build_object_instance(future_continuations=fc)
            d = inst["compression_map"]["direction"]
            forward_dirs.add(d)
            n_inward += d == "INWARD"
            n_outward += d == "OUTWARD"
            n_undef += d == "UNDEFINED"
    check("boundary: forward traversal can derive OUTWARD for SOME fields (not tautologically INWARD)",
          "OUTWARD" in forward_dirs and n_outward > 0)
    check("boundary: forward traversal can derive UNDEFINED for SOME fields",
          "UNDEFINED" in forward_dirs and n_undef > 0)
    check("boundary: forward traversal derives INWARD for SOME fields too (it is contingent)",
          n_inward > 0)
    print(f"     (forward direction over enumerated 2+2 fields: INWARD={n_inward} OUTWARD={n_outward} UNDEFINED={n_undef})")

    # Boundary: derive_orientation reads ONLY a scalar (cannot read a label).
    import inspect
    sig = inspect.signature(rpf.derive_orientation)
    params = list(sig.parameters)
    check("boundary: derive_orientation takes only (contraction_ratio, tol) -- no shell/label arg",
          params == ["contraction_ratio", "tol"])

    # Boundary: the contraction ratio is computed from candidate-set distances, NOT
    # from the selected anchor (whose final distance is tautologically 0). Confirm
    # the mean-distance sequence uses ALL branches, not just the anchor.
    inst = rpf.build_object_instance()
    contraction = inst["compression_map"]["contraction"]
    per = contraction["per_shell_distance"]
    # the outer shell mean-distance must reflect >1 branch (mean of 3 in canonical)
    check("boundary: contraction uses the full candidate set (mean over >1 branch)",
          len(per[0]["branches_on_shell"]) >= 2 and per[0]["mean_distance_to_fixed_point"] > 0)

    # Boundary: the fixed point x* is a genuine fixed point of the inner selection
    # map (a branch equal to x* scores 1.0 = maximal and persists).
    base = rpf.build_object_instance()
    xstar = base["present_survivor"]
    W = base["compatibility_weights"]
    deeper = sorted([xstar, "b0"])
    scores = {p: (1.0 if p == xstar else W[rpf.pair_key(p, xstar)]) for p in deeper}
    sel = max(deeper, key=lambda p: (scores[p], -rpf._branch_id_rank(p)))
    check("boundary: x* persists as the fixed point of the inner selection map",
          sel == xstar and abs(scores[xstar] - 1.0) < 1e-12)

    # Boundary: a single inward shell -> degenerate edge (multi-step fails, the
    # contraction ratio is NaN, orientation UNDEFINED -- cannot derive from one shell).
    one_shell = {"Sigma_2": ["b0", "b2", "b3"]}
    inst1 = rpf.build_object_instance(future_continuations=one_shell)
    check("boundary: single-inward-shell field cannot derive orientation (UNDEFINED, NaN ratio)",
          inst1["compression_map"]["direction"] == "UNDEFINED"
          and not math.isfinite(inst1["contraction_ratio"]))


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
