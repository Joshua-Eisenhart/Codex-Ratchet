# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_axis0_negsagb_search_failure__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## 1) Parent Batch
- parent batch:
  - `BATCH_sims_axis0_negsagb_stress_family__v1`
- parent artifacts used:
  - `SOURCE_MAP__v1.md`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`
- parent role in this reduction:
  - provides the bounded axis0 negativity-stress pair shell
  - isolates the full-grid zero-score exhaustion seam
  - preserves the best-plus-sample retention limit, the local evidence versus repo-top omission split, and the smaller-baseline-over-larger-stress inversion

## 2) Comparison Anchors
- comparison anchor:
  - `BATCH_A2MID_axis0_mutualinfo_killgate_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the directly adjacent smaller-baseline packet that outranks this larger stress sweep on stored negativity
- comparison anchor:
  - `BATCH_A2MID_axis0_ab_mi_revival__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the nearby metric-without-negativity caution style reused for the micro-delta anti-overread packet
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the local evidence versus repo-top admission boundary reused here

## 3) Candidate Dependency Map
### RC1) `AXIS0_NEGSAGB_STRESS_PAIR_RULE`
- parent dependencies:
  - cluster `A`
  - distillate `D1`
  - candidate summaries:
    - `C1`
    - `C2`

### RC2) `FULL_GRID_ZERO_SCORE_EXHAUSTION_RULE`
- parent dependencies:
  - cluster `B`
  - distillate `D2`
  - candidate summary `C3`
  - tension `T1`

### RC3) `BEST_PLUS_SAMPLE_RETENTION_RULE`
- parent dependencies:
  - clusters:
    - `B`
    - `C`
  - distillates:
    - `D2`
    - `D3`
  - candidate summary `C3`
  - tension `T3`

### RC4) `LOCAL_STRESS_EVIDENCE_WITHOUT_REPOTOP_ADMISSION_RULE`
- parent dependencies:
  - cluster `E`
  - distillate `D4`
  - tension `T5`
- comparison anchor dependencies:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`

### RC5) `BASELINE_OUTPERFORMS_STRESS_ON_NEGATIVITY_RULE`
- parent dependencies:
  - clusters:
    - `D`
    - `E`
  - distillates:
    - `D4`
    - `D6`
  - candidate summary `C5`
  - tension `T2`
- comparison anchor dependencies:
  - `BATCH_A2MID_axis0_mutualinfo_killgate_boundary__v1:RC5`

### RC6) `MICRO_DELTAS_DO_NOT_REDEEM_ZERO_SCORE_RULE`
- parent dependencies:
  - clusters:
    - `B`
    - `C`
  - distillate `D6`
  - candidate summary `C4`
  - tension `T4`
- comparison anchor dependencies:
  - `BATCH_A2MID_axis0_ab_mi_revival__v1:RC4`

## 4) Quarantine Dependency Map
### Q1) `SEARCH_BREADTH_AS_SEARCH_SUCCESS`
- parent dependencies:
  - distillate `D2`
  - candidate summary `C4`
  - tension `T1`

### Q2) `BEST_PLUS_SAMPLE_AS_FULL_SEARCH_TRACE`
- parent dependencies:
  - distillate `D3`
  - tension `T3`

### Q3) `LOCAL_EVIDENCE_AS_REPOTOP_ADMISSION`
- parent dependencies:
  - distillate `D4`
  - tension `T5`

### Q4) `LARGER_STRESS_SWEEP_AS_AUTOMATIC_BASELINE_SUPERSESSOR`
- parent dependencies:
  - distillate `D6`
  - candidate summary `C5`
  - tension `T2`

### Q5) `MICRO_BRANCH_DELTAS_AS_COMPENSATION_FOR_ZERO_NEGATIVITY`
- parent dependencies:
  - distillate `D6`
  - candidate summary `C4`
  - tension `T4`
