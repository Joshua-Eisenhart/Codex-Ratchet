# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_A2MID_axis0_historyop_reconstruction_controls__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Preserved contradiction set
### C1) Local evidence versus repo-top omission
- preserved contradiction:
  - the runner emits explicit local evidence blocks
  - the repo-held top-level evidence pack omits all four local `SIM_ID`s
- why preserved:
  - this is the family’s main evidence-status seam

### C2) Reconstruction control versus signal layer
- preserved contradiction:
  - reconstruction error changes strongly across the four cases
  - stored trajectory `MI` means remain invariant
- why preserved:
  - it blocks a false one-metric story

### C3) Sequence signal versus negativity absence
- preserved contradiction:
  - sequence-order `MI` signal survives in every case
  - `NEG_SAgB_end_frac` stays zero
- why preserved:
  - order sensitivity here does not depend on stored negativity events

### C4) Exact reconstruction versus signal persistence
- preserved contradiction:
  - `REC_ID` removes stored reconstruction error
  - `REC_ID` still carries the strongest stored `SEQ02-SEQ01` `dMI_traj_mean`
- why preserved:
  - exact rec quality is not the same as no underlying axis0 discriminator

### C5) Compact writer summary versus stronger stored extrema
- preserved contradiction:
  - the writer foregrounds `SEQ02-SEQ01`
  - the strongest stored extrema localize on `SEQ03`
- why preserved:
  - emitted summary lines are useful but not exhaustive

## Quarantine markers
- quarantine marker:
  - `LOCAL_EVIDENCE_PLUS_CATALOG_AS_REPOTOP_ADMISSION`
- quarantine marker:
  - `RECONSTRUCTION_ERROR_AS_MI_DRIFT`
- quarantine marker:
  - `NO_NEGATIVITY_AS_NO_SEQUENCE_SIGNAL`
- quarantine marker:
  - `EXACT_RECONSTRUCTION_AS_SIGNAL_ERASURE`
- quarantine marker:
  - `WRITER_SEQ02_SEQ01_SUMMARY_AS_COMPLETE_FAMILY_STORY`
