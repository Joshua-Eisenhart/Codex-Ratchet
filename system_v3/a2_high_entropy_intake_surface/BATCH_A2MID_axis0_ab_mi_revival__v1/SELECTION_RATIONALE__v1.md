# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION RATIONALE
Batch: `BATCH_A2MID_axis0_ab_mi_revival__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Why this parent batch
- `BATCH_sims_axis0_mi_discrim_branches_ab_family__v1` is the next clean residual runner/result pair after the non-AB control batch.
- it is already tightly bounded:
  - one runner
  - one paired result
  - one local `SIM_ID`
  - one explicit comparison boundary to the prior non-AB sibling
- it exposes one especially reusable contradiction set:
  - the runner frames the added `CNOT` as `the fix`
  - real stored `MI` signal appears
  - negativity still does not appear
  - compared with non-AB, `MI` increases while the absolute `SAgB` gap softens

## Why this reduction now
- the previous A2-mid batch preserved the non-AB control family and explicitly deferred the AB successor.
- this turn keeps the residual campaign pairwise and source-bounded.
- it also preserves the non-AB comparison boundary without projecting the AB signal backward.

## Why this is smaller than the parent
- the parent includes full runner/result shape, detailed prior-family comparison, and next-pair continuity.
- this A2-mid pass keeps only the reusable packets:
  - AB pair shell
  - CNOT-dependent MI revival
  - local-only evidence status
  - MI signal without negativity
  - MI gain with `SAgB` attenuation
  - non-AB control boundary

## Deferred alternatives
- deferred:
  - `BATCH_sims_axis0_mutual_info_family__v1`
  - reason:
    - it is the next residual pair, but it must stay outside this batch
- deferred:
  - one merged non-AB plus AB discriminator batch
  - reason:
    - would erase the control-versus-successor boundary preserved by both parent batches
- deferred:
  - raw sims reread
  - reason:
    - unnecessary because the parent batch already isolates the needed seams

## Raw reread decision
- raw source reread needed:
  - `false`
- rationale:
  - the parent family batch plus nearby A2-mid sims anchors are sufficient for this second-pass reduction
