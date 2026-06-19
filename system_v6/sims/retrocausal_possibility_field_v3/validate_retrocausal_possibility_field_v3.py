#!/usr/bin/env python3
"""
Validator for retrocausal_possibility_field_v3.

Written to the v3 HARD ACCEPTANCE bar (the controller re-runs it fresh). It asserts
(and reports), re-deriving the load-bearing facts from the sim module rather than
trusting the stored result booleans:

  1. ALL first-class object keys present in the result JSON and genuinely shaped.
  2. ALL required invariants hold on the canonical instance (incl. the v3 acceptance
     gate, the v1 SHELL_REASSIGNMENT_MOVES_SURVIVOR, the v2 orientation-emergence).
  3. The HARD-STOP holds: future_continuations != present_survivor.

  THE v3 DECISIVE ACCEPTANCE GATE (the Wizard verdict's demand):
  4. Re-run BOTH selectors fresh from the sim module on the canonical inputs and
     assert present_survivor_retro != present_survivor_forward (the genuine global
     co-admissibility compressor is PROBE-DISTINGUISHABLE from forward sequential
     selection). The validator also confirms the global joint assignment beats the
     greedy path on the co-admissible pair count (the divergence is a real
     global-vs-greedy gap, not a tie-break accident). If they were identical the
     validator FAILS (retrocausal not earned).
  5. CONSTRAINT C is the load-bearing source of compatibility: the compatibility
     structure is a BOOLEAN relation over pairs (not a similarity weight); it is
     NON-degenerate; and the parity_drop control changes the survivor (each clause
     matters); the uniform (all-True) constraint collapses the earned probe.

  ORIENTATION DERIVED FROM MEASURED FIBER CARDINALITY (adopted from v2):
  6. NO shell carries a stipulated orientation string; orientation is re-derived from
     the stored per-stratum fiber cardinality and matches the instance label; the
     emergence control (reverse the cardinality -> the label flips) holds, re-run
     fresh in both directions and end-to-end.

  CONTAMINATION FIX (the v1 b3.a=6 bug):
  7. The serialized branch_states equals the canonical carrier (the state-mutation
     trap restored it via deepcopy and never contaminated the object).

  RETAINED WINS:
  8. shell-reassignment (union identical) MOVES the present_survivor.
  9. scramble breaks the build; state-mutation moves the survivor.

Exits 0 (green) only if ALL of the above hold.

Run:  <sim-stack python3> validate_retrocausal_possibility_field_v3.py
"""

from __future__ import annotations

import copy
import json
import os
import sys

SIM_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SIM_DIR)

import retrocausal_possibility_field_v3 as rpf  # noqa: E402


FIRST_CLASS_KEYS = rpf.FIRST_CLASS_KEYS


def check_keys_present(result: dict) -> dict:
    """Each first-class key present AND genuinely shaped (not a degenerate proxy).
    Note: v3's compatibility field is the boolean relation C; the FIRST_CLASS_KEYS
    list keeps the canonical 'compatibility_weights' slot name, satisfied here by the
    present compatibility_relation_C field."""
    checks = {}
    for k in FIRST_CLASS_KEYS:
        if k == "compatibility_weights":
            checks[f"key_present:{k}_as_compatibility_relation_C"] = (
                "compatibility_relation_C" in result
            )
        else:
            checks[f"key_present:{k}"] = k in result

    fc = result.get("future_continuations", {})
    checks["future_continuations_is_shell_keyed_dict_of_lists"] = (
        isinstance(fc, dict)
        and len(fc) >= 1
        and all(isinstance(v, list) and len(set(v)) >= 2 for v in fc.values())
    )
    rel = result.get("compatibility_relation_C", {})
    checks["compatibility_is_boolean_pair_relation_not_similarity_weight"] = (
        isinstance(rel, dict)
        and len(rel) >= 1
        and all("|" in k for k in rel.keys())
        and all(isinstance(v, bool) for v in rel.values())
    )
    cm = result.get("compression_map", {})
    checks["compression_map_is_global_joint_compressor"] = (
        isinstance(cm, dict)
        and cm.get("selector") == "retrocausal_global_compressor"
        and cm.get("direction") == "INWARD"
        and isinstance(cm.get("global_joint_assignment"), dict)
        and len([s for s in cm.get("per_stratum", []) if s.get("branches_on_shell")]) >= 2
    )
    fwd = result.get("forward_sequential_control", {})
    checks["forward_sequential_control_present_with_no_inward_semantics"] = (
        isinstance(fwd, dict)
        and fwd.get("selector") == "forward_sequential_selector"
        and "NO inward/retrocausal semantics" in fwd.get("semantics", "")
    )
    rec = result.get("outward_record", {})
    checks["outward_record_is_outward_hash_chain"] = (
        isinstance(rec, dict)
        and rec.get("record_orientation") == "OUTWARD"
        and bool(rec.get("append_only_recomputed"))
        and bool(rec.get("reflects_per_shell_compression_steps"))
    )
    return checks


