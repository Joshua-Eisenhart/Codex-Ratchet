#!/usr/bin/env python3
"""
Tests for retrocausal_possibility_field_v3 -- positive + negative + boundary.

Focus of v3 (the Wizard verdict's NOT-EARNED axis): the genuine global
co-admissibility compressor must be PROBE-DISTINGUISHABLE from a forward sequential
selector. The decisive test is the acceptance gate (present_survivor_retro !=
present_survivor_forward), plus: the constraint family C is load-bearing (each
clause matters; uniform C collapses the probe), orientation is derived from measured
fiber cardinality (emergence flip), and the v1 contamination bug is fixed.

Run:  <sim-stack python3> tests/test_retrocausal_possibility_field_v3.py
Exits 0 only if every test passes.
"""

from __future__ import annotations

import copy
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.dirname(TESTS_DIR)
sys.path.insert(0, SIM_DIR)

import retrocausal_possibility_field_v3 as rpf  # noqa: E402


FAILURES: list[str] = []


def check(name: str, cond: bool) -> None:
    status = "PASS" if cond else "FAIL"
    if not cond:
        FAILURES.append(name)
    print(f"[{status}] {name}")


# =====================================================================
# POSITIVE: the genuine compressor differs from forward selection (EARNED)
# =====================================================================

def test_positive_acceptance_gate_earned() -> None:
    fc = rpf.FUTURE_CONTINUATIONS_BY_SHELL
    relation = rpf.co_admissibility_relation(fc)
    gate = rpf.acceptance_gate_differs_from_forward(fc, relation, rpf.SHELLS)
    check("positive: present_survivor_retro != present_survivor_forward (single anchor)",
          gate["present_survivor_retro"] != gate["present_survivor_forward"])
    check("positive: present_survivor_retro != full-history forward survivor",
          gate["present_survivor_retro"] != gate["present_survivor_forward_full_history"])
    check("positive: retrocausal_earned is True", gate["retrocausal_earned"] is True)
    check("positive: differs_from_forward_selection is True",
          gate["differs_from_forward_selection"] is True)
    check("positive: differs from BOTH forward variants",
          gate["differs_from_single_anchor_forward"] and gate["differs_from_full_history_forward"])
    # canonical pin: retro=b8, both forward variants=b2
    check("positive: canonical retro survivor is b8", gate["present_survivor_retro"] == "b8")
    check("positive: canonical single-anchor forward survivor is b2",
          gate["present_survivor_forward"] == "b2")
    check("positive: canonical full-history forward survivor is b2",
          gate["present_survivor_forward_full_history"] == "b2")


def test_positive_global_beats_greedy() -> None:
    """The divergence is a real global-vs-greedy gap, not a tie-break accident, and is
    NOT defeatable by a stronger forward tie-break: the global joint assignment scores
    strictly more co-admissible pairs than BOTH forward paths' assignments, and differs
    from BOTH forward survivors."""
    div = rpf.independent_divergence_search()
    check("positive: global co-adm count > single-anchor forward count",
          div["global_coadm_pair_count"] > div["forward_coadm_pair_count"])
    check("positive: global co-adm count > full-history forward count",
          div["global_coadm_pair_count"] > div["forward_full_history_coadm_pair_count"])
    check("positive: survivor differs from single-anchor forward in independent search",
          div["survivors_differ_from_single_anchor"] is True)
    check("positive: survivor differs from full-history forward in independent search",
          div["survivors_differ_from_full_history"] is True)


def test_positive_all_invariants_hold() -> None:
    inst = rpf.build_object_instance()
    inv = rpf.check_invariants(inst)
    for name, val in inv.items():
        check(f"invariant: {name}", bool(val))


