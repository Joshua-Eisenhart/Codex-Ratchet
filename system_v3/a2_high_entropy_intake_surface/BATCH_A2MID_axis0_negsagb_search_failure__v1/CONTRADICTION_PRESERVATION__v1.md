# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_A2MID_axis0_negsagb_search_failure__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Preserved contradiction set
### C1) Full sweep versus zero score
- preserved contradiction:
  - the runner exhausts all `3456` configurations
  - the stored result still has `best.score = 0.0`
- why preserved:
  - completion and success remain different claims

### C2) Search execution versus compressed retention
- preserved contradiction:
  - the runner explores a full grid
  - the stored surface keeps only `best` plus a `10`-record sample
- why preserved:
  - retained output is useful but not the same as full-trace storage

### C3) Larger stress sweep versus smaller baseline
- preserved contradiction:
  - the larger stress family stores zero best negativity
  - the smaller mutual-information baseline stores a tiny nonzero negativity tail
- why preserved:
  - search breadth does not automatically dominate stored comparison evidence

### C4) Tiny branch deltas versus failed objective
- preserved contradiction:
  - the best record retains small mixed-sign deltas
  - the negativity objective still fails with zero best score and zero best-record negativity fraction
- why preserved:
  - incidental metric movement does not settle the stronger negativity claim

### C5) Local evidence versus repo-top omission
- preserved contradiction:
  - the family is catalog-visible and locally evidenced
  - the repo-held top-level evidence pack omits the local `SIM_ID`
- why preserved:
  - local evidence and repo-top admission remain separate layers

## Quarantine markers
- quarantine marker:
  - `SEARCH_BREADTH_AS_SEARCH_SUCCESS`
- quarantine marker:
  - `BEST_PLUS_SAMPLE_AS_FULL_SEARCH_TRACE`
- quarantine marker:
  - `LOCAL_EVIDENCE_AS_REPOTOP_ADMISSION`
- quarantine marker:
  - `LARGER_STRESS_SWEEP_AS_AUTOMATIC_BASELINE_SUPERSESSOR`
- quarantine marker:
  - `MICRO_BRANCH_DELTAS_AS_COMPENSATION_FOR_ZERO_NEGATIVITY`
