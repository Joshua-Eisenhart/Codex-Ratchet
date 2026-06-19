#!/usr/bin/env python3
"""Behavior tests for basin_two_engine_joint_v0."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SIM_ID = "basin_two_engine_joint_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
MODULE_PATH = SIM_DIR / f"{SIM_ID}_common.py"


def load_module():
    spec = importlib.util.spec_from_file_location(f"{SIM_ID}_common", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_joint_hierarchy_earns_64_subsubbasins_without_promotion():
    module = load_module()
    payload = module.build_joint_payload()

    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["joint_object"]["state_count"] == 64
    assert payload["joint_object"]["stage_configuration_shape"] == [8, 8]

    hierarchy = payload["hierarchy"]
    assert hierarchy["basins"]["both"]["terminal_class_count"] == 1
    assert hierarchy["subbasins"]["synchronous"]["terminal_class_count"] == 8
    assert hierarchy["subbasins"]["l_only"]["terminal_class_count"] == 8
    assert hierarchy["subbasins"]["r_only"]["terminal_class_count"] == 8
    assert hierarchy["subsubbasins"]["earned_count"] == 64
    assert hierarchy["subsubbasins"]["class_size_multiset"] == [1] * 64
    assert hierarchy["subsubbasins"]["promotion_allowed"] is False

    adjudication = payload["prediction_adjudication"]
    assert adjudication["pre_registered_count"] == 64
    assert adjudication["computed_subsubbasin_count"] == 64
    assert adjudication["count_result"] == "confirmed_at_scratch_ceiling"
    assert adjudication["realized_factorization"] == "8x8_joint_stage_configuration"
    assert adjudication["candidate_factorizations"]["8x8_joint_stage_configuration"]["status"] == "realized"
    assert adjudication["candidate_factorizations"]["64_matrix"]["status"] == "cardinality_compatible_not_structure_identified"
    assert adjudication["candidate_factorizations"]["16x4"]["status"] == "not_realized_by_primary_partition"


def test_signature_is_label_free_and_permutation_stable():
    module = load_module()
    payload = module.build_joint_payload()

    discipline = payload["signature_discipline"]
    assert discipline["order_blind"] is True
    assert discipline["label_free"] is True
    assert discipline["forbidden_components_present"] == []
    assert discipline["signature_component_names"] == [
        "l_marginal_terminal_equivalence_class",
        "r_marginal_terminal_equivalence_class",
        "synchronous_orbit_equivalence_class",
    ]

    label_control = payload["controls"]["label_permutation"]
    assert label_control["fired"] is True
    assert label_control["count_invariant"] is True
    assert label_control["class_size_multiset_invariant"] is True
    assert label_control["permuted_subsubbasin_count"] == 64

    decode = payload["controls"]["decode_test"]
    assert decode["passed"] is True
    assert decode["stage_label_recovered"] is False
    assert decode["stage_order_recovered"] is False
    assert decode["automorphism_lower_bound"] == "8!*8!"


def test_may_must_terminal_and_morse_rows_are_present_at_all_levels():
    module = load_module()
    payload = module.build_joint_payload()

    for row in payload["hierarchy"]["level_rows"]:
        assert row["terminal_classes"]
        assert row["morse_ordering"]["nodes"]
        assert row["may_must_partition"]["rows"]
        for terminal in row["terminal_classes"]:
            assert terminal["absent_exit_proof"]["no_exit"] is True

    both = payload["hierarchy"]["basins"]["both"]
    assert both["may_must_partition"]["rows"][0]["can_reach_terminal"]["size"] == 64
    assert both["may_must_partition"]["rows"][0]["sure_basin_omega_containment"]["size"] == 64
    sync = payload["hierarchy"]["subbasins"]["synchronous"]
    assert sorted(r["can_reach_terminal"]["size"] for r in sync["may_must_partition"]["rows"]) == [8] * 8
    assert sorted(r["sure_basin_omega_containment"]["size"] for r in sync["may_must_partition"]["rows"]) == [8] * 8


def test_lr_structure_controls_and_smt_flip_are_bound_to_computation():
    module = load_module()
    payload = module.build_joint_payload()

    lr = payload["lr_structure_rows"]
    assert lr["chirality_asymmetry"]["topological_partition_differs"] is False
    assert lr["chirality_asymmetry"]["trace_word_differs"] is True
    assert lr["chirality_asymmetry"]["mirror_law_scope"] == "family_local_no_universal_mirror_assumed"
    assert lr["noncommutation"]["state_partition_moves"] is False
    assert lr["noncommutation"]["trace_order_moves"] is True

    controls = payload["controls"]
    assert controls["similarity_cluster_contrast"]["fired"] is True
    assert controls["root_off"]["fired"] is True
    assert controls["single_engine_marginals"]["l_terminal_count"] == 8
    assert controls["single_engine_marginals"]["r_terminal_count"] == 8

    proofs = payload["crossover_proofs"]
    assert proofs["z3"]["verdict"] == "unsat"
    assert proofs["z3"]["erased_flip_verdict"] == "sat"
    assert proofs["cvc5"]["verdict"] == "unsat"
    assert proofs["cvc5"]["erased_flip_verdict"] == "sat"
    assert proofs["proof_row"]["computed_subsubbasin_count"] == 64
    assert proofs["proof_row"]["asserted_precomputed_boolean"] is False


def test_secondary_carrier_row_is_bounded_and_nonclaiming():
    module = load_module()
    payload = module.build_joint_payload()

    row = payload["secondary_carrier_grid_product_sample"]
    assert row["sample_shape"] == [4, 4]
    assert row["state_count"] == 16
    assert row["dense_carrier"] is False
    assert row["claim_role"] == "consistency_row_only"
    assert row["subsubbasin_count_claim"] is None
