# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_axis12_edge_partition_v4_seam__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## 1) Parent Batch
- parent batch:
  - `BATCH_sims_axis12_channel_realization_suite_family__v1`
- parent artifacts used:
  - `SOURCE_MAP__v1.md`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`
- parent role in this reduction:
  - provides the bounded fixed-parameter axis12 realization-suite pair shell
  - isolates the local-suite-versus-`V4` descendant seam
  - preserves coarse `SENI/NESI` partition versus finer endpoint ordering, global sign directionality, fixed-snapshot versus grid-scan divergence, and the stable `SEQ02` advantage

## 2) Comparison Anchors
- comparison anchor:
  - `BATCH_A2MID_axis0_traj_suite_descendant_seams__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the immediately adjacent local-suite-versus-descendant admission pattern and compressed-surface caution style
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the local evidence versus repo-top admission boundary reused here
- comparison anchor:
  - `BATCH_A2MID_axis0_traj_bell_ginibre_asymmetry__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies a nearby axis-labeled anti-collapse style for separating coarse partitioning from stronger outcome claims

## 3) Candidate Dependency Map
### RC1) `AXIS12_REALIZATION_SUITE_PAIR_RULE`
- parent dependencies:
  - cluster `A`
  - distillate `D1`
  - candidate summaries:
    - `C1`
    - `C2`

### RC2) `LOCAL_SUITE_VS_V4_DESCENDANT_ADMISSION_RULE`
- parent dependencies:
  - cluster `D`
  - distillates:
    - `D4`
    - `D6`
  - candidate summary `C4`
  - tension `T1`
- comparison anchor dependencies:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`
  - `BATCH_A2MID_axis0_traj_suite_descendant_seams__v1:RC2`

### RC3) `EDGE_PARTITION_COARSE_CLASSIFIER_RULE`
- parent dependencies:
  - clusters:
    - `B`
    - `C`
  - distillates:
    - `D2`
    - `D6`
  - candidate summary `C3`
  - tension `T2`

### RC4) `GLOBAL_AXIS3_SIGN_DIRECTIONALITY_RULE`
- parent dependencies:
  - cluster `C`
  - distillates:
    - `D2`
    - `D6`
  - tension `T3`

### RC5) `FIXED_SNAPSHOT_VS_GRIDSCAN_DESCENDANT_RULE`
- parent dependencies:
  - clusters:
    - `A`
    - `D`
  - distillates:
    - `D2`
    - `D4`
    - `D6`
  - candidate summary `C5`
  - tension `T4`
- comparison anchor dependencies:
  - `BATCH_A2MID_axis0_traj_suite_descendant_seams__v1:RC2`

### RC6) `SEQ02_STABLE_LOCAL_BEST_RULE`
- parent dependencies:
  - clusters:
    - `B`
    - `C`
  - distillates:
    - `D3`
    - `D6`
  - candidate summary `C3`
  - tension `T6`

## 4) Quarantine Dependency Map
### Q1) `LOCAL_SUITE_AS_REPOTOP_ADMITTED_VIA_SHARED_HASH`
- parent dependencies:
  - distillates:
    - `D4`
    - `D6`
  - candidate summary `C4`
  - tension `T1`

### Q2) `EDGE_FLAGS_AS_FULL_ENDPOINT_ORDERING_MODEL`
- parent dependencies:
  - distillates:
    - `D2`
    - `D6`
  - candidate summary `C3`
  - tension `T2`

### Q3) `AXIS12_FAMILY_AS_PURELY_AXIS12_STRUCTURAL_WITHOUT_SIGN_LAYER`
- parent dependencies:
  - distillates:
    - `D2`
    - `D6`
  - tension `T3`

### Q4) `V4_AS_RENAMED_COPY_OF_LOCAL_SNAPSHOT`
- parent dependencies:
  - distillates:
    - `D4`
    - `D6`
  - candidate summary `C5`
  - tension `T4`

### Q5) `ADJACENT_HARDEN_RUNNERS_AS_CURRENT_PAIRED_BATCH`
- parent dependencies:
  - distillates:
    - `D5`
    - `D6`
  - candidate summary `C2`
  - tension `T5`
