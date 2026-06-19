#!/usr/bin/env python3
"""
Tests for retrocausal_possibility_field_v2_irreversibility -- positive + negative
+ boundary.

Focus of v2 (the audited gap): shell_orientation INWARD/OUTWARD is DERIVED from
measured compression irreversibility (fan-in/fan-out), not a stipulated string.
The discriminating test is the orientation-emergence control (reverse the measured
asymmetry -> the derived label flips), plus the assertion that NO shell carries a
stored orientation string. v1's wins (shell-reassignment, traps, hard-stop) must
still pass.

Run:  <sim-stack python3> tests/test_retrocausal_possibility_field_v2_irreversibility.py
Exits 0 only if every test passes.
"""

from __future__ import annotations

import json
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.dirname(TESTS_DIR)
sys.path.insert(0, SIM_DIR)

import retrocausal_possibility_field_v2_irreversibility as rpf  # noqa: E402


FAILURES: list[str] = []


def check(name: str, cond: bool) -> None:
    status = "PASS" if cond else "FAIL"
    if not cond:
        FAILURES.append(name)
    print(f"[{status}] {name}")


# =====================================================================
# POSITIVE -- object instantiates, orientation is derived, emergence holds
# =====================================================================

def positive_tests() -> None:
    print("\n=== POSITIVE (field instantiation + DERIVED orientation + emergence) ===")
    result = rpf.build_result()

    for k in rpf.FIRST_CLASS_KEYS:
        check(f"positive: first-class key present -> {k}", k in result)

    fc = result["future_continuations"]
    check("positive: future_continuations keyed by >=1 future stratum", len(fc) >= 1)
    check(
        "positive: each future stratum carries a LIST of >=2 distinct branches",
        all(isinstance(v, list) and len(set(v)) >= 2 for v in fc.values()),
    )

    cw = result["compatibility_weights"]
    check("positive: compatibility_weights over PAIRS", all("|" in k for k in cw))
    check("positive: compatibility_weights real-valued", all(isinstance(v, float) for v in cw.values()))
    check("positive: compatibility_weights non-uniform", len(set(round(v, 12) for v in cw.values())) >= 2)

    cm = result["compression_map"]
    check("positive: compression_map direction INWARD", cm["direction"] == "INWARD")
    check("positive: compression_map direction is flagged DERIVED",
          cm.get("direction_is_derived_from_irreversibility") is True)
    nonempty = [s for s in cm["traversal_steps"] if s["branches_on_shell"]]
    check("positive: compression_map is MULTI-STEP (>=2 non-empty future strata)", len(nonempty) >= 2)

    # v2 CORE: NO shell carries a stipulated orientation string
    check("positive: NO shell dict carries a stipulated 'shell_orientation' string",
          all("shell_orientation" not in s for s in result["shells"]))

    # v2 CORE: each inward stratum map is many-to-one and DERIVES INWARD
    for s in nonempty:
        irr = s["irreversibility"]
        check(f"positive: inward stratum {s['shell_id']} map is many-to-one (fan_in>fan_out)",
              irr["many_to_one"] is True and irr["fan_in"] > irr["fan_out"])
        check(f"positive: inward stratum {s['shell_id']} derives INWARD from its measure",
              rpf.derive_orientation(irr) == "INWARD" and s["derived_orientation"] == "INWARD")
        check(f"positive: instance shell_orientation[{s['shell_id']}] matches the derived label",
              result["shell_orientation"][s["shell_id"]] == "INWARD")

    # v2 CORE: record stratum is injective and DERIVES OUTWARD
    rec = result["outward_record"]
    rec_irr = rec["record_irreversibility"]
    check("positive: record map is injective (fan_in == fan_out)",
          rec_irr["injective"] is True and rec_irr["fan_in"] == rec_irr["fan_out"])
    check("positive: record derives OUTWARD from its injectivity",
          rpf.derive_orientation(rec_irr) == "OUTWARD" and rec["record_orientation"] == "OUTWARD")
    check("positive: instance shell_orientation[record] matches the derived label",
          result["shell_orientation"][rec["record_shell_id"]] == "OUTWARD")

    # v2 ACCEPTANCE: orientation is emergent (reversing the asymmetry flips it)
    check("positive: orientation_is_emergent (the v2 fix)", result["orientation_is_emergent"] is True)
    emc = result["orientation_emergence_control"]
    check("positive: inward orientation flips INWARD->OUTWARD under reversal",
          emc["inward_orientation_flips_under_reversal"] is True
          and emc["inward_actual_orientation"] == "INWARD"
          and emc["inward_reversed_orientation"] == "OUTWARD")
    check("positive: record orientation flips OUTWARD->INWARD under reversal",
          emc["record_orientation_flips_under_reversal"] is True
          and emc["record_actual_orientation"] == "OUTWARD"
          and emc["record_reversed_orientation"] == "INWARD")
    check("positive: record orientation flips end-to-end on full rebuild",
          emc["record_orientation_flips_end_to_end"] is True)

    ps = result["present_survivor"]
    check("positive: present_survivor is a single branch id", isinstance(ps, str) and ps in rpf.BRANCH_STATES)
    check("positive: present_survivor derived (final selected anchor)",
          ps == cm["present_survivor"] and ps == nonempty[-1]["selected_anchor"])

    check("positive: outward_record hash-chain recomputes", rec["append_only_recomputed"] is True)

    # v1 win retained: shell-reassignment moves the survivor
    check("positive: shell_reassignment_moves_survivor (v1 win retained)",
          result["shell_reassignment_moves_survivor"] is True)

    check("positive: all invariants hold", result["all_invariants_hold"] is True)
    check("positive: classification scratch_diagnostic", result["classification"] == "scratch_diagnostic")
    check("positive: promotion_allowed false", result["promotion_allowed"] is False)
    check("positive: formal_admission_allowed false", result["formal_admission_allowed"] is False)