def test_positive_first_class_fields_genuine() -> None:
    inst = rpf.build_object_instance()
    fc = inst["future_continuations"]
    check("field: future_continuations is shell-keyed dict of >=2-distinct lists",
          isinstance(fc, dict) and all(isinstance(v, list) and len(set(v)) >= 2 for v in fc.values()))
    rel = inst["compatibility_relation_C"]
    check("field: compatibility relation C is boolean over pairs",
          all("|" in k for k in rel) and all(isinstance(v, bool) for v in rel.values()))
    cm = inst["compression_map"]
    check("field: compression_map is the global compressor",
          cm["selector"] == "retrocausal_global_compressor")
    check("field: forward control carries NO inward semantics",
          "NO inward/retrocausal semantics" in inst["forward_sequential_control"]["semantics"])


# =====================================================================
# CONSTRAINT C is load-bearing (the derived source of compatibility)
# =====================================================================

def test_constraint_C_clauses_load_bearing() -> None:
    parity = rpf.parity_drop_control()
    check("constraint: dropping the parity clause changes the survivor",
          parity["parity_clause_is_load_bearing"] is True)
    check("constraint: full-C survivor b8 != gap-only survivor b2",
          parity["full_C_survivor"] != parity["gap_only_survivor"])

    fc = rpf.FUTURE_CONTINUATIONS_BY_SHELL
    rel = rpf.co_admissibility_relation(fc)
    n_true = sum(1 for v in rel.values() if v)
    check("constraint: C is non-degenerate (some pairs admissible, some not)",
          0 < n_true < len(rel))


def test_constraint_co_admissible_predicate() -> None:
    """Spot-check the boolean predicate against the definition directly."""
    # b0=(0,0), b2=(1,0): a-sum=1 (odd) -> NOT co-admissible
    check("predicate: b0,b2 odd-parity -> not co-admissible", rpf.co_admissible("b0", "b2") is False)
    # b0=(0,0), b4=(2,0): a-sum=2 even, b-gap=0 -> co-admissible
    check("predicate: b0,b4 even-parity bounded-gap -> co-admissible", rpf.co_admissible("b0", "b4") is True)
    # b1=(0,1), b8=(0,3): a-sum=0 even, b-gap=2 (>1) -> NOT co-admissible
    check("predicate: b1,b8 even-parity but gap>1 -> not co-admissible", rpf.co_admissible("b1", "b8") is False)


# =====================================================================
# NEGATIVE: uniform constraint collapses the earned probe
# =====================================================================

def test_negative_uniform_constraint_collapses_probe() -> None:
    u = rpf.uniform_constraint_control()
    check("negative: uniform (all-True) C kills the earned probe (no longer differs)",
          u["uniform_correctly_kills_the_probe"] is True)
    check("negative: under uniform C, still_differs is False",
          u["still_differs_from_forward"] is False)


def test_negative_scramble_breaks_build() -> None:
    s = rpf.scramble_futures_negative_control()
    check("negative: scrambling to 1 branch/shell breaks the build", s["control_breaks"] is True)


# =====================================================================
# ORIENTATION derived from measured fiber cardinality (emergence)
# =====================================================================

def test_orientation_derived_not_stored() -> None:
    inst = rpf.build_object_instance()
    check("orientation: NO shell stores a stipulated orientation string",
          all("shell_orientation" not in s for s in inst["shells"]))
    # re-derive inward from cardinality
    for s in inst["compression_map"]["per_stratum"]:
        if s["branches_on_shell"]:
            rederived = rpf.derive_orientation(s["fiber_cardinality"])
            check(f"orientation: {s['shell_id']} re-derives INWARD from many-to-one",
                  rederived == "INWARD" and rederived == inst["shell_orientation"][s["shell_id"]])
    rec = inst["outward_record"]
    check("orientation: record re-derives OUTWARD from injectivity",
          rpf.derive_orientation(rec["record_fiber_cardinality"]) == "OUTWARD")


