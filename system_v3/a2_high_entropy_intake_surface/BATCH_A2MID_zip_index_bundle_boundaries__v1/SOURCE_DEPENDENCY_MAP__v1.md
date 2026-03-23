# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_zip_index_bundle_boundaries__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent batch
- `BATCH_archived_state_zip_index_v1__v1`
- reused parent artifacts:
  - `SOURCE_MAP__v1.md`
  - `CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_DISTILLATES__v1.md`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Comparison anchors
- `BATCH_A2MID_upgrade_plan_integration_targets__v1`
  - used because the index includes the archived upgrade-pass family only as bundle membership, and the prior A2-mid batch already narrowed the upgrade side into planning packets
- `BATCH_A2MID_export_pack_restart_bundle__v1`
  - used because the index contains a dated export-pack subtree and duplicated A2 carry materials
- `BATCH_A2MID_system_spec_role_boundaries__v1`
  - used because the index includes save and export zip members while the archived system-spec reduction already narrows save durability away from transport or mutation elevation

## Candidate dependency map
- `RC1 ARCHIVED_ZIP_INDEX_NONAUTHORITY_RULE`
  - parent dependencies:
    - `A2_3_DISTILLATES__v1.md:D1`
    - `A2_3_DISTILLATES__v1.md:D4`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C1`
    - `TENSION_MAP__v1.md:T1`
- `RC2 BUNDLE_TOPOLOGY_CROSS_CLASS_COLOCATION_PACKET`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C1`
    - `CLUSTER_MAP__v1.md:C2`
    - `CLUSTER_MAP__v1.md:C3`
    - `CLUSTER_MAP__v1.md:C4`
    - `CLUSTER_MAP__v1.md:C5`
    - `A2_3_DISTILLATES__v1.md:D2`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
- `RC3 INVENTORY_MEMBERSHIP_WITHOUT_PAYLOAD_REREAD_RULE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C3`
    - `CLUSTER_MAP__v1.md:C4`
    - `A2_3_DISTILLATES__v1.md:D4`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
    - `TENSION_MAP__v1.md:T1`
    - `TENSION_MAP__v1.md:T5`
  - comparison anchors:
    - `BATCH_A2MID_upgrade_plan_integration_targets__v1:RC1`
    - `BATCH_A2MID_upgrade_plan_integration_targets__v1:RC6`
- `RC4 DUPLICATED_STATE_AND_EXPORT_PACK_STALE_STATE_PACKET`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C5`
    - `A2_3_DISTILLATES__v1.md:D3`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
    - `TENSION_MAP__v1.md:T3`
  - comparison anchors:
    - `BATCH_A2MID_export_pack_restart_bundle__v1:RC4`
    - `BATCH_A2MID_export_pack_restart_bundle__v1:RC5`
- `RC5 MIRROR_AND_SIDECAR_RESIDUE_PRESERVATION_RULE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C6`
    - `A2_3_DISTILLATES__v1.md:D3`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
    - `TENSION_MAP__v1.md:T4`
- `RC6 ZIP_TRANSPORT_HISTORY_VS_ACTIVE_NONMUTATION_BOUNDARY_PACKET`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C4`
    - `CLUSTER_MAP__v1.md:C5`
    - `A2_3_DISTILLATES__v1.md:D5`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
    - `TENSION_MAP__v1.md:T2`
  - comparison anchors:
    - `BATCH_A2MID_system_spec_role_boundaries__v1:RC4`
    - `BATCH_A2MID_upgrade_plan_integration_targets__v1:RC5`

## Quarantine dependency map
- `Q1 INDEXED_PAYLOAD_INCLUSION_AS_CORRECTNESS_OR_CURRENT_STATUS_PROOF`
  - `A2_3_DISTILLATES__v1.md:D4`
  - `TENSION_MAP__v1.md:T1`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
- `Q2 LISTED_UPGRADE_DOCS_AS_IF_THIS_LANE_PROCESSED_THEM`
  - `CLUSTER_MAP__v1.md:C3`
  - `TENSION_MAP__v1.md:T5`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
- `Q3 THREAD_SAVE_AND_EXPORT_ZIPS_AS_CURRENT_TRANSPORT_DOCTRINE`
  - `CLUSTER_MAP__v1.md:C4`
  - `CLUSTER_MAP__v1.md:C5`
  - `A2_3_DISTILLATES__v1.md:D5`
  - `TENSION_MAP__v1.md:T2`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
- `Q4 HAND_ASSEMBLED_BUNDLE_TOPOLOGY_AS_CURRENT_REQUIRED_PACKAGE_SCHEMA`
  - `A2_3_DISTILLATES__v1.md:D2`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
- `Q5 DUPLICATED_A2_COPIES_AS_SINGLE_CURRENT_STATE_PROOF`
  - `CLUSTER_MAP__v1.md:C5`
  - `A2_3_DISTILLATES__v1.md:D3`
  - `TENSION_MAP__v1.md:T3`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the parent batch already isolates the archived bundle topology, inclusion-only boundary, stale duplication markers, packaging residue, and zip-transport drift needed for this bounded reduction
