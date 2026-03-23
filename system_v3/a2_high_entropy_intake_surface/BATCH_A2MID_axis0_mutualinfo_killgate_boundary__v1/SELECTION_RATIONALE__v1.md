# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION RATIONALE
Batch: `BATCH_A2MID_axis0_mutualinfo_killgate_boundary__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Why this parent batch
- `BATCH_sims_axis0_mutual_info_family__v1` is the next clean residual runner/result pair after the AB-coupled discriminator family.
- it is already tightly bounded:
  - one runner
  - one paired result
  - one local `SIM_ID`
  - one adjacent search-style comparison family
- it exposes a reusable contradiction set:
  - the runner includes a kill gate for zero negativity
  - the stored result escapes that gate only by a one-in-512 negative event
  - the family is catalog-visible and locally evidenced but still absent from repo-top evidence
  - the larger `negsagb_stress` sweep still stores zero best negativity

## Why this reduction now
- the previous A2-mid batch preserved the AB-discriminator successor and explicitly deferred this baseline pair.
- this turn keeps the residual campaign pairwise and source-bounded.
- it also preserves the inversion where the smaller baseline beats the larger stress sweep on stored negativity appearance.

## Why this is smaller than the parent
- the parent includes full metric summaries, kill-gate details, and stress-sweep comparison context.
- this A2-mid pass keeps only the reusable packets:
  - baseline pair shell
  - kill-gate versus stored-output escape
  - local-only evidence status
  - positive MI with tiny negativity tail
  - baseline-over-stress inversion
  - compact-baseline granularity caution

## Deferred alternatives
- deferred:
  - `BATCH_sims_axis0_negsagb_stress_family__v1`
  - reason:
    - it is the next residual pair, but it must stay comparison-only in this turn
- deferred:
  - one merged baseline-plus-stress negativity packet
  - reason:
    - would erase the bounded baseline-versus-search-family boundary preserved by the parent batch
- deferred:
  - raw sims reread
  - reason:
    - unnecessary because the parent batch already isolates the needed seams

## Raw reread decision
- raw source reread needed:
  - `false`
- rationale:
  - the parent family batch plus nearby A2-mid sims anchors are sufficient for this second-pass reduction
