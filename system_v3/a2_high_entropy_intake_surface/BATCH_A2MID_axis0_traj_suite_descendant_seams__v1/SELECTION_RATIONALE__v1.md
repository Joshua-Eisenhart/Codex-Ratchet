# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION RATIONALE
Batch: `BATCH_A2MID_axis0_traj_suite_descendant_seams__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Why this parent batch
- `BATCH_sims_axis0_traj_corr_suite_family__v1` is the next residual paired family after the trajectory-metrics batch.
- it is already tightly bounded:
  - one runner
  - one paired result
  - one local `SIM_ID`
  - one 32-case signed directional lattice
- it exposes a reusable contradiction set:
  - the local suite SIM_ID is omitted from repo-top evidence while `V4` and `V5` descendants are admitted under the same code hash
  - the runner stores a full 32-case lattice but emits only `SEQ01`-relative deltas in its evidence block
  - `SEQ04` flips from suppressed Bell behavior in `FWD` to the strongest Bell anomaly in `REV`
  - Bell keeps trajectory negativity across the suite while Ginibre remains at zero
  - sign reversal is close to symmetric but not exact

## Why this reduction now
- the previous A2-mid trajectory-metrics batch explicitly deferred this suite.
- this turn keeps the residual campaign pairwise and source-bounded.
- it also preserves the descendant seam and lattice-compression seam without collapsing the local suite into its admitted descendants or into one flattened Bell story.

## Why this is smaller than the parent
- the parent includes the full 32-case table, descendant references, evidence-emission mechanics, and residual-campaign continuity.
- this A2-mid pass keeps only the reusable packets:
  - suite pair shell
  - local-suite versus `V4/V5` descendant admission split
  - delta-only evidence versus full lattice
  - `SEQ04` direction-flip anomaly
  - Bell/Ginibre suite negativity field split
  - near-sign-symmetry with nonzero residuals

## Deferred alternatives
- deferred:
  - `BATCH_sims_axis12_channel_realization_suite_family__v1`
  - reason:
    - it is the next residual pair, but it must stay outside this bounded axis0 suite pass
- deferred:
  - one merged axis0 trajectory omnibus batch
  - reason:
    - would erase the metrics-versus-suite boundary and the local-suite-versus-descendant seam preserved by the parent batch
- deferred:
  - raw sims reread
  - reason:
    - unnecessary because the parent family batch already isolates the needed seams

## Raw reread decision
- raw source reread needed:
  - `false`
- rationale:
  - the parent trajectory-suite batch plus nearby A2-mid sims anchors are sufficient for this second-pass reduction
