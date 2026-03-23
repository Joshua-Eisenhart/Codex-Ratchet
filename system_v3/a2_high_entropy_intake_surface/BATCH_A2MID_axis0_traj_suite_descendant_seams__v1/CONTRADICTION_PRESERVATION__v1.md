# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_A2MID_axis0_traj_suite_descendant_seams__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Preserved contradiction set
### C1) Local suite versus admitted descendants
- preserved contradiction:
  - the local suite emits evidence under its own SIM_ID
  - the repo-held evidence pack omits that SIM_ID but admits `V4` and `V5` descendants under the same runner hash
- why preserved:
  - code-hash continuity and SIM_ID continuity remain different claims

### C2) Full lattice versus delta-only evidence
- preserved contradiction:
  - the result surface stores a full 32-case lattice
  - the emitted evidence block compresses it to `SEQ01`-relative deltas
- why preserved:
  - local evidence emission and full result coverage remain different layers

### C3) `SEQ04` identity versus direction-sensitive behavior
- preserved contradiction:
  - `SEQ04` remains one case family within the suite
  - its Bell behavior flips from suppressed in `FWD` to strongest anomaly in `REV`
- why preserved:
  - sequence identity does not erase direction sensitivity

### C4) One suite versus two negativity fields
- preserved contradiction:
  - Bell cases keep nonzero trajectory negativity
  - Ginibre cases keep zero trajectory negativity
- why preserved:
  - one lattice does not collapse Bell and Ginibre into one averaged field

### C5) Near symmetry versus exact symmetry
- preserved contradiction:
  - sign reversal often looks close to symmetric
  - nonzero residuals remain in stored metrics
- why preserved:
  - approximate symmetry remains weaker than exact symmetry

## Quarantine markers
- quarantine marker:
  - `LOCAL_SUITE_AS_REPOTOP_ADMITTED_VIA_CODE_HASH`
- quarantine marker:
  - `DELTA_EVIDENCE_BLOCK_AS_FULL_32CASE_SURFACE`
- quarantine marker:
  - `SEQ04_AS_DIRECTION_INVARIANT`
- quarantine marker:
  - `BELL_AND_GINIBRE_AS_ONE_AVERAGED_NEGATIVITY_FIELD`
- quarantine marker:
  - `EXACT_SIGN_SYMMETRY`
