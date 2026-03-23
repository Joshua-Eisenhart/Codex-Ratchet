# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_stage16_mix_contract_baseline__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Parent batch
- `BATCH_sims_stage16_axis6_mix_control_sweep_family__v1`
- reused parent artifacts:
  - `SOURCE_MAP__v1.md`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Comparison anchors
- `BATCH_A2MID_sims_evidence_boundary__v1`
  - used because it provides the nearest sims-wide catalog-versus-evidence separation and hash-anchored evidence-boundary packet
- `BATCH_A2MID_sim_suite_v1_descendant_provenance_split__v1`
  - used because it provides the nearest earlier Stage16 packet where local surface, stored identity, and current top-level provenance diverge
- `BATCH_A2MID_sim_suite_v2_externalized_provenance__v1`
  - used because it preserves the nearest successor-side Stage16 byte-identity and provenance-drift warning packet

## Candidate dependency map
- `RC1 STAGE16_MIXED_AXIS6_QUESTION_FAMILY_WITH_CONTRACT_SPLIT`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster A`
    - `SIM_CLUSTER_MAP__v1.md:Cluster B`
    - `A2_3_SIM_DISTILLATES__v1.md:D1`
    - `A2_3_SIM_DISTILLATES__v1.md:D3`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C2`
    - `TENSION_MAP__v1.md:T1`
- `RC2 PAIRED_CONTROL_VERSUS_SWEEP_MODE_NONINTERCHANGEABILITY_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster A`
    - `SIM_CLUSTER_MAP__v1.md:Cluster B`
    - `A2_3_SIM_DISTILLATES__v1.md:D3`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`
    - `TENSION_MAP__v1.md:T1`
- `RC3 SUB4_AXIS6U_EXACT_UNIFORM_BASELINE_ANCHOR_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster C`
    - `A2_3_SIM_DISTILLATES__v1.md:D2`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C3`
    - `TENSION_MAP__v1.md:T2`
- `RC4 CATALOG_STAGE16_TRIO_WITH_TOPLEVEL_EVIDENCE_ABSENCE_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cross-Cluster Read`
    - `A2_3_SIM_DISTILLATES__v1.md:D4`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C4`
    - `TENSION_MAP__v1.md:T3`
  - comparison anchors:
    - `BATCH_A2MID_sims_evidence_boundary__v1:RC2`
- `RC5 CONTROL_LOCALITY_VERSUS_SWEEP_SCALE_ASYMMETRY_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster A`
    - `SIM_CLUSTER_MAP__v1.md:Cluster B`
    - `A2_3_SIM_DISTILLATES__v1.md:D5`
    - `TENSION_MAP__v1.md:T4`
    - `TENSION_MAP__v1.md:T5`
- `RC6 CONTROL_SE_REGION_VERSUS_SWEEP_SI_REGION_DOMINANCE_RULE`
  - parent dependencies:
    - `A2_3_SIM_DISTILLATES__v1.md:D5`
    - `TENSION_MAP__v1.md:T5`
    - `TENSION_MAP__v1.md:T6`

## Quarantine dependency map
- `Q1 SAME_COMPUTATION_JUST_MORE_MODES_STORY`
  - `A2_3_SIM_DISTILLATES__v1.md:D3`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`
  - `TENSION_MAP__v1.md:T1`
- `Q2 EXACT_BASELINE_EQUALITY_AS_FAMILY_MEMBERSHIP`
  - `A2_3_SIM_DISTILLATES__v1.md:D2`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C3`
  - `TENSION_MAP__v1.md:T2`
- `Q3 CATALOG_MEMBERSHIP_AS_TOPLEVEL_EVIDENCE_ADMISSION`
  - `A2_3_SIM_DISTILLATES__v1.md:D4`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C4`
  - `TENSION_MAP__v1.md:T3`
- `Q4 ONE_UNIFORM_PERTURBATION_SCALE_ACROSS_CONTROL_AND_SWEEP`
  - `A2_3_SIM_DISTILLATES__v1.md:D5`
  - `TENSION_MAP__v1.md:T4`
  - `TENSION_MAP__v1.md:T5`
- `Q5 CONTROL_SE_DOMINANCE_AS_FULL_SWEEP_MAP`
  - `A2_3_SIM_DISTILLATES__v1.md:D5`
  - `TENSION_MAP__v1.md:T6`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the parent batch already isolates the contract split, exact baseline anchoring, evidence-admission gap, and stage-specific signal asymmetry needed for this bounded reduction
