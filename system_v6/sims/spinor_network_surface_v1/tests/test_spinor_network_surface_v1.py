from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SIM_DIR = ROOT / "system_v6" / "sims" / "spinor_network_surface_v1"
RESULT_DIR = SIM_DIR / "results"


def load_envelope() -> dict:
    return json.loads((RESULT_DIR / "spinor_network_surface_v1_envelope_results.json").read_text(encoding="utf-8"))


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
    assert env["negative_section"]["falsifier_reachability"]["control_fail_count"] == 4


def test_recoverability_is_nontrivial_partial_not_full_a33() -> None:
    env = load_envelope()
    verdict = env["recoverability_VERDICT"]
    assert verdict["verdict"] == "RECOVERY_PASS_NONTRIVIAL_PARTIAL_A33"
    assert verdict["recovered_nonorigin_cell_count"] == 6
    assert verdict["expected_cell_count"] == 33
    assert len(verdict["recovered_nonorigin_cell_ids"]) == 6


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
