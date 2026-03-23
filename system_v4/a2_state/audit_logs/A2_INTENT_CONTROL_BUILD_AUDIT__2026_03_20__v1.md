# A2 Intent Control Surface Build Audit

- schema: `A2_INTENT_CONTROL_SURFACE_v1`
- json_path: `system_v4/a2_state/A2_INTENT_CONTROL__CURRENT__v1.json`
- maker_intents: `3`
- runtime_contexts: `1`
- refined_intents: `3`
- focus_terms: `12`
- steering_focus_terms: `8`
- executable_focus_terms: `4`
- executable_focus_refinement_candidates: `3`
- executable_focus_promotion_ready: `3`
- executable_focus_cluster_precision_candidates: `2`
- executable_focus_execution_binding_candidates: `1`
- executable_focus_execution_binding_positive_probes: `1`
- non_negotiables: `4`

## Focus Terms

intent, system, context, continuously, graphs, skills, memory, graph, skill, preserved, runtime, agents

## Executable Focus Refinement Candidates

- integration: novel=41 hits=51
- preservation: novel=14 hits=17
- derivation: novel=14 hits=15

## Promotion Readiness

- derivation: status=candidate_for_execution_binding_check cluster=coherent exec_probe=bounded_positive_effect solo_gate=True novel=14 scope=narrow
- integration: status=candidate_for_cluster_precision_check cluster=mixed exec_probe=blocked_by_cluster_precision solo_gate=True novel=41 scope=narrow
- preservation: status=candidate_for_cluster_precision_check cluster=mixed exec_probe=blocked_by_cluster_precision solo_gate=True novel=14 scope=narrow

## Semantic Comparison

- comparison_pair: `derivation, integration`
- structural_front_runner: `derivation`
- semantic_hygiene_front_runner: `integration`
- decision: `keep_audit_only_no_promotion`

- derivation family: posture=mixed_clustered top_family=A2_3::SOURCE_MAP_PASS share=0.466667
- integration family: posture=highly_concentrated top_family=A2_3::SOURCE_MAP_PASS share=0.960784

## Derivation Contamination Audit

- status: `audit_only_nonoperative`
- contamination_risk: `mixed_but_not_pure_source_map_carryover`
- risk_flags: `high_intake_dominance, provenance_sparse_hits`
- counter_signals: `engine_pattern_family_present, stripped_layer_present, refined_concepts_present, shared_semantic_tag_signal`
- source_map_share: `0.466667`
- engine_pattern_share: `0.333333`
- stripped_share: `0.2`
- high_intake_share: `0.8`
- provenance_sparse_share: `1.0`

## Semantic Sample Comparison

- status: `audit_only_nonoperative`
- comparison_result: `inconclusive_audit_only`
- confidence: `medium`
- left_family: `derivation` posture=`mixed_sample`
- right_family: `integration` posture=`source_map_residue_lean`
- left_sample_node_ids: `A1_STRIPPED::CONSTRAINT_MANIFOLD_DERIVATION_V1, A1_STRIPPED::CONSTRAINT_MANIFOLD_FORMAL_DERIVATION, A2_3::ENGINE_PATTERN_PASS::CMD_Compatibility_From_Transport::e079375fe93c8abf, A2_3::SOURCE_MAP_PASS::Pure_QIT_Free_Energy_Principle::63a6e51e1155c939, A2_3::SOURCE_MAP_PASS::a2_state_v3_a2_update_note__a1_family_slice_track_de::5350a243a392237f, A2_3::SOURCE_MAP_PASS::cl_constraint_manifold_derivation_v1::f13ebd74ae1262de`
- right_sample_node_ids: `A1_STRIPPED::A2_WORKER_INTAKE_WARM_COLD_CONSUMER_INTEGRATION, A2_3::ENGINE_PATTERN_PASS::DETERMINISTIC_REPLAY_HASH_EQUALITY::bdb42d5287cc4361, A2_3::SOURCE_MAP_PASS::test_a1_a0_b_sim_integration_py::cbb03ffa74a628fb, A2_3::SOURCE_MAP_PASS::01_system_understanding_integration__2026_03_17__v::bb7e1a59fc22d640, A2_3::SOURCE_MAP_PASS::03_plan_execution_integration__2026_03_17__v1::39753fe85970a1cd, A2_3::SOURCE_MAP_PASS::05_overall_recovery_integration__2026_03_17__v1::5157b3f185e3a708`

## Derivation Sample Provenance Strength

