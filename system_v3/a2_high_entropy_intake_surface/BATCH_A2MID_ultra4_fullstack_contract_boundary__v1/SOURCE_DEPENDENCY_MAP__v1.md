# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_ultra4_fullstack_contract_boundary__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Parent batch
- `BATCH_sims_ultra4_full_stack_family__v1`
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
- `BATCH_A2MID_ultra2_macro_hidden_scope__v1`
  - used because it provides the nearest prior ultra-family macro-shell and adjacent-family boundary packet
- `BATCH_A2MID_stage16_absolute_delta_boundary__v1`
  - used because it provides the nearest local-only admission split packet for a structurally richer family

## Candidate dependency map
- `RC1 ULTRA4_FULL_STACK_SHELL_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster A`
    - `A2_3_SIM_DISTILLATES__v1.md:D1`
    - `A2_3_SIM_DISTILLATES__v1.md:D2`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C2`
- `RC2 LOCAL_ULTRA4_SIM_ID_WITHOUT_REPOTOP_ADMISSION_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster A`
    - `A2_3_SIM_DISTILLATES__v1.md:D4`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C3`
    - `TENSION_MAP__v1.md:T1`
  - comparison anchors:
    - `BATCH_A2MID_sims_evidence_boundary__v1:RC2`
    - `BATCH_A2MID_stage16_absolute_delta_boundary__v1:RC2`
- `RC3 AXIS0_AB_BASELINE_DELTA_MIXED_RECORD_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster D`
    - `A2_3_SIM_DISTILLATES__v1.md:D3`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C4`
    - `TENSION_MAP__v1.md:T2`
- `RC4 BERRY_FLUX_SIGN_SYMMETRY_WITH_NONEXACT_MAGNITUDE_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster B`
    - `A2_3_SIM_DISTILLATES__v1.md:D2`
    - `A2_3_SIM_DISTILLATES__v1.md:D5`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`
    - `TENSION_MAP__v1.md:T3`
- `RC5 BRANCH_SPECIFIC_SCALE_SPLIT_WITH_SE_CENTERED_STAGE16_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster C`
    - `SIM_CLUSTER_MAP__v1.md:Cluster D`
    - `A2_3_SIM_DISTILLATES__v1.md:D5`
    - `TENSION_MAP__v1.md:T4`
    - `TENSION_MAP__v1.md:T5`
- `RC6 ULTRA_SWEEP_NEXT_FAMILY_NONMERGE_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster E`
    - `A2_3_SIM_DISTILLATES__v1.md:D4`
    - `A2_3_SIM_DISTILLATES__v1.md:D6`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C6`
    - `TENSION_MAP__v1.md:T6`
  - comparison anchors:
    - `BATCH_A2MID_ultra2_macro_hidden_scope__v1:RC6`

## Quarantine dependency map
- `Q1 CATALOG_PLUS_LOCAL_WRITER_AS_REPOTOP_EVIDENCE_STATUS`
  - `A2_3_SIM_DISTILLATES__v1.md:D4`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C3`
  - `TENSION_MAP__v1.md:T1`
- `Q2 AXIS0_AB_AS_ONE_UNIFORM_RECORD_CONTRACT`
  - `A2_3_SIM_DISTILLATES__v1.md:D3`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C4`
  - `TENSION_MAP__v1.md:T2`
- `Q3 BERRY_FLUX_AS_EXACTLY_QUANTIZED_FROM_THIS_SURFACE_ALONE`
  - `A2_3_SIM_DISTILLATES__v1.md:D2`
  - `A2_3_SIM_DISTILLATES__v1.md:D5`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`
  - `TENSION_MAP__v1.md:T3`
- `Q4 ONE_UNIFORM_ULTRA4_EFFECT_SCALE`
  - `A2_3_SIM_DISTILLATES__v1.md:D5`
  - `TENSION_MAP__v1.md:T4`
  - `TENSION_MAP__v1.md:T5`
- `Q5 ULTRA_SWEEP_AS_SAME_BOUNDED_FAMILY`
  - `A2_3_SIM_DISTILLATES__v1.md:D4`
  - `A2_3_SIM_DISTILLATES__v1.md:D6`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`
  - `TENSION_MAP__v1.md:T6`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the parent batch already isolates the full-stack shell, mixed record contracts, Berry-flux seam, branch-specific scales, and ultra-sweep boundary needed for this bounded reduction
