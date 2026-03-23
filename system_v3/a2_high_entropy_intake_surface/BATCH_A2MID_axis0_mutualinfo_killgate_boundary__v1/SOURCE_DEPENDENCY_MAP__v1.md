# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_axis0_mutualinfo_killgate_boundary__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## 1) Parent Batch
- parent batch:
  - `BATCH_sims_axis0_mutual_info_family__v1`
- parent artifacts used:
  - `SOURCE_MAP__v1.md`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`
- parent role in this reduction:
  - provides the minimal axis0 mutual-information baseline shell
  - isolates the kill-gate versus stored-output seam
  - preserves the tiny negativity tail and the boundary against the larger `negsagb_stress` search family

## 2) Comparison Anchors
- comparison anchor:
  - `BATCH_A2MID_axis0_ab_mi_revival__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the immediately preceding residual-pair shell and the MI-without-negativity comparison packet
- comparison anchor:
  - `BATCH_A2MID_axis0_nonab_sagb_vs_mi__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies a nearby compact-result anti-overread packet and control-family boundary style
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the local evidence versus repo-top omission pattern reused here

## 3) Candidate Dependency Map
### RC1) `AXIS0_MUTUALINFO_BASELINE_PAIR_RULE`
- parent dependencies:
  - cluster `A`
  - distillate `D1`
  - candidate summaries:
    - `C1`
    - `C2`
- comparison anchor dependencies:
  - `BATCH_A2MID_axis0_ab_mi_revival__v1:RC1`

### RC2) `KILL_GATE_VS_STORED_NEGATIVITY_ESCAPE_RULE`
- parent dependencies:
  - clusters:
    - `A`
    - `B`
  - distillates:
    - `D2`
    - `D3`
  - candidate summary `C3`
  - tension `T1`

### RC3) `LOCAL_BASELINE_EVIDENCE_WITHOUT_REPOTOP_ADMISSION_RULE`
- parent dependencies:
  - cluster `D`
  - distillate `D4`
  - tension `T2`
- comparison anchor dependencies:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`

### RC4) `POSITIVE_MI_WITH_TINY_NEGATIVITY_TAIL_RULE`
- parent dependencies:
  - cluster `B`
  - distillates:
    - `D2`
    - `D6`
  - candidate summary `C4`
  - tension `T4`

### RC5) `BASELINE_OVER_STRESS_SWEEP_NEGATIVITY_INVERSION_RULE`
- parent dependencies:
  - clusters:
    - `B`
    - `C`
  - distillates:
    - `D5`
    - `D6`
  - candidate summary `C5`
  - tension `T3`

### RC6) `COMPACT_BASELINE_GRANULARITY_LIMIT_RULE`
- parent dependencies:
  - cluster `B`
  - distillate `D6`
  - tension `T5`
- comparison anchor dependencies:
  - `BATCH_A2MID_axis0_nonab_sagb_vs_mi__v1:RC6`

## 4) Quarantine Dependency Map
### Q1) `KILL_GATE_PRESENCE_AS_KILL_TRIGGER`
- parent dependencies:
  - distillate `D3`
  - tension `T1`

### Q2) `LOCAL_EVIDENCE_OR_KILL_TOKEN_AS_REPOTOP_ADMISSION`
- parent dependencies:
  - distillate `D4`
  - tension `T2`

### Q3) `POSITIVE_MI_AS_ROBUST_NEGATIVITY`
- parent dependencies:
  - distillates:
    - `D2`
    - `D6`
  - candidate summary `C4`
  - tension `T4`

### Q4) `STRESS_SWEEP_AS_AUTOMATIC_BASELINE_SUPERSESSOR`
- parent dependencies:
  - distillate `D5`
  - candidate summary `C5`
  - tension `T3`

### Q5) `COMPACT_BASELINE_SUMMARY_AS_TRIAL_LEVEL_PROOF`
- parent dependencies:
  - distillate `D6`
  - tension `T5`
