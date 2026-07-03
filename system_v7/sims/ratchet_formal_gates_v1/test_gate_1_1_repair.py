#!/usr/bin/env python3
"""Regression checks for the Gate 1.1 repair round."""

from __future__ import annotations

import ratchet_formal_gates_numpy as gates


def test_r5_token_identity_is_derived_from_tuple_fields() -> None:
    smt = gates.smt_gates()["token_identity_R5"]
    assert "content_id" in smt["formal_criterion"]
    assert "probe_signature" in smt["formal_criterion"]
    assert smt["identity_grounding"] == "probe_signature_not_content_id"
    assert smt["content_id_role"] == "provenance_metadata_only"
    assert smt["domain_quantification"]["all_tuple_pairs_checked"] is True
    assert smt["content_perturbation_same_probe_signature"]["z3_violation"] == "unsat"
    assert smt["content_perturbation_same_probe_signature"]["cvc5_violation"] == "unsat"
    assert smt["different_probe_signature"]["z3_violation"] == "unsat"
    assert smt["different_probe_signature"]["cvc5_violation"] == "unsat"


def test_r6_progress_derives_nonstep_and_fuel_bound() -> None:
    progress = gates.smt_gates()["progress_measure_R6"]
    assert progress["registers"] == {
        "X": "finite set bitmask",
        "H": "finite counter/sequence id",
        "Q": "finite quotient class count",
    }
    assert progress["non_step_predicate"].startswith("derived:")
    assert progress["register_equality_objectivity"]["z3_definition_violation"] == "unsat"
    assert progress["register_equality_objectivity"]["cvc5_definition_violation"] == "unsat"
    assert progress["anti_stall_fuel_bound"]["K"] >= 1
    assert progress["anti_stall_fuel_bound"]["z3_with_axioms"] == "unsat"
    assert progress["anti_stall_fuel_bound"]["z3_erased_fuel_axiom"] == "sat"
    assert progress["anti_stall_fuel_bound"]["cvc5_with_axioms"] == "unsat"
    assert progress["anti_stall_fuel_bound"]["cvc5_erased_fuel_axiom"] == "sat"


def test_r4_materializes_roster_formula_and_probe_epoching() -> None:
    states = gates.enumerate_carrier()
    quotient = gates.quotient_classes(states)
    assert quotient["roster_formula"]["formula"] == "8 terrains x (1 fixed + 2 native operators x 2 order states)"
    assert quotient["roster_formula"]["expected_count"] == 40
    assert quotient["roster_formula"]["actual_count"] == 40
    assert quotient["roster_formula"]["count_matches_formula"] is True
    epoching = quotient["probe_epoching"]
    assert epoching["equivalence_scope"] == "within_epoch_only"
    assert epoching["cross_epoch_identity_rule"] == "requires_reprojection"
    assert epoching["two_epoch_example"]["lineage_survives_reprojection"] is True
    assert epoching["two_epoch_example"]["full_pauli_epoch"]["quotient_class_count"] == 40
    assert epoching["two_epoch_example"]["coarse_z_epoch"]["multi_representative_class_count"] > 0


def test_xi_ref_runs_on_nontrivial_coarse_probe_quotient() -> None:
    states = gates.enumerate_carrier()
    coarse = gates.coarse_probe_quotient_classes(states)
    xi = gates.xi_ref_lift_check(states, coarse)
    assert coarse["probe_epoch_id"] == "M_coarse_single_qubit_Z"
    assert coarse["multi_representative_class_count"] > 0
    assert xi["probe_epoch_id"] == "M_coarse_single_qubit_Z"
    assert xi["multi_representative_class_count"] > 0
    if xi["gate_pass"]:
        assert xi["status"] == "quotient_lift_constructed_nontrivial"
    else:
        assert xi["status"] == "demoted_to_raw_carrier_discriminator"
        assert xi["failure_count"] > 0
