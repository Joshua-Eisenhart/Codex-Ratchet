# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_axis0_ab_mi_revival__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## 1) Parent Batch
- parent batch:
  - `BATCH_sims_axis0_mi_discrim_branches_ab_family__v1`
- parent artifacts used:
  - `SOURCE_MAP__v1.md`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`
- parent role in this reduction:
  - provides the third residual paired-family shell
  - isolates the AB-coupled MI revival seam
  - preserves the local-only evidence status, the no-negativity fence, and the non-AB comparison boundary

## 2) Comparison Anchors
- comparison anchor:
  - `BATCH_A2MID_axis0_nonab_sagb_vs_mi__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the exact non-AB control packet and the sibling-boundary frame reused here from the AB side
- comparison anchor:
  - `BATCH_A2MID_axis0_historyop_reconstruction_controls__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the preceding residual-pair shell and local-only evidence packet
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the local evidence versus repo-top omission pattern reused here

## 3) Candidate Dependency Map
### RC1) `AXIS0_AB_BRANCH_PAIR_RULE`
- parent dependencies:
  - cluster `A`
  - distillate `D1`
  - candidate summaries:
    - `C1`
    - `C2`
- comparison anchor dependencies:
  - `BATCH_A2MID_axis0_nonab_sagb_vs_mi__v1:RC1`
  - `BATCH_A2MID_axis0_historyop_reconstruction_controls__v1:RC1`

### RC2) `CNOT_COUPLING_MI_REVIVAL_RULE`
- parent dependencies:
  - clusters:
    - `A`
    - `B`
  - distillate `D2`
  - candidate summary `C3`
  - tensions:
    - `T2`
    - `T4`

### RC3) `LOCAL_AB_EVIDENCE_WITHOUT_REPOTOP_ADMISSION_RULE`
- parent dependencies:
  - cluster `D`
  - distillate `D4`
  - candidate summary `C5`
  - tension `T1`
- comparison anchor dependencies:
  - `BATCH_A2MID_axis0_historyop_reconstruction_controls__v1:RC3`
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`

### RC4) `MI_SIGNAL_WITHOUT_NEGATIVITY_RULE`
- parent dependencies:
  - cluster `B`
  - distillates:
    - `D2`
    - `D5`
  - tension `T2`

### RC5) `MI_GAIN_WITH_SAGB_ATTENUATION_RULE`
- parent dependencies:
  - clusters:
    - `B`
    - `C`
  - distillates:
    - `D3`
    - `D6`
  - candidate summary `C4`
  - tension `T3`
- comparison anchor dependencies:
  - `BATCH_A2MID_axis0_nonab_sagb_vs_mi__v1:RC2`
  - `BATCH_A2MID_axis0_nonab_sagb_vs_mi__v1:RC4`

### RC6) `NONAB_CONTROL_BOUNDARY_RULE`
- parent dependencies:
  - cluster `C`
  - distillates:
    - `D3`
    - `D6`
  - candidate summary `C5`
  - tension `T4`
- comparison anchor dependencies:
  - `BATCH_A2MID_axis0_nonab_sagb_vs_mi__v1:RC5`

## 4) Quarantine Dependency Map
### Q1) `THE_FIX_COMMENT_AS_REPOTOP_ADMISSION_OR_CANONIZATION`
- parent dependencies:
  - distillate `D6`
  - candidate summary `C5`
  - tension `T1`

### Q2) `NONZERO_MI_AS_NEGATIVITY_ONSET`
- parent dependencies:
  - distillates:
    - `D2`
    - `D5`
  - tension `T2`

### Q3) `AB_COUPLING_AS_ONE_DIMENSIONAL_METRIC_IMPROVEMENT`
- parent dependencies:
  - distillate `D3`
  - candidate summary `C4`
  - tension `T3`

### Q4) `AB_SIGNAL_BACKPROJECTED_ONTO_NONAB_CONTROL`
- parent dependencies:
  - distillate `D6`
  - tension `T4`

### Q5) `COMPACT_BRANCH_MEANS_AS_FULL_DYNAMIC_PROOF`
- parent dependencies:
  - distillate `D6`
  - tension `T5`
