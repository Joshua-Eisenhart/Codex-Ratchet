from __future__ import annotations

import json
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
RESULT_DIR = SIM_DIR / "results"
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

import discrete_axis3_placement_v0_common as common  # noqa: E402
import validate_discrete_axis3_placement_v0 as validator  # noqa: E402


def load_envelope() -> dict:
    return json.loads((RESULT_DIR / f"{common.SIM_ID}_envelope_results.json").read_text(encoding="utf-8"))


def test_build_card_and_boundary_fields() -> None:
    build_card = SIM_DIR / "build_card.md"
    assert build_card.is_file()
    text = build_card.read_text(encoding="utf-8")
    assert common.SIM_ID in text
    assert common.CLAIM_CEILING in text
    envelope = load_envelope()
    assert envelope["classification"] == "scratch_diagnostic"
    assert envelope["promotion_allowed"] is False
    assert envelope["formal_admission_allowed"] is False
    assert envelope["claim_ceiling"] == "axis_readout_candidate_only"
    assert envelope["envelope_built_with_helper"] is True
    assert envelope["no_builder_audit_verdict"] is True
    assert not (SIM_DIR / "audit_verdict.md").exists()


def test_gamma_in_gamma_out_computed_conditions() -> None:
    envelope = load_envelope()
    table = envelope["placement_table"]
    assert len(table) == 48
    for row in table:
        if row["pinned_family_formula"] == "gamma_in":
            assert row["density_stationary"] is True
            assert row["placement_sign"] == -1
        if row["pinned_family_formula"] == "gamma_out":
            assert row["density_traversing"] is True
            assert row["horizontal_condition_A_dot_gamma_zero"] is True
            assert row["placement_sign"] == 1
    assert envelope["placement_counts"]["axis3_minus_fiber_placed_gamma_in"] == 24
    assert envelope["placement_counts"]["axis3_plus_base_placed_gamma_out"] == 24


def test_controls_and_stability_are_nonvacuous() -> None:
    envelope = load_envelope()
    controls = envelope["controls"]
    assert controls["placement_degenerate_control"]["neutral_count"] == 8
    assert controls["placement_degenerate_control"]["fired"] is True
    assert controls["shuffled_connection_control"]["changed_count"] == 24
    assert controls["shuffled_connection_control"]["fired"] is True
    assert controls["falsifier_reachability"]["fired"] is True
    stability = envelope["stability_under_committed_dynamics"]
    assert stability["stable_edge_count"] > 0
    assert stability["changed_edge_count"] > 0
    assert stability["all_stable_every_step"] is False
    assert stability["all_changed_every_step"] is False


def test_axis0_axis3_independence_rows() -> None:
    envelope = load_envelope()
    independence = envelope["independence_rows_vs_axis0"]
    assert independence["placement_not_recoverable_from_axis0_response"] is True
    assert independence["axis0_response_not_recoverable_from_placement"] is True
    assert independence["same_axis0_response_different_placement_witness"]
    assert independence["same_placement_different_axis0_response_witness"]
    assert independence["frozen_factor_projection_check"]["placement_not_recovered"] is True


def test_overlay_registry_is_staged_not_run() -> None:
    envelope = load_envelope()
    rows = envelope["overlay_discriminator_registry"]
    assert {row["contender"] for row in rows} == {"Type1_Type2_inversion", "L_R_chirality", "flux_in_out"}
    assert all(row["status"] == "staged_not_run" for row in rows)
    assert all(row["not_axis3_replacement"] is True for row in rows)


def test_packet_validator_passes() -> None:
    envelope = load_envelope()
    errors = validator.validate_payload(envelope)
    assert errors == []
