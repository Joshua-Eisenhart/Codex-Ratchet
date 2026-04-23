"""Smoke test for intent-aware alternative trimming in A1 brain."""

from __future__ import annotations

import tempfile

from system_v4.skills.a1_brain import A1Brain, Assertion, DefField, KernelCandidate
from system_v4.skills.intent_runtime_policy import build_runtime_policy


def test_a1_brain_intent_alternative_policy_smoke() -> None:
    with tempfile.TemporaryDirectory() as td:
        brain = A1Brain(td, eval_mode=True)
        concept_id = "A2_TEST::density_matrix_channel"
        graph_nodes = {
            concept_id: {
                "id": concept_id,
                "name": "density_matrix_channel",
                "description": "Finite dimensional hilbert space density matrix channel.",
                "tags": ["MATH", "TEST"],
            }
        }

        def fake_extract(*_args, **_kwargs):
            return [
                KernelCandidate(
                    item_class="AXIOM_HYP",
                    id="F001",
                    kind="MATH_DEF",
                    requires=[],
                    def_fields=[DefField("DF_F001_01", "structural_form", "BARE", "density_matrix_channel")],
                    asserts=[Assertion("A_F001_01", "STRUCTURAL", "density_matrix_channel")],
                    source_concept_id=concept_id,
                )
            ]

        brain.extract_kernel_candidate = fake_extract  # type: ignore[assignment]

        baseline_packet = brain.build_strategy_packet(
            [concept_id],
            graph_nodes,
            strategy_id="A1_STRAT_ALT_BASELINE",
        )
        assert len(baseline_packet.alternatives) == 3
        assert baseline_packet.self_audit["alternative_count"] == 3
        runtime_policy = build_runtime_policy(
            ["intent", "skill", "context"],
            [{"label": "intent_first_class"}],
        )
        runtime_policy["concept_selection_runtime"] = {
            "effective_mode": "reorder_only",
            "explicit_targets_used": False,
        }

        intent_control = {
            "surface_id": "A2_INTENT_CONTROL__TEST",
            "provenance": {"surface_hash": "abc123"},
            "maker_intent": {
                "summary": "Intent-first preserved memory.",
                "constraints": [{"label": "intent_first_class"}],
                "queue_notes": [],
            },
            "control": {
                "runtime_policy": runtime_policy,
                "packet_policy_notes": ["Intent control is bounded guidance."],
            },
            "self_audit": {"source_ids": ["WITNESS_CORPUS::0"]},
        }

        bounded_packet = brain.build_strategy_packet(
            [concept_id],
            graph_nodes,
            strategy_id="A1_STRAT_ALT_INTENT",
            intent_control=intent_control,
        )
        assert len(bounded_packet.alternatives) == 2
        assert bounded_packet.inputs["bias_config"]["max_alternatives_per_primary"] == 2
        assert bounded_packet.self_audit["lane_stats"]["bias_config"]["max_alternatives_per_primary"] == 2
        assert bounded_packet.inputs["intent_control"]["runtime_policy"]["alternative_policy"]["max_alternatives_per_primary"] == 2
        assert bounded_packet.inputs["intent_control"]["surface_id"] == "A2_INTENT_CONTROL__TEST"
        alt_runtime = bounded_packet.self_audit["intent_control"]["alternative_policy_runtime"]
        assert alt_runtime["primaries_evaluated"] == 1
        assert alt_runtime["primaries_trimmed"] == 1
        assert alt_runtime["alternatives_trimmed"] == 1
        assert len(alt_runtime["trimmed_primary_ids"]) == 1
        assert alt_runtime["trimmed_primary_ids"][0].startswith("F")

        degraded_policy = build_runtime_policy(
            ["its", "saved", "extracting"],
            [],
        )
        degraded_policy["steering_focus_terms"] = []
        degraded_policy["steering_quality"] = {
            "status": "degraded",
            "downgrade_applied": True,
            "reasons": ["too_few_steering_focus_terms"],
            "descriptive_focus_term_count": 3,
            "steering_focus_term_count": 0,
            "top_weak_terms": ["its", "saved"],
        }
        degraded_policy["concept_selection"]["mode"] = "reorder_only"
        degraded_policy["concept_selection_runtime"] = {
            "effective_mode": "reorder_only",
            "explicit_targets_used": False,
        }
        degraded_policy["candidate_policy"]["mode"] = "disabled"
        degraded_policy["candidate_policy"]["apply_on_modes"] = []
        degraded_policy["candidate_policy"]["suppress_term_defs_without_focus"] = False
        degraded_policy["candidate_policy"]["disabled_reason"] = "degraded_steering_quality"
        degraded_policy["bias_config"]["intent_focus_terms"] = []

        degraded_packet = brain.build_strategy_packet(
            [concept_id],
            graph_nodes,
            strategy_id="A1_STRAT_ALT_DEGRADED",
            intent_control={
                "surface_id": "A2_INTENT_CONTROL__WEAK",
                "provenance": {"surface_hash": "weak123"},
                "maker_intent": {
                    "summary": "Weak lexical intent remains preserved.",
                    "constraints": [],
                    "queue_notes": [],
                },
                "control": {
                    "runtime_policy": degraded_policy,
                    "packet_policy_notes": ["Intent control degraded to reorder-only."],
                },
                "self_audit": {"source_ids": ["WITNESS_CORPUS::1"]},
            },
        )
        assert degraded_packet.inputs["intent_control"]["runtime_policy"]["steering_quality"]["status"] == "degraded"
        assert len(degraded_packet.alternatives) == 2
        degraded_alt_runtime = degraded_packet.self_audit["intent_control"]["alternative_policy_runtime"]
        assert degraded_alt_runtime["primaries_trimmed"] == 1
        assert degraded_alt_runtime["alternatives_trimmed"] == 1

    print("PASS: test_a1_brain_intent_alternative_policy_smoke")


if __name__ == "__main__":
    test_a1_brain_intent_alternative_policy_smoke()
