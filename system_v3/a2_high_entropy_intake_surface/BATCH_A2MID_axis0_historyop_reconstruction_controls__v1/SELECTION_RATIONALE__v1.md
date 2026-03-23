# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION RATIONALE
Batch: `BATCH_A2MID_axis0_historyop_reconstruction_controls__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Why this parent batch
- `BATCH_sims_axis0_historyop_rec_suite_v1_family__v1` is the first clean residual runner/result pair identified by the residual closure audit.
- it is already strongly bounded:
  - one runner
  - one paired result
  - four internal reconstruction cases
- it exposes a clean contradiction set without requiring raw reread:
  - local evidence emission without repo-top admission
  - reconstruction error drift without MI drift
  - surviving sequence signal without negativity
  - stronger stored extrema on `SEQ03` than the writer’s compact `SEQ02-SEQ01` summary suggests

## Why this reduction now
- the previous batch preserved the residual lane structure and said residual work must proceed pair-by-pair.
- this family is the first concrete paired-family restart inside that lane.
- compressing it now keeps the first residual pair reusable without broadening into the next pair.

## Why this is smaller than the parent
- the parent includes full result-shape details, raw parameter listings, and deferred-next-pair continuity.
- this A2-mid pass keeps only the reusable packets:
  - paired-family shell
  - four-case reconstruction cluster
  - local-only evidence status
  - reconstruction-control vs MI split
  - sequence signal without negativity
  - `SEQ03` anti-summary rule

## Deferred alternatives
- deferred:
  - `BATCH_sims_axis0_mi_discrim_branches_family__v1`
  - reason:
    - it is the next residual pair, but this turn stays bounded to the first pair only
- deferred:
  - a multi-pair axis0 omnibus
  - reason:
    - would erase the pair-by-pair residual campaign boundary preserved by the closure batch
- deferred:
  - raw sims reread
  - reason:
    - unnecessary because the parent batch already isolates the needed seams cleanly

## Raw reread decision
- raw source reread needed:
  - `false`
- rationale:
  - the parent family batch plus nearby A2-mid sims anchors are sufficient for this second-pass reduction