def test_orientation_emergence_flips() -> None:
    e = rpf.orientation_emergence_control()
    check("emergence: inward stratum made injective flips INWARD->OUTWARD",
          e["inward_orientation_flips_under_reversal"] is True)
    check("emergence: record stratum collapsed flips OUTWARD->INWARD",
          e["record_orientation_flips_under_reversal"] is True)
    check("emergence: record flip holds end-to-end (full rebuild)",
          e["record_orientation_flips_end_to_end"] is True)
    check("emergence: orientation_is_emergent overall", e["orientation_is_emergent"] is True)


def test_boundary_empty_and_injective_maps() -> None:
    """Boundary: derive_orientation on degenerate maps."""
    check("boundary: empty map -> orientation None",
          rpf.derive_orientation(rpf.measure_fiber_cardinality({})) is None)
    check("boundary: 1->1 injective map -> OUTWARD",
          rpf.derive_orientation(rpf.measure_fiber_cardinality({"x": "y"})) == "OUTWARD")
    check("boundary: 2->1 many-to-one map -> INWARD",
          rpf.derive_orientation(rpf.measure_fiber_cardinality({"x": "z", "y": "z"})) == "INWARD")


# =====================================================================
# RETAINED WINS: shell reassignment, hard-stop
# =====================================================================

def test_shell_reassignment_moves_survivor() -> None:
    r = rpf.shell_reassignment_control()
    check("retained: shell-reassignment union identical", r["union_identical"] is True)
    check("retained: shell-reassignment MOVES the survivor (b8->b2)",
          r["shell_reassignment_moves_survivor"] is True
          and r["base_present_survivor"] == "b8"
          and r["reassigned_present_survivor"] == "b2")


def test_hard_stop() -> None:
    inst = rpf.build_object_instance()
    check("hard-stop: future_continuations != present_survivor",
          inst["future_continuations"] != inst["present_survivor"]
          and inst["present_survivor"] is not None)


# =====================================================================
# CONTAMINATION FIX (the v1 b3.a=6 bug)
# =====================================================================

def test_no_state_mutation_contamination() -> None:
    canonical = copy.deepcopy(rpf.BRANCH_STATES)
    trap = rpf.state_mutation_trap()
    check("contamination: state-mutation trap still moves the survivor",
          trap["state_mutation_moves_survivor"] is True)
    check("contamination: trap reports carrier restored",
          trap["carrier_restored_no_contamination"] is True)
    check("contamination: module global BRANCH_STATES uncontaminated after trap",
          rpf.BRANCH_STATES == canonical)
    check("contamination: b5.a is restored to 2 (NOT the mutated 7)",
          rpf.BRANCH_STATES["b5"]["a"] == 2)
    # build a fresh result and confirm the serialized carrier is clean
    result = rpf.build_result()
    check("contamination: serialized result branch_states match canonical",
          result["branch_states"] == canonical)


# =====================================================================
# Result-level acceptance
# =====================================================================

def test_result_all_pass_and_ceiling() -> None:
    result = rpf.build_result()
    check("result: all_pass True (invariants AND retrocausal earned)",
          result["all_pass"] is True)
    check("result: retrocausal_earned True", result["retrocausal_earned"] is True)
    check("result: classification scratch_diagnostic",
          result["classification"] == "scratch_diagnostic")
    check("result: promotion_allowed False", result["promotion_allowed"] is False)
    check("result: formal_admission_allowed False", result["formal_admission_allowed"] is False)


def main() -> int:
    test_positive_acceptance_gate_earned()
    test_positive_global_beats_greedy()
    test_positive_all_invariants_hold()
    test_positive_first_class_fields_genuine()
    test_constraint_C_clauses_load_bearing()
    test_constraint_co_admissible_predicate()
    test_negative_uniform_constraint_collapses_probe()
    test_negative_scramble_breaks_build()
    test_orientation_derived_not_stored()
    test_orientation_emergence_flips()
    test_boundary_empty_and_injective_maps()
    test_shell_reassignment_moves_survivor()
    test_hard_stop()
    test_no_state_mutation_contamination()
    test_result_all_pass_and_ceiling()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("ALL TESTS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
