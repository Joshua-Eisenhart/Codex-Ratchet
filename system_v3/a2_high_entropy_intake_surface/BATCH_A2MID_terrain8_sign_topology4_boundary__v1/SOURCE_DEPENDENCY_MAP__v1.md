# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_terrain8_sign_topology4_boundary__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Parent batch
- `BATCH_sims_terrain8_sign_suite_family__v1`
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
- `BATCH_A2MID_stage16_absolute_delta_boundary__v1`
  - used because it provides the nearest prior local-versus-repo-top admission split and next-family boundary packet
- `BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1`
  - used because it provides the strongest existing intake anchor that the repo-top Terrain8 block belongs to a separate Axis12/Topology4 seam family rather than to the local terrain-only suite

## Candidate dependency map
- `RC1 TERRAIN_ONLY_SIGN_SUITE_ISOLATION_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster A`
    - `A2_3_SIM_DISTILLATES__v1.md:D1`
    - `A2_3_SIM_DISTILLATES__v1.md:D2`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C2`
- `RC2 LOCAL_TERRAIN8_SIM_ID_VERSUS_REPOTOP_TOPOLOGY4_ADMISSION_SPLIT_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster A`
    - `SIM_CLUSTER_MAP__v1.md:Cluster B`
    - `A2_3_SIM_DISTILLATES__v1.md:D3`
    - `A2_3_SIM_DISTILLATES__v1.md:D4`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C3`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C4`
    - `TENSION_MAP__v1.md:T1`
    - `TENSION_MAP__v1.md:T6`
  - comparison anchors:
    - `BATCH_A2MID_sims_evidence_boundary__v1:RC2`
    - `BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1:D4`
- `RC3 TERRAIN8_NAME_SHARED_BUT_TOPOLOGY4_FAMILY_NONIDENTITY_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster A`
    - `SIM_CLUSTER_MAP__v1.md:Cluster B`
    - `A2_3_SIM_DISTILLATES__v1.md:D3`
    - `A2_3_SIM_DISTILLATES__v1.md:D6`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`
    - `TENSION_MAP__v1.md:T2`
  - comparison anchors:
    - `BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1:D1`
    - `BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1:D3`
    - `BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1:C3`
    - `BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1:C4`
- `RC4 NI_PRIMARY_SI_SECONDARY_NE_NEAR_INVARIANT_SIGN_ASYMMETRY_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster A`
    - `A2_3_SIM_DISTILLATES__v1.md:D5`
    - `TENSION_MAP__v1.md:T3`
- `RC5 STABLE_SE_NE_ORDERING_WITH_INCREMENTAL_SIGN_DELTA_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster A`
    - `A2_3_SIM_DISTILLATES__v1.md:D5`
    - `TENSION_MAP__v1.md:T4`
- `RC6 ULTRA2_CATALOG_VISIBLE_NEXT_FAMILY_NONMERGE_RULE`
  - parent dependencies:
    - `SIM_CLUSTER_MAP__v1.md:Cluster C`
    - `A2_3_SIM_DISTILLATES__v1.md:D4`
    - `A2_3_SIM_DISTILLATES__v1.md:D6`
    - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C6`
    - `TENSION_MAP__v1.md:T5`
    - `TENSION_MAP__v1.md:T6`
  - comparison anchors:
    - `BATCH_A2MID_stage16_absolute_delta_boundary__v1:RC6`

## Quarantine dependency map
- `Q1 REPO_TOP_TOPOLOGY4_TERRAIN8_BLOCK_AS_LOCAL_TERRAIN_SUITE_ADMISSION`
  - `A2_3_SIM_DISTILLATES__v1.md:D3`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C4`
  - `TENSION_MAP__v1.md:T1`
- `Q2 SHARED_TERRAIN8_NAME_AS_NUMERIC_OR_CONTRACT_CONTINUITY`
  - `A2_3_SIM_DISTILLATES__v1.md:D3`
  - `A2_3_SIM_DISTILLATES__v1.md:D6`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md:C5`
  - `TENSION_MAP__v1.md:T2`
- `Q3 UNIFORM_SIGN_SENSITIVITY_OR_UNIFORM_SIGN_INVARIANCE_STORY`
  - `A2_3_SIM_DISTILLATES__v1.md:D5`
  - `TENSION_MAP__v1.md:T3`
- `Q4 STABLE_ORDERING_AS_ZERO_SIGN_EFFECT`
  - `A2_3_SIM_DISTILLATES__v1.md:D5`
  - `TENSION_MAP__v1.md:T4`
- `Q5 ULTRA2_ADJACENCY_OR_CATALOG_COLOCATION_AS_FAMILY_MERGE_OR_ADMISSION`
  - `A2_3_SIM_DISTILLATES__v1.md:D4`
  - `A2_3_SIM_DISTILLATES__v1.md:D6`
  - `TENSION_MAP__v1.md:T5`
  - `TENSION_MAP__v1.md:T6`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the parent batch plus the existing Topology4 seam intake batch already isolate the naming/provenance boundary, local sign asymmetry, and `ultra2` family break needed for this bounded reduction
