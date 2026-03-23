# SOURCE DEPENDENCY MAP

- batch id: `BATCH_A2MID_axis0_bookkeep_slice_anchor__v1`
- extraction mode: `A2_MID_REFINEMENT_PASS`
- promotion status: `PROPOSAL_ONLY_NONCANON`
- raw source reread needed: `no`

## Parent Batch

- parent batch id: `BATCH_sims_axis0_boundary_bookkeep_v1_orphan_slice__v1`
- parent files used:
  - `MANIFEST.json`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`

## Comparison Anchors

- `BATCH_sims_leading_space_runner_result_family__v1/MANIFEST.json`
- `BATCH_sims_axis0_traj_corr_suite_family__v1/MANIFEST.json`
- `BATCH_A2MID_sims_residual_coverage_split__v1/A2_2_REFINED_CANDIDATES__v1.md`

## Dependency Notes

- This reduction depends on the parent batch for:
  - the one-file orphan slice shell
  - the exact overlap with the already-batched boundary/bookkeep sweep family
  - the local enrichment beyond the matching sweep slice
  - the BELL-vs-GINIBRE bookkeeping contrast at zero stored negativity
  - the trajectory-orphan non-merge boundary
  - the catalog-only visibility seam
- The leading-space runner/result family manifest is used only as the original sweep-family anchor for `results_axis0_boundary_bookkeep_sweep_v2.json`.
- The axis0 trajectory-correlation suite manifest is used only as a separation anchor so the adjacent `traj_corr_suite_v2` orphan does not get pulled into this bookkeeping slice.
- The residual coverage split reduction is used only as a class-boundary anchor so this orphan remains one bounded result-only unit rather than getting flattened into broad residual coverage claims.
- No reread of raw result JSON or runner code was needed because the parent batch already preserved the exact sweep overlap, the extra local fields, the visibility seam, and the separation basis against the trajectory orphan.