def check_acceptance_gate_independently() -> dict:
    """
    THE v3 CORE CHECK. Re-run the genuine compressor and BOTH forward selectors fresh
    from the sim module and assert the genuine compressor DIFFERS from BOTH forward
    variants (the single-anchor selector AND the strongest full-history selector), and
    that the global optimum genuinely beats both greedy paths on the co-admissible pair
    count (a real global-vs-greedy gap, not a tie-break accident, and not defeatable by
    a stronger forward tie-break).
    """
    checks: dict[str, bool] = {}

    fc = rpf.FUTURE_CONTINUATIONS_BY_SHELL
    relation = rpf.co_admissibility_relation(fc)
    forward = rpf.forward_sequential_selector(fc, relation, rpf.SHELLS)
    forward_hist = rpf.forward_full_history_selector(fc, relation, rpf.SHELLS)
    retro = rpf.retrocausal_global_compressor(fc, relation, rpf.SHELLS)

    fwd_survivor = forward["present_survivor_forward"]
    fwd_hist_survivor = forward_hist["present_survivor_full_history"]
    retro_survivor = retro["present_survivor_retro"]

    checks["forward_and_retro_run_on_same_inputs"] = True
    checks["retrocausal_survivor_DIFFERS_from_single_anchor_forward"] = (
        fwd_survivor != retro_survivor
    )
    checks["retrocausal_survivor_DIFFERS_from_full_history_forward"] = (
        fwd_hist_survivor != retro_survivor
    )

    def coadm_count(ids: list[str]) -> int:
        return sum(
            1
            for i in range(len(ids))
            for j in range(i + 1, len(ids))
            if relation.get(rpf.pair_key(ids[i], ids[j]), False)
        )

    fwd_count = coadm_count(list(dict(forward["forward_path"]).values()))
    fwd_hist_count = coadm_count(list(forward_hist["committed_assignment"].values()))
    checks["global_optimum_beats_single_anchor_path"] = retro["global_coadm_pair_count"] > fwd_count
    checks["global_optimum_beats_full_history_path"] = retro["global_coadm_pair_count"] > fwd_hist_count

    return checks, {
        "present_survivor_forward": fwd_survivor,
        "present_survivor_forward_full_history": fwd_hist_survivor,
        "present_survivor_retro": retro_survivor,
        "forward_coadm_pair_count": fwd_count,
        "forward_full_history_coadm_pair_count": fwd_hist_count,
        "global_coadm_pair_count": retro["global_coadm_pair_count"],
    }


def check_constraint_C_is_load_bearing() -> dict:
    """C is the derived source of compatibility AND each clause matters."""
    checks: dict[str, bool] = {}

    fc = rpf.FUTURE_CONTINUATIONS_BY_SHELL
    relation = rpf.co_admissibility_relation(fc)

    # boolean relation, non-degenerate
    checks["C_is_boolean_relation"] = all(isinstance(v, bool) for v in relation.values())
    n_true = sum(1 for v in relation.values() if v)
    checks["C_is_non_degenerate"] = 0 < n_true < len(relation)

    # parity clause load-bearing: dropping it changes the survivor
    parity = rpf.parity_drop_control()
    checks["parity_clause_load_bearing"] = bool(parity["parity_clause_is_load_bearing"])

    # uniform (all-True) constraint collapses the earned probe
    uniform = rpf.uniform_constraint_control()
    checks["uniform_constraint_collapses_the_probe"] = bool(
        uniform["uniform_correctly_kills_the_probe"]
    )
    return checks


