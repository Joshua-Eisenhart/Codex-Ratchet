from __future__ import annotations

import importlib
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))


def _common():
    return importlib.import_module("discrete_axes12_pair_v0_common")


def test_axes12_pair_ceiling_source_pins_and_product_table() -> None:
    common = _common()
    obj = common.build_axes12_object()

    assert obj["sim_id"] == "discrete_axes12_pair_v0"
    assert obj["classification"] == "scratch_diagnostic"
    assert obj["claim_ceiling"] == "axis_readout_candidate_only"
    assert obj["promotion_allowed"] is False
    assert obj["formal_admission_allowed"] is False
    assert obj["carrier"]["state_count"] == 33
    assert obj["terrain_sheet_substrate"]["status"] == "consumed_as_committed_scratch_substrate"
    assert obj["carnot_strokes_fence"]["same_object_as_axis12_product"] is False

    rows = obj["axis12_row_table"]
    assert len(rows) == 10
    aliases = {row["product_alias"] for row in rows}
    assert {"Se", "Ni", "Ne", "Si"} <= aliases
    assert all(row["product_source"] == "computed_axis1_x_axis2_then_alias" for row in rows)

    product = obj["joint_product_table"]
    assert product["proper_cptp|direct"]["alias"] == "Se"
    assert product["proper_cptp|conjugated"]["alias"] == "Ni"
    assert product["unitary|direct"]["alias"] == "Ne"
    assert product["unitary|conjugated"]["alias"] == "Si"


def test_legality_frame_witnesses_and_controls() -> None:
    common = _common()
    obj = common.build_axes12_object()

    rows = {row["row_id"]: row for row in obj["axis12_row_table"]}
    assert rows["Vortex:pure_hamiltonian"]["axis1_class"] == "unitary"
    assert rows["Vortex:pure_hamiltonian"]["axis1_witnesses"]["kraus_rank"] == 1
    assert rows["Vortex:pure_hamiltonian"]["axis1_witnesses"]["purity_preserved"] is True
    assert rows["Pit"]["axis1_class"] == "proper_cptp"
    assert rows["Pit"]["axis1_witnesses"]["kraus_rank"] > 1
    assert rows["Pit"]["axis1_witnesses"]["unital"] is False
    assert rows["Hill"]["axis2_frame_class"] == "conjugated"
    assert rows["Hill"]["axis2_witnesses"]["connection_K_norm"] > common.EPS
    assert rows["Funnel"]["axis2_frame_class"] == "direct"
    assert rows["Funnel"]["axis2_witnesses"]["connection_K_norm"] == 0.0

    controls = obj["controls"]
    assert controls["unitary_row_calibration"]["fired"] is True
    assert controls["manifestly_conjugated_nonzero_Kt"]["fired"] is True
    assert controls["product_degeneracy_forced_bits"]["flagged"] is True
    assert controls["shuffled_order"]["label_only_reproduction_pass"] is False
    assert controls["falsifier_reachability"]["reachable"] is True


def test_independence_rows_and_boundary_fields() -> None:
    common = _common()
    obj = common.build_axes12_object()

    rows = {row["row_id"]: row for row in obj["independence_rows_vs_axes0_4_5_6"]}
    for row_id in (
        "axis12_product_not_recoverable_from_axis0_response",
        "axis12_product_not_recoverable_from_axis4_composition",
        "axis12_product_not_recoverable_from_axis5_family",
        "axis12_product_not_recoverable_from_axis6_precedence",
        "identity_leak_report",
    ):
        assert row_id in rows
        assert rows[row_id]["pass"] is True
    assert rows["identity_leak_report"]["identity_leak_detected"] is True
    assert rows["identity_leak_report"]["identity_leak_excluded_best_accuracy"] < 1.0

    stability = obj["stability_under_axis0_standard"]
    assert stability["neither_trivial_nor_frozen"] is True
    assert stability["one_step"]["stable_edges"] > 0
    assert stability["one_step"]["changed_edges"] > 0

    assert obj["no_builder_audit_verdict"] is True
    assert not (SIM_DIR / "audit_verdict.md").exists()
