# NON_REGRESSION_PRESERVE

Preserved the existing richer A2 low-control owner surface instead of overwriting it with a thinner projection pass.
- attempted_node_count: 419
- attempted_edge_count: 238
- preserved_node_count: 419
- preserved_edge_count: 858
- preserved_only_edge_count: 620
- preserved_only_edge_ratio: 0.722611

# A2_LOW_CONTROL_GRAPH_AUDIT__2026_03_20__v1

generated_utc: 2026-03-21T01:58:56Z
build_status: MATERIALIZED
materialized: True
node_count: 419
edge_count: 858
derived_from.master_graph: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/system_graph_a2_refinery.json
derived_from.identity_registry: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/identity_registry_v1.json
derived_from.a2_high_intake_graph: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/a2_high_intake_graph_v1.json
derived_from.a2_mid_refinement_graph: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/a2_mid_refinement_graph_v1.json

## Projection Diagnostics
- attempted_internal_edge_count: 238
- selected_boundary_edge_count: 3912
- internal_edge_retention_ratio: 0.057349
- selected_node_counts_by_trust_zone: {'A2_1_KERNEL': 419}
- selected_node_counts_by_status: {'LIVE': 419}

## Upstream A2_MID Dependency
- a2_mid_dependency_mode: existence_prerequisite_only
- a2_mid_build_status: MATERIALIZED
- a2_mid_materialized: True
- a2_mid_preserved_only_edge_count: 2953
- a2_mid_preserved_only_overlap_edge_count: 2947
- a2_mid_overlap_edges_consumed_for_membership: 0
- a2_mid_overlap_edges_consumed_for_edge_selection: 0
- a2_mid_overlap_edges_consumed_for_runtime_policy: 0

## Included Node Layers
- A2_2_CANDIDATE: 341
- A2_LOW_CONTROL: 31
- A2_MID_REFINEMENT: 47

## Included Edge Relations
- DEPENDS_ON: 55
- EXCLUDES: 9
- OVERLAPS: 614
- RELATED_TO: 2
- STRUCTURALLY_RELATED: 178

## Excluded Node Types
- B_OUTCOME: 401
- B_PARKED: 96
- B_SURVIVOR: 78
- CARTRIDGE_PACKAGE: 401
- CONTEXT_SIGNAL: 1
- EXECUTION_BLOCK: 401
- EXTRACTED_CONCEPT: 5895
- GRAVEYARD_RECORD: 99
- INTENT_REFINEMENT: 3
- INTENT_SIGNAL: 3
- KERNEL_CONCEPT: 423
- REFINED_CONCEPT: 1287
- SIM_EVIDENCED: 67
- SIM_KILL: 98
- SKILL: 43
- SOURCE_DOCUMENT: 10099
- TERM_ADMITTED: 20
- THREAD_SEAL: 21

## Preserve Diagnostics
- preserved_only_node_count: 0
- attempted_only_node_count: 0
- preserved_only_edge_count: 620
- attempted_only_edge_count: 0
- shared_live_edge_count: 238
- preserved_only_edge_counts_by_relation:
  - DEPENDS_ON: 6
  - OVERLAPS: 614

## Preserved-Only OVERLAPS Hygiene
- preserved_only_overlap_edge_count: 614
- preserved_only_overlap_ratio_within_preserved_only_edges: 0.990323
- preserved_only_overlap_layer_pairs: {'A2_MID_REFINEMENT->A2_MID_REFINEMENT': 529, 'A2_LOW_CONTROL->A2_LOW_CONTROL': 37, 'A2_LOW_CONTROL->A2_MID_REFINEMENT': 33, 'A2_2_CANDIDATE->A2_2_CANDIDATE': 10, 'A2_2_CANDIDATE->A2_LOW_CONTROL': 5}
- preserved_only_overlap_trust_zone_pairs: {'A2_1_KERNEL->A2_1_KERNEL': 614}
- preserved_only_overlap_node_prefix_pairs: {'A2_2::REFINED->A2_2::REFINED': 528, 'A2_3::SOURCE_MAP_PASS->A2_3::SOURCE_MAP_PASS': 53, 'A2_1::KERNEL->A2_2::REFINED': 33}
- blank_link_type_count: 614
- zero_shared_count_count: 614

## Preserved-Only OVERLAPS Treatment
- current_runtime_effect: none_observed_in_live_consumers
- equal_runtime_weight_admissible_now: False
- recommended_future_handling: quarantine_or_downrank_before_equal_runtime_use
- reason_flags: ['preserved_only_carryover_not_in_current_master_graph', 'overlap_dominant_carryover', 'overlap_attribute_contract_mismatch', 'no_direct_live_owner_edge_consumer_observed']

## Non-Claims
- This owner graph is a bounded A2 low-control materialization, not a full nested graph stack.
- This pass does not materialize A1 Rosetta, stripped, or cartridge owner graphs.
- This pass does not treat retired graveyard kernels as active low-control memory.
