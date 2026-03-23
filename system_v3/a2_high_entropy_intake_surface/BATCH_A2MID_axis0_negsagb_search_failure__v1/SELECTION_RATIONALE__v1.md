# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION RATIONALE
Batch: `BATCH_A2MID_axis0_negsagb_search_failure__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Why this parent batch
- `BATCH_sims_axis0_negsagb_stress_family__v1` is the next residual paired family after the smaller mutual-information baseline batch.
- it is already tightly bounded:
  - one runner
  - one paired result
  - one local `SIM_ID`
  - one explicit smaller-baseline comparison
- it exposes a reusable contradiction set:
  - the full `3456`-record sweep exhausts and still stores `best.score = 0.0`
  - the stored surface keeps only `best` plus a `10`-record sample
  - the family is locally evidenced and catalog-visible but still absent from repo-top evidence
  - the smaller mutual-information baseline preserves stronger stored negativity evidence

## Why this reduction now
- the previous A2-mid batch preserved the baseline-over-stress inversion and explicitly deferred this larger stress family.
- this turn keeps the residual campaign pairwise and source-bounded.
- it also turns the parent batch's main warnings into reusable negative packets without smoothing the contradiction set.

## Why this is smaller than the parent
- the parent includes search-grid details, metric samples, visibility context, and backlog continuity.
- this A2-mid pass keeps only the reusable packets:
  - residual pair shell
  - full-grid zero-score exhaustion
  - best-plus-sample retention limit
  - local-only evidence status
  - smaller-baseline-over-larger-stress inversion
  - micro-delta anti-redemption caution

## Deferred alternatives
- deferred:
  - `BATCH_sims_axis0_sagb_entangle_seed_family__v1`
  - reason:
    - it is the next residual pair, but it must stay outside this bounded stress-failure pass
- deferred:
  - one merged baseline-plus-stress negativity packet
  - reason:
    - would erase the smaller-baseline-versus-larger-search-family boundary preserved by the parent batch
- deferred:
  - raw sims reread
  - reason:
    - unnecessary because the parent family batch already isolates the needed seams

## Raw reread decision
- raw source reread needed:
  - `false`
- rationale:
  - the parent stress-family batch plus nearby A2-mid sims anchors are sufficient for this second-pass reduction
