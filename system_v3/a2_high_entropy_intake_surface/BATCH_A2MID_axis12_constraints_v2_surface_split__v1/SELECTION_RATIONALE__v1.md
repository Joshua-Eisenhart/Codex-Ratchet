# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION RATIONALE
Batch: `BATCH_A2MID_axis12_constraints_v2_surface_split__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Why this parent batch
- `BATCH_sims_axis12_seq_constraints_family__v1` is the next residual paired family after the axis12 realization-suite batch.
- it is already tightly bounded:
  - one runner
  - one paired result
  - one local `SIM_ID`
  - one local full constraint surface
- it exposes a reusable contradiction set:
  - the local surface SIM_ID is omitted from repo-top evidence while `V2` is admitted under the same runner hash
  - the local surface stores four metric layers while `V2` keeps only a narrower edge subset
  - the shared code hash does not preserve the same stored `seni` behavior
  - `SEQ03` and `SEQ04` share the same axis1 profile but split on opposite axis2 failures
  - the balanced pair is retained even though the current stored counts do not separate it

## Why this reduction now
- the previous A2-mid axis12 realization batch explicitly deferred this pair.
- this turn keeps the residual campaign pairwise and source-bounded.
- it also preserves the `V2` descendant seam and the local axis2-count layer without collapsing the local full surface into the repo-top descendant.

## Why this is smaller than the parent
- the parent includes the local full metric surface, descendant comparison, pair classes, and residual-campaign continuity.
- this A2-mid pass keeps only the reusable packets:
  - pair shell
  - local-surface-versus-`V2` admission seam
  - local four-layer surface versus descendant edge subset
  - same-hash `seni` divergence
  - asymmetric-pair axis2 orientation split
  - balanced-pair non-separation limit

## Deferred alternatives
- deferred:
  - `BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1`
  - reason:
    - it is the next residual pair, but it must stay outside this bounded axis12 constraints pass
- deferred:
  - one merged axis12 omnibus batch
  - reason:
    - would erase the local-full-surface-versus-`V2` seam and the paired-family boundary preserved by the parent batch
- deferred:
  - raw sims reread
  - reason:
    - unnecessary because the parent family batch already isolates the needed seams

## Raw reread decision
- raw source reread needed:
  - `false`
- rationale:
  - the parent axis12 constraints batch plus nearby A2-mid sims anchors are sufficient for this second-pass reduction
