# A2_2_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / CANDIDATE REDUCTIONS
Batch: `BATCH_work_surface_autowiggle_lane_blockage__v1`
Extraction mode: `DIAGNOSTIC_BLOCKAGE_PASS`

## Candidate 1: `AUTOWIGGLE_SIM_SPEC_ONLY_BLOCKAGE_PACKET`
- candidate type:
  - failure-class packet
- compressed read:
  - autowiggle can emit lots of simulation-family churn while never instantiating the canonical ascent ladder
- promotion caution:
  - preserve the T1-failure vs missing-ladder dual reading

## Candidate 2: `AUTOWIGGLE_RAW_EXTRACT_DRIFT_PACKET`
- candidate type:
  - contradiction packet
- compressed read:
  - the raw state extract is useful precisely because it is messy, count-drifting, and still convergent on zero canon
- promotion caution:
  - later reduction should keep the mismatched counts visible

## Candidate 3: `FAIL_CLOSED_A1_LANE_REQUEST_SHELL`
- candidate type:
  - packaging/process subset
- compressed read:
  - strict external lane request packs can demand exact per-role JSON outputs with deterministic read order and a ZIP-only response surface
- promotion caution:
  - verify active-path relevance before promoting the shell pattern

## Candidate 4: `FOUR_ROLE_COMPENSATION_HARNESS`
- candidate type:
  - role-split exploration subset
- compressed read:
  - the four-role split is a concrete prototype for externalized A1 diversity and selector reconciliation
- promotion caution:
  - keep sandbox memos and downstream selector output sharply separated

## Candidate 5: `OFFLOAD_VS_INTERNAL_REPAIR_TENSION`
- candidate type:
  - strategy tension packet
- compressed read:
  - this batch preserves the unresolved choice between:
    - repairing autowiggle’s internal emission path
    - compensating with external role-lane packaging
- promotion caution:
  - later A2-mid work should not collapse these into one story
