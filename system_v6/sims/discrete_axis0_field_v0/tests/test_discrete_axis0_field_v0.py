from __future__ import annotations

import json
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
RESULT_DIR = SIM_DIR / "results"
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

import discrete_axis0_field_v0_common as common  # noqa: E402
import validate_discrete_axis0_field_v0 as validator  # noqa: E402


def load_envelope() -> dict:
    return json.loads((RESULT_DIR / f"{common.SIM_ID}_envelope_results.json").read_text(encoding="utf-8"))


def test_build_card_and_boundary_fields() -> None:
    build_card = SIM_DIR / "build_card.md"
    assert build_card.is_file()
    text = build_card.read_text(encoding="utf-8")
    assert "discrete_axis0_field_v0" in text
    assert "axis_readout_candidate_only" in text
    envelope = load_envelope()
    assert envelope["classification"] == "scratch_diagnostic"
    assert envelope["promotion_allowed"] is False
    assert envelope["formal_admission_allowed"] is False
    assert envelope["claim_ceiling"] == "axis_readout_candidate_only"
    assert envelope["envelope_built_with_helper"] is True
    assert envelope["build_helper_path"] == "scripts/build_three_engine_envelope.py"
    assert envelope["no_builder_audit_verdict"] is True
    assert not (SIM_DIR / "audit_verdict.md").exists()


def test_committed_carrier_and_exact_gradients_recompute() -> None:
    envelope = load_envelope()
    carrier = envelope["carrier"]
    assert carrier["state_count"] == 33
    assert carrier["edge_count"] == 198
    assert carrier["family_a_commit"] == common.PARENT_COMMITS["manifold_super_sim_v0"]
    field_by_cell = {row["cell_id"]: row["phi"] for row in envelope["readout_table"]}
    for row in envelope["gradient_table"]:
        expected = common.sub_fraction(field_by_cell[row["dst"]], field_by_cell[row["src"]])
        assert expected == row["directed_gradient_phi"]
    assert envelope["gradient_summary"]["nonzero_gradient_edges"] > 0


def test_controls_and_stability_are_nonvacuous() -> None:
    envelope = load_envelope()
    controls = envelope["controls"]
    assert controls["constant_field"]["all_degenerate_no_polarity"] is True
    assert controls["constant_field"]["nonzero_gradient_edges"] == 0
    assert controls["shuffled_adjacency"]["fired"] is True
    assert controls["reversed_orientation"]["fired"] is True
    assert controls["label_shuffle"]["label_only_reproduction_pass"] is False
    assert controls["row_count_only_ladder"]["fired"] is True
    assert controls["frozen_factor_projection"]["fired"] is True
    assert controls["erased_coloring"]["fired"] is True
    assert controls["erased_nesting"]["fired"] is True
    stability = envelope["stability_under_committed_dynamics"]
    assert stability["edge_count"] == 198
    assert stability["stable_edge_count"] > 0
    assert stability["changed_edge_count"] > 0
    assert stability["all_changed_every_step"] is False


def test_three_polarities_independence_discriminators() -> None:
    envelope = load_envelope()
    independence = envelope["three_polarities_independence"]
    assert independence["axis0_not_recoverable_from_axis3_placement"] is True
    assert independence["axis0_not_recoverable_from_axis6_order"] is True
    assert independence["axis3_witness_pair"]["same_axis3_placement_key"] is True
    assert independence["axis6_witness_pair"]["same_axis6_order_key"] is True
    assert independence["axis3_majority_accuracy"] < 1.0
    assert independence["axis6_majority_accuracy"] < 1.0


def test_packet_validator_passes() -> None:
    envelope = load_envelope()
    errors = validator.validate_payload(envelope)
    assert errors == []
