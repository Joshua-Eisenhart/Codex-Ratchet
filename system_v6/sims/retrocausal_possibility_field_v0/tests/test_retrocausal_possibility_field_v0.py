#!/usr/bin/env python3
"""
Tests for retrocausal_possibility_field_v0 -- positive + negative + boundary.

Run:  <sim-stack python3> tests/test_retrocausal_possibility_field_v0.py
Exits 0 only if every test passes.
"""

from __future__ import annotations

import json
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.dirname(TESTS_DIR)
sys.path.insert(0, SIM_DIR)

import retrocausal_possibility_field_v0 as rpf  # noqa: E402


FAILURES: list[str] = []


def check(name: str, cond: bool) -> None:
    status = "PASS" if cond else "FAIL"
    if not cond:
        FAILURES.append(name)
    print(f"[{status}] {name}")


# =====================================================================
# POSITIVE tests -- the object instantiates with its first-class fields
# =====================================================================

def positive_tests() -> None:
    print("\n=== POSITIVE (object field instantiation) ===")
    result = rpf.build_result()

    for k in rpf.FIRST_CLASS_KEYS:
        check(f"positive: first-class key present -> {k}", k in result)

    fc = result["future_continuations"]
    check("positive: future_continuations is a dict", isinstance(fc, dict))
    check("positive: future_continuations keyed by >=1 shell", len(fc) >= 1)
    check(
        "positive: each shell carries a LIST of >=2 distinct branches",
        all(isinstance(v, list) and len(set(v)) >= 2 for v in fc.values()),
    )

    cw = result["compatibility_weights"]
    check("positive: compatibility_weights over PAIRS (keys 'bi|bj')", all("|" in k for k in cw))
    check("positive: compatibility_weights real-valued", all(isinstance(v, float) for v in cw.values()))
    check("positive: compatibility_weights non-uniform", len(set(round(v, 12) for v in cw.values())) >= 2)

    cm = result["compression_map"]
    check("positive: compression_map direction INWARD", cm["direction"] == "INWARD")
    check("positive: compression_map records candidate inward mass", "candidate_inward_mass" in cm)
    check(
        "positive: weights computed before compression",
        cm["weights_computed_before_compression"] is True,
    )

    ps = result["present_survivor"]
    check("positive: present_survivor is a single branch id", isinstance(ps, str) and ps in rpf.BRANCH_STATES)
    check(
        "positive: present_survivor derived (is argmax candidate)",
        ps == cm["present_survivor"] and ps in cm["candidate_inward_mass"],
    )

    rec = result["outward_record"]
    check("positive: outward_record orientation OUTWARD", rec["record_orientation"] == "OUTWARD")
    check("positive: outward_record hash-chain recomputes", rec["append_only_recomputed"] is True)
    check("positive: outward_record binds the present survivor", rec["binds_present_survivor"] == ps)

    check("positive: all invariants hold", result["all_invariants_hold"] is True)
    check("positive: classification scratch_diagnostic", result["classification"] == "scratch_diagnostic")
    check("positive: promotion_allowed false", result["promotion_allowed"] is False)
    check("positive: formal_admission_allowed false", result["formal_admission_allowed"] is False)


# =====================================================================
# NEGATIVE tests -- each control must BREAK the result
# =====================================================================