def check_orientation_derived_not_stored(result: dict) -> dict:
    """Orientation re-derived from stored fiber cardinality, NO stored string, and
    the emergence control flips the label both ways (re-run fresh)."""
    checks: dict[str, bool] = {}

    shells = result.get("shells", [])
    checks["no_shell_carries_stipulated_orientation_string"] = all(
        "shell_orientation" not in s for s in shells
    )

    shell_orientation = result.get("shell_orientation", {})
    cm = result.get("compression_map", {})
    rec = result.get("outward_record", {})

    inward_ok = True
    nonempty = [s for s in cm.get("per_stratum", []) if s.get("branches_on_shell")]
    if len(nonempty) < 2:
        inward_ok = False
    for s in nonempty:
        meas = s.get("fiber_cardinality", {})
        rederived = rpf.derive_orientation(meas)
        if not (meas.get("max_fiber", 0) > 1):
            inward_ok = False
        if rederived != "INWARD":
            inward_ok = False
        if rederived != s.get("derived_orientation"):
            inward_ok = False
        if rederived != shell_orientation.get(s["shell_id"]):
            inward_ok = False
    checks["inward_orientation_rederived_from_fiber_cardinality_matches"] = inward_ok

    rec_meas = rec.get("record_fiber_cardinality", {})
    rec_rederived = rpf.derive_orientation(rec_meas)
    checks["record_orientation_rederived_from_injectivity_matches"] = (
        bool(rec_meas.get("injective"))
        and rec_rederived == "OUTWARD"
        and rec_rederived == rec.get("record_orientation")
        and rec_rederived == shell_orientation.get(rec.get("record_shell_id"))
    )

    checks["compression_flags_direction_is_derived"] = bool(
        cm.get("direction_is_derived_from_fiber_cardinality")
    )
    checks["record_flags_orientation_is_derived"] = bool(
        rec.get("record_orientation_is_derived_from_fiber_cardinality")
    )

    # emergence control re-run fresh in both directions
    base = rpf.build_object_instance()
    sample = [s for s in base["compression_map"]["per_stratum"] if s["branches_on_shell"]][0]
    actual_inward = rpf.derive_orientation(rpf.measure_fiber_cardinality(sample["stratum_map"]))
    injective_map = {b: f"img_{b}" for b in sample["branches_on_shell"]}
    reversed_inward = rpf.derive_orientation(rpf.measure_fiber_cardinality(injective_map))
    checks["inward_orientation_flips_under_reversal"] = (
        actual_inward == "INWARD" and reversed_inward == "OUTWARD"
    )

    actual_record = rpf.derive_orientation(
        rpf.measure_fiber_cardinality(base["outward_record"]["record_map"])
    )
    domain = sorted(base["outward_record"]["record_map"].keys())
    collapsed = {ev: "one_image" for ev in domain}
    reversed_record = rpf.derive_orientation(rpf.measure_fiber_cardinality(collapsed))
    checks["record_orientation_flips_under_reversal"] = (
        actual_record == "OUTWARD" and reversed_record == "INWARD"
    )

    record_shell_id = base["outward_record"]["record_shell_id"]
    reversed_instance = rpf.build_object_instance(record_map_override=collapsed)
    checks["record_flips_end_to_end_full_rebuild"] = (
        base["shell_orientation"][record_shell_id] == "OUTWARD"
        and reversed_instance["shell_orientation"][record_shell_id] == "INWARD"
    )
    return checks


