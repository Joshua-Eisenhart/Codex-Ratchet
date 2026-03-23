# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION RATIONALE
Batch: `BATCH_A2MID_axis0_nonab_sagb_vs_mi__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Why this parent batch
- `BATCH_sims_axis0_mi_discrim_branches_family__v1` is the next clean residual runner/result pair after the historyop family.
- it is already tightly bounded:
  - one runner
  - one paired result
  - one local `SIM_ID`
  - one adjacent `_ab` sibling held comparison-only
- it exposes one especially reusable contradiction:
  - the filename and writer posture say `MI discriminator`
  - the stored non-AB `MI` layer is effectively machine-zero
  - the actual stored split is in `SAgB`

## Why this reduction now
- the previous A2-mid batch preserved the first residual pair and explicitly deferred this pair.
- this turn keeps the residual campaign pairwise and source-bounded.
- it also preserves the next-family boundary to the `_ab` sibling instead of flattening both files into one story.

## Why this is smaller than the parent
- the parent includes full runner/result shape, sibling comparison details, and backlog continuity.
- this A2-mid pass keeps only the reusable packets:
  - pair shell
  - MI-name versus `SAgB` reality
  - local-only evidence status
  - branch split without negativity
  - `_ab` sibling boundary with revived MI
  - compact-result anti-overread

## Deferred alternatives
- deferred:
  - `BATCH_sims_axis0_mi_discrim_branches_ab_family__v1`
  - reason:
    - it is the next residual pair, but it must stay comparison-only in this batch
- deferred:
  - one merged non-AB plus AB discriminator batch
  - reason:
    - would erase the executable-contract boundary preserved by the parent batch
- deferred:
  - raw sims reread
  - reason:
    - unnecessary because the parent batch already isolates the needed seams

## Raw reread decision
- raw source reread needed:
  - `false`
- rationale:
  - the parent family batch plus nearby A2-mid sims anchors are sufficient for this second-pass reduction
