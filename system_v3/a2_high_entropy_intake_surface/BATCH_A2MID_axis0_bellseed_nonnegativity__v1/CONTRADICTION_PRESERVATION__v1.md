# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_A2MID_axis0_bellseed_nonnegativity__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Preserved contradiction set
### C1) Randomized scramble versus deterministic output
- preserved contradiction:
  - each trial begins from a randomized Bell-seed scramble
  - stored branch ranges collapse to floating-point-noise scale
- why preserved:
  - randomized initialization and meaningful stored variance remain different claims

### C2) Entangling setup versus zero stored negativity
- preserved contradiction:
  - the family uses Bell seeds, weak noise, and repeated `CNOT` coupling
  - both branches still store zero negativity and positive `S(A|B)` minima
- why preserved:
  - entangling setup does not automatically prove negative conditional entropy in storage

### C3) Tiny branch differences versus negativity success
- preserved contradiction:
  - small branch deltas survive between `SEQ01` and `SEQ02`
  - `delta_negfrac_SEQ02_minus_SEQ01 = 0.0`
- why preserved:
  - branch discrimination and negativity success remain different claims

### C4) Shared zero-negativity outcome versus different failure type
- preserved contradiction:
  - the current fixed Bell-seed family stores zero negativity
  - the prior stress family also stores zero negativity after a broad search
- why preserved:
  - same outcome does not erase the difference between fixed-contract nonnegativity and search failure

### C5) Local evidence versus repo-top omission
- preserved contradiction:
  - the family is catalog-visible and locally evidenced
  - the repo-held top-level evidence pack omits the local `SIM_ID`
- why preserved:
  - local evidence and repo-top admission remain separate layers

## Quarantine markers
- quarantine marker:
  - `RANDOM_BELL_SCRAMBLE_AS_MEANINGFUL_TRIAL_VARIANCE`
- quarantine marker:
  - `BELL_SEED_PLUS_CNOT_AS_NEGATIVITY_PROOF`
- quarantine marker:
  - `TINY_BRANCH_DELTAS_AS_NEGATIVITY_SUCCESS`
- quarantine marker:
  - `ZERO_NEGATIVITY_CONVERGENCE_AS_SAME_FAILURE_MODE`
- quarantine marker:
  - `LOCAL_EVIDENCE_AS_REPOTOP_ADMISSION`
