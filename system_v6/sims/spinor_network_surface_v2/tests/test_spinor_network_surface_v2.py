from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SIM_DIR = ROOT / "system_v6" / "sims" / "spinor_network_surface_v2"
RESULT_DIR = SIM_DIR / "results"


def load_envelope() -> dict:
    return json.loads((RESULT_DIR / "spinor_network_surface_v2_envelope_results.json").read_text(encoding="utf-8"))


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


def test_recoverability_is_family_tied_identity_above_haar_null() -> None:
    env = load_envelope()
    verdict = env["recoverability_VERDICT"]
    assert verdict["verdict"] == "RECOVERY_PASS_FAMILY_TIED_IDENTITY_ABOVE_HAAR_NULL"
    assert verdict["recovered_nonorigin_cell_count"] == 16
    assert verdict["load_bearing_recovered_nonorigin_cell_count"] == 11
    assert verdict["expected_cell_count"] == 33
    assert len(verdict["recovered_nonorigin_cell_ids"]) == 16
    assert len(verdict["load_bearing_family_cell_pairs"]) == 16
    null = env["haar_null_row"]
    assert null["trials"] == 2048
    assert 7.0 <= null["expected_nonorigin_cell_count"] <= 8.3
    assert null["observed_load_bearing_nonorigin_cell_count"] == 11
    assert null["observed_identity_surprisal"] > null["null_identity_surprisal_mean"]
    assert null["identity_surprisal_z"] > 0.0
    assert null["verdict"] == "IDENTITY_ABOVE_NULL"


def test_per_family_table_names_bias_and_load_bearing_rows() -> None:
    env = load_envelope()
    rows = env["per_family_recovery_table"]
    load_bearing = [row for row in rows if row["load_bearing_for_identity_claim"] is True]
    assert len(load_bearing) == 4
    assert {row["family_id"] for row in load_bearing} == {
        "haar_pinned_seed_6608",
        "haar_pinned_seed_6609",
        "haar_pinned_seed_6610",
        "haar_pinned_seed_6611",
    }
    for row in load_bearing:
        assert row["bias_class"] == "haar_sampled_then_seed_pinned_no_preferred_chart_axis"
        assert row["seed_hash"]
        assert row["recovered_nonorigin_cell_count"] == 4


def test_a33_ceiling_kraus_choi_and_v1_anchor_rows() -> None:
    env = load_envelope()
    a33 = env["A33_reachability_ceiling"]
    assert a33["geometric_ceiling_cell_count"] == 33
    assert a33["recovered_reachable_cell_count"] == 16
    assert len(a33["reachable_not_recovered_cell_ids"]) == 17
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
