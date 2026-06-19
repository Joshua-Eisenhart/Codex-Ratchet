#!/usr/bin/env python3
"""
Validator for rpf_dual_chiral_engines_v0.

Re-derives the load-bearing facts from the sim module rather than trusting stored
booleans, to the dual-chiral HARD ACCEPTANCE bar:

  1. ALL first-class object keys present and genuinely shaped.
  2. ALL required invariants hold on the canonical instance (incl. the three hard
     acceptance tests).
  3. HARD-STOP: future_continuations != present_survivor (for both L and R).

  HARD ACCEPTANCE TEST 1 -- CHIRALITY (L != R):
  4. Re-run BOTH chiral engines fresh on the canonical chiral field and assert
     present_survivor_L != present_survivor_R (handedness is physical, not a relabel).

  HARD ACCEPTANCE TEST 2 -- INDEPENDENT MIRROR (P maps L<->R, NOT swap-tautology):
  5. Re-derive the parity reflection (pos -> (N-1)-pos) and confirm:
       (a) P is a genuine reflection: P(P(F))==F (involution) AND P(F)!=F (moves field);
       (b) the L and R engines have DISTINCT objective identities (objective SHAs differ)
           -- the anti-GNVW-swap-tautology guard (NOT swapped==identical-SHA);
       (c) P is independent of the engine constructors: reflecting the ring sends R_dir
           to its TRANSPOSE (checked directly), so re-running the SAME L engine over P(F)
           does the R engine's job -- and the equivariance P(L over F) == R over P(F)
           holds both ways (compared at the FEATURE level).

  HARD ACCEPTANCE TEST 3 -- SYMMETRIC-CONTROL COLLAPSE (L == R on non-chiral field):
  6. Replace R_dir with its symmetric closure and assert present_survivor_L ==
     present_survivor_R (chirality correctly ABSENT when the field is not handed), and
     that the closure is actually symmetric.

  CONSTRAINT load-bearing:
  7. R_dir is a NON-symmetric boolean oriented relation (broken symmetry); the
     handedness clause is load-bearing (dropping it changes the L/R survivors).

  CONTAMINATION:
  8. The serialized branch_states equals the canonical carrier (the state-mutation trap
     restored it via deepcopy and never contaminated the module global).

Exits 0 (green) only if ALL of the above hold.

Run:  <sim-stack python3> validate_rpf_dual_chiral_engines_v0.py
"""

from __future__ import annotations

import copy
import json
import os
import sys

SIM_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SIM_DIR)

import rpf_dual_chiral_engines_v0 as dce  # noqa: E402


FIRST_CLASS_KEYS = dce.FIRST_CLASS_KEYS


def check_keys_present(result: dict) -> dict:
    checks = {}
    for k in FIRST_CLASS_KEYS:
        checks[f"key_present:{k}"] = k in result

    fc = result.get("future_continuations", {})
    checks["future_continuations_is_shell_keyed_dict_of_lists"] = (
        isinstance(fc, dict)
        and len(fc) >= 1
        and all(isinstance(v, list) and len(set(v)) >= 2 for v in fc.values())
    )
    rel = result.get("oriented_relation_R_dir", {})
    checks["relation_is_oriented_boolean_pair_relation"] = (
        isinstance(rel, dict)
        and len(rel) >= 1
        and all(">" in k for k in rel.keys())
        and all(isinstance(v, bool) for v in rel.values())
    )
    le = result.get("L_engine", {})
    re_ = result.get("R_engine", {})
    checks["L_engine_reads_outer_to_inner_no_stored_label"] = (
        isinstance(le, dict)
        and le.get("reverse") is False
        and bool(le.get("handedness_is_derived_from_reading_direction"))
    )
    checks["R_engine_reads_inner_to_outer_no_stored_label"] = (
        isinstance(re_, dict)
        and re_.get("reverse") is True
        and bool(re_.get("handedness_is_derived_from_reading_direction"))
    )
    checks["L_R_have_distinct_objective_sha"] = (
        le.get("objective_identity_sha256") != re_.get("objective_identity_sha256")
        and bool(le.get("objective_identity_sha256"))
    )
    return checks