- status: `audit_only_nonoperative`
- assessment_result: `mixed_provenance`
- risk_flags: `sample_provenance_sparse, sample_residue_heavy`
- dual_provenance: `True`
- witness_backed: `True`
- lineage_backed: `True`
- sample_semantic_support_share: `0.333333`
- sample_residue_risk_share: `0.5`
- sample_provenance_sparse_share: `1.0`
- sample_uplift_ratio: `0.333333`

## Derivation Lineage Bridge Audit

- status: `audit_only_nonoperative`
- bridge_status: `bridgeable_via_upper_surfaces_but_unmaterialized`
- direct_intent_bridge_count: `0`
- reachable_within_3_hops_count: `0`
- upper_surface_neighbor_count: `1`
- no_observed_bridge_count: `5`

## Derivation Bridge Materialization Precondition

- status: `audit_only_nonoperative`
- decision: `keep_self_audit_only_no_edge_materialization`
- single_bridgeable_path: `True`
- candidate_middle_node_id: `A1_STRIPPED::CONSTRAINT_MANIFOLD_FORMAL_DERIVATION`
- candidate_middle_node_layer: `A1_STRIPPED`
- recommended_relation: `RELATED_TO`
- materialization_allowed_in_current_surface: `False`
- hard_blockers: `missing_direct_candidate_provenance, no_direct_or_short_graph_bridge_to_intent, no_existing_relation_label_for_honest_intent_alignment`

## Stripped Provenance Backfill Precondition

- status: `audit_only_nonoperative`
- decision: `keep_self_audit_only_no_provenance_backfill`
- target_node_id: `A1_STRIPPED::CONSTRAINT_MANIFOLD_FORMAL_DERIVATION`
- admissible_now: `False`
- materialization_allowed_in_current_surface: `False`
- candidate_backfill_source_node_ids: `A2_2::REFINED::constraint_manifold_formal_derivation::e2a796f27a003a3d, A2_1::KERNEL::CONSTRAINT_MANIFOLD_FORMAL_DERIVATION::82183474d44c7ead, A2_3::SOURCE_MAP_PASS::constraint_manifold_formal_derivation::e2a796f27a003a3d`
- do_not_backfill_fields: `lineage_refs, witness_refs`
- hard_blockers: `basis_is_indirect_graph_chain_only, direct_field_backfill_would_overclaim_provenance, donor_chain_has_no_direct_provenance, target_has_no_direct_provenance`

## Stripped Provenance Annotation Admission

- status: `audit_only_nonoperative`
- decision: `keep_fail_closed_namespaced_overlay_only_manual_review`
- annotation_path: `properties.overlay_provenance_audit`
- admissible_now: `False`
- builder_supports_properties_merge: `True`
- forbidden_fields: `lineage_refs, witness_refs, source_class, trust_zone, authority, admissibility_state, properties.source_concept_id, properties.target_ref, properties.candidate_id`
- hard_blockers: `basis_is_indirect_graph_chain_only, direct_field_backfill_would_overclaim_provenance, donor_chain_has_no_direct_provenance, no_grounded_trace_anchor, target_has_no_direct_provenance`

## Stripped Provenance Overlay Archive

- json_path: `system_v4/a2_state/audit_logs/STRIPPED_PROVENANCE_OVERLAY__2026_03_20__v1.json`
- surface_class: `ARCHIVE_ONLY`
- status: `NONOWNER_AUDIT_OVERLAY`
- target_node_id: `A1_STRIPPED::CONSTRAINT_MANIFOLD_FORMAL_DERIVATION`
- primary_chain_count: `3`

## Open Tensions

- Graph-discrimination pruned 4 broad or redundant steering terms from executable use.
- 3 narrower graph-backed intent-term candidates are available for future executable refinement.
- No staged semantic executable term is promoted yet; promotion readiness remains audit-only pending cluster precision and execution-binding proof.
- 1 staged semantic term(s) show bounded positive execution-binding probe results but remain audit-only pending manual promotion review.
- Structural and semantic staged-term signals are compared explicitly, but disagreement still resolves to audit-only.
- Derivation staged-term contamination evidence is tracked in self_audit only and remains non-operative.
- Semantic sample comparison between derivation and integration is tracked in self_audit only and remains non-operative.
- Derivation sample provenance strength is tracked in self_audit only and remains non-operative.
- Derivation lineage bridge audit is tracked in self_audit only and remains non-operative.
- Derivation bridge materialization preconditions are tracked in self_audit only and remain non-operative.
- Stripped provenance backfill preconditions are tracked in self_audit only and remain non-operative.
- Stripped provenance annotation admission is tracked in self_audit only and remains non-operative.
