# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION RATIONALE
Batch: `BATCH_A2MID_axis0_traj_bell_ginibre_asymmetry__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Why this parent batch
- `BATCH_sims_axis0_traj_corr_metrics_family__v1` is the next residual paired family after the Bell-seed entangle batch.
- it is already tightly bounded:
  - one runner
  - one paired result
  - one local `SIM_ID`
  - one shared branch pair under two init regimes
- it exposes a reusable contradiction set:
  - Bell stores nonzero trajectory negativity while Ginibre stays strictly nonnegative
  - Bell begins at negative conditional entropy yet ends with positive final `S(A|B)` in both branches
  - small sequence-order deltas flip sign across init modes
  - Bell carries higher trajectory `MI` while Ginibre carries larger positive trajectory `S(A|B)`
  - the family is locally evidenced and catalog-visible but still absent from repo-top evidence

## Why this reduction now
- the previous A2-mid Bell-seed batch explicitly deferred this pair.
- this turn keeps the residual campaign pairwise and source-bounded.
- it also preserves Bell-vs-Ginibre trajectory asymmetry without collapsing trajectory negativity into final-state semantics or one global sequence-order story.

## Why this is smaller than the parent
- the parent includes runner setup detail, dual-init metric tables, visibility context, and residual-campaign continuity.
- this A2-mid pass keeps only the reusable packets:
  - dual-init pair shell
  - Bell-versus-Ginibre trajectory-negativity split
  - trajectory negativity with positive final state
  - init-qualified sequence direction
  - MI-versus-trajectory-`SAgB` decoupling
  - local-only evidence status

## Deferred alternatives
- deferred:
  - `BATCH_sims_axis0_traj_corr_suite_family__v1`
  - reason:
    - it is the next residual pair, but it must stay outside this bounded metrics pass
- deferred:
  - one merged trajectory omnibus batch
  - reason:
    - would erase the metrics-versus-suite boundary and the init-qualified distinctions preserved by the parent batch
- deferred:
  - raw sims reread
  - reason:
    - unnecessary because the parent family batch already isolates the needed seams

## Raw reread decision
- raw source reread needed:
  - `false`
- rationale:
  - the parent trajectory-metrics batch plus nearby A2-mid sims anchors are sufficient for this second-pass reduction
