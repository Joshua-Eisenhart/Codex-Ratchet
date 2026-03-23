# identity_bridge_contracts__v1

This note records only the bridge signals that are trustworthy enough for the first identity-registry scaffold.

## Reliable Now
- `canonical_concept_id`: use the A2 graph node id as the canonical anchor when a record descends from graph material.
- `carrier_layer` plus local `carrier_id`: use this pair for per-surface binding instead of overloading lexical fields.
- `properties.source_concept_id`: primary lower-loop bridge for B/graveyard/runtime records.
- exact graph node id reuse across `A1_GRAPH_PROJECTION`: treat as projection membership only, not a fresh identity key.
- `rosetta_v2.source_concept_id` plus `packet_id`: usable Rosetta bridge only when `source_concept_id` is populated.
- `candidate_id`, `primary_candidate_id`, `target_id`, `sim_id`, and `failure_mode_id`: runtime-local bridge handles only within their declared carrier layers.

## Allowed Strong Bridge Signals
- `properties.source_concept_id`: primary lower-loop bridge for B/graveyard/runtime records.
- single resolvable `lineage_refs` chain: allowed for conservative ancestor-root grouping.
- `SOURCE_DOCUMENT.original_path`: allowed to stabilize document-root identities.
- exact graph node id reuse across projection surfaces: allowed as a projection membership, not a new entity.

## Weak Or External-Only Signals
- `name`, `description`, `tags`, and heuristic cross-links are not identity proofs.
- Rosetta packets without `source_concept_id` remain external references only.
- Multiple `lineage_refs` are preserved as ambiguity, not auto-merged into one entity.
- `target_ref` and `target_id` are bridge hints only; they do not create canonical identity on their own.
- `source_term`, `candidate_sense_id`, and export text are lexical or reporting surfaces, not canonical identity.

## Minimal Bridge Contract Fields
- `canonical_concept_id`
- `carrier_layer`
- `carrier_id`
- `dispatch_batch_id`
- `kernel_batch_id`
- `primary_candidate_id`
- `target_candidate_id`
- `failure_mode_id`
- `bridge_relation`
- `legacy_target_ref` (deprecated, non-canonical)

## Skill Cluster Bridge Extensions
- `SKILL_CLUSTER` is an allowed derived node type when the cluster is already explicit in repo-held docs.
- `MEMBER_OF` may link a `SKILL::<skill_id>` node to a `SKILL_CLUSTER::<cluster_id>` node.
- `PART_OF` may link a child cluster to a parent cluster.
- Repo-held cluster truth must come first from:
  - `system_v4/skill_specs/SKILL_CLUSTER_SCHEMA__v1.md`
  - `system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md`
- Shared tags, names, or corpus-family membership alone are not enough to create a cluster node.
- Cluster graph projection is observational only; it does not replace per-skill registry truth or tracker state.

## Current Scaffold Counts
- registry_entities: 19636
- anchored_rosetta_packets: 18
- unanchored_rosetta_packets: 9
- a1_rosetta_correspondence_count: 401
- a1_cartridge_wrapper_count: 401
- unresolved_node_count: 9513

## Explicit Non-Claims
- This scaffold does not claim the six intended layer stores already exist.
- This scaffold does not flatten topology, axis, basin, or Rosetta semantics into a false canonical ontology.
- This scaffold does not treat projections as authoritative owner stores.
