from __future__ import annotations

import importlib
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))


def _common():
    return importlib.import_module("discrete_axis6_precedence_v0_common")


def test_pinned_family_a_axis6_object_shape_and_ceiling() -> None:
    common = _common()
    obj = common.build_axis6_object()

    assert obj["sim_id"] == "discrete_axis6_precedence_v0"
    assert obj["classification"] == "scratch_diagnostic"
    assert obj["claim_ceiling"] == "axis_readout_candidate_only"
    assert obj["carrier"]["state_count"] == 33
    assert obj["carrier"]["edge_count"] == 198
    assert obj["carrier"]["generator_names"] == [
        "Se_Funnel_L",
        "Ni_Pit_L",
        "Ni_Source_R",
        "Ne_Spiral_R",
        "D_z",
        "R_x",
    ]

    pinning = obj["pinning"]
    assert pinning["operator"]["id"] == "S4:D_z"
    assert pinning["operator"]["pin_sha256"] == common.S4_PIN_SHA256
    assert pinning["terrain"]["id"] == "S5:Ne_Spiral_R"
    assert pinning["terrain"]["h"] == "1/2"
    assert pinning["terrain"]["pin_sha256"] == common.S5_PIN_SHA256

    table = obj["precedence_table"]
    assert len(table) == 33
    assert {row["cell_id"] for row in table} == {
        row["cell_id"] for row in obj["axis0_alignment"]["axis0_readout_table"]
    }
    for row in table:
        assert "operator_first_bloch" in row
        assert "terrain_first_bloch" in row
        assert "z_component_difference" in row
        assert "trace_norm_weight" in row
        assert "weighted_z_difference" in row
        assert row["b6_sign"] in {-1, 0, 1}


def test_controls_and_independence_are_carrier_honest() -> None:
    common = _common()
    obj = common.build_axis6_object()

    counts = obj["precedence_counts"]
    assert counts["nonneutral"] > 0
    assert counts["positive"] > 0
    assert counts["negative"] > 0

    controls = obj["controls"]
    assert controls["commuting_control"]["all_cells_neutral"] is True
    assert controls["constant_field_degenerate"]["all_cells_neutral"] is True
    assert controls["shuffled_order_n01"]["n01_flips_or_demotes"] is True
    assert controls["shuffled_order_n01"]["flipped_nonzero_count"] == counts["nonneutral"]
    assert controls["frozen_factor_projection"]["best_frozen_factor_accuracy"] < 1.0
    assert controls["label_permutation"]["label_only_reproduction_pass"] is False

    stability = obj["stability_under_committed_dynamics"]
    assert stability["scope"] == "one_step_and_two_step_edges_on_committed_family_a_carrier"
    assert stability["one_step"]["stable_edges"] > 0
    assert stability["one_step"]["changed_edges"] > 0
    assert stability["two_step"]["stable_paths"] > 0
    assert stability["two_step"]["changed_paths"] > 0

    rows = obj["independence_rows_vs_axis0"]
    ids = {row["row_id"] for row in rows}
    assert "axis6_not_recoverable_from_axis0_response" in ids
    assert "axis0_response_not_recoverable_from_axis6" in ids
    assert "best_predictor_full_axis0_feature_report" in ids
    best = next(row for row in rows if row["row_id"] == "best_predictor_full_axis0_feature_report")
    assert best["identity_leak_excluded_best_accuracy"] < 1.0
    assert best["full_axis0_fields_included_in_report"] is True


def test_staged_three_way_and_registry_boundary() -> None:
    common = _common()
    obj = common.build_axis6_object()

    prediction = obj["b0_b6_prediction"]
    assert prediction["relation_status"] == (
        "staged_prediction_only_requires_axis3_same_carrier_follow_on"
    )
    assert len(prediction["table"]) == 33
    for row in prediction["table"]:
        assert row["prediction_for_negative_axis3_sign"] in {-1, 0, 1}
        assert row["claim"] == "prediction_of_minus_b3_not_axis3_measurement"

    registry = obj["axis6_contender_registry_staged_rows"]
    assert {row["contender_id"] for row in registry} == {
        "trace_norm_weighted_z_precedence",
        "commutator_sign_readout",
        "lr_action_spectral_order",
        "win_lose_pattern_discriminator",
    }
    assert registry[0]["status"] == "run_primary_candidate"
    assert all(row["status"] == "staged_not_run" for row in registry[1:])

    assert obj["no_builder_audit_verdict"] is True
    assert not (SIM_DIR / "audit_verdict.md").exists()
