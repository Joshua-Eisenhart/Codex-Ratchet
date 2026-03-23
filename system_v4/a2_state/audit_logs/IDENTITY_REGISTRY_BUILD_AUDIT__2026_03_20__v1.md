# NON_REGRESSION_PRESERVE

Preserved the existing populated identity owner surface instead of overwriting it with the older scaffold builder output.
- attempted_registry_entities: 19636
- preserved_node_count: 13481
- preserved_edge_count: 95106

# IDENTITY_REGISTRY_BUILD_AUDIT__2026_03_20__v1

generated_utc: 2026-03-20T20:45:43Z
master_graph_nodes: 19848
registry_entities: 19636
projection_nodes: 111
anchored_rosetta_packets: 18
unanchored_rosetta_packets: 9
a1_rosetta_correspondence_count: 401
a1_cartridge_wrapper_count: 401
unresolved_node_count: 9513

## Derivation Mode Counts
- self: 9527
- single_lineage_root: 40
- source_concept_id: 182
- source_document_path: 10099

## Pass Result
- emitted one additive identity-registry scaffold
- emitted one bridge-contract note
- preserved ambiguous identity cases instead of auto-merging them
- kept unanchored Rosetta packets external instead of inventing graph membership

## Remaining Limits
- separate A2/A1 owner graphs are still not materialized
- multi-lineage cases remain unresolved by design
- topology/axes/attractor semantics are still concept-rich but structurally thin
