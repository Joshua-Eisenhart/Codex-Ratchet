from __future__ import annotations

import sys

SIM_DIR = __file__.rsplit("/tests/", 1)[0]
if SIM_DIR not in sys.path:
    sys.path.insert(0, SIM_DIR)

from qit_projection_battery_v0_common import RESULTS, SIM_ID, VIEW_MASKS, build_core_measurement, read_json


def test_projection_masks_exclude_direct_identity_fields() -> None:
    used = {idx for mask in VIEW_MASKS.values() for idx in mask}
    assert 5 not in used
    assert 6 not in used


def test_core_projection_battery_has_teeth() -> None:
    core = build_core_measurement()
    assert core["all_pass"] is True
    assert core["nominal"]["mean_heldout_accuracy"] >= 0.85
    assert core["controls"]["bag_erased"]["mean_heldout_accuracy"] <= 0.25
    assert core["controls"]["view_erased"]["mean_heldout_accuracy"] <= 0.25
    assert len(core["object_cards"]) == 4
    assert all(len(card["projection_hashes"]) == 5 for card in core["object_cards"])


def test_generated_envelope_is_evidence_only() -> None:
    envelope = read_json(RESULTS / f"{SIM_ID}_envelope_results.json")
    assert envelope["all_pass"] is True
    assert set(envelope["engines"]) == {"julia", "jax", "pytorch"}
    assert envelope["divergence"]["max_divergence"] == 0.0
    assert envelope["lev_host_consumer_contract"]["graph_mutation_allowed"] is False
    assert envelope["lev_host_consumer_contract"]["mesh_projection_allowed"] is False
    assert "Lev_mesh_runtime" in envelope["blocked_consumers"]