# =====================================================================
# NEGATIVE -- controls must break / be inert / flip
# =====================================================================

def negative_tests() -> None:
    print("\n=== NEGATIVE (controls) ===")

    inst = rpf.build_object_instance()
    inv = rpf.check_invariants(inst)
    check("hard-stop holds (future_continuations != present_survivor)",
          inv["HARD_STOP_future_continuations_ne_present_survivor"] is True)

    # THE EMERGENCE DISCRIMINATING CONTROL re-derived directly via derive_orientation
    # (a) reverse an inward stratum's asymmetry -> injective -> derives OUTWARD
    base = rpf.build_object_instance()
    sample = [s for s in base["compression_map"]["traversal_steps"] if s["branches_on_shell"]][0]
    actual = rpf.derive_orientation(rpf.measure_irreversibility(sample["stratum_map"]))
    injective_map = {b: f"img_{b}" for b in sample["branches_on_shell"]}
    reversed_o = rpf.derive_orientation(rpf.measure_irreversibility(injective_map))
    check("negative (emergence-i): inward actual derives INWARD", actual == "INWARD")
    check("negative (emergence-i): inward made injective FLIPS to OUTWARD", reversed_o == "OUTWARD")

    # (b) reverse the record asymmetry -> many-to-one -> derives INWARD
    rec_actual = rpf.derive_orientation(rpf.measure_irreversibility(base["outward_record"]["record_map"]))
    collapsed = {ev: "one" for ev in base["outward_record"]["record_map"].keys()}
    rec_reversed = rpf.derive_orientation(rpf.measure_irreversibility(collapsed))
    check("negative (emergence-ii): record actual derives OUTWARD", rec_actual == "OUTWARD")
    check("negative (emergence-ii): record made many-to-one FLIPS to INWARD", rec_reversed == "INWARD")

    # (c) flat-union collapse inert under reassignment (traversal carries effect)
    flat = rpf.flat_union_negative_control()
    check("negative (a): flat-union collapse is INERT", flat["flat_union_control_correctly_inert"] is True)

    # (d) scramble future_continuations -> build breaks
    scr = rpf.scramble_futures_negative_control()
    check("negative (b): scramble future_continuations breaks", scr["control_breaks"] is True)

    # (e) uniform weights -> build breaks AND shell effect dies
    uni = rpf.uniform_weights_negative_control()
    check("negative (c): uniform weights break the build", uni["control_breaks"] is True)
    check("negative (c): uniform weights KILL the shell-reassignment effect",
          uni["uniform_correctly_kills_shell_effect"] is True)


