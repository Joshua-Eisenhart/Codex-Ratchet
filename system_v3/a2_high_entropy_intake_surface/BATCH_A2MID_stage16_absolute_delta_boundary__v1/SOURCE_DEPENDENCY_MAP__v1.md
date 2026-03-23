# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_stage16_absolute_delta_boundary__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Parent batch
- `BATCH_sims_stage16_sub4_axis6u_absolute_surface__v1`
- reused parent artifacts:
  - `SOURCE_MAP__v1.md`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Comparison anchors
- `BATCH_A2MID_stage16_mix_contract_baseline__v1`
  - used because it provides the nearest mixed-family packet that consumes this absolute surface as an exact baseline anchor without merging families
- `BATCH_A2MID_sim_suite_v1_descendant_provenance_split__v1`
  - used because it provides the nearest Stage16 V4 byte-identity and provenance-drift warning packet
- `BATCH_A2MID_sim_suite_v2_externalized_provenance__v1`
  - used because it provides the nearest Stage16 V5 byte-identity and mega-hash provenance-drift warning packet

## Candidate dependency map
- `RC1 STANDALONE_STAGE16_ABSOLUTE_BASELINE_SURFACE_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster A`
    - `A2_3_SIM_DISTILLATES__v1.md:D1`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C2`
- `RC2 LOCAL_SIM_ID_VERSUS_REPOTOP_DESCENDANT_ADMISSION_SPLIT_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster A`
    - `SIM_CLUSTER_MAP__v1.md:Cluster C`
    - `A2_3_SIM_DISTILLATES__v1.md:D3`
    - `A2_3_SIM_DISTILLATES__v1.md:D4`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C3`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C4`
    - `TENSION_MAP__v1.md:T1`
    - `TENSION_MAP__v1.md:T4`
  - comparison anchors:
    - `BATCH_A2MID_sim_suite_v1_descendant_provenance_split__v1:RC4`
    - `BATCH_A2MID_sim_suite_v2_externalized_provenance__v1:RC5`
- `RC3 ABSOLUTE_BASELINE_VERSUS_DELTA_DESCENDANT_CONTRACT_SPLIT_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster A`
    - `SIM_CLUSTER_MAP__v1.md:Cluster C`
    - `A2_3_SIM_DISTILLATES__v1.md:D4`
    - `A2_3_SIM_DISTILLATES__v1.md:D5`
    - `TENSION_MAP__v1.md:T2`
- `RC4 MIX_CONTROL_BASELINE_CONSUMER_WITHOUT_FAMILY_MERGE_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster B`
    - `A2_3_SIM_DISTILLATES__v1.md:D2`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`
    - `TENSION_MAP__v1.md:T3`
  - comparison anchors:
    - `BATCH_A2MID_stage16_mix_contract_baseline__v1:RC3`
- `RC5 V4_V5_BYTE_IDENTITY_WITHOUT_CURRENT_SURFACE_IDENTITY_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster C`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C3`
    - `TENSION_MAP__v1.md:T2`
  - comparison anchors:
    - `BATCH_A2MID_sim_suite_v1_descendant_provenance_split__v1:RC4`
    - `BATCH_A2MID_sim_suite_v2_externalized_provenance__v1:RC5`
- `RC6 TERRAIN8_ADJACENCY_NONMERGE_NEXT_FAMILY_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster D`
    - `A2_3_SIM_DISTILLATES__v1.md:D6`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C6`
    - `TENSION_MAP__v1.md:T5`
    - `TENSION_MAP__v1.md:T6`

## Quarantine dependency map
- `Q1 RELATED_STAGE16_DESCENDANTS_AS_PROOF_OF_LOCAL_REPOTOP_ADMISSION`
  - `A2_3_SIM_DISTILLATES__v1.md:D3`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C4`
  - `TENSION_MAP__v1.md:T1`
- `Q2 SAME_STAGE_LATTICE_AS_SAME_OUTPUT_CONTRACT`
  - `A2_3_SIM_DISTILLATES__v1.md:D4`
  - `TENSION_MAP__v1.md:T2`
- `Q3 EXACT_BASELINE_MATCH_AS_FAMILY_MERGE`
  - `A2_3_SIM_DISTILLATES__v1.md:D2`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`
  - `TENSION_MAP__v1.md:T3`
- `Q4 CATALOG_COLOCATION_AS_EVIDENCE_STRENGTH_EQUIVALENCE`
  - `A2_3_SIM_DISTILLATES__v1.md:D4`
  - `TENSION_MAP__v1.md:T4`
- `Q5 TERRAIN8_SIGN_GAPS_AS_STAGE16_CELL_BEHAVIOR`
  - `A2_3_SIM_DISTILLATES__v1.md:D6`
  - `TENSION_MAP__v1.md:T5`
  - `TENSION_MAP__v1.md:T6`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the parent batch already isolates the absolute-versus-delta contract split, local-versus-repo-top admission split, exact baseline-consumer relation, and terrain8 boundary needed for this bounded reduction
