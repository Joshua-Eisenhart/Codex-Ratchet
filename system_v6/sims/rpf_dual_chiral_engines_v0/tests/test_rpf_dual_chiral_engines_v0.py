#!/usr/bin/env python3
"""Focused pytest coverage for rpf_dual_chiral_engines_v0.

Positive / negative / boundary sections. Tests the load-bearing facts directly, not
the stored result booleans:
  - the three HARD ACCEPTANCE tests (chirality L!=R, independent mirror P maps L<->R,
    symmetric-control collapse);
  - the anti-swap-tautology guard (distinct engine objective SHAs);
  - the disjoint-optima robustness (no tie-break crossover);
  - controls (handedness clause load-bearing, scramble breaks, state-mutation moves,
    no contamination).
"""

from __future__ import annotations

import copy
import os
import sys

import pytest

SIM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SIM_DIR)

import rpf_dual_chiral_engines_v0 as dce  # noqa: E402


# ---------------------------------------------------------------- positive

def test_chirality_L_and_R_differ():
    fc = dce.FUTURE_CONTINUATIONS_BY_SHELL
    rel = dce.oriented_relation(fc)
    chir = dce.chirality_test(fc, rel, dce.SHELLS)
    assert chir["present_survivor_L"] != chir["present_survivor_R"]
    assert chir["chirality_is_physical"] is True


def test_optimal_survivor_sets_disjoint_no_tiebreak_crossover():
    fc = dce.FUTURE_CONTINUATIONS_BY_SHELL
    rel = dce.oriented_relation(fc)
    _, l_opt = dce._optimal_innermost_survivors(fc, rel, dce.SHELLS, reverse=False)
    _, r_opt = dce._optimal_innermost_survivors(fc, rel, dce.SHELLS, reverse=True)
    assert set(l_opt) & set(r_opt) == set(), (l_opt, r_opt)


def test_relation_is_non_symmetric_broken_symmetry():
    fc = dce.FUTURE_CONTINUATIONS_BY_SHELL
    rel = dce.oriented_relation(fc)
    assert dce._relation_is_non_symmetric(rel) is True
    # non-degenerate
    n_true = sum(1 for v in rel.values() if v)
    assert 0 < n_true < len(rel)


def test_engine_handedness_is_derived_not_stored():
    fc = dce.FUTURE_CONTINUATIONS_BY_SHELL
    rel = dce.oriented_relation(fc)
    left = dce.chiral_engine(fc, rel, dce.SHELLS, reverse=False)
    right = dce.chiral_engine(fc, rel, dce.SHELLS, reverse=True)
    assert left["handedness_is_derived_from_reading_direction"] is True
    assert right["handedness_is_derived_from_reading_direction"] is True
    assert left["handedness_DERIVED"] != right["handedness_DERIVED"]
    # no shell in SHELLS stores a chirality/orientation string
    assert all("shell_orientation" not in s for s in dce.SHELLS)


# ---------------------------- independent mirror (anti swap-tautology)

def test_parity_is_genuine_reflection_involution_that_moves_field():
    canon = copy.deepcopy(dce.BRANCH_STATES)
    once = dce.parity_reflect_branch_states(canon)
    twice = dce.parity_reflect_branch_states(once)
    assert twice == canon          # involution
    assert once != canon           # actually moves the field


def test_spatial_reflection_sends_Rdir_to_transpose():
    fc = dce.FUTURE_CONTINUATIONS_BY_SHELL
    rel = dce.oriented_relation(fc)
    transpose = {f"{k.split('>')[1]}>{k.split('>')[0]}": v for k, v in rel.items()}
    saved = copy.deepcopy(dce.BRANCH_STATES)
    try:
        dce.BRANCH_STATES = dce.parity_reflect_branch_states(copy.deepcopy(saved))
        rel_reflected = dce.oriented_relation(fc)
    finally:
        dce.BRANCH_STATES = saved
    assert rel_reflected == transpose


def test_engines_are_distinct_functions_not_swap_tautology():
    fc = dce.FUTURE_CONTINUATIONS_BY_SHELL
    rel = dce.oriented_relation(fc)
    left = dce.chiral_engine(fc, rel, dce.SHELLS, reverse=False)
    right = dce.chiral_engine(fc, rel, dce.SHELLS, reverse=True)
    assert left["objective_identity_sha256"] != right["objective_identity_sha256"]


def test_parity_maps_L_to_R_both_ways():
    mirror = dce.independent_mirror_test()
    assert mirror["equivariance_L_maps_to_R"] is True
    assert mirror["equivariance_R_maps_to_L"] is True
    assert mirror["parity_maps_L_to_R_and_R_to_L"] is True
    assert mirror["is_swap_tautology"] is False
    # over the reflected field the survivors actually swap (L<->R)
    assert mirror["present_survivor_L_over_PF"] == mirror["present_survivor_R_over_F"]
    assert mirror["present_survivor_R_over_PF"] == mirror["present_survivor_L_over_F"]


# ---------------------------------------------------------------- negative

def test_symmetric_control_collapses_L_equals_R():
    sym = dce.symmetric_control_collapse()
    assert sym["symmetric_closure_is_actually_symmetric"] is True
    assert sym["present_survivor_L_symmetric"] == sym["present_survivor_R_symmetric"]
    assert sym["chirality_correctly_absent_on_symmetric_field"] is True


def test_handedness_clause_is_load_bearing():
    ctrl = dce.relation_clause_load_bearing_control()
    assert ctrl["h_blind_relation_is_symmetric"] is True
    assert ctrl["h_blind_L_equals_R"] is True
    assert ctrl["handedness_clause_is_load_bearing"] is True


def test_scramble_breaks_the_build():
    assert dce.scramble_futures_negative_control()["control_breaks"] is True


# ---------------------------------------------------------------- boundary

def test_state_mutation_moves_a_survivor_and_no_contamination():
    trap = dce.state_mutation_trap()
    assert trap["handedness_mutation_moves_a_survivor"] is True
    assert trap["carrier_restored_no_contamination"] is True
    # the module global is uncontaminated after the trap
    assert dce.BRANCH_STATES["b0"]["h"] == +1


def test_hard_stop_future_continuations_ne_survivor():
    inst = dce.build_object_instance()
    fc = inst["future_continuations"]
    assert fc != inst["present_survivor_L"]
    assert fc != inst["present_survivor_R"]
    assert inst["present_survivor_L"] is not None
    assert inst["present_survivor_R"] is not None


def test_all_invariants_hold_and_chirality_earned():
    result = dce.build_result()
    assert result["all_invariants_hold"] is True
    assert result["chirality_earned"] is True
    assert result["all_pass"] is True
    # ceiling discipline
    assert result["classification"] == "scratch_diagnostic"
    assert result["promotion_allowed"] is False
    assert result["formal_admission_allowed"] is False


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
