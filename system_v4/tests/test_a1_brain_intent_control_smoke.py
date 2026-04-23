"""Smoke test for A1 strategy packet intent-control visibility."""

from __future__ import annotations

import tempfile

from system_v4.skills.a1_brain import A1Brain
from system_v4.skills.intent_runtime_policy import build_runtime_policy


def test_a1_brain_intent_control_smoke() -> None:
    with tempfile.TemporaryDirectory() as td:
        brain = A1Brain(td, eval_mode=True)
        runtime_policy = build_runtime_policy(
            ["intent", "context"],
            [{"label": "intent_first_class"}],
        )
        runtime_policy["concept_selection_runtime"] = {
            "effective_mode": "focus-term-gated",
            "selected_count": 2,
            "suppressed_count": 1,
        }
        intent_control = {
            "surface_id": "A2_INTENT_CONTROL__TEST",
            "provenance": {"surface_hash": "abc123"},
            "maker_intent": {
                "summary": "Preserve maker intent.",
                "queue_notes": [{"text": "Queue notes remain separate."}],
                "constraints": [{"label": "intent_first_class"}],
            },
            "control": {
                "packet_policy_notes": ["Intent control is bounded guidance."],
                "runtime_policy": runtime_policy,
            },
            "self_audit": {"source_ids": ["WITNESS_CORPUS::0"]},
        }

        packet = brain.build_strategy_packet(
            [],
            {},
            strategy_id="A1_STRAT_TEST",
            lane_id="INTENT_PRESERVING_CURRENT",
            bias_config={"intent_focus_terms": ["intent", "context"]},
            intent_control=intent_control,
        )

        assert packet.inputs["intent_control"]["surface_id"] == "A2_INTENT_CONTROL__TEST"
        assert packet.inputs["intent_control"]["surface_hash"] == "abc123"
        assert packet.inputs["intent_control"]["focus_terms"] == ["intent", "context"]
        assert packet.inputs["intent_control"]["runtime_policy"]["schema"] == "INTENT_RUNTIME_POLICY_v1"
        assert packet.inputs["intent_control"]["effective_runtime_policy"]["bias_config"]["max_alternatives_per_primary"] == 2
        assert packet.inputs["intent_control"]["concept_selection"]["mode"] == "focus-term-gate-then-reorder"
        assert packet.inputs["intent_control"]["concept_selection_runtime"]["effective_mode"] == "focus-term-gated"
        assert packet.inputs["intent_control"]["candidate_policy"]["mode"] == "suppress-off-focus-term-defs"
        assert packet.inputs["intent_control"]["alternative_policy"]["mode"] == "cap_alternatives_per_primary"
        assert packet.policy["intent_control"]["packet_policy_notes"] == [
            "Intent control is bounded guidance."
        ]
        assert packet.policy["intent_control"]["runtime_policy_schema"] == "INTENT_RUNTIME_POLICY_v1"
        assert packet.policy["intent_control"]["concept_selection_mode"] == "focus-term-gate-then-reorder"
        assert packet.policy["intent_control"]["candidate_policy_mode"] == "suppress-off-focus-term-defs"
        assert packet.policy["intent_control"]["alternative_policy_mode"] == "cap_alternatives_per_primary"
        assert packet.self_audit["intent_control"]["surface_id"] == "A2_INTENT_CONTROL__TEST"
        assert packet.self_audit["intent_control"]["runtime_policy"]["schema"] == "INTENT_RUNTIME_POLICY_v1"
        assert packet.self_audit["intent_control"]["queue_notes"] == [
            "Queue notes remain separate."
        ]
        assert packet.self_audit["intent_control"]["concept_selection_runtime"]["suppressed_count"] == 1
        assert packet.self_audit["intent_control"]["candidate_policy_runtime"]["concepts_evaluated"] == 0
        assert packet.self_audit["intent_control"]["alternative_policy_runtime"]["primaries_evaluated"] == 0

    print("PASS: test_a1_brain_intent_control_smoke")


if __name__ == "__main__":
    test_a1_brain_intent_control_smoke()
