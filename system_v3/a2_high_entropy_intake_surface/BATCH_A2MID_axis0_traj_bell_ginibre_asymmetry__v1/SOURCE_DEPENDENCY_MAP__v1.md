# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_axis0_traj_bell_ginibre_asymmetry__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## 1) Parent Batch
- parent batch:
  - `BATCH_sims_axis0_traj_corr_metrics_family__v1`
- parent artifacts used:
  - `SOURCE_MAP__v1.md`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`
- parent role in this reduction:
  - provides the bounded dual-init trajectory-correlation pair shell
  - isolates Bell-versus-Ginibre trajectory-negativity asymmetry
  - preserves trajectory negativity versus positive final-state `S(A|B)`, init-qualified sequence-order sign flips, MI-versus-trajectory-`SAgB` decoupling, and the local evidence versus repo-top omission split

## 2) Comparison Anchors
- comparison anchor:
  - `BATCH_A2MID_axis0_bellseed_nonnegativity__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the adjacent Bell-seed zero-negativity packet that this dual-init family now splits by initialization regime
- comparison anchor:
  - `BATCH_A2MID_axis0_ab_mi_revival__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the nearby MI-without-negativity caution style reused for metric anti-collapse
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the local evidence versus repo-top admission boundary reused here

## 3) Candidate Dependency Map
### RC1) `AXIS0_TRAJ_CORR_PAIR_RULE`
- parent dependencies:
  - cluster `A`
  - distillate `D1`
  - candidate summaries:
    - `C1`
    - `C2`

### RC2) `BELL_VS_GINIBRE_TRAJECTORY_NEGATIVITY_SPLIT_RULE`
- parent dependencies:
  - clusters:
    - `B`
    - `C`
  - distillates:
    - `D2`
    - `D3`
  - candidate summary `C3`
  - tension `T1`
- comparison anchor dependencies:
  - `BATCH_A2MID_axis0_bellseed_nonnegativity__v1:RC3`

### RC3) `TRAJECTORY_NEGATIVITY_WITH_POSITIVE_FINAL_STATE_RULE`
- parent dependencies:
  - cluster `C`
  - distillates:
    - `D3`
    - `D6`
  - candidate summary `C4`
  - tension `T2`

### RC4) `INIT_QUALIFIED_SEQUENCE_DIRECTION_RULE`
- parent dependencies:
  - clusters:
    - `B`
    - `C`
  - distillates:
    - `D2`
    - `D6`
  - candidate summary `C5`
  - tension `T3`

### RC5) `MI_VS_SAGB_TRAJECTORY_DECOUPLING_RULE`
- parent dependencies:
  - cluster `C`
  - distillates:
    - `D3`
    - `D6`
  - candidate summary `C3`
  - tension `T4`
- comparison anchor dependencies:
  - `BATCH_A2MID_axis0_ab_mi_revival__v1:RC5`

### RC6) `LOCAL_TRAJ_EVIDENCE_WITHOUT_REPOTOP_ADMISSION_RULE`
- parent dependencies:
  - cluster `D`
  - distillate `D4`
  - tension `T5`
- comparison anchor dependencies:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`

## 4) Quarantine Dependency Map
### Q1) `BELL_TRAJECTORY_NEGATIVITY_AS_NEGATIVE_FINAL_STATE`
- parent dependencies:
  - distillates:
    - `D3`
    - `D6`
  - candidate summary `C4`
  - tension `T2`

### Q2) `SMALL_SEQUENCE_DELTAS_AS_INIT_INDEPENDENT_DIRECTION`
- parent dependencies:
  - distillates:
    - `D2`
    - `D6`
  - candidate summary `C5`
  - tension `T3`

### Q3) `MI_AND_POSITIVE_SAGB_TRAJECTORY_MEANS_AS_CO_MOVING`
- parent dependencies:
  - distillates:
    - `D3`
    - `D6`
  - tension `T4`

### Q4) `BELL_AND_GINIBRE_AS_ONE_REGIME_STORY`
- parent dependencies:
  - distillates:
    - `D2`
    - `D3`
  - candidate summary `C3`
  - tension `T1`

### Q5) `LOCAL_EVIDENCE_AS_REPOTOP_ADMISSION`
- parent dependencies:
  - distillate `D4`
  - tension `T5`
