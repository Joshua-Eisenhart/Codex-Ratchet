# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_axis0_historyop_reconstruction_controls__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## 1) Parent Batch
- parent batch:
  - `BATCH_sims_axis0_historyop_rec_suite_v1_family__v1`
- parent artifacts used:
  - `SOURCE_MAP__v1.md`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`
- parent role in this reduction:
  - provides the first clean residual paired family after closure
  - isolates the four-case reconstruction cluster
  - preserves the main evidence contradiction, the error-vs-MI split, and the anti-summary `SEQ03` seam

## 2) Comparison Anchors
- comparison anchor:
  - `BATCH_A2MID_sims_residual_coverage_split__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the residual-lane handoff and the pair-by-pair restart posture
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the role-separated catalog / evidence / source-class framing used here for local evidence vs repo-top omission
- comparison anchor:
  - `BATCH_A2MID_sims_runner_pairing_hygiene__v1/A2_2_REFINED_CANDIDATES__v1.md`
  - role:
    - supplies the runner/result-pair interface pattern and a reusable anti-flattening sequence-effect anchor

## 3) Candidate Dependency Map
### RC1) `AXIS0_HISTORYOP_PAIRED_FAMILY_RULE`
- parent dependencies:
  - cluster `A`
  - distillate `D1`
  - candidate summaries:
    - `C1`
    - `C2`
- comparison anchor dependencies:
  - `BATCH_A2MID_sims_runner_pairing_hygiene__v1:RC1`
  - `BATCH_A2MID_sims_residual_coverage_split__v1:RC3`

### RC2) `FOUR_RECONSTRUCTION_CASE_CLUSTER_RULE`
- parent dependencies:
  - cluster `B`
  - distillate `D2`
  - candidate summary `C3`

### RC3) `LOCAL_HISTORYOP_EVIDENCE_WITHOUT_REPOTOP_ADMISSION_RULE`
- parent dependencies:
  - cluster `C`
  - distillate `D4`
  - candidate summary `C3`
  - tension `T1`
- comparison anchor dependencies:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`
  - `BATCH_A2MID_sims_residual_coverage_split__v1:RC5`

### RC4) `RECONSTRUCTION_ERROR_VS_MI_INVARIANCE_RULE`
- parent dependencies:
  - cluster `B`
  - distillates:
    - `D3`
    - `D6`
  - candidate summary `C4`
  - tension `T2`

### RC5) `SEQUENCE_SIGNAL_WITHOUT_NEGATIVITY_RULE`
- parent dependencies:
  - cluster `B`
  - distillates:
    - `D5`
    - `D6`
  - tensions:
    - `T3`
    - `T4`
- comparison anchor dependencies:
  - `BATCH_A2MID_sims_runner_pairing_hygiene__v1:RC6`

### RC6) `SEQ03_EXTREMUM_OVER_WRITER_SUMMARY_RULE`
- parent dependencies:
  - cluster `A`
  - distillate `D6`
  - candidate summary `C5`
  - tension `T5`

## 4) Quarantine Dependency Map
### Q1) `LOCAL_EVIDENCE_PLUS_CATALOG_AS_REPOTOP_ADMISSION`
- parent dependencies:
  - distillate `D4`
  - tension `T1`

### Q2) `RECONSTRUCTION_ERROR_AS_MI_DRIFT`
- parent dependencies:
  - distillate `D3`
  - candidate summary `C4`
  - tension `T2`

### Q3) `NO_NEGATIVITY_AS_NO_SEQUENCE_SIGNAL`
- parent dependencies:
  - distillate `D5`
  - tension `T3`

### Q4) `EXACT_RECONSTRUCTION_AS_SIGNAL_ERASURE`
- parent dependencies:
  - distillate `D6`
  - tension `T4`

### Q5) `WRITER_SEQ02_SEQ01_SUMMARY_AS_COMPLETE_FAMILY_STORY`
- parent dependencies:
  - distillate `D6`
  - candidate summary `C5`
  - tension `T5`
