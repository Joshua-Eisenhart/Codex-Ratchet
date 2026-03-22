"""Smoke tests for intent-aware fallback concept selection in run_real_ratchet."""

from __future__ import annotations

from system_v4.skills.intent_runtime_policy import (
    build_runtime_policy,
    normalize_intent_runtime_policy,
)
from system_v4.runners.run_real_ratchet import _apply_intent_concept_selection


def test_intent_concept_selection_smoke() -> None:
    graph_nodes = {
        "A2::intent_memory": {
            "name": "intent_memory_loop",
            "description": "Preserve maker intent continuously in memory.",
            "tags": ["INTENT", "MEMORY"],
        },
        "A2::skill_graph": {
            "name": "skill_graph_co_development",
            "description": "Develop skills and graphs together with context continuity.",
            "tags": ["SKILL", "GRAPH"],
        },
        "A2::math": {
            "name": "density_matrix_channel",
            "description": "Finite dimensional hilbert space density matrix channel.",
            "tags": ["MATH"],
        },
    }
    intent_control = {
        "control": {
            "runtime_policy": build_runtime_policy(
                ["intent", "skill", "context"],
                [{"label": "intent_first_class"}],
            ),
        }
    }

    selected, report = _apply_intent_concept_selection(
        [],
        ["A2::math", "A2::intent_memory", "A2::skill_graph"],
        graph_nodes,
        intent_control,
        explicit_targets_used=False,
        batch_limit=10,
    )
    assert selected == ["A2::skill_graph", "A2::intent_memory"]
    assert report["effective_mode"] == "focus-term-gated"
    assert report["gate_applied"] is True
    assert report["suppressed_count"] == 1

    selected_fallback, fallback_report = _apply_intent_concept_selection(
        [],
        ["A2::math", "A2::intent_memory"],
        graph_nodes,
        intent_control,
        explicit_targets_used=False,
        batch_limit=10,
    )
    assert fallback_report["effective_mode"] == "reorder_only"
    assert fallback_report["gate_applied"] is False
    assert selected_fallback == ["A2::intent_memory", "A2::math"]

    graph_nodes_with_overlay = {
        **graph_nodes,
        "A2::math": {
            **graph_nodes["A2::math"],
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
        },
    }
    overlay_selected, overlay_report = _apply_intent_concept_selection(
        [],
        ["A2::math", "A2::intent_memory"],
        graph_nodes_with_overlay,
        intent_control,
        explicit_targets_used=False,
        batch_limit=10,
    )
    assert overlay_selected == selected_fallback
    assert overlay_report == fallback_report

    selected_explicit, explicit_report = _apply_intent_concept_selection(
        [],
        [],
        graph_nodes,
        intent_control,
        explicit_targets_used=True,
        batch_limit=10,
    )
    assert selected_explicit == []
    assert explicit_report["effective_mode"] == "explicit-target-passthrough"

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
    degraded_policy["concept_selection"]["focus_terms"] = ["intent", "skill", "context"]
    degraded_policy["concept_selection"]["gating_focus_terms"] = []

    degraded_selected, degraded_report = _apply_intent_concept_selection(
        [],
        ["A2::math", "A2::intent_memory", "A2::skill_graph"],
        graph_nodes,
        {"control": {"runtime_policy": degraded_policy}},
        explicit_targets_used=False,
        batch_limit=10,
    )
    assert degraded_report["steering_quality_status"] == "degraded"
    assert degraded_report["effective_mode"] == "reorder_only"
    assert degraded_report["gate_applied"] is False
    assert degraded_report["suppressed_count"] == 0
    assert degraded_selected == ["A2::skill_graph", "A2::intent_memory", "A2::math"]

    executable_only_policy = build_runtime_policy(
        ["intent", "math"],
        [{"label": "intent_first_class"}],
        executable_focus_terms=["intent"],
        executable_non_negotiables=[{"label": "intent_first_class"}],
    )
    executable_only_policy["steering_quality"] = {
        "status": "strong",
        "downgrade_applied": False,
        "reasons": [],
        "descriptive_focus_term_count": 2,
        "steering_focus_term_count": 1,
        "top_weak_terms": [],
    }
    executable_selected, executable_report = _apply_intent_concept_selection(
        [],
        ["A2::math", "A2::intent_memory"],
        graph_nodes,
        {"control": {"runtime_policy": executable_only_policy}},
        explicit_targets_used=False,
        batch_limit=10,
    )
    assert executable_report["ranking_focus_terms"] == ["intent"]
    assert executable_report["effective_mode"] == "reorder_only"
    assert executable_selected == ["A2::intent_memory", "A2::math"]

    alias_policy = build_runtime_policy(
        ["graphs"],
        [{"label": "intent_first_class"}],
        executable_focus_terms=["graph"],
        executable_non_negotiables=[{"label": "intent_first_class"}],
    )
    alias_policy["steering_focus_terms"] = ["graph", "graphs"]
    alias_policy["steering_quality"] = {
        "status": "strong",
        "downgrade_applied": False,
        "reasons": [],
        "descriptive_focus_term_count": 2,
        "steering_focus_term_count": 2,
        "top_weak_terms": [],
    }
    alias_graph_nodes = {
        "A2::plural_graphs": {
            "name": "plural_graphs_surface",
            "description": "Plural graphs surface for steering alias coverage.",
            "tags": ["GRAPHS"],
        },
        "A2::math": graph_nodes["A2::math"],
    }
    alias_selected, alias_report = _apply_intent_concept_selection(
        [],
        ["A2::math", "A2::plural_graphs"],
        alias_graph_nodes,
        {"control": {"runtime_policy": alias_policy}},
        explicit_targets_used=False,
        batch_limit=10,
    )
    assert alias_report["gating_focus_terms"] == ["graph"]
    assert alias_report["effective_mode"] == "reorder_only"
    assert alias_selected == ["A2::plural_graphs", "A2::math"]

    cluster_audit_policy = build_runtime_policy(
        ["intent", "skill", "context"],
        [{"label": "intent_first_class"}],
        executable_focus_terms=["intent"],
        executable_non_negotiables=[{"label": "intent_first_class"}],
    )
    cluster_audit_policy["executable_focus_refinement_candidates"] = [
        {
            "term": "integration",
            "candidate_status": "audit_only",
            "eligible_concept_hit_count": 51,
            "novel_vs_current_executable_count": 41,
        }
    ]
    cluster_audit_policy["executable_focus_promotion_readiness"] = [
        {
            "term": "integration",
            "candidate_status": "audit_only",
            "readiness_status": "candidate_for_cluster_precision_check",
            "cluster_precision": {
                "status": "mixed",
                "intra_hit_edge_coverage": 0.43,
                "top_shared_semantic_tags": [],
                "top_shared_semantic_tokens": [{"token": "bounded", "count": 11, "share": 0.215686}],
            },
            "execution_binding_probe": {
                "status": "blocked_by_cluster_precision",
                "novel_hit_count": 41,
                "novel_hit_rate": 0.005709,
                "projected_executable_hit_count": 52,
                "projected_executable_hit_rate": 0.007241,
                "sample_new_focus_matches": [
                    {"node_id": "A2::integration", "name": "integration_lane", "node_type": "EXTRACTED_CONCEPT"}
                ],
            },
            "missing_proof": ["cluster_precision_check", "execution_binding_proof"],
        }
    ]
    cluster_selected, cluster_report = _apply_intent_concept_selection(
        [],
        ["A2::math", "A2::intent_memory"],
        graph_nodes,
        {"control": {"runtime_policy": cluster_audit_policy}},
        explicit_targets_used=False,
        batch_limit=10,
    )
    assert cluster_report["gating_focus_terms"] == ["intent"]
    assert cluster_report["ranking_focus_terms"] == ["intent"]
    assert cluster_report["effective_mode"] == "reorder_only"
    assert cluster_selected == ["A2::intent_memory", "A2::math"]

    execution_probe_policy = build_runtime_policy(
        ["intent", "skill", "context"],
        [{"label": "intent_first_class"}],
        executable_focus_terms=["intent"],
        executable_non_negotiables=[{"label": "intent_first_class"}],
    )
    execution_probe_policy["executable_focus_refinement_candidates"] = [
        {
            "term": "derivation",
            "candidate_status": "audit_only",
            "eligible_concept_hit_count": 15,
            "novel_vs_current_executable_count": 13,
        }
    ]
    execution_probe_policy["executable_focus_promotion_readiness"] = [
        {
            "term": "derivation",
            "candidate_status": "audit_only",
            "readiness_status": "candidate_for_execution_binding_check",
            "cluster_precision": {
                "status": "coherent",
                "intra_hit_edge_coverage": 0.46,
                "top_shared_semantic_tags": [{"tag": "manifold_derivation", "count": 4, "share": 0.266667}],
                "top_shared_semantic_tokens": [{"token": "transport", "count": 7, "share": 0.466667}],
            },
            "execution_binding_probe": {
                "status": "bounded_positive_effect",
                "novel_hit_count": 13,
                "novel_hit_rate": 0.00181,
                "projected_executable_hit_count": 32,
                "projected_executable_hit_rate": 0.004456,
                "sample_new_focus_matches": [
                    {"node_id": "A2::derivation", "name": "derivation_pipeline", "node_type": "REFINED_CONCEPT"}
                ],
            },
            "missing_proof": [],
        }
    ]
    execution_probe_policy["executable_focus_semantic_comparison"] = {
        "scope": "audit_only_nonbinding",
        "runtime_effect": "none",
        "comparison_pair": ["derivation", "integration"],
        "structural_front_runner": "derivation",
        "semantic_hygiene_front_runner": "integration",
        "decision": "keep_audit_only_no_promotion",
        "manual_review_required": True,
        "family_audit": {
            "scope": "audit_only_nonbinding",
            "runtime_effect": "none",
            "observations": [
                {"term": "derivation", "family_posture": "mixed_clustered"},
                {"term": "integration", "family_posture": "highly_concentrated"},
            ],
        },
    }
    execution_base_control = {"control": {"runtime_policy": execution_probe_policy}}
    execution_with_audit = {
        "control": {"runtime_policy": execution_probe_policy},
        "self_audit": {
            "derivation_family_contamination": {
                "status": "audit_only_nonoperative",
                "audit_only": True,
                "runtime_effect": "none",
                "assessed_term": "derivation",
                "contamination_risk": "mixed_but_not_pure_source_map_carryover",
                "risk_flags": ["provenance_sparse_hits"],
                "counter_signals": ["shared_semantic_tag_signal"],
                "missing_proof": ["execution_binding_proof"],
            },
            "semantic_sample_comparison": {
                "derivation_vs_integration": {
                    "status": "audit_only_nonoperative",
                    "audit_only": True,
                    "runtime_effect": "none",
                    "comparison_basis": "semantic_sample",
                    "comparison_scope": "derivation_vs_integration_sample",
                    "left_family": "derivation",
                    "right_family": "integration",
                    "left_sample_node_ids": ["A2::derivation"],
                    "right_sample_node_ids": ["A2::integration"],
                    "comparison_result": "inconclusive_audit_only",
                    "confidence": "low",
                    "missing_proof": [
                        "cluster_precision_check",
                        "execution_binding_proof",
                    ],
                }
            },
            "derivation_sample_provenance_strength": {
                "status": "audit_only_nonoperative",
                "audit_only": True,
                "runtime_effect": "none",
                "family": "derivation",
                "assessment_result": "mixed_provenance",
                "source_labels": [
                    "maker_topic:skill_derivation_sources",
                    "refined_tag:skill_derivation_sources",
                ],
                "source_witness_refs": ["WITNESS_CORPUS::2"],
                "derived_refined_node_ids": ["INTENT::REFINED::TEST_C"],
                "sample_node_ids": ["A2::derivation"],
                "provenance_signals": {
                    "dual_provenance": True,
                    "witness_backed": True,
                    "lineage_backed": True,
                    "sample_semantic_support_share": 0.5,
                    "sample_residue_risk_share": 0.5,
                    "sample_provenance_sparse_share": 1.0,
                    "sample_uplift_ratio": 1.0,
                },
                "missing_proof": [
                    "cluster_precision_check",
                    "execution_binding_proof",
                ],
            },
            "derivation_lineage_bridge": {
                "status": "audit_only_nonoperative",
                "audit_only": True,
                "runtime_effect": "none",
                "family": "derivation",
                "source_labels": [
                    "maker_topic:skill_derivation_sources",
                    "refined_tag:skill_derivation_sources",
                ],
                "source_witness_refs": ["WITNESS_CORPUS::2"],
                "derived_refined_node_ids": ["INTENT::REFINED::TEST_C"],
                "lineage_refs": ["INTENT::SIGNAL::C"],
                "sample_node_ids": ["A2::derivation"],
                "bridge_status": "audit_only",
                "bridge_signals": {
                    "direct_intent_bridge_count": 0,
                    "reachable_within_3_hops_count": 0,
                    "upper_surface_neighbor_count": 0,
                    "no_observed_bridge_count": 1,
                },
                "missing_proof": [
                    "cluster_precision_check",
                    "execution_binding_proof",
                ],
            },
            "derivation_bridge_materialization_precondition": {
                "status": "audit_only_nonoperative",
                "audit_only": True,
                "runtime_effect": "none",
                "family": "derivation",
                "path_term": "derivation",
                "source_labels": [
                    "maker_topic:skill_derivation_sources",
                    "refined_tag:skill_derivation_sources",
                ],
                "source_witness_refs": ["WITNESS_CORPUS::2"],
                "target_refined_intent_id": "INTENT::REFINED::TEST_C",
                "single_bridgeable_path": True,
                "bridge_source_node_ids": ["A2::source_bridge"],
                "candidate_middle_node_id": "A1::formal_derivation",
                "candidate_middle_node_type": "REFINED_CONCEPT",
                "recommended_relation": "RELATED_TO",
                "materialization_allowed_in_current_surface": False,
                "decision": "keep_self_audit_only_no_edge_materialization",
                "hard_blockers": [
                    "missing_direct_candidate_provenance",
                    "no_direct_or_short_graph_bridge_to_intent",
                    "no_existing_relation_label_for_honest_intent_alignment",
                ],
                "missing_proof": [
                    "direct_candidate_provenance",
                    "execution_binding_proof",
                    "materialized_lineage_bridge",
                    "relation_semantics_review",
                ],
            },
            "stripped_provenance_backfill_precondition": {
                "status": "audit_only_nonoperative",
                "audit_only": True,
                "runtime_effect": "none",
                "target_node_id": "A1::formal_derivation",
                "target_node_layer": "A1_STRIPPED",
                "target_node_type": "REFINED_CONCEPT",
                "candidate_backfill_source_node_ids": [
                    "A2::derivation_refined",
                    "A2::derivation_source_map",
                ],
                "supporting_bridge_target_ids": [
                    "A2::derivation_refined",
                    "A2::derivation_source_map",
                    "A2::derivation_kernel",
                ],
                "bridge_source_node_ids": ["A2::source_bridge"],
                "recommended_noncanonical_fields": [
                    "properties.provenance_backfill_status",
                    "properties.provenance_backfill_basis_node_ids",
                ],
                "do_not_backfill_fields": ["lineage_refs", "witness_refs"],
                "precondition_status": "audit_only_precondition",
                "admissible_now": False,
                "materialization_allowed_in_current_surface": False,
                "relation_chain_summary": {
                    "supporting_edge_relations": ["ROSETTA_MAP", "STRIPPED_FROM"],
                    "supporting_source_doc_ids": [],
                },
                "decision": "keep_self_audit_only_no_provenance_backfill",
                "hard_blockers": [
                    "basis_is_indirect_graph_chain_only",
                    "direct_field_backfill_would_overclaim_provenance",
                    "donor_chain_has_no_direct_provenance",
                    "target_has_no_direct_provenance",
                ],
                "missing_proof": [
                    "direct_candidate_provenance",
                    "donor_witness_lineage_proof",
                    "noncanonical_field_admission_review",
                    "source_concept_id_backfill_proof",
                ],
            },
            "stripped_provenance_annotation_admission": {
                "status": "audit_only_nonoperative",
                "audit_only": True,
                "runtime_effect": "none",
                "target_node_id": "A1::formal_derivation",
                "target_node_layer": "A1_STRIPPED",
                "annotation_path": "properties.overlay_provenance_audit",
                "admissible_now": False,
                "manual_review_required": True,
                "builder_supports_properties_merge": True,
                "write_scope": "namespaced_audit_overlay_only_no_provenance_field_mutation",
                "basis_node_ids": [
                    "A2::derivation_refined",
                    "A2::derivation_source_map",
                ],
                "basis_edge_relations": ["ROSETTA_MAP", "STRIPPED_FROM"],
                "safest_annotation_shape": {
                    "field": "properties.overlay_provenance_audit",
                    "allowed_fields": [
                        "status",
                        "overlay_kind",
                        "authority_posture",
                        "manual_review_required",
                        "primary_donor_chain",
                        "secondary_context_node_ids",
                        "basis_edge_relations",
                        "supporting_source_doc_ids",
                        "bridge_source_node_ids",
                        "disclaimers",
                    ],
                },
                "forbidden_fields": [
                    "lineage_refs",
                    "witness_refs",
                    "source_class",
                    "trust_zone",
                    "authority",
                    "admissibility_state",
                    "properties.source_concept_id",
                    "properties.target_ref",
                    "properties.candidate_id",
                ],
                "decision": "keep_fail_closed_namespaced_overlay_only_manual_review",
                "hard_blockers": [
                    "basis_is_indirect_graph_chain_only",
                    "direct_field_backfill_would_overclaim_provenance",
                    "donor_chain_has_no_direct_provenance",
                    "no_grounded_trace_anchor",
                    "target_has_no_direct_provenance",
                ],
                "missing_proof": [
                    "direct_candidate_provenance",
                    "donor_witness_lineage_proof",
                    "noncanonical_field_admission_review",
                ],
            },
        },
    }
    assert normalize_intent_runtime_policy(execution_with_audit) == normalize_intent_runtime_policy(
        execution_base_control
    )
    execution_base_selected, execution_base_report = _apply_intent_concept_selection(
        [],
        ["A2::math", "A2::intent_memory"],
        graph_nodes,
        execution_base_control,
        explicit_targets_used=False,
        batch_limit=10,
    )
    execution_selected, execution_report = _apply_intent_concept_selection(
        [],
        ["A2::math", "A2::intent_memory"],
        graph_nodes,
        execution_with_audit,
        explicit_targets_used=False,
        batch_limit=10,
    )
    assert execution_selected == execution_base_selected
    assert execution_report == execution_base_report
    assert execution_report["gating_focus_terms"] == ["intent"]
    assert execution_report["ranking_focus_terms"] == ["intent"]
    assert execution_report["effective_mode"] == "reorder_only"
    assert execution_selected == ["A2::intent_memory", "A2::math"]

    print("PASS: test_intent_concept_selection_smoke")


if __name__ == "__main__":
    test_intent_concept_selection_smoke()
