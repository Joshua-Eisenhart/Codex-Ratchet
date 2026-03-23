# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_ultra2_macro_hidden_scope__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Parent batch
- `BATCH_sims_ultra2_axis0_ab_stage16_axis6_macro_family__v1`
- reused parent artifacts:
  - `SOURCE_MAP__v1.md`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Comparison anchors
- `BATCH_A2MID_sims_evidence_boundary__v1`
  - used because it provides the nearest sims-wide catalog-versus-evidence separation packet
- `BATCH_A2MID_stage16_absolute_delta_boundary__v1`
  - used because it provides the nearest local-only admission split and next-family boundary packet
- `BATCH_A2MID_terrain8_sign_topology4_boundary__v1`
  - used because it provides the nearest local family versus adjacent next-family nonmerge pattern

## Candidate dependency map
- `RC1 ULTRA2_MACRO_COMPOSITE_SHELL_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster A`
    - `A2_3_SIM_DISTILLATES__v1.md:D1`
    - `A2_3_SIM_DISTILLATES__v1.md:D2`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C2`
- `RC2 LOCAL_ULTRA2_SIM_ID_WITHOUT_REPOTOP_ADMISSION_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster A`
    - `A2_3_SIM_DISTILLATES__v1.md:D4`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C3`
    - `TENSION_MAP__v1.md:T1`
  - comparison anchors:
    - `BATCH_A2MID_sims_evidence_boundary__v1:RC2`
    - `BATCH_A2MID_stage16_absolute_delta_boundary__v1:RC2`
- `RC3 AXIS12_HIDDEN_SEQUENCE_SCOPE_BEYOND_SEQS_FIELD_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster D`
    - `A2_3_SIM_DISTILLATES__v1.md:D3`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C4`
    - `TENSION_MAP__v1.md:T3`
- `RC4 BRANCH_SPECIFIC_SCALE_AND_SEMANTIC_SPLIT_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster B`
    - `SIM_CLUSTER_MAP__v1.md:Cluster C`
    - `SIM_CLUSTER_MAP__v1.md:Cluster D`
    - `A2_3_SIM_DISTILLATES__v1.md:D2`
    - `A2_3_SIM_DISTILLATES__v1.md:D5`
    - `TENSION_MAP__v1.md:T2`
    - `TENSION_MAP__v1.md:T4`
- `RC5 ULTRA2_STAGE16_SE_CONCENTRATION_WITHIN_MACRO_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster B`
    - `A2_3_SIM_DISTILLATES__v1.md:D5`
    - `TENSION_MAP__v1.md:T5`
- `RC6 ULTRA4_FULL_STACK_EXPANSION_BOUNDARY_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster E`
    - `A2_3_SIM_DISTILLATES__v1.md:D4`
    - `A2_3_SIM_DISTILLATES__v1.md:D6`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C6`
    - `TENSION_MAP__v1.md:T6`
  - comparison anchors:
    - `BATCH_A2MID_terrain8_sign_topology4_boundary__v1:RC6`

## Quarantine dependency map
- `Q1 CATALOG_PLUS_LOCAL_WRITER_AS_REPOTOP_EVIDENCE_STATUS`
  - `A2_3_SIM_DISTILLATES__v1.md:D4`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C3`
  - `TENSION_MAP__v1.md:T1`
- `Q2 ONE_MACRO_RESULT_AS_ONE_UNIFORM_BEHAVIOR_CLASS`
  - `A2_3_SIM_DISTILLATES__v1.md:D2`
  - `A2_3_SIM_DISTILLATES__v1.md:D6`
  - `TENSION_MAP__v1.md:T2`
- `Q3 SEQS_FIELD_AS_EXHAUSTIVE_AXIS12_SCOPE_DECLARATION`
  - `A2_3_SIM_DISTILLATES__v1.md:D3`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C4`
  - `TENSION_MAP__v1.md:T3`
- `Q4 ONE_UNIFORM_ULTRA2_EFFECT_SCALE`
  - `A2_3_SIM_DISTILLATES__v1.md:D5`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`
  - `TENSION_MAP__v1.md:T4`
- `Q5 ULTRA4_AS_SAME_BOUNDED_FAMILY`
  - `A2_3_SIM_DISTILLATES__v1.md:D4`
  - `A2_3_SIM_DISTILLATES__v1.md:D6`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`
  - `TENSION_MAP__v1.md:T6`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the parent batch already isolates the macro shell, hidden Axis12 scope, branch-specific scales, and ultra4 expansion boundary needed for this bounded reduction
