# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION RATIONALE
Batch: `BATCH_A2MID_axis12_edge_partition_v4_seam__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Why this parent batch
- `BATCH_sims_axis12_channel_realization_suite_family__v1` is the next residual paired family after the axis0 trajectory-suite batch.
- it is already tightly bounded:
  - one runner
  - one paired result
  - one local `SIM_ID`
  - one fixed-parameter axis12 suite
- it exposes a reusable contradiction set:
  - the local suite SIM_ID is omitted from repo-top evidence while `V4` is admitted under the same runner hash
  - the `SENI/NESI` edge partition separates sequences into two classes but does not determine full endpoint ordering
  - axis3 sign is globally directional inside this axis12-labeled family
  - the local suite is a fixed snapshot while `V4` is a broader grid scan
  - `SEQ02` is locally strongest under both signs even though it shares the no-edge class with `SEQ01`

## Why this reduction now
- the previous A2-mid axis0 suite batch explicitly deferred this pair.
- this turn keeps the residual campaign pairwise and source-bounded.
- it also preserves the `V4` descendant seam and the coarse-edge-versus-full-order split without collapsing the family into descendant, edge-only, or runner-only stories.

## Why this is smaller than the parent
- the parent includes the full endpoint table, descendant reference, local evidence seam, and residual-campaign continuity.
- this A2-mid pass keeps only the reusable packets:
  - suite pair shell
  - local-suite-versus-`V4` descendant admission seam
  - edge partition as coarse classifier
  - global sign directionality
  - fixed-snapshot versus grid-scan divergence
  - stable `SEQ02` local best

## Deferred alternatives
- deferred:
  - `BATCH_sims_axis12_seq_constraints_family__v1`
  - reason:
    - it is the next residual pair, but it must stay outside this bounded axis12 realization pass
- deferred:
  - one merged axis12 omnibus batch
  - reason:
    - would erase the local-suite-versus-descendant seam and the paired-family boundary preserved by the parent batch
- deferred:
  - raw sims reread
  - reason:
    - unnecessary because the parent family batch already isolates the needed seams

## Raw reread decision
- raw source reread needed:
  - `false`
- rationale:
  - the parent axis12 realization batch plus nearby A2-mid sims anchors are sufficient for this second-pass reduction
