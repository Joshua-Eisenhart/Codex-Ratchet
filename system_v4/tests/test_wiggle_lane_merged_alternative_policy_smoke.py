"""Smoke test for merged wiggle alternative-policy enforcement."""

from __future__ import annotations

from system_v4.skills.a1_brain import A1StrategyPacket
from system_v4.skills.intent_runtime_policy import build_runtime_policy
from system_v4.skills.wiggle_lane_runner import _merge_strategy_packets


def test_wiggle_lane_merged_alternative_policy_smoke() -> None:
    runtime_policy = build_runtime_policy(
        ["intent", "context"],
        [{"label": "intent_first_class"}],
    )
    intent_control = {
        "surface_id": "A2_INTENT_CONTROL__TEST",
        "provenance": {"surface_hash": "abc123"},
        "control": {"runtime_policy": runtime_policy},
    }
    shared_target = {
        "item_class": "AXIOM_HYP",
        "id": "F001",
        "kind": "MATH_DEF",
        "source_concept_id": "A2::intent_memory_loop",
        "def_fields": [{"name": "structural_form", "value_kind": "BARE", "value": "intent_memory_loop"}],
        "asserts": [{"token_class": "STRUCTURAL", "token": "intent_memory_loop"}],
        "requires": [],
    }
    lane_packets = [
        A1StrategyPacket(
            strategy_id="LANE1",
            inputs={},
            targets=[shared_target],
            alternatives=[
                {
                    "item_class": "AXIOM_HYP",
                    "id": "F101",
                    "kind": "MATH_DEF",
                    "source_concept_id": "A2::intent_memory_loop",
                    "primary_candidate_id": "F001",
                    "def_fields": [{"name": "structural_form", "value_kind": "BARE", "value": "intent_memory_loop_poison"}],
                    "asserts": [{"token_class": "STRUCTURAL", "token": "intent_memory_loop"}],
                    "requires": [],
                },
                {
                    "item_class": "AXIOM_HYP",
                    "id": "F102",
                    "kind": "MATH_DEF",
                    "source_concept_id": "A2::intent_memory_loop",
                    "primary_candidate_id": "F001",
                    "def_fields": [{"name": "structural_form", "value_kind": "BARE", "value": "intent_memory_loop_forward"}],
                    "asserts": [{"token_class": "STRUCTURAL", "token": "intent_memory_loop"}],
                    "requires": ["UNDEFINED_999"],
                },
            ],
            sims={"positive": [], "negative": []},
            self_audit={},
        ),
        A1StrategyPacket(
            strategy_id="LANE2",
            inputs={},
            targets=[shared_target],
            alternatives=[
                {
                    "item_class": "AXIOM_HYP",
                    "id": "F103",
                    "kind": "MATH_DEF",
                    "source_concept_id": "A2::intent_memory_loop",
                    "primary_candidate_id": "F001",
                    "def_fields": [{"name": "structural_form", "value_kind": "BARE", "value": "intent_memory_loop_variant"}],
                    "asserts": [{"token_class": "STRUCTURAL", "token": "intent_memory_loop"}],
                    "requires": [],
                },
            ],
            sims={"positive": [], "negative": []},
            self_audit={},
        ),
    ]
    merged_packet, merge_report = _merge_strategy_packets(
        lane_packets=lane_packets,
        wiggle_id="A1_WIGGLE",
        concept_ids=["A2::intent_memory_loop"],
        lane_configs=[{"lane_id": "lane1"}, {"lane_id": "lane2"}],
        intent_control=intent_control,
    )

    assert len(merged_packet.alternatives) == 2
    assert merge_report["merged_alternative_count"] == 2
    runtime = merge_report["alternative_policy_runtime"]
    assert runtime["applied"] is True
    assert runtime["primaries_evaluated"] == 1
    assert runtime["primaries_trimmed"] == 1
    assert runtime["alternatives_trimmed"] == 1

    print("PASS: test_wiggle_lane_merged_alternative_policy_smoke")


if __name__ == "__main__":
    test_wiggle_lane_merged_alternative_policy_smoke()
