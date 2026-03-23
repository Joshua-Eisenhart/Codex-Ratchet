# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_test_det_b_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved Tensions
- preserve the tension that summary counts three completed steps while the event ledger and canonical state preserve only two executed steps
- preserve the tension that summary/state sidecar bind to `3ce0407f...` while the last executed event ends on `232c1595...`
- preserve the tension that replay-authored A1 strategy lineage survives under `zip_packets/` while both `a1_inbox/` and `a1_strategies 2/` are empty
- preserve the tension that summary and soak report zero parked packets while state keeps three `PARKED` promotion states and three unresolved blockers
- preserve the tension that the run stops on `A2_OPERATOR_SET_EXHAUSTED` under `SCHEMA_FAIL` pressure while a fully formed third strategy packet remains preserved
- preserve the tension that the visible `PERTURBATION -> BASELINE -> BOUNDARY_SWEEP` family progression still leaves the third family in queued continuation state rather than executed history

## Non-Smoothing Rule
- this reduction does not flatten the parent into either:
  - a three-step completed run
  - or a clean compact run with no packaging residue or promotion debt
- the usable controller read is narrower:
  - keep executed history and queued continuation distinct
  - keep final-snapshot and event-endpoint layers distinct
  - keep transport lineage, packaging residue, family progression, and fail-closed debt explicit
