# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_axis0_traj_suite_descendant_seams__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## 1) Parent Batch
- parent batch:
  - `BATCH_sims_axis0_traj_corr_suite_family__v1`
- parent artifacts used:
  - `SOURCE_MAP__v1.md`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`
- parent role in this reduction:
  - provides the bounded 32-case signed directional trajectory-suite pair
  - isolates the local-suite versus admitted `V4/V5` descendant seam
  - preserves delta-only evidence compression versus full lattice storage, the `SEQ04` direction flip, Bell-versus-Ginibre suite negativity asymmetry, and near-symmetry with nonzero residuals

## 2) Comparison Anchors
- comparison anchor:
  - `BATCH_A2MID_axis0_traj_bell_ginibre_asymmetry__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the immediately preceding Bell-versus-Ginibre trajectory-split packet that this suite broadens into a 32-case lattice
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the local evidence versus repo-top admission boundary reused here
- comparison anchor:
  - `BATCH_A2MID_axis0_bellseed_nonnegativity__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies a nearby direction-sensitive anomaly style and anti-collapse framing for local case behavior

## 3) Candidate Dependency Map
### RC1) `AXIS0_TRAJ_SUITE_PAIR_RULE`
- parent dependencies:
  - cluster `A`
  - distillate `D1`
  - candidate summaries:
    - `C1`
    - `C2`

### RC2) `LOCAL_SUITE_VS_V4V5_DESCENDANT_ADMISSION_RULE`
- parent dependencies:
  - cluster `D`
  - distillates:
    - `D4`
    - `D6`
  - candidate summary `C4`
  - tension `T1`
- comparison anchor dependencies:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`

### RC3) `DELTA_EVIDENCE_VS_FULL_LATTICE_RULE`
- parent dependencies:
  - clusters:
    - `A`
    - `D`
  - distillates:
    - `D2`
    - `D4`
    - `D6`
  - candidate summary `C5`
  - tension `T2`

### RC4) `SEQ04_DIRECTION_FLIP_ANOMALY_RULE`
- parent dependencies:
  - clusters:
    - `B`
    - `C`
  - distillates:
    - `D2`
    - `D3`
    - `D6`
  - candidate summary `C3`
  - tension `T3`
- comparison anchor dependencies:
  - `BATCH_A2MID_axis0_bellseed_nonnegativity__v1:RC4`

### RC5) `BELL_GINIBRE_SUITE_NEGATIVITY_FIELD_RULE`
- parent dependencies:
  - clusters:
    - `B`
    - `C`
  - distillates:
    - `D2`
    - `D3`
  - candidate summary `C3`
  - tension `T4`
- comparison anchor dependencies:
  - `BATCH_A2MID_axis0_traj_bell_ginibre_asymmetry__v1:RC2`

### RC6) `NEAR_SIGN_SYMMETRY_WITH_NONZERO_RESIDUAL_RULE`
- parent dependencies:
  - clusters:
    - `B`
    - `C`
  - distillates:
    - `D2`
    - `D6`
  - tension `T5`

## 4) Quarantine Dependency Map
### Q1) `LOCAL_SUITE_AS_REPOTOP_ADMITTED_VIA_CODE_HASH`
- parent dependencies:
  - distillates:
    - `D4`
    - `D6`
  - candidate summary `C4`
  - tension `T1`

### Q2) `DELTA_EVIDENCE_BLOCK_AS_FULL_32CASE_SURFACE`
- parent dependencies:
  - distillates:
    - `D4`
    - `D6`
  - candidate summary `C5`
  - tension `T2`

### Q3) `SEQ04_AS_DIRECTION_INVARIANT`
- parent dependencies:
  - distillates:
    - `D3`
    - `D6`
  - candidate summary `C3`
  - tension `T3`

### Q4) `BELL_AND_GINIBRE_AS_ONE_AVERAGED_NEGATIVITY_FIELD`
- parent dependencies:
  - distillates:
    - `D2`
    - `D3`
  - tension `T4`

### Q5) `EXACT_SIGN_SYMMETRY`
- parent dependencies:
  - distillates:
    - `D2`
    - `D6`
  - tension `T5`
