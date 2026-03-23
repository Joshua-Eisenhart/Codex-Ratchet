# A2_LOW_CONTROL_GRAPH_AUDIT__2026_03_20__v1

generated_utc: 2026-03-23T07:08:40Z
build_status: MATERIALIZED
materialized: True
node_count: 667
edge_count: 1270
derived_from.master_graph: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/system_graph_a2_refinery.json
derived_from.identity_registry: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/identity_registry_v1.json
derived_from.a2_high_intake_graph: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/a2_high_intake_graph_v1.json
derived_from.a2_mid_refinement_graph: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/a2_mid_refinement_graph_v1.json

## Projection Diagnostics
- attempted_internal_edge_count: 1270
- selected_boundary_edge_count: 5888
- internal_edge_retention_ratio: 0.177424
- selected_node_counts_by_trust_zone: {'A2_1_KERNEL': 667}
- selected_node_counts_by_status: {'LIVE': 667}

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
- A2_2_CANDIDATE: 371
- A2_LOW_CONTROL: 296

## Included Edge Relations
- CONSTRAINS: 45
- CONTRADICTS: 2
- CO_EXTRACTED: 140
- DEPENDS_ON: 106
- EXCLUDES: 179
- PROMOTED_TO_KERNEL: 6
- REFINED_INTO: 38
- RELATED_TO: 43
- STRUCTURALLY_RELATED: 711

## Excluded Node Types
- B_OUTCOME: 401
- B_PARKED: 96
- B_SURVIVOR: 78
- CARTRIDGE_PACKAGE: 401
- CONCEPT: 1
- CONTEXT_SIGNAL: 2
- EMPIRICAL_EVIDENCE: 1
- EXECUTION_BLOCK: 401
- EXTRACTED_CONCEPT: 5895
- GRAVEYARD_RECORD: 99
- INTENT_REFINEMENT: 3
- INTENT_SIGNAL: 6
- KERNEL_CONCEPT: 277
- REFINED_CONCEPT: 1185
- SIM_EVIDENCED: 67
- SIM_KILL: 98
- SKILL: 123
- SOURCE_DOCUMENT: 10099
- TERM_ADMITTED: 20
- THREAD_SEAL: 21

## Non-Claims
- This owner graph is a bounded A2 low-control materialization, not a full nested graph stack.
- This pass does not materialize A1 Rosetta, stripped, or cartridge owner graphs.
- This pass does not treat retired graveyard kernels as active low-control memory.
