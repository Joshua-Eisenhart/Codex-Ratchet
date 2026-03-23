# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_structural_memory_wayfinding__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent batch
- `BATCH_archived_state_structural_memory_map_v2__v1`
- reused parent artifacts:
  - `SOURCE_MAP__v1.md`
  - `CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_DISTILLATES__v1.md`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Comparison anchors
- `BATCH_A2MID_episode01_persistence_transition__v1`
  - used because the map's first large outline is the Episode 01 family
- `BATCH_A2MID_working_context_bridge_cautions__v1`
  - used because the map's second large outline is the working-context bridge family
- `BATCH_A2MID_export_pack_restart_bundle__v1`
  - used because the map explicitly keeps export-pack and path-level wayfinding material visible

## Candidate dependency map
- `RC1 ARCHIVED_STRUCTURAL_MAP_NONAUTHORITY_RULE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C1`
    - `A2_3_DISTILLATES__v1.md:D1`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C1`
- `RC2 TWO_DOC_CENTER_OF_GRAVITY_WAYFINDING_PACKET`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C2`
    - `A2_3_DISTILLATES__v1.md:D2`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C1`
  - comparison anchors:
    - `BATCH_A2MID_episode01_persistence_transition__v1:RC1`
    - `BATCH_A2MID_working_context_bridge_cautions__v1:RC1`
- `RC3 MAP_REQUIRES_SOURCE_BACKREFERENCE_RULE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C1`
    - `A2_3_DISTILLATES__v1.md:D1`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
    - `TENSION_MAP__v1.md:T1`
    - `TENSION_MAP__v1.md:T3`
  - comparison anchors:
    - `BATCH_A2MID_episode01_persistence_transition__v1:RC3`
    - `BATCH_A2MID_working_context_bridge_cautions__v1:RC4`
- `RC4 THIN_CANON_CAUTION_PRESERVED_INSIDE_SUMMARY_LAYER`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C3`
    - `A2_3_DISTILLATES__v1.md:D3`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C1`
    - `TENSION_MAP__v1.md:T5`
  - comparison anchors:
    - `BATCH_A2MID_episode01_persistence_transition__v1:RC4`
    - `BATCH_A2MID_working_context_bridge_cautions__v1:RC5`
- `RC5 ARTIFACT_PATH_AND_EXPORT_POINTER_WAYFINDING_PACKET`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C4`
    - `A2_3_DISTILLATES__v1.md:D3`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
  - comparison anchor:
    - `BATCH_A2MID_export_pack_restart_bundle__v1:RC2`
    - `BATCH_A2MID_export_pack_restart_bundle__v1:RC6`
- `RC6 NAMED_STUB_POINTERS_WITHOUT_CONTENT_RULE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C5`
    - `A2_3_DISTILLATES__v1.md:D4`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
    - `TENSION_MAP__v1.md:T2`

## Quarantine dependency map
- `Q1 COMPRESSED_BULLETS_AS_BETTER_AUTHORITY_THAN_SOURCE_DOCS`
  - `CLUSTER_MAP__v1.md:C1`
  - `TENSION_MAP__v1.md:T1`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
- `Q2 STUBBED_MIGRATION_AND_CONVERSATION_DOCS_AS_IF_CONTENT_WERE_PRESENT`
  - `CLUSTER_MAP__v1.md:C5`
  - `A2_3_DISTILLATES__v1.md:D4`
  - `TENSION_MAP__v1.md:T2`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
- `Q3 ARCHIVED_MAP_TOPOLOGY_AS_CURRENT_ACTIVE_A2_SURFACE_LAYOUT`
  - `A2_3_DISTILLATES__v1.md:D2`
  - `TENSION_MAP__v1.md:T4`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
- `Q4 WAYFINDING_PATH_LISTS_AS_CURRENT_ARTIFACT_INVENTORY_TRUTH`
  - `CLUSTER_MAP__v1.md:C4`
  - `A2_3_DISTILLATES__v1.md:D3`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
- `Q5 SUMMARY_LAYER_THIN_CANON_WARNINGS_AS_CANON_RESOLUTION`
  - `CLUSTER_MAP__v1.md:C3`
  - `TENSION_MAP__v1.md:T5`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C1`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the parent batch already isolates the map's topology role, source-authority gap, two-doc center of gravity, stub pointers, and preserved warning lines
