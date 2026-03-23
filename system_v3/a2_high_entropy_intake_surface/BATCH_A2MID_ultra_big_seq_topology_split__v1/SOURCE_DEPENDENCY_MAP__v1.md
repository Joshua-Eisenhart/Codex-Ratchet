# SOURCE DEPENDENCY MAP

- batch id: `BATCH_A2MID_ultra_big_seq_topology_split__v1`
- extraction mode: `A2_MID_REFINEMENT_PASS`
- promotion status: `PROPOSAL_ONLY_NONCANON`
- raw source reread needed: `no`

## Parent Batch

- parent batch id: `BATCH_sims_ultra_big_ax012346_orphan_family__v1`
- parent files used:
  - `MANIFEST.json`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`

## Comparison Anchors

- `BATCH_A2MID_ultra3_geometry_stage16_axis0_seam__v1/A2_2_REFINED_CANDIDATES__v1.md`
- `BATCH_A2MID_sims_residual_coverage_split__v1/A2_2_REFINED_CANDIDATES__v1.md`
- `BATCH_sims_mega_sims_diagnostic_strip__v1/MANIFEST.json`

## Dependency Notes

- This reduction depends on the parent batch for:
  - the one-file ultra-big orphan shell
  - the compact two-sequence axis0 trajectory summary contract
  - the Bell-dominant sequence split
  - the near-inert ent-repeat seam
  - the adaptive-vs-fixed and EC-vs-EO topology4 branch split
  - the non-merge boundary against ultra3
  - the result-only-strip exhaustion handoff into diagnostics
- The ultra3 A2-mid seam reduction is used only as a family-separation anchor so the current orphan does not collapse back into the earlier ultra3 shell.
- The residual coverage split is used only as a class-boundary anchor so the end of result-only orphan work is not overstated as full sims closure.
- The mega diagnostic-strip manifest is used only as the next-lane anchor so the handoff out of result-only work stays explicit.
- No reread of raw result JSON or runner code was needed because the parent batch already preserved the trajectory/topology structure, the ent-repeat seam, the non-merge rule, and the residual-class handoff.
