from __future__ import annotations

import importlib
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))


def _common():
    return importlib.import_module("discrete_axis5_family_partial_v0_common")


def test_axis5_partial_family_table_ceiling_and_witnesses() -> None:
    common = _common()
    obj = common.build_axis5_object()

    assert obj["sim_id"] == "discrete_axis5_family_partial_v0"
    assert obj["classification"] == "scratch_diagnostic"
    assert obj["claim_ceiling"] == "axis_readout_candidate_only"
    assert obj["partial_scope"] == "axis5_operator_family_half_only"
    assert obj["substage_product_status"]["status"] == "blocked"
    assert obj["carrier"]["state_count"] == 33
    assert len(obj["axis5_family_table"]) == 132

    counts = obj["family_counts"]
    assert counts["dephasing_gradient_side"] == 66
    assert counts["unitary_hamiltonian_side"] == 66
    assert counts["boundary"] == 0

    for row in obj["axis5_family_table"]:
        assert row["classification_source"] == "computed_witnesses_not_label_resolution"
        assert row["label_drift_resolution"] == "unresolved_carried_as_annotation"
        assert row["substage_product_built"] is False
        if row["operator"] in {"Ti", "Te"}:
            assert row["axis5_family"] == "dephasing_gradient_side"
            assert row["entropy_production"] >= -common.EPS
            assert row["contractivity_to_mixed"] is True
        else:
            assert row["axis5_family"] == "unitary_hamiltonian_side"
            assert abs(row["purity_delta"]) <= common.EPS
            assert row["orbit_norm_preserved"] is True


def test_controls_independence_and_blocked_rows_are_explicit() -> None:
    common = _common()
    obj = common.build_axis5_object()

    controls = obj["controls"]
    assert controls["weak_dephasing_near_unitary_boundary"]["classification"] == "boundary"
    assert controls["weak_dephasing_near_unitary_boundary"]["computed"] is True
    assert controls["shuffled_order"]["family_counts_preserved"] is True
    assert controls["commuting_controls"]["Ti_Fe_commutator_neutral"] is True
    assert controls["pure_controls"]["unitary_purity_preservation"] is True

    rows = {row["row_id"]: row for row in obj["independence_rows_vs_axes0_6"]}
    assert rows["axis5_not_recoverable_from_axis0_response"]["pass"] is True
    assert rows["axis0_response_not_recoverable_from_axis5"]["pass"] is True
    assert rows["axis5_not_recoverable_from_axis6_precedence"]["pass"] is True
    assert rows["axis6_precedence_not_recoverable_from_axis5"]["pass"] is True
    assert rows["operator_label_identity_leak_report"]["identity_leak_detected"] is True
    assert rows["operator_label_identity_leak_report"]["identity_leak_excluded"] is True

    blocked = obj["substage_product_rows"]
    assert len(blocked) == 4
    assert all(row["status"] == "blocked_not_built" for row in blocked)
    assert all(row["reason"] == "substage_transition_convention_not_owner_pinned" for row in blocked)
    assert "axis5_axis6_substage_product" in obj["blocked_consumers"]
