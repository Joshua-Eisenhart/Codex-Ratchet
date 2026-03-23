# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_axis0_nonab_sagb_vs_mi__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## 1) Parent Batch
- parent batch:
  - `BATCH_sims_axis0_mi_discrim_branches_family__v1`
- parent artifacts used:
  - `SOURCE_MAP__v1.md`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`
- parent role in this reduction:
  - provides the second residual paired-family shell
  - isolates the MI-name versus stored-`SAgB` seam
  - preserves the local-only evidence status and the boundary to the adjacent `_ab` sibling

## 2) Comparison Anchors
- comparison anchor:
  - `BATCH_A2MID_axis0_historyop_reconstruction_controls__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the immediately preceding residual paired-family shell and local-only evidence packet
- comparison anchor:
  - `BATCH_A2MID_sims_residual_coverage_split__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the residual-lane pair-by-pair continuity rule
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the transport/evidence layer separation reused here for local evidence versus repo-top omission

## 3) Candidate Dependency Map
### RC1) `AXIS0_NONAB_BRANCH_PAIR_RULE`
- parent dependencies:
  - cluster `A`
  - distillate `D1`
  - candidate summaries:
    - `C1`
    - `C2`
- comparison anchor dependencies:
  - `BATCH_A2MID_axis0_historyop_reconstruction_controls__v1:RC1`
  - `BATCH_A2MID_sims_residual_coverage_split__v1:RC3`

### RC2) `MI_NAME_WITH_SAGB_REALITY_RULE`
- parent dependencies:
  - cluster `B`
  - distillate `D2`
  - candidate summaries:
    - `C3`
    - `C4`
  - tension `T2`

### RC3) `LOCAL_NONAB_EVIDENCE_WITHOUT_REPOTOP_ADMISSION_RULE`
- parent dependencies:
  - cluster `D`
  - distillate `D4`
  - tension `T1`
- comparison anchor dependencies:
  - `BATCH_A2MID_axis0_historyop_reconstruction_controls__v1:RC3`
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`

### RC4) `SAGB_BRANCH_SPLIT_WITH_ZERO_NEGATIVITY_RULE`
- parent dependencies:
  - cluster `B`
  - distillates:
    - `D2`
    - `D5`
  - tension `T4`

### RC5) `AB_SIBLING_MI_REVIVAL_BOUNDARY_RULE`
- parent dependencies:
  - cluster `C`
  - distillates:
    - `D3`
    - `D6`
  - candidate summary `C5`
  - tension `T3`

### RC6) `COMPACT_RESULT_SURFACE_SIGNAL_STRENGTH_CAUTION_RULE`
- parent dependencies:
  - cluster `B`
  - distillate `D6`
  - tension `T5`

## 4) Quarantine Dependency Map
### Q1) `LOCAL_EVIDENCE_PLUS_CATALOG_AS_REPOTOP_ADMISSION`
- parent dependencies:
  - distillate `D4`
  - tension `T1`

### Q2) `MI_DISCRIMINATOR_NAME_AS_MATERIAL_MI_SIGNAL`
- parent dependencies:
  - distillate `D2`
  - candidate summary `C4`
  - tension `T2`

### Q3) `ZERO_NEGATIVITY_AS_TOTAL_BRANCH_INVARIANCE`
- parent dependencies:
  - distillate `D5`
  - tension `T4`

### Q4) `NONAB_AND_AB_SIBLING_AS_ONE_FAMILY`
- parent dependencies:
  - distillate `D3`
  - candidate summary `C5`
  - tension `T3`

### Q5) `COMPACT_RESULT_FORMAT_AS_STRONG_MI_PROOF`
- parent dependencies:
  - distillate `D6`
  - tension `T5`
