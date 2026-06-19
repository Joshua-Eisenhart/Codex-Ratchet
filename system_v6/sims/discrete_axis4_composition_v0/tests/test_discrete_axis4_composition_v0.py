from __future__ import annotations

import importlib
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))


def _common():
    return importlib.import_module("discrete_axis4_composition_v0_common")


def test_pinned_family_a_axis4_object_shape_and_ceiling() -> None:
    common = _common()
    obj = common.build_axis4_object()

    assert obj["sim_id"] == "discrete_axis4_composition_v0"
    assert obj["classification"] == "scratch_diagnostic"
    assert obj["claim_ceiling"] == "axis_readout_candidate_only"
    assert obj["carrier"]["state_count"] == 33
    assert obj["carrier"]["edge_count"] == 198

    pinning = obj["pinning"]
    assert pinning["source"]["pin_sha256"] == common.S4_PIN_SHA256
    assert pinning["R"]["id"] == "S4:R_x"
    assert pinning["C"]["id"] == "S4:D_z"
    assert pinning["R"]["tau"] == 1.0
    assert pinning["C"]["tau"] == 1.0

    table = obj["axis4_readout_table"]
    assert len(table) == 33
    for row in table:
        assert "Phi_D_bloch" in row
        assert "Phi_I_bloch" in row
        assert "Delta_D_minus_I_bloch" in row
        assert row["axis4_sign"] in {-1, 0, 1}

    counts = obj["axis4_counts"]
    assert counts["positive"] == 14
    assert counts["negative"] == 14
    assert counts["neutral"] == 5


def test_controls_are_live_and_panel_form_is_separate() -> None:
    common = _common()
    obj = common.build_axis4_object()
    controls = obj["controls"]

    assert controls["commuting_pair_all_neutral"]["all_cells_neutral"] is True
    assert controls["commuting_pair_all_neutral"]["neutral_count"] == 33
    assert controls["panel7_leading_order_2ue_commutator"]["pass"] is True
    assert controls["panel7_leading_order_2ue_commutator"]["relative_error"] < 5e-4
    assert controls["shuffled_order_not_primary"]["pass"] is True
    assert controls["shuffled_order_not_primary"]["changed_count"] > 0
    assert controls["axis4_vs_axis6_discriminator"]["pass"] is True
    assert controls["axis4_vs_axis6_discriminator"]["axis6_predicts_axis4_majority_accuracy"] < 1.0


def test_independence_matrix_and_boundary_helper() -> None:
    common = _common()
    obj = common.build_axis4_object()

    rows = {row["row_id"]: row for row in obj["carrier_honest_independence_matrix"]}
    for row_id in (
        "axis4_not_recoverable_from_axis0_response",
        "axis0_response_not_recoverable_from_axis4",
        "axis4_not_recoverable_from_axis6_precedence",
        "axis6_precedence_not_recoverable_from_axis4",
        "best_predictor_full_0_4_6_feature_report",
    ):
        assert rows[row_id]["pass"] is True

    best = rows["best_predictor_full_0_4_6_feature_report"]
    assert best["identity_leak_detected"] is True
    assert best["identity_leak_excluded_best_accuracy"] < 1.0
    assert obj["axis0_alignment"]["same_carrier"] is True
    assert obj["axis6_alignment"]["same_carrier"] is True
    assert obj["no_builder_audit_verdict"] is True
    assert not (SIM_DIR / "audit_verdict.md").exists()


def test_smt_and_claim_boundaries() -> None:
    common = _common()
    obj = common.build_axis4_object()

    for row in obj["smt_rows"].values():
        assert row["verdict"] == "unsat"
        assert row["erased_flip_verdict"] == "sat"
        assert row["asserted_precomputed_boolean"] is False

    assert "Axis-6 precedence claim" in obj["disallowed_claims"]
    assert "canonical Axis-4 readout" in obj["disallowed_claims"]
    assert obj["all_pass"] is True
