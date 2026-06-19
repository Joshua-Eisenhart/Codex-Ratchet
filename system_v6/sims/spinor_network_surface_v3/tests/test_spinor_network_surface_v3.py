from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SIM_DIR = ROOT / "system_v6" / "sims" / "spinor_network_surface_v3"
RESULT_DIR = SIM_DIR / "results"


def load_envelope() -> dict:
    return json.loads((RESULT_DIR / "spinor_network_surface_v3_envelope_results.json").read_text(encoding="utf-8"))


def test_builder_boundary_and_classification() -> None:
    env = load_envelope()
    assert env["classification"] == "scratch_diagnostic"
    assert env["promotion_allowed"] is False
    assert env["formal_admission_allowed"] is False
    assert env["no_builder_audit_verdict"] is True
    assert env["builder_gates"]["no_builder_audit_verdict"] is True
    assert not (SIM_DIR / "audit_verdict.md").exists()
    assert env["all_pass"] is True


def test_falsifier_reachability_controls_fail_through_real_predicate() -> None:
    env = load_envelope()
    controls = env["negative_section"]["no_structure_controls"]
    assert set(controls) == {
        "maximally_mixed_state",
        "quotient_erased_state",
        "off_axis_rotated_states",
        "wrong_row_classifier",
    }
    for row in controls.values():
        assert row["verdict"] == "RECOVERY_FAIL"
        assert row["control_fired"] is True
        assert row["registered_falsifier_fired"] is True
        assert row["classifier_id"] == "A33_committed_predeclared"
    assert controls["maximally_mixed_state"]["recovered_nonorigin_cell_count"] == 0
    assert controls["quotient_erased_state"]["recovered_nonorigin_cell_count"] == 0
    assert controls["off_axis_rotated_states"]["identity_pairs_match_expected"] is False
    assert controls["wrong_row_classifier"]["identity_pairs_match_expected"] is False
    assert "permuted row-label ledger" in controls["wrong_row_classifier"]["control_design"]
    assert env["negative_section"]["falsifier_reachability"]["control_fail_count"] == 4


def test_recoverability_is_pre_registered_partial_prediction() -> None:
    env = load_envelope()
    verdict = env["recoverability_VERDICT"]
    assert verdict["verdict"] == "PARTIAL_PREDICTED_CELL_RECOVERY"
    assert verdict["recovered_nonorigin_cell_count"] == 10
    assert verdict["load_bearing_recovered_nonorigin_cell_count"] == 4
    assert verdict["expected_cell_count"] == 33
    assert len(verdict["recovered_nonorigin_cell_ids"]) == 10
    assert set(verdict["load_bearing_family_cell_pairs"]) == {
        "entangled_nonproduct:A33_x00_y00_zp10",
        "estate_chiral_quaternion_Hopf_Weyl:A33_xp10_y00_z00",
        "estate_chiral_quaternion_Hopf_Weyl:A33_xp5_y00_zm5",
        "estate_chiral_quaternion_Hopf_Weyl:A33_xp5_y00_zp5",
    }
    prereg = env["pre_registered_structured_prediction"]
    assert prereg["pre_registered_before_run"] is True
    assert prereg["expected_predicted_pair_count"] == 4
    assert prereg["recovered_predicted_pair_count"] == 3
    assert prereg["missed_predicted_family_cell_pairs"] == ["entangled_nonproduct:A33_x00_y00_zm10"]
    assert prereg["verdict"] == "PARTIAL_PREDICTED_CELL_RECOVERY"
    null = env["haar_null_row"]
    assert null["trials"] == 2048
    assert 7.0 <= null["expected_nonorigin_cell_count"] <= 8.3
    assert null["observed_load_bearing_nonorigin_cell_count"] == 0
    assert null["observed_family_tied_pair_count"] == 0


def test_per_family_table_names_bias_and_load_bearing_rows() -> None:
    env = load_envelope()
    rows = env["per_family_recovery_table"]
    load_bearing = [row for row in rows if row["load_bearing_for_identity_claim"] is True]
    assert len(load_bearing) == 3
    assert {row["family_id"] for row in load_bearing} == {
        "estate_chiral_quaternion_Hopf_Weyl",
        "entangled_nonproduct",
    }
    seed_controls = [row for row in rows if str(row["family_id"]).startswith("precommitted_seed_control_")]
    assert {row["seed"] for row in seed_controls} == {20260611, 20260612, 777, 31337}
    for row in seed_controls:
        assert row["seed_hash"]


def test_a33_ceiling_kraus_choi_and_v1_anchor_rows() -> None:
    env = load_envelope()
    a33 = env["A33_reachability_ceiling"]
    assert a33["geometric_ceiling_cell_count"] == 33
    assert a33["recovered_reachable_cell_count"] == 10
    assert len(a33["reachable_not_recovered_cell_ids"]) == 23
    kraus = env["kraus_choi_witness_ledger"]
    assert kraus["witness_count"] == 10
    assert kraus["all_completeness_pass"] is True
    assert kraus["all_choi_positivity_pass"] is True
    assert kraus["all_trace_preserving_pass"] is True
    anchor = env["v1_anchor_reproduction"]["actual"]
    assert set(anchor["recovered_nonorigin_cell_ids"]) == {
        "A33_x00_y00_zp10",
        "A33_x00_yp5_z00",
        "A33_xp10_y00_z00",
        "A33_xp5_y00_z00",
        "A33_xp5_y00_zm5",
        "A33_xp5_y00_zp5",
    }


def test_transition_graph_spurious_coverage_and_escape_evidence() -> None:
    env = load_envelope()
    basin = env["basin_partition"]
    assert basin["node_count"] == 48
    assert basin["edge_count"] == 48
    assert basin["terminal_scc_count"] == 14
    assert basin["stored_patterns_all_trapping"] is True
    assert basin["absent_exit_ok"] is True
    assert basin["spurious_attractor_count"] == 6
    coverage = basin["coverage"]
    assert coverage["pair_mixture_enumerated"] == coverage["pair_mixture_denominator"] == 6
    assert len(env["spurious_attractor_table"]) == 6
    spurious3 = env["three_pattern_spurious_extension"]
    assert spurious3["coverage_enumerated"] == spurious3["coverage_denominator"] == 4
    assert spurious3["spurious3_detected_count"] == 0
    assert len(spurious3["rows"]) == 4
    assert env["escape_graph_evidence"]["trajectory_count"] == coverage["seed_state_count"] == 14


def test_typed_entropy_gate_and_nonhermitian_same_row_control() -> None:
    env = load_envelope()
    typed = env["typed_information"]
    assert typed["bipartition"] == {"A": [0], "B": [1, 2, 3]}
    assert typed["entangled_negative_conditional_rows"]
    assert env["premature_typed_row_control"]["raised"] is True
    nonhermitian = env["nonhermitian_control"]
    assert nonhermitian["control_fired"] is True
    assert nonhermitian["same_row_as_positive_claim"] == "V(rho)=1-max terminal fidelity"
    assert nonhermitian["lyapunov_delta"] > 0


def test_pytorch_autograd_and_source_boundaries() -> None:
    env = load_envelope()
    pytorch = env["engines"]["pytorch"]
    assert "torch.func" in pytorch["aligned_packages_load_bearing"]
    torch_func_rows = [row for row in pytorch["tool_calls"] if row["tool"] == "torch.func"]
    assert torch_func_rows
    assert torch_func_rows[0]["output_object"]["descent_verified"] is True
    assert env["boundary_section"]["independence_boundary"].startswith("Julia/JAX/PyTorch are self-contained")
    assert len(env["source_line_quotes"]) == 4