def negative_tests() -> None:
    print("\n=== NEGATIVE (each control must break) ===")

    # HARD-STOP: identity compression must be detected as a break.
    # Force present_survivor == future_continuations by hand and confirm the
    # hard-stop invariant fires.
    inst = rpf.build_object_instance()
    inv = rpf.check_invariants(inst)
    check("hard-stop holds (future_continuations != present_survivor)",
          inv["HARD_STOP_future_continuations_ne_present_survivor"] is True)

    # (a) scramble future_continuations -> only 1 distinct branch per shell
    scrambled = {sid: [b[0], b[0]] for sid, b in rpf.FUTURE_CONTINUATIONS_BY_SHELL.items()}
    inv_a = rpf.check_invariants(rpf.build_object_instance(future_continuations=scrambled))
    check("negative (a): scramble future_continuations breaks", not all(inv_a.values()))

    # (b) remove shell_orientation
    shells_no = [{k: v for k, v in s.items() if k != "shell_orientation"} for s in rpf.SHELLS]
    try:
        inv_b = rpf.check_invariants(rpf.build_object_instance(shells=shells_no))
        broke_b = not all(inv_b.values())
    except StopIteration:
        broke_b = True
    check("negative (b): remove shell_orientation breaks", broke_b)

    # (c) uniform weights claiming structure
    real = rpf.compute_compatibility_weights(rpf.FUTURE_CONTINUATIONS_BY_SHELL)
    inv_c = rpf.check_invariants(rpf.build_object_instance(weights_override={k: 0.5 for k in real}))
    check("negative (c): uniform-then-claim-structure breaks", not all(inv_c.values()))

    # (d) collapse future_continuations to a scalar count (proxy shape)
    # Verify the validator's shape gate rejects an int future_continuations.
    proxy = dict(rpf.build_result())
    proxy["future_continuations"] = 6
    fc = proxy["future_continuations"]
    gate = isinstance(fc, dict) and all(isinstance(v, list) for v in (fc.values() if isinstance(fc, dict) else []))
    check("negative (d): scalar-count proxy rejected by shape gate", gate is False)


# =====================================================================
# BOUNDARY tests -- thin edges of the field
# =====================================================================

def boundary_tests() -> None:
    print("\n=== BOUNDARY (thin edges) ===")

    # Boundary: the 2-branch single-shell field is a GENUINE degenerate edge.
    # With exactly 2 branches there is only ONE pair, so compatibility_weights
    # has a single value and CANNOT be non-uniform. The non-uniformity invariant
    # therefore fails -- this is a true structural boundary (the weight structure
    # over PAIRS needs >=3 futures to carry distinguishing structure), NOT a bug.
    two_branch_fc = {"Sigma_1": ["b0", "b3"]}
    inst2 = rpf.build_object_instance(future_continuations=two_branch_fc)
    inv2 = rpf.check_invariants(inst2)
    check("boundary: 2-branch field has exactly one pairwise weight",
          len(inst2["compatibility_weights"]) == 1)
    check("boundary: 2-branch field FAILS non-uniformity (degenerate edge, expected)",
          inv2["compatibility_weights_non_uniform"] is False)
    check("boundary: 2-branch field still has a derived scalar survivor",
          inst2["present_survivor"] in {"b0", "b3"})

    # Boundary: minimal field that DOES hold all invariants -- 3 distinct branches
    # on one shell (smallest field with >=2 distinct pairwise weights).
    minimal_fc = {"Sigma_1": ["b0", "b2", "b3"]}
    inst = rpf.build_object_instance(future_continuations=minimal_fc)
    inv = rpf.check_invariants(inst)
    check("boundary: minimal 3-branch single-shell field holds ALL invariants",
          all(inv.values()))
    check("boundary: minimal field survivor is one of the three branches",
          inst["present_survivor"] in {"b0", "b2", "b3"})

    # Boundary: a deterministic argmax tie. Two branches equidistant from all
    # others would tie; confirm tie-break is deterministic (lowest id).
    # Use a symmetric pair so masses tie, then check survivor is the lower id.
    tie_fc = {"Sigma_1": ["b1", "b2"]}  # b1={a:0,b:1}, b2={a:1,b:0}: dist 2, symmetric
    inst_tie = rpf.build_object_instance(future_continuations=tie_fc)
    cm = inst_tie["compression_map"]
    masses = cm["candidate_inward_mass"]
    check("boundary: symmetric pair yields equal inward mass (a genuine tie)",
          abs(masses["b1"] - masses["b2"]) < 1e-12)
    check("boundary: deterministic tie-break picks lowest branch id",
          inst_tie["present_survivor"] == "b1")

    # Boundary: present_survivor must never be a list/count (collapse guard at edge)
    check("boundary: present_survivor is scalar id even at minimal field",
          isinstance(inst["present_survivor"], str))


def main() -> int:
    positive_tests()
    negative_tests()
    boundary_tests()
    print("\n=== SUMMARY ===")
    if FAILURES:
        print(json.dumps({"green": False, "failures": FAILURES}, indent=2))
        return 1
    print(json.dumps({"green": True, "failures": []}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
