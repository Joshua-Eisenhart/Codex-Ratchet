"""Smoke test for extraction-level intent candidate policy in A1 brain."""

from __future__ import annotations

import tempfile

from system_v4.skills.a1_brain import A1Brain, Assertion, DefField, KernelCandidate
from system_v4.skills.intent_runtime_policy import build_runtime_policy


def test_a1_brain_intent_candidate_policy_smoke() -> None:
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
                ),
                KernelCandidate(
                    item_class="AXIOM_HYP",
                    id="F002",
                    kind="TERM_DEF",
                    requires=[],
                    def_fields=[DefField("DF_F002_01", "term_literal", "BARE", "custombridge")],
                    asserts=[Assertion("A_F002_01", "TERM_ADMISSION", "custombridge")],
                    source_concept_id=concept_id,
                ),
                KernelCandidate(
                    item_class="PROBE_HYP",
                    id="P001",
                    kind="SIM_SPEC",
                    requires=["F001"],
                    def_fields=[DefField("DF_P001_01", "probe_target", "BARE", "F001")],
                    asserts=[Assertion("A_P001_01", "PROBE_CHECK", "structural_consistency_F001")],
                    source_concept_id=concept_id,
                ),
            ]

        brain.extract_kernel_candidate = fake_extract  # type: ignore[assignment]
        runtime_policy = build_runtime_policy(
            ["intent", "skill", "context"],
            [{"label": "intent_first_class"}],
        )
        runtime_policy["alternative_policy"]["max_alternatives_per_primary"] = 3
        runtime_policy["bias_config"]["max_alternatives_per_primary"] = 3
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

        packet = brain.build_strategy_packet(
            [concept_id],
            graph_nodes,
            strategy_id="A1_STRAT_INTENT_POLICY_TEST",
            intent_control=intent_control,
        )

        target_ids = [t["id"] for t in packet.targets]
        target_kinds = [t["kind"] for t in packet.targets]
        assert target_ids == ["F001", "P001"]
        assert target_kinds == ["MATH_DEF", "SIM_SPEC"]
        assert packet.inputs["intent_control"]["runtime_policy"]["focus_terms"] == ["intent", "skill", "context"]
        assert len(packet.alternatives) == 3
        assert all(a["primary_candidate_id"] == "F001" for a in packet.alternatives)
        assert all(a["kind"] == "MATH_DEF" for a in packet.alternatives)
        runtime = packet.self_audit["intent_control"]["candidate_policy_runtime"]
        assert runtime["concepts_evaluated"] == 1
        assert runtime["concepts_suppressed"] == 1
        assert runtime["suppressed_term_defs"] == 1
        assert runtime["suppressed_concepts"] == [concept_id]

        overlay_noise_packet = brain.build_strategy_packet(
            [concept_id],
            {
                concept_id: {
                    **graph_nodes[concept_id],
                    "properties": {
                        "overlay_provenance_audit": {
                            "overlay_kind": "stripped_provenance_archive_projection",
                            "authority_posture": "intent skill context graph memory",
                            "primary_donor_chain": [
                                {
                                    "node_id": "A2::intent_noise",
                                    "role": "strongest_semantic_donor",
                                    "name": "intent skill context graph memory",
                                    "via_relations": ["SOURCE_MAP_PASS"],
                                }
                            ],
                            "disclaimers": ["intent skill context graph memory"],
                        }
                    },
                }
            },
            strategy_id="A1_STRAT_INTENT_POLICY_OVERLAY_NOISE",
            intent_control=intent_control,
        )
        assert [t["id"] for t in overlay_noise_packet.targets] == target_ids
        assert [t["kind"] for t in overlay_noise_packet.targets] == target_kinds
        overlay_noise_runtime = overlay_noise_packet.self_audit["intent_control"][
            "candidate_policy_runtime"
        ]
        assert overlay_noise_runtime == runtime

        executable_override_policy = build_runtime_policy(
            ["intent", "system"],
            [{"label": "intent_first_class"}],
            executable_focus_terms=["intent"],
            executable_non_negotiables=[{"label": "intent_first_class"}],
        )
        executable_override_policy["steering_focus_terms"] = ["intent", "system"]
        executable_override_policy["concept_selection_runtime"] = {
            "effective_mode": "reorder_only",
            "explicit_targets_used": False,
        }
        system_only_graph_nodes = {
            concept_id: {
                "id": concept_id,
                "name": "system_architecture_surface",
                "description": "System architecture and graph skill coordination surface.",
                "tags": ["SYSTEM", "GRAPH", "SKILL"],
            }
        }
        executable_override_packet = brain.build_strategy_packet(
            [concept_id],
            system_only_graph_nodes,
            strategy_id="A1_STRAT_INTENT_POLICY_EXECUTABLE_OVERRIDE",
            intent_control={
                "surface_id": "A2_INTENT_CONTROL__EXEC_ONLY",
                "provenance": {"surface_hash": "exec123"},
                "maker_intent": {
                    "summary": "Executable focus terms should remain narrower than descriptive steering terms.",
                    "constraints": [{"label": "intent_first_class"}],
                    "queue_notes": [],
                },
                "control": {
                    "runtime_policy": executable_override_policy,
                    "packet_policy_notes": ["Executable focus terms are narrower than descriptive steering terms."],
                },
                "self_audit": {"source_ids": ["WITNESS_CORPUS::2"]},
            },
        )
        executable_override_ids = [t["id"] for t in executable_override_packet.targets]
        assert executable_override_ids == ["F001", "P001"]
        executable_override_runtime = executable_override_packet.self_audit["intent_control"]["candidate_policy_runtime"]
        assert executable_override_packet.inputs["intent_control"]["runtime_policy"]["executable_focus_terms"] == ["intent"]
        assert executable_override_runtime["concepts_evaluated"] == 1
        assert executable_override_runtime["concepts_suppressed"] == 1
        assert executable_override_runtime["suppressed_term_defs"] == 1

        alias_policy = build_runtime_policy(
            ["skills"],
            [{"label": "intent_first_class"}],
            executable_focus_terms=["skill"],
            executable_non_negotiables=[{"label": "intent_first_class"}],
        )
        alias_policy["steering_focus_terms"] = ["skill", "skills"]
        alias_policy["concept_selection_runtime"] = {
            "effective_mode": "reorder_only",
            "explicit_targets_used": False,
        }
        alias_packet = brain.build_strategy_packet(
            [concept_id],
            {
                concept_id: {
                    "id": concept_id,
                    "name": "plural_skills_surface",
                    "description": "Plural skills coordination surface.",
                    "tags": ["SKILLS"],
                }
            },
            strategy_id="A1_STRAT_INTENT_POLICY_ALIAS",
            intent_control={
                "surface_id": "A2_INTENT_CONTROL__ALIAS",
                "provenance": {"surface_hash": "alias123"},
                "maker_intent": {
                    "summary": "Canonical executable terms should still match plural surface language.",
                    "constraints": [{"label": "intent_first_class"}],
                    "queue_notes": [],
                },
                "control": {
                    "runtime_policy": alias_policy,
                    "packet_policy_notes": ["Canonical executable focus terms may match plural lexical variants."],
                },
                "self_audit": {"source_ids": ["WITNESS_CORPUS::3"]},
            },
        )
        alias_target_ids = [t["id"] for t in alias_packet.targets]
        alias_runtime = alias_packet.self_audit["intent_control"]["candidate_policy_runtime"]
        assert alias_packet.inputs["intent_control"]["runtime_policy"]["executable_focus_terms"] == ["skill"]
        assert alias_target_ids == ["F001", "F002", "P001"]
        assert alias_runtime["concepts_evaluated"] == 1
        assert alias_runtime["concepts_with_focus"] == 1
        assert alias_runtime["concepts_suppressed"] == 0
        assert alias_runtime["suppressed_term_defs"] == 0

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
            strategy_id="A1_STRAT_INTENT_POLICY_DEGRADED",
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

        degraded_target_ids = [t["id"] for t in degraded_packet.targets]
        assert degraded_target_ids == ["F001", "F002", "P001"]
        degraded_runtime = degraded_packet.self_audit["intent_control"]["candidate_policy_runtime"]
        assert degraded_packet.inputs["intent_control"]["runtime_policy"]["steering_quality"]["status"] == "degraded"
        assert degraded_runtime["concepts_evaluated"] == 1
        assert degraded_runtime["concepts_suppressed"] == 0
        assert degraded_runtime["suppressed_term_defs"] == 0
        assert degraded_runtime["suppressed_concepts"] == []

    print("PASS: test_a1_brain_intent_candidate_policy_smoke")


if __name__ == "__main__":
    test_a1_brain_intent_candidate_policy_smoke()
