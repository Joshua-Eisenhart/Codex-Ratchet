# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_batch_v3_precursor_lineage__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Parent batch
- `BATCH_sims_batch_v3_composite_precursor_bundle__v1`
- reused parent artifacts:
  - `SOURCE_MAP__v1.md`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Comparison anchors
- `BATCH_A2MID_sims_evidence_boundary__v1`
  - used because it provides the nearest existing sims-wide evidence transport and hash-boundary contract
- `BATCH_A2MID_axis4_directional_evidence_isolation__v1`
  - used because it provides the nearest producer-hash suspension and aggregate-layer separation packet
- `BATCH_sims_engine32_axis0_axis6_attack_family__v1`
  - used because the parent batch explicitly excludes adjacent `engine32` as a separate next family rather than another embedded precursor block

## Candidate dependency map
- `RC1 BATCH_V3_COMPOSITE_PRECURSOR_NONAUTHORITY_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:S1`
    - `A2_3_SIM_DISTILLATES__v1.md:D1`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C1`
- `RC2 PER_SUBPAYLOAD_HASH_OVER_AGGREGATE_CONTAINER_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:S2`
    - `A2_3_SIM_DISTILLATES__v1.md:D2`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C2`
    - `TENSION_MAP__v1.md:T2`
  - comparison anchors:
    - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`
    - `BATCH_A2MID_axis4_directional_evidence_isolation__v1:RC2`
- `RC3 BUNDLE_LOCAL_IDS_TO_STANDALONE_DESCENDANT_EVIDENCE_SHIFT_PACKET`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:S3`
    - `A2_3_SIM_DISTILLATES__v1.md:D3`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C3`
    - `TENSION_MAP__v1.md:T3`
- `RC4 DESCENDANT_DRIFT_IS_FAMILY_SPECIFIC_NOT_ONE_TO_ONE_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:S4`
    - `A2_3_SIM_DISTILLATES__v1.md:D4`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C4`
    - `TENSION_MAP__v1.md:T4`
- `RC5 STAGE16_DUPLICATE_LABEL_SAME_BYTES_RESIDUE_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:S5`
    - `TENSION_MAP__v1.md:T5`
- `RC6 ADJACENT_ENGINE32_SEPARATION_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:S6`
    - `A2_3_SIM_DISTILLATES__v1.md:D5`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`
    - `TENSION_MAP__v1.md:T7`
  - comparison anchors:
    - `BATCH_sims_engine32_axis0_axis6_attack_family__v1:A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C1`
    - `BATCH_sims_engine32_axis0_axis6_attack_family__v1:A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`

## Quarantine dependency map
- `Q1 CATALOG_OTHER_PLACEMENT_AS_SUBJECT_MATTER_LOCATION_OR_AUTHORITY`
  - `SIM_CLUSTER_MAP__v1.md:S3`
  - `TENSION_MAP__v1.md:T1`
- `Q2 AGGREGATE_RESULTS_BATCH_V3_HASH_AS_EVIDENCE_CITED_OUTPUT_HASH`
  - `SIM_CLUSTER_MAP__v1.md:S2`
  - `A2_3_SIM_DISTILLATES__v1.md:D2`
  - `TENSION_MAP__v1.md:T2`
- `Q3 LATER_STANDALONE_DESCENDANTS_AS_EXACT_RENAMES_OF_BUNDLE_PAYLOADS`
  - `SIM_CLUSTER_MAP__v1.md:S4`
  - `A2_3_SIM_DISTILLATES__v1.md:D4`
  - `TENSION_MAP__v1.md:T4`
- `Q4 NEGCTRL_V2_AND_V3_AS_INTERCHANGEABLE_BECAUSE_MEANS_MATCH`
  - `TENSION_MAP__v1.md:T6`
- `Q5 ENGINE32_MERGED_INTO_BATCH_V3_DUE_SHARED_AXIS_VOCABULARY`
  - `SIM_CLUSTER_MAP__v1.md:S6`
  - `TENSION_MAP__v1.md:T7`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the parent batch already isolates the precursor packaging pattern, per-payload evidence model, descendant drift, duplicate descendant residue, and adjacent family separation needed for this bounded reduction