def check_no_contamination(result: dict) -> dict:
    """The v1 bug fix: the serialized branch_states equals the canonical carrier."""
    canonical = {
        "b0": {"a": 0, "b": 0}, "b1": {"a": 0, "b": 1}, "b2": {"a": 1, "b": 0},
        "b3": {"a": 1, "b": 1}, "b4": {"a": 2, "b": 0}, "b5": {"a": 2, "b": 2},
        "b6": {"a": 3, "b": 1}, "b7": {"a": 3, "b": 3}, "b8": {"a": 0, "b": 3},
    }
    serialized = result.get("branch_states", {})
    # run the mutation trap, then confirm the module global is still canonical
    trap = rpf.state_mutation_trap()
    return {
        "serialized_branch_states_match_canonical": serialized == canonical,
        "module_global_uncontaminated_after_trap": rpf.BRANCH_STATES == canonical,
        "trap_reports_carrier_restored": bool(trap["carrier_restored_no_contamination"]),
    }


def main() -> int:
    result = rpf.build_result()

    key_checks = check_keys_present(result)
    gate_checks, gate_values = check_acceptance_gate_independently()
    constraint_checks = check_constraint_C_is_load_bearing()
    orientation_checks = check_orientation_derived_not_stored(result)
    contamination_checks = check_no_contamination(result)

    invariants = result["invariants"]
    hard_stop = invariants["HARD_STOP_future_continuations_ne_present_survivor"]

    reassignment = rpf.shell_reassignment_control()
    shell_reassignment_moves = (
        reassignment["union_identical"] and reassignment["shell_reassignment_moves_survivor"]
    )
    scramble_breaks = rpf.scramble_futures_negative_control()["control_breaks"]
    state_trap = rpf.state_mutation_trap()
    state_mutation_moves = state_trap["state_mutation_moves_survivor"]

    keys_ok = all(key_checks.values())
    gate_ok = all(gate_checks.values())
    constraint_ok = all(constraint_checks.values())
    orientation_ok = all(orientation_checks.values())
    contamination_ok = all(contamination_checks.values())
    invariants_ok = all(invariants.values())

    green = (
        keys_ok
        and gate_ok
        and constraint_ok
        and orientation_ok
        and contamination_ok
        and invariants_ok
        and hard_stop
        and shell_reassignment_moves
        and scramble_breaks
        and state_mutation_moves
        and bool(result["retrocausal_earned"])
    )

    report = {
        "validator": "validate_retrocausal_possibility_field_v3",
        "first_class_keys_present_in_result": [
            k for k in FIRST_CLASS_KEYS
            if (k in result) or (k == "compatibility_weights" and "compatibility_relation_C" in result)
        ],
        "key_shape_checks": key_checks,
        "all_keys_present_and_shaped": keys_ok,

        # --- THE v3 DECISIVE ACCEPTANCE GATE (re-derived fresh) ---
        "acceptance_gate_checks": gate_checks,
        "acceptance_gate_values": gate_values,
        "retrocausal_earned_differs_from_forward_selection": gate_ok,

        # --- CONSTRAINT C is the load-bearing derived source of compatibility ---
        "constraint_C_checks": constraint_checks,
        "constraint_C_is_load_bearing": constraint_ok,

        # --- ORIENTATION derived from measured fiber cardinality ---
        "orientation_checks": orientation_checks,
        "orientation_is_derived_and_emergent": orientation_ok,

        # --- CONTAMINATION fix (v1 bug) ---
        "contamination_checks": contamination_checks,
        "no_contamination": contamination_ok,

        "invariants": invariants,
        "all_invariants_hold": invariants_ok,
        "HARD_STOP_future_continuations_ne_present_survivor": hard_stop,

        # --- retained wins ---
        "shell_reassignment_moves_survivor": shell_reassignment_moves,
        "shell_reassignment_base_survivor": reassignment["base_present_survivor"],
        "shell_reassignment_reassigned_survivor": reassignment["reassigned_present_survivor"],
        "scramble_breaks_the_build": scramble_breaks,
        "state_mutation_moves_survivor": state_mutation_moves,

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
