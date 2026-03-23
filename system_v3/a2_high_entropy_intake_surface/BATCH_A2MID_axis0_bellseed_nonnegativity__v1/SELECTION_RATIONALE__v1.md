# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION RATIONALE
Batch: `BATCH_A2MID_axis0_bellseed_nonnegativity__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Why this parent batch
- `BATCH_sims_axis0_sagb_entangle_seed_family__v1` is the next residual paired family after the prior negativity-stress batch.
- it is already tightly bounded:
  - one runner
  - one paired result
  - one local `SIM_ID`
  - one explicit prior zero-negativity comparison family
- it exposes a reusable contradiction set:
  - randomized Bell-seed scrambling collapses into near-deterministic stored branch ranges
  - Bell seeds plus weak noise plus repeated `CNOT` coupling still produce zero stored negativity in both branches
  - tiny branch deltas survive only inside positive `S(A|B)` space
  - the family matches the prior stress batch on zero negativity but not on failure type
  - the family is locally evidenced and catalog-visible but still absent from repo-top evidence

## Why this reduction now
- the previous A2-mid batch explicitly deferred this pair.
- this turn keeps the residual campaign pairwise and source-bounded.
- it also preserves the distinction between fixed-contract nonnegativity and broader search-failure nonnegativity instead of flattening both into one story.

## Why this is smaller than the parent
- the parent includes runner setup detail, explicit branch metrics, visibility context, and residual-campaign continuity.
- this A2-mid pass keeps only the reusable packets:
  - Bell-seed pair shell
  - randomized scramble versus deterministic stored output
  - entangling setup with zero stored negativity
  - tiny positive-space branch discrimination
  - fixed-contract nonnegativity versus search failure
  - local-only evidence status

## Deferred alternatives
- deferred:
  - `BATCH_sims_axis0_traj_corr_metrics_family__v1`
  - reason:
    - it is the next residual pair, but it must stay outside this bounded Bell-seed pass
- deferred:
  - one merged zero-negativity omnibus packet
  - reason:
    - would erase the distinction between fixed-contract nonnegativity and prior search failure preserved by the parent batch
- deferred:
  - raw sims reread
  - reason:
    - unnecessary because the parent family batch already isolates the needed seams

## Raw reread decision
- raw source reread needed:
  - `false`
- rationale:
  - the parent Bell-seed family batch plus nearby A2-mid sims anchors are sufficient for this second-pass reduction
