from __future__ import annotations

import json
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
RESULT_DIR = SIM_DIR / "results"
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

import basin_dof_perturb_and_read_v0_common as common  # noqa: E402
import validate_basin_dof_perturb_and_read_v0 as validator  # noqa: E402


def load_envelope() -> dict:
    return json.loads((RESULT_DIR / f"{common.SIM_ID}_envelope_results.json").read_text(encoding="utf-8"))


def test_build_card_and_boundary_fields() -> None:
    build_card = SIM_DIR / "build_card.md"
    assert build_card.is_file()
    text = build_card.read_text(encoding="utf-8")
    assert "basin_dof_perturb_and_read_v0" in text
    assert "basin_dof_readout_rows_only" in text
    assert "NO git add/commit" in text
    envelope = load_envelope()
    assert envelope["classification"] == "scratch_diagnostic"
    assert envelope["promotion_allowed"] is False
    assert envelope["formal_admission_allowed"] is False
    assert envelope["claim_ceiling"] == "basin_dof_readout_rows_only"
    assert envelope["no_builder_audit_verdict"] is True
    assert envelope["no_builder_audit_verdict_envelope_gate"] is True
    assert envelope["builder_gates"]["packet_audit_verdict_absent"] is True
    assert not (SIM_DIR / "audit_verdict.md").exists()


def test_dof_table_has_return_and_boundary_rows() -> None:
    envelope = load_envelope()
    table = envelope["dof_classification_table"]
    by_id = {row["dof_id"]: row for row in table}
    required = {"G0", "G1", "G2", "G3L", "G3R", "G4", "G5", "stage_shift_Rx_to_Rz", "loop_reverse_G5"}
    assert required <= set(by_id)
    assert by_id["G0"]["classification"] == "RETURN"
    assert by_id["G2"]["classification"] == "RETURN"
    assert by_id["G1"]["classification"] == "BOUNDARY"
    assert by_id["G3L"]["classification"] == "BOUNDARY"
    assert by_id["G3R"]["classification"] == "BOUNDARY"
    assert by_id["G5"]["classification"] == "BOUNDARY"
    assert envelope["result_summary"]["return_dof_count"] >= 1
    assert envelope["result_summary"]["boundary_dof_count"] >= 1
    assert envelope["result_summary"]["pre_registered_expectation_2_pass"] is True
    for row in table:
        assert row["pinned_perturbation_sizes"]
        assert row["trajectory_rows"]
        assert row["absent_exit_checked"] is True
        assert row["axis0_recomputed_by_source"] is True


def test_controls_are_nonvacuous_and_axis_load_bearing() -> None:
    envelope = load_envelope()
    controls = envelope["controls"]
    assert controls["zero_perturbation"]["classification"] == "RETURN"
    assert controls["zero_perturbation"]["trivial_return_calibration"] is True
    assert controls["over_perturbation"]["classification"] == "BOUNDARY"
    assert controls["over_perturbation"]["past_basin_scale"] is True
    assert controls["probe_erased_constant_field"]["classification"] == "DEGRADED"
    assert controls["probe_erased_constant_field"]["axis_readout_load_bearing"] is True
    assert controls["shuffled_order_N01"]["classification"] in {"BOUNDARY", "SCRAMBLING"}
    assert controls["shuffled_order_N01"]["n01_order_control_fired"] is True


def test_axis0_rebuilt_and_reconvergence_values_are_computed() -> None:
    envelope = load_envelope()
    axis0 = envelope["axis0_readout_rebuild"]
    assert axis0["source_sim_id"] == "discrete_axis0_field_v0"
    assert axis0["commit_hint"] == "5d330b427"
    assert axis0["recomputed"] is True
    assert axis0["polarity_counts"]
    for row in envelope["dof_classification_table"]:
        if row["classification"] == "RETURN":
            assert row["returned_to_prior_terminal_class"] is True
            assert row["axis0_readout_reconverged"] is True
        if row["classification"] == "BOUNDARY":
            assert row["boundary_found"] is True
            assert row["escaped_to_different_terminal_class"] is True


def test_smt_rows_and_packet_validator_pass() -> None:
    envelope = load_envelope()
    proofs = envelope["crossover_proofs"]
    for name in ("z3", "cvc5"):
        assert proofs[name]["ran"] is True
        assert proofs[name]["load_bearing"] is True
        assert proofs[name]["verdict"] == "unsat"
        assert proofs[name]["erased_flip_verdict"] == "sat"
        assert proofs[name]["asserted_precomputed_boolean"] is False
        assert proofs[name]["bound_values"]["return_dof_count"] >= 1
        assert proofs[name]["bound_values"]["boundary_dof_count"] >= 1
    errors = validator.validate_payload(envelope)
    assert errors == []
