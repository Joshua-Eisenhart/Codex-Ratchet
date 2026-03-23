# NON_REGRESSION_PRESERVE

Preserved the existing richer A2 mid-refinement owner surface instead of overwriting it with a thinner projection pass.
- attempted_node_count: 858
- attempted_edge_count: 76
- preserved_node_count: 858
- preserved_edge_count: 3029
- preserved_only_edge_count: 2953
- preserved_only_edge_ratio: 0.974909

# A2_MID_REFINEMENT_GRAPH_AUDIT__2026_03_20__v1

generated_utc: 2026-03-21T02:00:41Z
build_status: MATERIALIZED
materialized: True
node_count: 858
edge_count: 3029
derived_from.master_graph: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/system_graph_a2_refinery.json
derived_from.identity_registry: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/identity_registry_v1.json
derived_from.a2_high_intake_graph: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/a2_high_intake_graph_v1.json

## Projection Diagnostics
- attempted_internal_edge_count: 76
- selected_boundary_edge_count: 3899
- internal_edge_retention_ratio: 0.019119
- source_map_origin_node_count: 786
- source_map_origin_ratio: 0.916084
- selected_node_counts_by_trust_zone: {'A2_2_CANDIDATE': 858}
- selected_node_counts_by_status: {'LIVE': 858}
- selected_node_count_with_owner_declared_layer: 76
- selected_node_count_with_non_owner_declared_layer: 782

## Included Node Layers
- A2_2_CANDIDATE: 782
- A2_MID_REFINEMENT: 76

## Included Edge Relations
- DEPENDS_ON: 43
- EXCLUDES: 5
- OVERLAPS: 2947
- REFINED_INTO: 2
- RELATED_TO: 2
- STRUCTURALLY_RELATED: 30

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
- KERNEL_CONCEPT: 842
- REFINED_CONCEPT: 429
- SIM_EVIDENCED: 67
- SIM_KILL: 98
- SKILL: 43
- SOURCE_DOCUMENT: 10099
- TERM_ADMITTED: 20
- THREAD_SEAL: 21

## Preserve Diagnostics
- preserved_only_node_count: 0
- attempted_only_node_count: 0
- preserved_only_edge_count: 2953
- attempted_only_edge_count: 0
- shared_live_edge_count: 76
- preserved_only_edge_counts_by_relation:
  - DEPENDS_ON: 6
  - OVERLAPS: 2947

## Preserved-Only OVERLAPS Hygiene
- preserved_only_overlap_edge_count: 2947
- preserved_only_overlap_ratio_within_preserved_only_edges: 0.997968
- blank_link_type_count: 2947
- zero_shared_count_count: 2947
- preserved_only_overlap_layer_pairs:
  - A2_2_CANDIDATE->A2_2_CANDIDATE: 2378
  - A2_MID_REFINEMENT->A2_MID_REFINEMENT: 566
  - A2_MID_REFINEMENT->A2_2_CANDIDATE: 3
- preserved_only_overlap_trust_zone_pairs:
  - A2_2_CANDIDATE->A2_2_CANDIDATE: 2947
- preserved_only_overlap_node_prefix_pairs:
  - A2_3::SOURCE_MAP_PASS->A2_3::SOURCE_MAP_PASS: 2378
  - A2_2::REFINED->A2_2::REFINED: 566
  - A2_2::REFINED->A2_3::SOURCE_MAP_PASS: 3

## Preserved-Only OVERLAPS Treatment
- current_runtime_effect: none_observed_in_live_consumers
- equal_runtime_weight_admissible_now: False
- recommended_future_handling: quarantine_or_downrank_before_equal_runtime_use
- reason_flags: ['preserved_only_carryover_not_in_current_master_graph', 'overlap_dominant_carryover', 'overlap_attribute_contract_mismatch', 'no_direct_live_owner_edge_consumer_observed']

## Non-Claims
- This owner graph is a bounded A2 mid-refinement materialization, not a full nested graph stack.
- This pass does not materialize kernel, Rosetta, stripped, or cartridge owner graphs.
- This pass does not treat promoted_subgraph or contradiction notes as authority for node membership.
