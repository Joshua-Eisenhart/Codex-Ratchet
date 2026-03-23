# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_system_spec_role_boundaries__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent batch
- `BATCH_archived_state_system_spec_v1__v1`
- reused parent artifacts:
  - `SOURCE_MAP__v1.md`
  - `CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_DISTILLATES__v1.md`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Comparison anchors
- `BATCH_A2MID_jp_boot_artifact_boundaries__v1`
  - used to align archived A2 boundary language with the surrounding archived interaction-harness packet
- `BATCH_A2MID_low_entropy_canon_boundaries__v1`
  - used to align the archived role plaque with the adjacent archived canon-boundary summary packet

## Candidate dependency map
- `RC1 ARCHIVED_SYSTEM_SPEC_PLAQUE_NONAUTHORITY_RULE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C5`
    - `A2_3_DISTILLATES__v1.md:D1`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C1`
- `RC2 NONCANON_A2_OUTER_LAYER_IDENTITY_PACKET`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C1`
    - `A2_3_DISTILLATES__v1.md:D1`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C1`
  - comparison anchors:
    - `BATCH_A2MID_jp_boot_artifact_boundaries__v1:RC3`
- `RC3 A2_VS_THREAD_B_RATCHET_BOUNDARY_PACKET`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C2`
    - `A2_3_DISTILLATES__v1.md:D2`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
  - comparison anchors:
    - `BATCH_A2MID_low_entropy_canon_boundaries__v1:RC2`
- `RC4 SAVE_DURABILITY_WITHOUT_TRANSPORT_ELEVATION_RULE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C4`
    - `A2_3_DISTILLATES__v1.md:D3`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
    - `TENSION_MAP__v1.md:T1`
    - `TENSION_MAP__v1.md:T3`
  - comparison anchors:
    - `BATCH_A2MID_jp_boot_artifact_boundaries__v1:RC2`
    - `BATCH_A2MID_jp_boot_artifact_boundaries__v1:RC6`
- `RC5 THREE_DOC_CORE_AS_TIME_BOUNDED_MEMORY_TOPOLOGY_RULE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C3`
    - `A2_3_DISTILLATES__v1.md:D4`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C4`
    - `TENSION_MAP__v1.md:T2`
- `RC6 PLAQUE_REQUIRES_THICKER_DOCTRINE_CONTEXT_RULE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C5`
    - `A2_3_DISTILLATES__v1.md:D1`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
    - `TENSION_MAP__v1.md:T4`
  - comparison anchors:
    - `BATCH_A2MID_jp_boot_artifact_boundaries__v1:RC1`
    - `BATCH_A2MID_low_entropy_canon_boundaries__v1:RC1`
    - `BATCH_A2MID_low_entropy_canon_boundaries__v1:RC6`

## Quarantine dependency map
- `Q1 ARCHIVED_VERB_SET_AS_CURRENT_ACTIVE_A2_CAPABILITY_INTERFACE`
  - `CLUSTER_MAP__v1.md:C1`
  - `TENSION_MAP__v1.md:T1`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C4`
- `Q2 THREE_DOC_CORE_AS_CURRENT_ACTIVE_A2_SURFACE_SET`
  - `CLUSTER_MAP__v1.md:C3`
  - `A2_3_DISTILLATES__v1.md:D4`
  - `TENSION_MAP__v1.md:T2`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C4`
- `Q3 FULL_SNAPSHOT_ZIP_WORDING_AS_CURRENT_SAVE_DOCTRINE`
  - `CLUSTER_MAP__v1.md:C4`
  - `A2_3_DISTILLATES__v1.md:D3`
  - `TENSION_MAP__v1.md:T3`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C4`
- `Q4 PLAQUE_COMPRESSION_AS_SUFFICIENT_OPERATIONAL_SPEC`
  - `CLUSTER_MAP__v1.md:C5`
  - `TENSION_MAP__v1.md:T4`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C4`
- `Q5 TRANSPORT_ARTIFACTS_AS_RATCHET_STATE_OR_MUTATION_AUTHORITY`
  - `CLUSTER_MAP__v1.md:C4`
  - `A2_3_DISTILLATES__v1.md:D3`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the parent batch already isolates the archived role, boundary, topology, and durability tensions needed for this second-pass reduction
