# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_axis12_constraints_v2_surface_split__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## 1) Parent Batch
- parent batch:
  - `BATCH_sims_axis12_seq_constraints_family__v1`
- parent artifacts used:
  - `SOURCE_MAP__v1.md`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`
- parent role in this reduction:
  - provides the bounded local full axis12 constraint pair shell
  - isolates the local-surface-versus-`V2` descendant seam
  - preserves local four-layer constraint retention, same-hash `seni` divergence, the balanced-pair versus asymmetric-pair split, and the retained axis2-count layer

## 2) Comparison Anchors
- comparison anchor:
  - `BATCH_A2MID_axis12_edge_partition_v4_seam__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the immediately preceding local-suite-versus-descendant seam style and coarse-structural-versus-stronger-order caution
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the local evidence versus repo-top admission boundary reused here
- comparison anchor:
  - `BATCH_A2MID_axis0_traj_suite_descendant_seams__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies a nearby full-surface-versus-compressed-descendant seam style

## 3) Candidate Dependency Map
### RC1) `AXIS12_SEQ_CONSTRAINTS_PAIR_RULE`
- parent dependencies:
  - cluster `A`
  - distillate `D1`
  - candidate summaries:
    - `C1`
    - `C2`

### RC2) `LOCAL_SURFACE_VS_V2_DESCENDANT_ADMISSION_RULE`
- parent dependencies:
  - cluster `D`
  - distillates:
    - `D4`
    - `D6`
  - candidate summary `C4`
  - tension `T1`
- comparison anchor dependencies:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`
  - `BATCH_A2MID_axis12_edge_partition_v4_seam__v1:RC2`

### RC3) `LOCAL_FOUR_LAYER_VS_V2_EDGE_SUBSET_RULE`
- parent dependencies:
  - clusters:
    - `B`
    - `D`
  - distillates:
    - `D2`
    - `D4`
    - `D6`
  - candidate summary `C5`
  - tension `T2`
- comparison anchor dependencies:
  - `BATCH_A2MID_axis0_traj_suite_descendant_seams__v1:RC3`

### RC4) `SAME_HASH_SENI_DIVERGENCE_RULE`
- parent dependencies:
  - clusters:
    - `B`
    - `D`
  - distillates:
    - `D2`
    - `D4`
    - `D6`
  - candidate summary `C5`
  - tension `T3`

### RC5) `ASYMMETRIC_PAIR_AXIS2_ORIENTATION_RULE`
- parent dependencies:
  - clusters:
    - `B`
    - `C`
  - distillates:
    - `D2`
    - `D3`
    - `D6`
  - candidate summary `C3`
  - tension `T4`

### RC6) `BALANCED_PAIR_NONSEPARATION_LIMIT_RULE`
- parent dependencies:
  - clusters:
    - `B`
    - `C`
  - distillates:
    - `D2`
    - `D3`
    - `D6`
  - candidate summary `C3`
  - tension `T5`

## 4) Quarantine Dependency Map
### Q1) `LOCAL_SURFACE_AS_REPOTOP_ADMITTED_VIA_SHARED_HASH`
- parent dependencies:
  - distillates:
    - `D4`
    - `D6`
  - candidate summary `C4`
  - tension `T1`

### Q2) `V2_AS_FULL_LOCAL_METRIC_SURFACE`
- parent dependencies:
  - distillates:
    - `D2`
    - `D4`
    - `D6`
  - candidate summary `C5`
  - tension `T2`

### Q3) `SAME_HASH_AS_BEHAVIORAL_IDENTITY`
- parent dependencies:
  - distillates:
    - `D4`
    - `D6`
  - candidate summary `C5`
  - tension `T3`

### Q4) `SEQ03_SEQ04_AS_ONE_UNDIFFERENTIATED_ASYMMETRIC_CLASS`
- parent dependencies:
  - distillates:
    - `D3`
    - `D6`
  - candidate summary `C3`
  - tension `T4`

### Q5) `BALANCED_PAIR_AS_SEMANTICALLY_RESOLVED`
- parent dependencies:
  - distillates:
    - `D3`
    - `D6`
  - candidate summary `C3`
  - tension `T5`
