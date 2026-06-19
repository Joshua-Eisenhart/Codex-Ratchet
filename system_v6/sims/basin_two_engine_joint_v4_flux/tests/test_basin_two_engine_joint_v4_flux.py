#!/usr/bin/env python3
"""Behavior tests for basin_two_engine_joint_v4_flux."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SIM_ID = "basin_two_engine_joint_v4_flux"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
MODULE_PATH = SIM_DIR / f"{SIM_ID}_common.py"


def load_module():
    spec = importlib.util.spec_from_file_location(f"{SIM_ID}_common", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_stage1_flux_erased_reproduces_corrected_v3_cores():
    module = load_module()
    payload = module.build_flux_payload()
    stage1 = payload["stage1"]["within_engine"]

    for engine in ("L", "R"):
        assert stage1["A_readout_transition_dwell"][engine]["flux_erased"]["terminal_class_count"] == 1
        assert stage1["A_readout_transition_dwell"][engine]["flux_erased"]["terminal_sizes"] == [28]
        assert stage1["D_matrix64_b_order_overlay"][engine]["flux_erased"]["terminal_class_count"] == 1
        assert stage1["D_matrix64_b_order_overlay"][engine]["flux_erased"]["terminal_sizes"] == [24]

    assert payload["controls"]["flux_erased_continuity"]["all_pass"] is True


def test_stage1_flux_is_live_and_sign_flip_control_mirrors():
    module = load_module()
    payload = module.build_flux_payload()
    comparison = payload["stage1"]["L_R_comparison"]

    assert comparison["A_readout_transition_dwell"]["slightly_different"] is False
    assert comparison["D_matrix64_b_order_overlay"]["slightly_different"] is True
    assert payload["stage1"]["sign_flip_control"]["A_readout_transition_dwell"]["mirrors_nonzero_delta"] is True
    assert payload["stage1"]["sign_flip_control"]["D_matrix64_b_order_overlay"]["mirrors_nonzero_delta"] is True

    d_l = payload["stage1"]["within_engine"]["D_matrix64_b_order_overlay"]["L"]["flux_carried"]
    d_r = payload["stage1"]["within_engine"]["D_matrix64_b_order_overlay"]["R"]["flux_carried"]
    assert d_l["terminal_sizes"] == [48]
    assert d_r["terminal_sizes"] == [24, 24]


def test_stage2_source_rows_and_fenced_controls():
    module = load_module()
    payload = module.build_flux_payload()
    rows = payload["stage2"]["coupling_rows"]

    for variant_id, coupling_rows in rows.items():
        assert coupling_rows["C1_constrained_fibered_placement"]["accepted_as_primary_evidence"] is True
        assert coupling_rows["C2_fibered_system"]["accepted_as_primary_evidence"] is True
        assert coupling_rows["O6_720_double_cover"]["accepted_as_primary_evidence"] is True
        assert coupling_rows["contrast_sync_non_source_faithful"]["accepted_as_primary_evidence"] is False
        assert coupling_rows["contrast_full_interleave_non_source_faithful"]["accepted_as_primary_evidence"] is False
        assert payload["stage2"]["product_controls"][variant_id]["by_construction"] is True
        assert payload["stage2"]["product_controls"][variant_id]["accepted_as_primary_evidence"] is False

    assert payload["prediction_adjudication"]["source_valid_primary_64_level_count"] == 0


def test_projection_checks_and_smt_flips_are_bound_to_counts():
    module = load_module()
    payload = module.build_flux_payload()

    checks = payload["stage2"]["one_sided_projection_checks"]
    assert len(checks) == 4
    assert all(check["frozen_factor_echo_detected"] is True for check in checks)

    proofs = payload["crossover_proofs"]
    assert proofs["z3"]["verdict"] == "unsat"
    assert proofs["cvc5"]["verdict"] == "unsat"
    assert proofs["z3"]["flipped_control_verdict"] == "sat"
    assert proofs["cvc5"]["flipped_control_verdict"] == "sat"
    assert proofs["proof_row"]["asserted_precomputed_boolean"] is False


def test_no_builder_audit_verdict_and_packet_ceiling():
    module = load_module()
    payload = module.build_flux_payload()

    assert not (SIM_DIR / "audit_verdict.md").exists()
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["build_gates"]["no_builder_audit_verdict"] is True

