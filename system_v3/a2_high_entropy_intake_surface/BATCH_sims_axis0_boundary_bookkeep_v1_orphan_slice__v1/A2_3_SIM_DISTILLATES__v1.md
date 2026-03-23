# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_axis0_boundary_bookkeep_v1_orphan_slice__v1`
Extraction mode: `SIM_AXIS0_BOUNDARY_BOOKKEEP_V1_ORPHAN_SLICE_PASS`

## Distillate D1
- strongest source-bound read:
  - this batch correctly reopens `results_axis0_boundary_bookkeep_v1.json` as a standalone result-only orphan slice rather than merging it with the adjacent trajectory-correlation orphan
- supporting anchors:
  - current source membership
  - current separation read against `traj_corr_suite_v2`

## Distillate D2
- strongest source-bound read:
  - the current orphan is an exact overlapping-metric slice of the already-batched `results_axis0_boundary_bookkeep_sweep_v2.json` family
- supporting anchors:
  - current sweep overlap comparison

## Distillate D3
- strongest source-bound read:
  - the current surface adds extra extrema and zero-negativity fields beyond the matching sweep slice, so it is compact but not redundant
- supporting anchors:
  - current orphan fields
  - current sweep comparison

## Distillate D4
- strongest source-bound read:
  - BELL shows much larger bookkeeping displacement than GINIBRE while all stored negativity fractions remain zero
- supporting anchors:
  - current payload metrics

## Distillate D5
- evidence assumptions extracted:
  - the current orphan is catalog-visible by filename alias
  - the top-level evidence pack omits both the current orphan and the deferred `traj_corr_suite_v2` orphan
  - exact sweep-family overlap is the current orphan's best source anchor
- supporting anchors:
  - `SIM_CATALOG_v1.3.md`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - current sweep-family comparison

## Distillate D6
- failure modes extracted:
  - mistaking current orphan status for lack of family anchor
  - treating the current surface as a redundant duplicate of the sweep slice
  - merging `traj_corr_suite_v2` into this batch on catalog adjacency alone
  - reading large bookkeeping displacement as implied negativity
  - mistaking catalog presence for evidence-pack admission
- supporting anchors:
  - tension items `T1` through `T6`
