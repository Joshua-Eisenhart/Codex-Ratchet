# SOURCE DEPENDENCY MAP

- batch id: `BATCH_A2MID_ultra3_geometry_stage16_axis0_seam__v1`
- extraction mode: `A2_MID_REFINEMENT_PASS`
- promotion status: `PROPOSAL_ONLY_NONCANON`
- raw source reread needed: `no`

## Parent Batch

- parent batch id: `BATCH_sims_ultra3_full_geometry_stage16_axis0_orphan_family__v1`
- parent files used:
  - `MANIFEST.json`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`

## Comparison Anchors

- `BATCH_A2MID_axis0_traj_v2_delta_lattice__v1/A2_2_REFINED_CANDIDATES__v1.md`
- `BATCH_A2MID_sims_residual_coverage_split__v1/A2_2_REFINED_CANDIDATES__v1.md`
- `BATCH_sims_ultra_big_ax012346_orphan_family__v1/MANIFEST.json`

## Dependency Notes

- This reduction depends on the parent batch for:
  - the one-file ultra3 orphan shell
  - the geometry layer with exact sign symmetry and approximate magnitude
  - the `stage16` branch with its small Se-centered effect scale
  - the `axis0_ab` branch with its mixed absolute/delta contract
  - the ultra-strip seam against `ultra4` and the final ultra sweep
  - the deferred `ultra_big` non-merge boundary
  - the catalog-visible / evidence-omitted seam
- The axis0 trajectory-v2 A2-mid reduction is used only as a sequencing anchor so this ultra3 pass stays clearly after the axis0 orphan lane.
- The residual coverage split is used only as a class-boundary anchor so this orphan remains one bounded result-only unit rather than being overread as final sims closure.
- The `ultra_big` orphan manifest is used only as the next bounded-family anchor so adjacency does not collapse the two ultra surfaces.
- No reread of raw result JSON or raw ultra strip docs was needed because the parent batch already preserved the geometry, stage16, axis0_ab, visibility, and family-separation seams needed for this pass.
