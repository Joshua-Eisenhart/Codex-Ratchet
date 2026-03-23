"""Smoke test for bounded refined-focus candidates on the intent control surface."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from system_v4.skills.intent_control_surface_builder import (
    GRAPH_REL_PATH,
    PROVENANCE_OVERLAY_REL_PATH,
    SURFACE_REL_PATH,
    WITNESS_REL_PATH,
    _build_stripped_provenance_overlay_archive,
    build_intent_control_surface,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_intent_control_surface_builder_refined_focus_candidates_smoke() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        graph_path = root / GRAPH_REL_PATH
        witness_path = root / WITNESS_REL_PATH

        nodes = {
            "INTENT::REFINED::TEST_A": {
                "id": "INTENT::REFINED::TEST_A",
                "node_type": "INTENT_REFINEMENT",
                "name": "intent_preservation_intent_contract",
                "description": "Current derived intent for this maker topic.",
                "tags": ["intent", "intent-refinement", "intent_preservation", "witness-derived"],
                "properties": {"source_intent_ids": ["INTENT::SIGNAL::A"]},
                "lineage_refs": ["INTENT::SIGNAL::A"],
                "witness_refs": ["WITNESS_CORPUS::0"],
            },
            "INTENT::REFINED::TEST_B": {
                "id": "INTENT::REFINED::TEST_B",
                "node_type": "INTENT_REFINEMENT",
                "name": "skill_graph_integration_intent_contract",
                "description": "Current derived intent for this maker topic.",
                "tags": ["intent", "intent-refinement", "skill_graph_integration", "witness-derived"],
                "properties": {"source_intent_ids": ["INTENT::SIGNAL::B"]},
                "lineage_refs": ["INTENT::SIGNAL::B"],
                "witness_refs": ["WITNESS_CORPUS::1"],
            },
            "INTENT::REFINED::TEST_C": {
                "id": "INTENT::REFINED::TEST_C",
                "node_type": "INTENT_REFINEMENT",
                "name": "skill_derivation_sources_intent_contract",
                "description": "Current derived intent for this maker topic.",
                "tags": ["intent", "intent-refinement", "skill_derivation_sources", "witness-derived"],
                "properties": {"source_intent_ids": ["INTENT::SIGNAL::C"]},
                "lineage_refs": ["INTENT::SIGNAL::C"],
                "witness_refs": ["WITNESS_CORPUS::2"],
            },
            "C001": {
                "id": "C001",
                "node_type": "EXTRACTED_CONCEPT",
                "name": "durable_preservation_surface",
                "description": "Preservation contract for durable state.",
                "tags": ["PRESERVATION"],
            },
            "C001B": {
                "id": "C001B",
                "node_type": "EXTRACTED_CONCEPT",
                "name": "memory_preservation_lane",
                "description": "Preservation lane for retained memory.",
                "tags": ["PRESERVATION"],
            },
            "C002": {
                "id": "C002",
                "node_type": "EXTRACTED_CONCEPT",
                "name": "operator_integration_lane",
                "description": "Integration between operators and control packets.",
                "tags": ["INTEGRATION"],
            },
            "C002B": {
                "id": "C002B",
                "node_type": "EXTRACTED_CONCEPT",
                "name": "bridge_integration_lane",
                "description": "Integration between bridges and packet routing.",
                "tags": ["INTEGRATION"],
            },
            "C003": {
                "id": "C003",
                "node_type": "REFINED_CONCEPT",
                "name": "operator_derivation_pipeline",
                "description": "Derivation path for new operator families.",
                "tags": ["DERIVATION"],
            },
            "C003B": {
                "id": "C003B",
                "node_type": "REFINED_CONCEPT",
                "name": "kernel_derivation_pipeline",
                "description": "Derivation path for new kernel families.",
                "tags": ["DERIVATION"],
            },
            "C004": {
                "id": "C004",
                "node_type": "REFINED_CONCEPT",
                "name": "graph_skill_memory",
                "description": "Graph skill memory intent context control.",
                "tags": ["GRAPH", "SKILL", "MEMORY", "INTENT", "CONTEXT"],
            },
        }
        for idx in range(60):
            nodes[f"FILLER::{idx:03d}"] = {
                "id": f"FILLER::{idx:03d}",
                "node_type": "EXTRACTED_CONCEPT",
                "name": f"filler_concept_{idx:03d}",
                "description": f"Filler concept {idx:03d} for bounded hit-rate coverage.",
                "tags": ["FILLER"],
            }
        _write_json(graph_path, {"nodes": nodes, "edges": []})
        _write_json(
            witness_path,
            [
                {
                    "recorded_at": "2026-03-20T00:00:00Z",
                    "witness": {
                        "kind": "intent",
                        "passed": True,
                        "violations": [],
                        "touched_boundaries": [],
                        "trace": [
                            {
                                "at": "2026-03-20T00:00:00Z",
                                "op": "intent:maker",
                                "before_hash": "",
                                "after_hash": "",
                                "notes": ["Keep this maker theme first-class."],
                            }
                        ],
                    },
                    "tags": {
                        "source": "maker",
                        "phase": "DESIGN_PRINCIPLE",
                        "priority": "P0",
                        "topic": "intent_preservation",
                    },
                },
                {
                    "recorded_at": "2026-03-20T00:00:01Z",
                    "witness": {
                        "kind": "intent",
                        "passed": True,
                        "violations": [],
                        "touched_boundaries": [],
                        "trace": [
                            {
                                "at": "2026-03-20T00:00:01Z",
                                "op": "intent:maker",
                                "before_hash": "",
                                "after_hash": "",
                                "notes": ["These operators should mature with the refinery."],
                            }
                        ],
                    },
                    "tags": {
                        "source": "maker",
                        "phase": "DESIGN_PRINCIPLE",
                        "priority": "P1",
                        "topic": "skill_graph_integration",
                    },
                },
                {
                    "recorded_at": "2026-03-20T00:00:02Z",
                    "witness": {
                        "kind": "intent",
                        "passed": True,
                        "violations": [],
                        "touched_boundaries": [],
                        "trace": [
                            {
                                "at": "2026-03-20T00:00:02Z",
                                "op": "intent:maker",
                                "before_hash": "",
                                "after_hash": "",
                                "notes": ["These source lanes should remain visible as fuel."],
                            }
                        ],
                    },
                    "tags": {
                        "source": "maker",
                        "phase": "DESIGN_PRINCIPLE",
                        "priority": "P1",
                        "topic": "skill_derivation_sources",
                    },
                },
            ],
        )

        result = build_intent_control_surface(td)
        payload = json.loads((root / SURFACE_REL_PATH).read_text(encoding="utf-8"))
        overlay = json.loads(
            (root / PROVENANCE_OVERLAY_REL_PATH).read_text(encoding="utf-8")
        )

        candidates = payload["control"]["executable_focus_refinement_candidates"]
        runtime_candidates = payload["control"]["runtime_policy"]["executable_focus_refinement_candidates"]
        readiness = payload["control"]["executable_focus_promotion_readiness"]
        runtime_readiness = payload["control"]["runtime_policy"]["executable_focus_promotion_readiness"]
        semantic_comparison = payload["control"]["executable_focus_semantic_comparison"]
        runtime_semantic_comparison = payload["control"]["runtime_policy"]["executable_focus_semantic_comparison"]
        contamination = payload["self_audit"]["derivation_family_contamination"]
        semantic_sample = payload["self_audit"]["semantic_sample_comparison"][
            "derivation_vs_integration"
        ]
        provenance_strength = payload["self_audit"][
            "derivation_sample_provenance_strength"
        ]
        lineage_bridge = payload["self_audit"]["derivation_lineage_bridge"]
        bridge_precondition = payload["self_audit"][
            "derivation_bridge_materialization_precondition"
        ]
        provenance_backfill = payload["self_audit"][
            "stripped_provenance_backfill_precondition"
        ]
        provenance_annotation = payload["self_audit"][
            "stripped_provenance_annotation_admission"
        ]
        terms = [item["term"] for item in candidates]
        readiness_by_term = {item["term"]: item for item in readiness}

        assert payload["classification"]["surface_class"] == "DERIVED_A2"
        assert payload["classification"]["status"] == "NONCANONICAL_ACTIVE_CONTROL"
        assert "not doctrine" in payload["classification"]["authority_posture"]
        assert candidates == runtime_candidates
        assert readiness == runtime_readiness
        assert semantic_comparison == runtime_semantic_comparison
        assert "integration" in terms
        assert "preservation" in terms
        assert "derivation" in terms
        assert "sources" not in terms
        assert all(item["candidate_status"] == "audit_only" for item in candidates)
        assert all(item["novel_vs_current_executable_count"] > 0 for item in candidates)
        assert readiness_by_term["integration"]["cluster_precision"]["status"] == "diffuse"
        assert readiness_by_term["integration"]["cluster_precision"]["intra_hit_edge_coverage"] == 0.0
        assert readiness_by_term["integration"]["cluster_precision"]["top_shared_semantic_tokens"]
        assert readiness_by_term["integration"]["readiness_status"] == "candidate_for_cluster_precision_check"
        assert readiness_by_term["integration"]["readiness_flags"]["solo_gate_ready"] is True
        assert readiness_by_term["integration"]["readiness_flags"]["novel_gain_ready"] is True
        assert readiness_by_term["integration"]["readiness_flags"]["dual_provenance"] is True
        assert (
            readiness_by_term["integration"]["execution_binding_probe"]["status"]
            == "blocked_by_cluster_precision"
        )
        assert (
            readiness_by_term["integration"]["execution_binding_probe"]["novel_hit_count"] == 2
        )
        assert readiness_by_term["integration"]["missing_proof"] == [
            "cluster_precision_check",
            "execution_binding_proof",
        ]
        assert readiness_by_term["derivation"]["cluster_precision"]["status"] == "diffuse"
        assert readiness_by_term["derivation"]["readiness_status"] == "candidate_for_cluster_precision_check"
        assert (
            readiness_by_term["derivation"]["execution_binding_probe"]["status"]
            == "blocked_by_cluster_precision"
        )
        assert readiness_by_term["derivation"]["missing_proof"] == [
            "cluster_precision_check",
            "execution_binding_proof",
        ]
        assert readiness_by_term["preservation"]["cluster_precision"]["status"] == "diffuse"
        assert readiness_by_term["preservation"]["readiness_status"] == "candidate_for_cluster_precision_check"
        assert (
            readiness_by_term["preservation"]["execution_binding_probe"]["status"]
            == "blocked_by_cluster_precision"
        )
        assert payload["self_audit"]["executable_focus_refinement_candidate_count"] == len(candidates)
        assert payload["self_audit"]["executable_focus_promotion_ready_count"] == len(candidates)
        assert payload["self_audit"]["executable_focus_cluster_precision_candidate_count"] == len(
            candidates
        )
        assert payload["self_audit"]["executable_focus_execution_binding_candidate_count"] == 0
        assert payload["self_audit"]["executable_focus_execution_binding_positive_probe_count"] == 0
        assert semantic_comparison["scope"] == "audit_only_nonbinding"
        assert semantic_comparison["runtime_effect"] == "none"
        assert semantic_comparison["comparison_pair"] == ["derivation", "integration"]
        assert semantic_comparison["structural_front_runner"] == "derivation"
        assert semantic_comparison["semantic_hygiene_front_runner"] == "integration"
        assert semantic_comparison["decision"] == "keep_audit_only_no_promotion"
        assert semantic_comparison["manual_review_required"] is True
        family_audit = semantic_comparison["family_audit"]
        assert family_audit["scope"] == "audit_only_nonbinding"
        assert family_audit["runtime_effect"] == "none"
        family_obs = {item["term"]: item for item in family_audit["observations"]}
        assert family_obs["derivation"]["family_posture"] == "mixed_clustered"
        assert family_obs["integration"]["family_posture"] == "mixed_clustered"
        assert family_obs["derivation"]["top_family"] == "C003"
        assert family_obs["integration"]["top_family"] == "C002"
        assert family_obs["derivation"]["node_type_distribution"][0]["label"] == "REFINED_CONCEPT"
        assert family_obs["integration"]["node_type_distribution"][0]["label"] == "EXTRACTED_CONCEPT"
        assert contamination["status"] == "audit_only_nonoperative"
        assert contamination["audit_only"] is True
        assert contamination["runtime_effect"] == "none"
        assert contamination["source_witness_refs"] == ["WITNESS_CORPUS::2"]
        assert contamination["derived_refined_node_ids"] == ["INTENT::REFINED::TEST_C"]
        assert "execution_binding_proof" in contamination["missing_proof"]
        assert "cluster_precision_check" in contamination["missing_proof"]
        assert "derivation_family_contamination" not in payload["control"]
        assert "derivation_family_contamination" not in payload["control"]["runtime_policy"]
        assert semantic_sample["status"] == "audit_only_nonoperative"
        assert semantic_sample["audit_only"] is True
        assert semantic_sample["runtime_effect"] == "none"
        assert semantic_sample["comparison_basis"] == "semantic_sample"
        assert semantic_sample["left_family"] == "derivation"
        assert semantic_sample["right_family"] == "integration"
        assert semantic_sample["left_source_labels"] == [
            "maker_topic:skill_derivation_sources",
            "refined_tag:skill_derivation_sources",
        ]
        assert semantic_sample["right_source_labels"] == [
            "maker_topic:skill_graph_integration",
            "refined_tag:skill_graph_integration",
        ]
        assert semantic_sample["left_sample_node_ids"] == ["C003", "C003B"]
        assert semantic_sample["right_sample_node_ids"] == ["C002", "C002B"]
        assert semantic_sample["confidence"] in {"low", "medium"}
        assert "execution_binding_proof" in semantic_sample["missing_proof"]
        assert "cluster_precision_check" in semantic_sample["missing_proof"]
        assert "semantic_sample_comparison" not in payload["control"]
        assert "semantic_sample_comparison" not in payload["control"]["runtime_policy"]
        assert provenance_strength["status"] == "audit_only_nonoperative"
        assert provenance_strength["audit_only"] is True
        assert provenance_strength["runtime_effect"] == "none"
        assert provenance_strength["family"] == "derivation"
        assert provenance_strength["source_labels"] == [
            "maker_topic:skill_derivation_sources",
            "refined_tag:skill_derivation_sources",
        ]
        assert provenance_strength["source_witness_refs"] == ["WITNESS_CORPUS::2"]
        assert provenance_strength["derived_refined_node_ids"] == [
            "INTENT::REFINED::TEST_C"
        ]
        assert provenance_strength["sample_node_ids"] == ["C003", "C003B"]
        assert provenance_strength["provenance_signals"]["dual_provenance"] is True
        assert provenance_strength["provenance_signals"]["witness_backed"] is True
        assert provenance_strength["provenance_signals"]["lineage_backed"] is True
        assert (
            provenance_strength["provenance_signals"]["sample_semantic_support_share"]
            == 1.0
        )
        assert (
            provenance_strength["provenance_signals"]["sample_residue_risk_share"]
            == 0.0
        )
        assert (
            provenance_strength["provenance_signals"]["sample_provenance_sparse_share"]
            == 1.0
        )
        assert provenance_strength["provenance_signals"]["sample_uplift_ratio"] == 1.0
        assert provenance_strength["assessment_result"] == "bounded_but_unproven"
        assert "execution_binding_proof" in provenance_strength["missing_proof"]
        assert "derivation_sample_provenance_strength" not in payload["control"]
        assert (
            "derivation_sample_provenance_strength"
            not in payload["control"]["runtime_policy"]
        )
        assert lineage_bridge["status"] == "audit_only_nonoperative"
        assert lineage_bridge["audit_only"] is True
        assert lineage_bridge["runtime_effect"] == "none"
        assert lineage_bridge["family"] == "derivation"
        assert lineage_bridge["source_labels"] == [
            "maker_topic:skill_derivation_sources",
            "refined_tag:skill_derivation_sources",
        ]
        assert lineage_bridge["source_witness_refs"] == ["WITNESS_CORPUS::2"]
        assert lineage_bridge["derived_refined_node_ids"] == ["INTENT::REFINED::TEST_C"]
        assert lineage_bridge["lineage_refs"] == ["INTENT::SIGNAL::C"]
        assert lineage_bridge["sample_node_ids"] == ["C003", "C003B"]
        assert lineage_bridge["bridge_status"] == "weak_or_missing_bridge"
        assert lineage_bridge["bridge_signals"]["direct_intent_bridge_count"] == 0
        assert lineage_bridge["bridge_signals"]["reachable_within_3_hops_count"] == 0
        assert lineage_bridge["bridge_signals"]["upper_surface_neighbor_count"] == 0
        assert lineage_bridge["bridge_signals"]["no_observed_bridge_count"] == 2
        assert "execution_binding_proof" in lineage_bridge["missing_proof"]
        assert "derivation_lineage_bridge" not in payload["control"]
        assert "derivation_lineage_bridge" not in payload["control"]["runtime_policy"]
        assert bridge_precondition["status"] == "audit_only_nonoperative"
        assert bridge_precondition["audit_only"] is True
        assert bridge_precondition["runtime_effect"] == "none"
        assert bridge_precondition["family"] == "derivation"
        assert bridge_precondition["path_term"] == "derivation"
        assert bridge_precondition["source_labels"] == [
            "maker_topic:skill_derivation_sources",
            "refined_tag:skill_derivation_sources",
        ]
        assert bridge_precondition["source_witness_refs"] == ["WITNESS_CORPUS::2"]
        assert bridge_precondition["target_refined_intent_id"] == "INTENT::REFINED::TEST_C"
        assert bridge_precondition["single_bridgeable_path"] is False
        assert bridge_precondition["bridge_source_node_ids"] == []
        assert bridge_precondition["candidate_middle_node_id"] == "C003"
        assert bridge_precondition["candidate_middle_node_type"] == "REFINED_CONCEPT"
        assert bridge_precondition["candidate_selection_basis"] == [
            "refined_concept",
            "non_archive_semantic_description",
            "derivation_language_present",
        ]
        assert (
            bridge_precondition["candidate_support"]["semantic_support"][
                "semantic_description_present"
            ]
            is True
        )
        assert (
            bridge_precondition["candidate_support"]["provenance_support"][
                "witness_backed"
            ]
            is False
        )
        assert bridge_precondition["recommended_relation"] == "RELATED_TO"
        assert bridge_precondition["materialization_allowed_in_current_surface"] is False
        assert bridge_precondition["decision"] == "keep_self_audit_only_no_edge_materialization"
        assert bridge_precondition["hard_blockers"] == [
            "missing_direct_candidate_provenance",
            "no_direct_or_short_graph_bridge_to_intent",
            "no_existing_relation_label_for_honest_intent_alignment",
        ]
        assert "execution_binding_proof" in bridge_precondition["missing_proof"]
        assert "direct_candidate_provenance" in bridge_precondition["missing_proof"]
        assert bridge_precondition["candidate_reviews"][0]["node_id"] == "C003"
        assert "derivation_bridge_materialization_precondition" not in payload["control"]
        assert (
            "derivation_bridge_materialization_precondition"
            not in payload["control"]["runtime_policy"]
        )
        assert provenance_backfill["status"] == "audit_only_nonoperative"
        assert provenance_backfill["audit_only"] is True
        assert provenance_backfill["runtime_effect"] == "none"
        assert provenance_backfill["target_node_id"] == "C003"
        assert provenance_backfill["target_node_type"] == "REFINED_CONCEPT"
        assert provenance_backfill["candidate_backfill_source_node_ids"] == []
        assert provenance_backfill["supporting_bridge_target_ids"] == []
        assert provenance_backfill["bridge_source_node_ids"] == []
        assert provenance_backfill["recommended_noncanonical_fields"] == [
            "properties.overlay_provenance_audit.status",
            "properties.overlay_provenance_audit.overlay_kind",
            "properties.overlay_provenance_audit.primary_donor_chain",
            "properties.overlay_provenance_audit.basis_edge_relations",
            "properties.overlay_provenance_audit.supporting_source_doc_ids",
            "properties.overlay_provenance_audit.disclaimers",
        ]
        assert provenance_backfill["do_not_backfill_fields"] == [
            "lineage_refs",
            "witness_refs",
        ]
        assert provenance_backfill["precondition_status"] == "audit_only_precondition"
        assert provenance_backfill["admissible_now"] is False
        assert provenance_backfill["materialization_allowed_in_current_surface"] is False
        assert provenance_backfill["relation_chain_summary"] == {
            "supporting_edge_relations": [],
            "supporting_source_doc_ids": [],
        }
        assert provenance_backfill["donor_review"] == {
            "semantic_donor_candidates": [],
            "hygiene_donor_candidates": [],
            "rows": [],
        }
        assert provenance_backfill["decision"] == "keep_self_audit_only_no_provenance_backfill"
        assert provenance_backfill["hard_blockers"] == [
            "direct_field_backfill_would_overclaim_provenance",
            "donor_chain_has_no_direct_provenance",
            "no_candidate_backfill_donor_chain",
            "target_has_no_direct_provenance",
        ]
        assert provenance_backfill["missing_proof"] == [
            "direct_candidate_provenance",
            "donor_witness_lineage_proof",
            "noncanonical_field_admission_review",
            "source_concept_id_backfill_proof",
        ]
        assert "stripped_provenance_backfill_precondition" not in payload["control"]
        assert (
            "stripped_provenance_backfill_precondition"
            not in payload["control"]["runtime_policy"]
        )
        assert provenance_annotation["status"] == "audit_only_nonoperative"
        assert provenance_annotation["audit_only"] is True
        assert provenance_annotation["runtime_effect"] == "none"
        assert provenance_annotation["target_node_id"] == "C003"
        assert provenance_annotation["target_node_layer"] == ""
        assert (
            provenance_annotation["annotation_path"]
            == "properties.overlay_provenance_audit"
        )
        assert provenance_annotation["admissible_now"] is False
        assert provenance_annotation["manual_review_required"] is True
        assert provenance_annotation["builder_supports_properties_merge"] is True
        assert (
            provenance_annotation["write_scope"]
            == "namespaced_audit_overlay_only_no_provenance_field_mutation"
        )
        assert provenance_annotation["basis_node_ids"] == []
        assert provenance_annotation["basis_edge_relations"] == []
        assert provenance_annotation["safest_annotation_shape"] == {
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
        }
        assert provenance_annotation["forbidden_fields"] == [
            "lineage_refs",
            "witness_refs",
            "source_class",
            "trust_zone",
            "authority",
            "admissibility_state",
            "properties.source_concept_id",
            "properties.target_ref",
            "properties.candidate_id",
        ]
        assert (
            provenance_annotation["decision"]
            == "keep_fail_closed_namespaced_overlay_only_manual_review"
        )
        assert provenance_annotation["hard_blockers"] == [
            "direct_field_backfill_would_overclaim_provenance",
            "donor_chain_has_no_direct_provenance",
            "no_candidate_backfill_donor_chain",
            "no_grounded_trace_anchor",
            "target_has_no_direct_provenance",
        ]
        assert provenance_annotation["missing_proof"] == [
            "direct_candidate_provenance",
            "donor_witness_lineage_proof",
            "noncanonical_field_admission_review",
        ]
        assert "stripped_provenance_annotation_admission" not in payload["control"]
        assert (
            "stripped_provenance_annotation_admission"
            not in payload["control"]["runtime_policy"]
        )
        assert (
            payload["self_audit"]["stripped_provenance_overlay_archive_path"]
            == PROVENANCE_OVERLAY_REL_PATH
        )
        assert result["provenance_overlay_path"] == PROVENANCE_OVERLAY_REL_PATH
        assert (root / result["provenance_overlay_path"]).exists()
        assert overlay["schema"] == "A2_STRIPPED_PROVENANCE_OVERLAY_v1"
        assert overlay["classification"]["surface_class"] == "ARCHIVE_ONLY"
        assert overlay["classification"]["status"] == "NONOWNER_AUDIT_OVERLAY"
        assert "not owner surface" in overlay["classification"]["authority_posture"]
        assert overlay["target"]["node_id"] == "C003"
        assert overlay["overlay_contract"]["runtime_effect"] == "none"
        assert overlay["overlay_contract"]["manual_review_required"] is True
        assert overlay["overlay_contract"]["do_not_write_fields"] == [
            "lineage_refs",
            "witness_refs",
            "source_class",
            "trust_zone",
            "authority",
            "admissibility_state",
            "properties.source_concept_id",
            "properties.target_ref",
            "properties.candidate_id",
        ]
        assert overlay["donor_chain"]["primary_chain"][0]["node_id"] == "C003"
        assert overlay["donor_chain"]["basis_node_ids"] == []
        assert overlay["donor_chain"]["supporting_source_doc_ids"] == []
        assert overlay["self_audit"]["admissible_now"] is False
        assert (
            overlay["self_audit"]["decision"]
            == "keep_fail_closed_namespaced_overlay_only_manual_review"
        )
        assert any(
            "future executable refinement" in tension
            for tension in payload["open_tensions"]
        )
        assert any(
            "promotion readiness remains audit-only" in tension
            for tension in payload["open_tensions"]
        )
        assert any(
            "Structural and semantic staged-term signals are compared explicitly" in tension
            for tension in payload["open_tensions"]
        )
        assert any(
            "Derivation staged-term contamination evidence is tracked in self_audit only"
            in tension
            for tension in payload["open_tensions"]
        )
        assert any(
            "Semantic sample comparison between derivation and integration is tracked in self_audit only"
            in tension
            for tension in payload["open_tensions"]
        )
        assert any(
            "Derivation sample provenance strength is tracked in self_audit only"
            in tension
            for tension in payload["open_tensions"]
        )
        assert any(
            "Derivation lineage bridge audit is tracked in self_audit only"
            in tension
            for tension in payload["open_tensions"]
        )
        assert any(
            "Derivation bridge materialization preconditions are tracked in self_audit only"
            in tension
            for tension in payload["open_tensions"]
        )
        assert any(
            "Stripped provenance backfill preconditions are tracked in self_audit only"
            in tension
            for tension in payload["open_tensions"]
        )
        assert any(
            "Stripped provenance annotation admission is tracked in self_audit only"
            in tension
            for tension in payload["open_tensions"]
        )


def test_intent_control_surface_builder_overlay_archive_contract_smoke() -> None:
    payload = {
        "self_audit": {
            "stripped_provenance_annotation_admission": {
                "target_node_id": "C003",
                "manual_review_required": True,
                "basis_node_ids": [
                    "  A2_2::REFINED::constraint_manifold_formal_derivation::e2a796f27a003a3d  ",
                    "A2_3::SOURCE_MAP_PASS::constraint_manifold_formal_derivation::e2a796f27a003a3d  ",
                ],
                "basis_edge_relations": ["STRIPPED_FROM", "ROSETTA_MAP", "SOURCE_MAP_PASS"],
                "forbidden_fields": [
                    "lineage_refs",
                    "witness_refs",
                    "properties.source_concept_id",
                ],
            },
            "stripped_provenance_backfill_precondition": {
                "bridge_source_node_ids": [
                    "A2_3::SOURCE::CONSTRAINT_MANIFOLD_DERIVATION_v1.md::ec1adffbe4396703"
                ]
            },
        },
        "provenance": {"surface_hash": "abc123"},
    }
    graph_nodes = {
        "C003": {
            "id": "C003",
            "layer": " A1_STRIPPED ",
            "node_type": "REFINED_CONCEPT",
            "name": " CONSTRAINT_MANIFOLD_FORMAL_DERIVATION ",
        },
        "A2_2::REFINED::constraint_manifold_formal_derivation::e2a796f27a003a3d": {
            "id": "A2_2::REFINED::constraint_manifold_formal_derivation::e2a796f27a003a3d",
            "layer": 7,
            "node_type": "REFINED_CONCEPT",
            "name": "constraint_manifold_formal_derivation",
        },
        "A2_3::SOURCE_MAP_PASS::constraint_manifold_formal_derivation::e2a796f27a003a3d": {
            "id": "A2_3::SOURCE_MAP_PASS::constraint_manifold_formal_derivation::e2a796f27a003a3d",
            "layer": "A2_3::SOURCE_MAP_PASS",
            "node_type": "REFINED_CONCEPT",
            "name": "constraint_manifold_formal_derivation",
        },
        "A2_3::SOURCE::CONSTRAINT_MANIFOLD_DERIVATION_v1.md::ec1adffbe4396703": {
            "id": "A2_3::SOURCE::CONSTRAINT_MANIFOLD_DERIVATION_v1.md::ec1adffbe4396703",
            "layer": {"bad": "shape"},
            "node_type": ["SOURCE_DOCUMENT"],
            "name": "CONSTRAINT_MANIFOLD_DERIVATION_v1.md",
        },
    }
    graph_edges = [
        {
            "source_id": "A2_3::SOURCE::CONSTRAINT_MANIFOLD_DERIVATION_v1.md::ec1adffbe4396703",
            "target_id": "A2_3::SOURCE_MAP_PASS::constraint_manifold_formal_derivation::e2a796f27a003a3d",
            "relation": "SOURCE_MAP_PASS",
        }
    ]

    overlay = _build_stripped_provenance_overlay_archive(
        payload=payload,
        graph_nodes=graph_nodes,
        graph_edges=graph_edges,
    )

    assert overlay["schema"] == "A2_STRIPPED_PROVENANCE_OVERLAY_v1"
    assert overlay["classification"]["surface_class"] == "ARCHIVE_ONLY"
    assert overlay["classification"]["status"] == "NONOWNER_AUDIT_OVERLAY"
    assert overlay["overlay_contract"]["runtime_effect"] == "none"
    assert overlay["overlay_contract"]["manual_review_required"] is True
    assert overlay["overlay_contract"]["do_not_write_fields"] == [
        "lineage_refs",
        "witness_refs",
        "properties.source_concept_id",
    ]
    assert overlay["provenance"]["source_surface_path"] == SURFACE_REL_PATH
    assert overlay["provenance"]["source_graph_path"] == GRAPH_REL_PATH
    assert overlay["provenance"]["source_surface_hash"] == "abc123"

    primary_chain = overlay["donor_chain"]["primary_chain"]
    assert [item["role"] for item in primary_chain] == [
        "target_stripped_node",
        "strongest_semantic_donor",
        "source_document_ancestor",
    ]
    assert [item["node_id"] for item in primary_chain] == [
        "C003",
        "A2_3::SOURCE_MAP_PASS::constraint_manifold_formal_derivation::e2a796f27a003a3d",
        "A2_3::SOURCE::CONSTRAINT_MANIFOLD_DERIVATION_v1.md::ec1adffbe4396703",
    ]
    assert all(
        set(item.keys()) <= {"node_id", "role", "layer", "node_type", "name", "via_relations"}
        for item in primary_chain
    )
    forbidden_item_fields = {
        "lineage_refs",
        "witness_refs",
        "source_class",
        "trust_zone",
        "authority",
        "admissibility_state",
        "source_concept_id",
        "target_ref",
        "candidate_id",
    }
    assert all(not (set(item.keys()) & forbidden_item_fields) for item in primary_chain)
    assert primary_chain[0]["layer"] == "A1_STRIPPED"
    assert primary_chain[0]["name"] == "CONSTRAINT_MANIFOLD_FORMAL_DERIVATION"
    assert "via_relations" not in primary_chain[0]
    assert primary_chain[1]["via_relations"] == ["STRIPPED_FROM", "ROSETTA_MAP"]
    assert primary_chain[1]["node_id"] == "A2_3::SOURCE_MAP_PASS::constraint_manifold_formal_derivation::e2a796f27a003a3d"
    assert primary_chain[2]["via_relations"] == ["SOURCE_MAP_PASS"]
    assert primary_chain[2]["layer"] == ""
    assert primary_chain[2]["node_type"] == ""

    secondary_context = overlay["donor_chain"]["secondary_context_only"]
    assert secondary_context == [
        {
            "node_id": "A2_2::REFINED::constraint_manifold_formal_derivation::e2a796f27a003a3d",
            "layer": "",
            "node_type": "REFINED_CONCEPT",
            "name": "constraint_manifold_formal_derivation",
            "role": "secondary_context_only",
        }
    ]
    assert all(
        set(item.keys()) == {"node_id", "layer", "node_type", "name", "role"}
        for item in secondary_context
    )
    assert overlay["donor_chain"]["basis_node_ids"] == [
        "A2_2::REFINED::constraint_manifold_formal_derivation::e2a796f27a003a3d",
        "A2_3::SOURCE_MAP_PASS::constraint_manifold_formal_derivation::e2a796f27a003a3d",
    ]
    assert overlay["donor_chain"]["basis_edge_relations"] == [
        "STRIPPED_FROM",
        "ROSETTA_MAP",
        "SOURCE_MAP_PASS",
    ]
    assert overlay["donor_chain"]["bridge_source_node_ids"] == [
        "A2_3::SOURCE::CONSTRAINT_MANIFOLD_DERIVATION_v1.md::ec1adffbe4396703"
    ]
    assert overlay["donor_chain"]["supporting_source_doc_ids"] == [
        "A2_3::SOURCE::CONSTRAINT_MANIFOLD_DERIVATION_v1.md::ec1adffbe4396703"
    ]

    print("PASS: test_intent_control_surface_builder_refined_focus_candidates_smoke")


if __name__ == "__main__":
    test_intent_control_surface_builder_refined_focus_candidates_smoke()
    test_intent_control_surface_builder_overlay_archive_contract_smoke()