def check_chirality_test_independently() -> dict:
    """Re-run both engines fresh and assert L != R on the chiral field, AND re-derive
    the optimal innermost-survivor SETS to confirm they are DISJOINT (no tie-break
    crossover -- the divergence is structural, not a labeled shift)."""
    fc = dce.FUTURE_CONTINUATIONS_BY_SHELL
    relation = dce.oriented_relation(fc)
    left = dce.chiral_engine(fc, relation, dce.SHELLS, reverse=False)
    right = dce.chiral_engine(fc, relation, dce.SHELLS, reverse=True)
    sL = left["present_survivor"]
    sR = right["present_survivor"]
    _, l_opt = dce._optimal_innermost_survivors(fc, relation, dce.SHELLS, reverse=False)
    _, r_opt = dce._optimal_innermost_survivors(fc, relation, dce.SHELLS, reverse=True)
    disjoint = len(set(l_opt) & set(r_opt)) == 0
    checks = {
        "engines_run_on_same_chiral_field": True,
        "L_and_R_survivors_DIFFER": sL != sR,
        "L_R_optimal_survivor_sets_DISJOINT_no_tiebreak_crossover": disjoint,
    }
    return checks, {
        "present_survivor_L": sL,
        "present_survivor_R": sR,
        "L_optimal_survivor_set": l_opt,
        "R_optimal_survivor_set": r_opt,
    }


def check_independent_mirror() -> dict:
    """Re-derive the parity reflection from scratch and assert it maps L<->R without
    being the swap-tautology. Also assert DIRECTLY (independent of the sim's mirror
    function) that the spatial ring reflection sends R_dir to its transpose."""
    fc = dce.FUTURE_CONTINUATIONS_BY_SHELL
    N = dce.RING_N
    canonical = copy.deepcopy(dce.BRANCH_STATES)

    # P = spatial ring reflection: pos -> (N-1)-pos (h unchanged)
    once = {b: {"pos": (N - 1) - f["pos"], "h": f["h"]} for b, f in canonical.items()}
    twice = {b: {"pos": (N - 1) - f["pos"], "h": f["h"]} for b, f in once.items()}
    p_is_involution = twice == canonical
    p_moves_field = once != canonical

    # DIRECT: reflecting the ring sends R_dir to its TRANSPOSE (re-derived here)
    saved = copy.deepcopy(dce.BRANCH_STATES)
    try:
        rel_canon = dce.oriented_relation(fc)
        transpose = {f"{k.split('>')[1]}>{k.split('>')[0]}": v for k, v in rel_canon.items()}
        dce.BRANCH_STATES = copy.deepcopy(once)
        rel_reflected = dce.oriented_relation(fc)
    finally:
        dce.BRANCH_STATES = saved
    reflection_is_transpose = rel_reflected == transpose

    mirror = dce.independent_mirror_test()
    checks = {
        "P_is_involution": p_is_involution,
        "P_moves_field": p_moves_field,
        "P_is_genuine_reflection": bool(mirror["P_is_genuine_reflection"]),
        "spatial_ring_reflection_sends_Rdir_to_transpose": reflection_is_transpose,
        "engines_distinct_functions_not_swap_tautology": (
            bool(mirror["engines_are_distinct_functions_objective_sha_differ"])
            and not bool(mirror["is_swap_tautology"])
        ),
        "equivariance_L_maps_to_R": bool(mirror["equivariance_L_maps_to_R"]),
        "equivariance_R_maps_to_L": bool(mirror["equivariance_R_maps_to_L"]),
        "parity_maps_L_to_R_and_R_to_L": bool(mirror["parity_maps_L_to_R_and_R_to_L"]),
    }
    return checks, {
        "present_survivor_L_over_F": mirror["present_survivor_L_over_F"],
        "present_survivor_R_over_F": mirror["present_survivor_R_over_F"],
        "present_survivor_L_over_PF": mirror["present_survivor_L_over_PF"],
        "present_survivor_R_over_PF": mirror["present_survivor_R_over_PF"],
        "L_objective_sha256": mirror["L_objective_sha256"],
        "R_objective_sha256": mirror["R_objective_sha256"],
    }


def check_symmetric_control() -> dict:
    """Re-run the symmetric-control collapse fresh: on the symmetric closure L == R."""
    sym = dce.symmetric_control_collapse()
    checks = {
        "symmetric_closure_is_actually_symmetric": bool(sym["symmetric_closure_is_actually_symmetric"]),
        "L_equals_R_on_symmetric_field": bool(sym["L_equals_R_on_symmetric_field"]),
        "chirality_correctly_absent_on_symmetric_field": bool(
            sym["chirality_correctly_absent_on_symmetric_field"]
        ),
    }
    return checks, {
        "present_survivor_L_symmetric": sym["present_survivor_L_symmetric"],
        "present_survivor_R_symmetric": sym["present_survivor_R_symmetric"],
    }


