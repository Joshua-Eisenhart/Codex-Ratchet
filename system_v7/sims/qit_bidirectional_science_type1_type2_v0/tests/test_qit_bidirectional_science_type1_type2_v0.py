from __future__ import annotations

import sys

SIM_DIR = __file__.rsplit("/tests/", 1)[0]
if SIM_DIR not in sys.path:
    sys.path.insert(0, SIM_DIR)

from qit_bidirectional_science_type1_type2_v0_common import (  # noqa: E402
    RESULTS,
    SIM_ID,
    V43_VALIDATION,
    build_core_measurement,
    read_json,
)


def test_bidirectional_science_methods_have_distinct_teeth() -> None:
    core = build_core_measurement()
    assert core["all_pass"] is True
    assert core["comparison"]["trial_count"] == 40
    assert core["type1"]["nominal"]["trial_count"] == 20
    assert core["type2"]["nominal"]["trial_count"] == 20
    assert core["type1"]["nominal"]["accuracy"] == 1.0
    assert core["type2"]["nominal"]["accuracy"] == 0.9
    assert core["comparison"]["unique_win_table"]["counts"] == {
        "shared_fail": 0,
        "shared_win": 18,
        "type1_only": 2,
        "type2_only": 0,
    }


def test_controls_block_erased_or_wrong_projection_success() -> None:
    core = build_core_measurement()
    assert core["type1"]["controls"]["wrong_candidate"]["accepted_rate"] <= 0.25
    assert core["type1"]["controls"]["shuffled_projection"]["accepted_rate"] <= 0.25
    assert core["type2"]["controls"]["bag_erased"]["accuracy"] <= 0.25
    assert core["type2"]["controls"]["view_erased"]["accuracy"] <= 0.25
    assert core["type2"]["nominal"]["accuracy"] - core["type2"]["controls"]["bag_erased"]["accuracy"] >= 0.5


def test_generated_envelope_is_evidence_only() -> None:
    envelope = read_json(RESULTS / f"{SIM_ID}_envelope_results.json")
    assert envelope["schema_version"] == "three_engine_sim_result_v1"
    assert envelope["all_pass"] is True
    assert envelope["promotion_allowed"] is False
    assert envelope["formal_admission_allowed"] is False
    assert set(envelope["engines"]) == {"julia", "jax", "pytorch"}
    assert envelope["divergence"]["max_divergence"] == 0.0
    assert envelope["divergence"]["trial_values"] == {"jax": 40.0, "julia": 40.0, "pytorch": 40.0}
    assert envelope["stability_pairs"]["type1_vs_type2"]["unique_win_counts"]["type1_only"] == 2
    assert envelope["lev_host_consumer_contract"]["graph_mutation_allowed"] is False
    assert envelope["lev_host_consumer_contract"]["mesh_projection_allowed"] is False
    assert "Lev_mesh_runtime" in envelope["blocked_consumers"]


def test_v43_object_card_validation_receipt_exists() -> None:
    validation = read_json(V43_VALIDATION)
    assert validation["ok"] is True
    assert validation["errors"] == []
