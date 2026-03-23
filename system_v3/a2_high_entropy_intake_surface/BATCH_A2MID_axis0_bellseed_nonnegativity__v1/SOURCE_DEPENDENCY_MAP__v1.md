# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_axis0_bellseed_nonnegativity__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## 1) Parent Batch
- parent batch:
  - `BATCH_sims_axis0_sagb_entangle_seed_family__v1`
- parent artifacts used:
  - `SOURCE_MAP__v1.md`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`
- parent role in this reduction:
  - provides the bounded Bell-seed entangle pair shell
  - isolates randomized Bell scramble versus deterministic stored output
  - preserves entangling setup with zero stored negativity, tiny positive-space branch discrimination, the contrast with prior search-failure nonnegativity, and the local evidence versus repo-top omission split

## 2) Comparison Anchors
- comparison anchor:
  - `BATCH_A2MID_axis0_negsagb_search_failure__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the adjacent zero-negativity family whose outcome matches this batch while preserving a different failure mode
- comparison anchor:
  - `BATCH_A2MID_axis0_ab_mi_revival__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the nearby signal-without-negativity caution style reused for positive-space branch discrimination
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the local evidence versus repo-top admission boundary reused here

## 3) Candidate Dependency Map
### RC1) `AXIS0_BELLSEED_ENTANGLE_PAIR_RULE`
- parent dependencies:
  - cluster `A`
  - distillate `D1`
  - candidate summaries:
    - `C1`
    - `C2`

### RC2) `RANDOMIZED_BELLSCRAMBLE_WITH_DETERMINISTIC_OUTPUT_RULE`
- parent dependencies:
  - cluster `B`
  - distillates:
    - `D2`
    - `D6`
  - candidate summary `C5`
  - tension `T1`

### RC3) `ENTANGLING_SETUP_WITH_ZERO_NEGATIVITY_RULE`
- parent dependencies:
  - clusters:
    - `B`
    - `C`
  - distillates:
    - `D3`
    - `D6`
  - candidate summary `C4`
  - tension `T2`

### RC4) `POSITIVE_SPACE_BRANCH_DISCRIMINATION_RULE`
- parent dependencies:
  - cluster `C`
  - distillate `D3`
  - candidate summary `C3`
  - tension `T3`
- comparison anchor dependencies:
  - `BATCH_A2MID_axis0_ab_mi_revival__v1:RC4`

### RC5) `FIXED_CONTRACT_NONNEGATIVITY_VS_SEARCH_FAILURE_RULE`
- parent dependencies:
  - clusters:
    - `D`
    - `E`
  - distillates:
    - `D5`
    - `D6`
  - candidate summary `C3`
  - tension `T4`
- comparison anchor dependencies:
  - `BATCH_A2MID_axis0_negsagb_search_failure__v1:RC2`

### RC6) `LOCAL_BELLSEED_EVIDENCE_WITHOUT_REPOTOP_ADMISSION_RULE`
- parent dependencies:
  - cluster `E`
  - distillate `D4`
  - tension `T5`
- comparison anchor dependencies:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`

## 4) Quarantine Dependency Map
### Q1) `RANDOM_BELL_SCRAMBLE_AS_MEANINGFUL_TRIAL_VARIANCE`
- parent dependencies:
  - distillates:
    - `D2`
    - `D6`
  - candidate summary `C5`
  - tension `T1`

### Q2) `BELL_SEED_PLUS_CNOT_AS_NEGATIVITY_PROOF`
- parent dependencies:
  - distillates:
    - `D3`
    - `D6`
  - candidate summary `C4`
  - tension `T2`

### Q3) `TINY_BRANCH_DELTAS_AS_NEGATIVITY_SUCCESS`
- parent dependencies:
  - distillate `D3`
  - candidate summary `C3`
  - tension `T3`

### Q4) `ZERO_NEGATIVITY_CONVERGENCE_AS_SAME_FAILURE_MODE`
- parent dependencies:
  - distillates:
    - `D5`
    - `D6`
  - tension `T4`

### Q5) `LOCAL_EVIDENCE_AS_REPOTOP_ADMISSION`
- parent dependencies:
  - distillate `D4`
  - tension `T5`
