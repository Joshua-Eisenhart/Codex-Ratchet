# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_ultra_sweep_terminal_exhaustion__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Parent batch
- `BATCH_sims_ultra_axis0_ab_axis6_sweep_family__v1`
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
- `BATCH_A2MID_ultra4_fullstack_contract_boundary__v1`
  - used because it provides the nearest preceding ultra-family boundary and contract-split packet
- `BATCH_A2MID_ultra2_macro_hidden_scope__v1`
  - used because it provides the nearest earlier ultra-lane macro-shell and branch-scale split packet

## Candidate dependency map
- `RC1 FINAL_ULTRA_SWEEP_SHELL_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster A`
    - `A2_3_SIM_DISTILLATES__v1.md:D1`
    - `A2_3_SIM_DISTILLATES__v1.md:D2`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C2`
- `RC2 LOCAL_ULTRA_SWEEP_SIM_ID_WITHOUT_REPOTOP_ADMISSION_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster A`
    - `A2_3_SIM_DISTILLATES__v1.md:D4`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C3`
    - `TENSION_MAP__v1.md:T1`
  - comparison anchors:
    - `BATCH_A2MID_sims_evidence_boundary__v1:RC2`
- `RC3 AXIS0_AB_BASELINE_DELTA_MIXED_RECORD_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster C`
    - `A2_3_SIM_DISTILLATES__v1.md:D3`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C4`
    - `TENSION_MAP__v1.md:T2`
- `RC4 ULTRA4_KEYSET_PARITY_WITH_VALUE_REGIME_NONIDENTITY_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster B`
    - `SIM_CLUSTER_MAP__v1.md:Cluster D`
    - `A2_3_SIM_DISTILLATES__v1.md:D2`
    - `TENSION_MAP__v1.md:T3`
  - comparison anchors:
    - `BATCH_A2MID_ultra4_fullstack_contract_boundary__v1:RC6`
- `RC5 BRANCH_SPECIFIC_SCALE_SPLIT_WITH_SE_CENTERED_STAGE16_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster B`
    - `SIM_CLUSTER_MAP__v1.md:Cluster C`
    - `A2_3_SIM_DISTILLATES__v1.md:D5`
    - `TENSION_MAP__v1.md:T4`
    - `TENSION_MAP__v1.md:T5`
  - comparison anchors:
    - `BATCH_A2MID_ultra2_macro_hidden_scope__v1:RC4`
    - `BATCH_A2MID_ultra2_macro_hidden_scope__v1:RC5`
- `RC6 SIMPY_RAW_ORDER_TERMINAL_EXHAUSTION_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cross-Cluster Read`
    - `A2_3_SIM_DISTILLATES__v1.md:D6`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C6`
    - `TENSION_MAP__v1.md:T6`

## Quarantine dependency map
- `Q1 CATALOG_PLUS_LOCAL_WRITER_AS_REPOTOP_EVIDENCE_STATUS`
  - `A2_3_SIM_DISTILLATES__v1.md:D4`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C3`
  - `TENSION_MAP__v1.md:T1`
- `Q2 AXIS0_AB_AS_ONE_UNIFORM_RECORD_CONTRACT`
  - `A2_3_SIM_DISTILLATES__v1.md:D3`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C4`
  - `TENSION_MAP__v1.md:T2`
- `Q3 CURRENT_SWEEP_AS_ULTRA4_WITHOUT_GEOMETRY`
  - `A2_3_SIM_DISTILLATES__v1.md:D2`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C4`
  - `TENSION_MAP__v1.md:T3`
- `Q4 ONE_UNIFORM_SWEEP_EFFECT_SCALE`
  - `A2_3_SIM_DISTILLATES__v1.md:D5`
  - `TENSION_MAP__v1.md:T4`
  - `TENSION_MAP__v1.md:T5`
- `Q5 MORE_RAW_ORDER_SIMPY_FAMILIES_REMAIN`
  - `A2_3_SIM_DISTILLATES__v1.md:D6`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C6`
  - `TENSION_MAP__v1.md:T6`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the parent batch already isolates the terminal ultra-sweep shell, mixed Axis0 contract, ultra4 divergence, branch-scale split, and raw-order exhaustion needed for this bounded reduction