# =====================================================================
# TRAP -- v0 traps must STILL pass (no regression)
# =====================================================================

def trap_tests() -> None:
    print("\n=== TRAPS retained from v0 (must still pass) ===")
    t1 = rpf.weight_permutation_trap()
    check("trap #1: weight permutation moves the survivor", t1["weight_permutation_moves_survivor"] is True)
    print(f"     (weight perm: {t1['base_survivor']} -> {t1['permuted_survivor']})")
    t4 = rpf.state_mutation_trap()
    check("trap #4: state mutation moves the survivor", t4["state_mutation_moves_survivor"] is True)
    print(f"     (state mut: {t4['base_survivor']} -> {t4['mutated_survivor']})")


# =====================================================================
# BOUNDARY -- thin edges of the irreversibility measure
# =====================================================================

def boundary_tests() -> None:
    print("\n=== BOUNDARY (thin edges of the measure) ===")

    # Boundary: an exactly 2->1 map is the minimal compression (many-to-one).
    m_min = rpf.measure_irreversibility({"x": "z", "y": "z"})
    check("boundary: 2->1 map measured many-to-one (fan_in 2 > fan_out 1)",
          m_min["many_to_one"] is True and m_min["fan_in"] == 2 and m_min["fan_out"] == 1)
    check("boundary: minimal 2->1 map derives INWARD", rpf.derive_orientation(m_min) == "INWARD")

    # Boundary: a 1->1 map is injective -> derives OUTWARD (the knife edge).
    m_id = rpf.measure_irreversibility({"x": "x"})
    check("boundary: 1->1 map measured injective (fan_in == fan_out)",
          m_id["injective"] is True and m_id["fan_in"] == m_id["fan_out"] == 1)
    check("boundary: 1->1 map derives OUTWARD", rpf.derive_orientation(m_id) == "OUTWARD")

    # Boundary: collapse_ratio is exactly 1.0 for injective, <1.0 for compressive.
    check("boundary: injective collapse_ratio == 1.0", abs(m_id["collapse_ratio"] - 1.0) < 1e-12)
    check("boundary: 2->1 collapse_ratio == 0.5", abs(m_min["collapse_ratio"] - 0.5) < 1e-12)

    # Boundary: empty map -> derive_orientation returns None (no map -> no orientation).
    m_empty = rpf.measure_irreversibility({})
    check("boundary: empty map domain_size 0", m_empty["domain_size"] == 0)
    check("boundary: empty map derives None (no orientation)", rpf.derive_orientation(m_empty) is None)

    # Boundary: a single inward shell collapses the traversal to its seed step;
    # the multi-step invariant fails (structural edge -- needs >=2 inward shells).
    one_shell = {"Sigma_2": ["b0", "b2", "b3"]}
    inst1 = rpf.build_object_instance(future_continuations=one_shell)
    inv1 = rpf.check_invariants(inst1, include_emergent_controls=False)
    check("boundary: single-inward-shell field FAILS multi-step (degenerate edge, expected)",
          inv1["compression_is_multi_step_traversal"] is False)
    # but the single inward shell's own map is still many-to-one (3->1) -> INWARD
    nm = [s for s in inst1["compression_map"]["traversal_steps"] if s["branches_on_shell"]]
    check("boundary: single shell still derives INWARD on its 3->1 map",
          nm[0]["derived_orientation"] == "INWARD")

    # Boundary: a future stratum carrying branches that already share an image is
    # still many-to-one regardless of WHICH anchor wins (the measure is map-shape,
    # not survivor-identity).
    fmap = rpf.future_stratum_map(["b0", "b1", "b5"], "b1")
    check("boundary: 3-branch future stratum map is 3->1 (many-to-one)",
          rpf.measure_irreversibility(fmap)["many_to_one"] is True)

    # Boundary: present_survivor must never be a list/count.
    tie_fc = {"Sigma_2": ["b1", "b2"], "Sigma_1": ["b0", "b3"]}
    inst_tie = rpf.build_object_instance(future_continuations=tie_fc)
    check("boundary: present_survivor is scalar id at minimal multi-shell field",
          isinstance(inst_tie["present_survivor"], str))


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
