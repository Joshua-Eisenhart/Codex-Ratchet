# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_full_readlog_audit_signatures__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent batch
- `BATCH_archived_state_full_read_log_pass4__v1`
- reused parent artifacts:
  - `SOURCE_MAP__v1.md`
  - `CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_DISTILLATES__v1.md`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Comparison anchors
- `BATCH_A2MID_working_context_bridge_cautions__v1`
  - used to keep the read log tied to the bridge-layer rationale for artifact ingestion and drift policing
- `BATCH_A2MID_episode01_persistence_transition__v1`
  - used to keep source-class separation and contradiction layering explicit
- `BATCH_A2MID_sims_evidence_boundary__v1`
  - used to keep SIM runners/results classified as inventory artifacts rather than interpreted evidence

## Candidate dependency map
- `RC1 ARCHIVED_READ_LOG_LEDGER_NONAUTHORITY_RULE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C1`
    - `CLUSTER_MAP__v1.md:C4`
    - `A2_3_DISTILLATES__v1.md:D1`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C1`
- `RC2 UNIFORM_PER_DOCUMENT_AUDIT_SCHEMA_PACKET`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C1`
    - `SOURCE_MAP__v1.md:Segment A`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
- `RC3 MIXED_CORPUS_REQUIRES_SOURCE_CLASS_RESEPARATION_RULE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C4`
    - `A2_3_DISTILLATES__v1.md:D3`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
    - `TENSION_MAP__v1.md:T1`
  - comparison anchors:
    - `BATCH_A2MID_episode01_persistence_transition__v1:RC3`
    - `BATCH_A2MID_working_context_bridge_cautions__v1:RC3`
- `RC4 RECURRING_CONFLICT_SIGNATURE_SET_PACKET`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C2`
    - `CLUSTER_MAP__v1.md:C3`
    - `CLUSTER_MAP__v1.md:C6`
    - `A2_3_DISTILLATES__v1.md:D2`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
    - `TENSION_MAP__v1.md:T3`
    - `TENSION_MAP__v1.md:T4`
    - `TENSION_MAP__v1.md:T5`
- `RC5 CANON_UNDECLARED_RICHNESS_AUTHORITY_GAP_RULE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C3`
    - `A2_3_DISTILLATES__v1.md:D4`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
    - `TENSION_MAP__v1.md:T2`
  - comparison anchor:
    - `BATCH_A2MID_low_entropy_canon_boundaries__v1:RC2`
- `RC6 SIM_ARTIFACT_INVENTORY_NOT_EVIDENCE_SYNTHESIS_RULE`
  - parent dependencies:
    - `CLUSTER_MAP__v1.md:C5`
    - `A2_3_DISTILLATES__v1.md:D5`
    - `A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
    - `TENSION_MAP__v1.md:T6`
  - comparison anchor:
    - `BATCH_A2MID_sims_evidence_boundary__v1:RC1`
    - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`

## Quarantine dependency map
- `Q1 LOGGED_DOCUMENT_PRESENCE_AS_CONTENT_ENDORSEMENT`
  - `A2_3_DISTILLATES__v1.md:D1`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C4`
- `Q2 CONFLICT_COUNTS_AS_CURRENT_REPO_WIDE_POLICY_TRUTH`
  - `CLUSTER_MAP__v1.md:C6`
  - `A2_3_DISTILLATES__v1.md:D2`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C4`
- `Q3 MIXED_SOURCE_INVENTORY_AS_VALID_ACTIVE_MEMORY_SHAPE`
  - `CLUSTER_MAP__v1.md:C4`
  - `TENSION_MAP__v1.md:T1`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C4`
- `Q4 SIM_RESULTS_LOG_AS_INTERPRETED_EVIDENCE_SURFACE`
  - `CLUSTER_MAP__v1.md:C5`
  - `A2_3_DISTILLATES__v1.md:D5`
  - `TENSION_MAP__v1.md:T6`
- `Q5 ROOT_CONSTRAINT_LABEL_MISMATCH_AS_REPAIRED_STATE`
  - `CLUSTER_MAP__v1.md:C2`
  - `A2_3_DISTILLATES__v1.md:D2`
  - `TENSION_MAP__v1.md:T4`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the parent batch already isolates the audit schema, mixed-corpus shape, recurring conflict signatures, authority gaps, and SIM inventory posture needed for this second-pass reduction
