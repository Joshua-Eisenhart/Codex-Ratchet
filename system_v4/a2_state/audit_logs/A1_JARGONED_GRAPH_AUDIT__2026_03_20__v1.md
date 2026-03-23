# NON_REGRESSION_PRESERVE

Preserved the existing materialized A1 jargoned owner surface instead of overwriting it with a thinner or fail-closed rebuild.
- attempted_node_count: 0
- attempted_edge_count: 0
- attempted_build_status: FAIL_CLOSED
- preserved_node_count: 2
- preserved_edge_count: 0
- preserved_build_status: MATERIALIZED

# A1_JARGONED_GRAPH_AUDIT__2026_03_20__v1

generated_utc: 2026-03-20T20:45:46Z
build_status: FAIL_CLOSED
materialized: False
node_count: 0
edge_count: 0
anchored_rosetta_packet_count: 18
queue_scoped_packet_count: 2
selected_family_slice_name: 

## Selection Contract
- included_node_rule: Include only Rosetta v2 packets with a non-empty source_concept_id that resolves in the live master graph and whose source_term falls inside the queued A1 scope.
- edge_rule: No internal A1_JARGONED edges are materialized in this pass. ROSETTA_MAP and STRIPPED_FROM remain downstream explicit strip bridges.
- projection_policy: A1_GRAPH_PROJECTION is non-authoritative and cannot seed nodes.

## Scope Terms (Selected Family Slice)
- none

## Scope Terms (Declared Handoff Family Slice)
- probe_induced_partition_boundary
- correlation_diversity_functional
- left_weyl_spinor_engine
- right_weyl_spinor_engine

## Anchored Packet Classes
- AMBIGUOUS_LABEL: 5
- SENSE_CANDIDATE: 13

## Anchored Packet Statuses
- AMBIGUOUS: 5
- PARKED: 13

## Blockers
- queue candidate registry does not declare a selected_family_slice_json

## Non-Claims
- This pass does not promote A1_GRAPH_PROJECTION to owner authority.
- This pass does not infer lexical or heuristic Rosetta graph edges.
- This pass does not claim A1_STRIPPED or A1_CARTRIDGE already exist as owner graphs.
