#!/usr/bin/env python3
"""Pytest checks for ECD.01 order-programmability."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))


def _common():
    return importlib.import_module("ecd01_order_programmable_computer_v0_common")


def test_qit_stage_orders_compute_distinct_channels_on_axis4_carrier() -> None:
    common = _common()
    obj = common.build_order_programmability_object()

    assert obj["sim_id"] == "ecd01_order_programmable_computer_v0"
    assert obj["classification"] == "scratch_diagnostic"
    assert obj["claim_ceiling"] == "capability_discriminator_only"
    assert obj["carrier"]["source_sim_id"] == "discrete_axis4_composition_v0"
    assert obj["carrier"]["state_count"] == 33

    metric = obj["capability_metric"]
    assert metric["qit_distinct_channel_count"] >= 3
    assert metric["qit_pairwise_positive_count"] >= 3
    assert metric["qit_diversity_strictly_exceeds_szilard"] is True
    assert metric["szilard_distinct_channel_count"] == 1

    distance = obj["channel_distinguishability_matrix"]
    assert distance["labels"] == obj["registered_order_words"]
    assert any(
        value > 0
        for row in distance["l1_output_distribution_distance"]
        for value in row
    )


def test_baseline_and_controls_are_live_not_label_only() -> None:
    common = _common()
    obj = common.build_order_programmability_object()

    baseline = obj["szilard_baseline"]
    assert baseline["loop"] == ["measure", "feedback", "erase"]
    assert baseline["admissible_order_count"] == 1
    assert baseline["distinct_channel_count"] == 1
    assert baseline["fails_ecd01"] is True
    assert baseline["divergence_log"]

    controls = obj["controls"]
    assert controls["commuting_generator_engine"]["distinct_channel_count"] == 1
    assert controls["commuting_generator_engine"]["capability_gone_without_N01"] is True
    assert controls["shuffled_labels"]["same_diversity_after_label_shuffle"] is True
    assert controls["shuffled_labels"]["same_distance_multiset_after_label_shuffle"] is True
    assert controls["falsifier_reachable"]["baseline_must_fail_or_discriminator_dies"] is True
    assert controls["falsifier_reachable"]["would_die_if_szilard_distinct_count_gte_qit"] is True


def test_validator_result_and_boundary_helper() -> None:
    common = _common()
    result_path = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
    if not result_path.exists():
        return
    payload = json.loads(result_path.read_text(encoding="utf-8"))

    assert payload["no_builder_audit_verdict"] is True
    assert not (SIM_DIR / "audit_verdict.md").exists()
    assert "universal quantum computer" in payload["disallowed_claims"]
    assert payload["TOOL_MANIFEST"]["torch.func"]["reason"]
    assert payload["TOOL_INTEGRATION_DEPTH"]["z3"] == "load_bearing"
