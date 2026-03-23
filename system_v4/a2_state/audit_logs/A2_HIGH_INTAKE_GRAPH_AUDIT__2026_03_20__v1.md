# A2_HIGH_INTAKE_GRAPH_AUDIT__2026_03_20__v1

generated_utc: 2026-03-21T02:03:26Z
build_status: MATERIALIZED
materialized: True
node_count: 8793
edge_count: 16279
derived_from.master_graph: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/system_graph_a2_refinery.json
derived_from.identity_registry: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/identity_registry_v1.json

## Projection Diagnostics
- attempted_internal_edge_count: 16279
- selected_boundary_edge_count: 9815
- internal_edge_retention_ratio: 0.62386
- selected_node_counts_by_trust_zone: {'A2_3_INTAKE': 8793}
- selected_node_counts_by_status: {'LIVE': 8793}

## Included Node Types
- EXTRACTED_CONCEPT: 5765
- SOURCE_DOCUMENT: 3028

## Included Edge Relations
- CONTRADICTS: 3
- DEPENDS_ON: 753
- ENGINE_PATTERN_PASS: 258
- EXCLUDES: 793
- MATH_CLASS_PASS: 6
- OVERLAPS: 1
- QIT_BRIDGE_PASS: 5
- RELATED_TO: 6001
- SOURCE_MAP_PASS: 5449
- STRUCTURALLY_RELATED: 3010

## Excluded Node Types
- B_OUTCOME: 401
- B_PARKED: 96
- B_SURVIVOR: 78
- CARTRIDGE_PACKAGE: 401
- CONTEXT_SIGNAL: 1
- EXECUTION_BLOCK: 401
- EXTRACTED_CONCEPT: 130
- GRAVEYARD_RECORD: 99
- INTENT_REFINEMENT: 3
- INTENT_SIGNAL: 3
- KERNEL_CONCEPT: 842
- REFINED_CONCEPT: 1287
- SIM_EVIDENCED: 67
- SIM_KILL: 98
- SKILL: 43
- SOURCE_DOCUMENT: 7071
- TERM_ADMITTED: 20
- THREAD_SEAL: 21

## Non-Claims
- This owner graph is a bounded A2 high-intake materialization, not a full nested graph stack.
- This pass does not materialize contradiction, kernel, Rosetta, stripped, or cartridge owner graphs.
- This pass does not promote projection artifacts to authority.
