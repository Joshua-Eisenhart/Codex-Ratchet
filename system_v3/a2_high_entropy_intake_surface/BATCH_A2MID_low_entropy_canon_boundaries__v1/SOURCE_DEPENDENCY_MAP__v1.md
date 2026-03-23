# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_low_entropy_canon_boundaries__v1`
Extraction mode: `TERM_CONFLICT_REDUCTION_PASS`
Date: 2026-03-09

## Parent batch
- `BATCH_archived_state_low_entropy_library_v4__v1`
- reused parent artifacts:
  - `SOURCE_MAP__v1.md`
  - `CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_DISTILLATES__v1.md`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Comparison anchors
- `BATCH_A2MID_episode01_persistence_transition__v1`
  - used to keep low-entropy summary claims tied to thicker archived process-history context

## Candidate dependency map
- `RC1 ARCHIVED_LOW_ENTROPY_SUMMARY_NONAUTHORITY_RULE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C4`
    - `CLUSTER_MAP__v1.md:C5`
    - `A2_3_DISTILLATES__v1.md:D1`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C1`
- `RC2 THIN_CANON_INVENTORY_AND_SCOPE_BOUNDARY_PACKET`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C1`
    - `CLUSTER_MAP__v1.md:C2`
    - `A2_3_DISTILLATES__v1.md:D2`
    - `A2_3_DISTILLATES__v1.md:D4`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
    - `TENSION_MAP__v1.md:T2`
- `RC3 APPEND_ONLY_SCOPE_CORRECTION_WITHOUT_REWRITE_RULE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C2`
    - `CLUSTER_MAP__v1.md:C4`
    - `A2_3_DISTILLATES__v1.md:D4`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C1`
    - `TENSION_MAP__v1.md:T1`
    - `TENSION_MAP__v1.md:T2`
- `RC4 POST_CANON_CONSEQUENCE_LAYER_CLASSIFICATION_PACKET`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C3`
    - `CLUSTER_MAP__v1.md:C5`
    - `A2_3_DISTILLATES__v1.md:D3`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
    - `TENSION_MAP__v1.md:T3`
    - `TENSION_MAP__v1.md:T4`
  - comparison anchors:
    - `BATCH_A2MID_episode01_persistence_transition__v1:RC4`
- `RC5 STATE_SNAPSHOT_VS_STRUCTURAL_LAW_SEPARATION_RULE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C1`
    - `A2_3_DISTILLATES__v1.md:D5`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C4`
    - `TENSION_MAP__v1.md:T6`
- `RC6 LOW_ENTROPY_REQUIRES_THICKER_REASONING_CONTEXT_RULE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C4`
    - `CLUSTER_MAP__v1.md:C5`
    - `A2_3_DISTILLATES__v1.md:D1`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C5`
    - `TENSION_MAP__v1.md:T5`
  - comparison anchors:
    - `BATCH_A2MID_episode01_persistence_transition__v1:RC1`
    - `BATCH_A2MID_episode01_persistence_transition__v1:RC3`

## Quarantine dependency map
- `Q1 HEADER_V1_BODY_V4_VERSION_MISMATCH_AS_CURRENT_INTERFACE_SIGNAL`
  - `TENSION_MAP__v1.md:T1`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C4`
- `Q2 SYSTEM_WIDE_NONCOMMUTATION_WITHOUT_THREAD_B_SCOPE_CAVEAT`
  - `TENSION_MAP__v1.md:T2`
  - `CLUSTER_MAP__v1.md:C2`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C4`
- `Q3 POST_CANON_COMPOSITION_EQUIVALENCE_UPDATE_CLAIMS_AS_THIN_CANON_FACTS`
  - `CLUSTER_MAP__v1.md:C3`
  - `CLUSTER_MAP__v1.md:C5`
  - `A2_3_DISTILLATES__v1.md:D3`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
- `Q4 CANON_CLEAN_SNAPSHOT_ENTRIES_AS_TIMELESS_LAW`
  - `A2_3_DISTILLATES__v1.md:D5`
  - `TENSION_MAP__v1.md:T6`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C4`
- `Q5 LOW_ENTROPY_COMPRESSION_AS_SUFFICIENT_REASONING_SUBSTRATE`
  - `A2_3_DISTILLATES__v1.md:D1`
  - `TENSION_MAP__v1.md:T5`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C5`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the parent batch already isolates the inventory, boundary, consequence, and snapshot tensions needed for this second-pass reduction