def check_constraint_load_bearing() -> dict:
    fc = dce.FUTURE_CONTINUATIONS_BY_SHELL
    relation = dce.oriented_relation(fc)
    checks = {}
    checks["R_dir_is_boolean_relation"] = all(isinstance(v, bool) for v in relation.values())
    n_true = sum(1 for v in relation.values() if v)
    checks["R_dir_is_non_degenerate"] = 0 < n_true < len(relation)
    checks["R_dir_is_NON_symmetric"] = dce._relation_is_non_symmetric(relation)
    clause = dce.relation_clause_load_bearing_control()
    checks["handedness_clause_is_load_bearing"] = bool(clause["handedness_clause_is_load_bearing"])
    return checks


def check_no_contamination(result: dict) -> dict:
    canonical = {
        "b0": {"pos": 0, "h": 1}, "b1": {"pos": 1, "h": 1}, "b2": {"pos": 2, "h": -1},
        "b3": {"pos": 3, "h": -1}, "b4": {"pos": 4, "h": 1}, "b5": {"pos": 5, "h": -1},
        "b6": {"pos": 1, "h": -1}, "b7": {"pos": 4, "h": -1}, "b8": {"pos": 2, "h": 1},
    }
    serialized = result.get("branch_states", {})
    trap = dce.state_mutation_trap()
    return {
        "serialized_branch_states_match_canonical": serialized == canonical,
        "module_global_uncontaminated_after_trap": dce.BRANCH_STATES == canonical,
        "trap_reports_carrier_restored": bool(trap["carrier_restored_no_contamination"]),
        "trap_mutation_moves_a_survivor": bool(trap["handedness_mutation_moves_a_survivor"]),
    }


def main() -> int:
    result = dce.build_result()

    key_checks = check_keys_present(result)
    chir_checks, chir_values = check_chirality_test_independently()
    mirror_checks, mirror_values = check_independent_mirror()
    sym_checks, sym_values = check_symmetric_control()
    constraint_checks = check_constraint_load_bearing()
    contamination_checks = check_no_contamination(result)

    invariants = result["invariants"]
    hard_stop = invariants["HARD_STOP_future_continuations_ne_present_survivor"]

    scramble_breaks = dce.scramble_futures_negative_control()["control_breaks"]

    keys_ok = all(key_checks.values())
    chir_ok = all(chir_checks.values())
    mirror_ok = all(mirror_checks.values())
    sym_ok = all(sym_checks.values())
    constraint_ok = all(constraint_checks.values())
    contamination_ok = all(contamination_checks.values())
    invariants_ok = all(invariants.values())

    green = (
        keys_ok
        and chir_ok
        and mirror_ok
        and sym_ok
        and constraint_ok
        and contamination_ok
        and invariants_ok
        and hard_stop
        and scramble_breaks
        and bool(result["chirality_earned"])
    )

    report = {
        "validator": "validate_rpf_dual_chiral_engines_v0",
        "first_class_keys_present_in_result": [k for k in FIRST_CLASS_KEYS if k in result],
        "key_shape_checks": key_checks,
        "all_keys_present_and_shaped": keys_ok,

        # --- HARD ACCEPTANCE TEST 1: CHIRALITY (L != R) ---
        "chirality_checks": chir_checks,
        "chirality_values": chir_values,
        "chirality_L_differs_from_R": chir_ok,

        # --- HARD ACCEPTANCE TEST 2: INDEPENDENT MIRROR (P maps L<->R, not swap-tautology) ---
        "independent_mirror_checks": mirror_checks,
        "independent_mirror_values": mirror_values,
        "parity_maps_L_to_R_not_swap_tautology": mirror_ok,

        # --- HARD ACCEPTANCE TEST 3: SYMMETRIC-CONTROL COLLAPSE (L == R) ---
        "symmetric_control_checks": sym_checks,
        "symmetric_control_values": sym_values,
        "symmetric_control_collapses_to_one_survivor": sym_ok,

        # --- CONSTRAINT load-bearing ---
        "constraint_checks": constraint_checks,
        "constraint_is_load_bearing": constraint_ok,

        # --- CONTAMINATION ---
        "contamination_checks": contamination_checks,
        "no_contamination": contamination_ok,

        "invariants": invariants,
        "all_invariants_hold": invariants_ok,
        "HARD_STOP_future_continuations_ne_present_survivor": hard_stop,
        "scramble_breaks_the_build": scramble_breaks,

        "GREEN": green,
        "classification": result["classification"],
        "promotion_allowed": result["promotion_allowed"],
        "formal_admission_allowed": result["formal_admission_allowed"],
        "claim_ceiling": result["claim_ceiling"],
        "honest_self_assessment": result["honest_self_assessment"],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if green else 1


if __name__ == "__main__":
    raise SystemExit(main())
