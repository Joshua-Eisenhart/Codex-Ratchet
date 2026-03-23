# SOURCE DEPENDENCY MAP

- batch id: `BATCH_A2MID_axis0_traj_v2_delta_lattice__v1`
- extraction mode: `A2_MID_REFINEMENT_PASS`
- promotion status: `PROPOSAL_ONLY_NONCANON`
- raw source reread needed: `no`

## Parent Batch

- parent batch id: `BATCH_sims_axis0_traj_corr_suite_v2_orphan_family__v1`
- parent files used:
  - `MANIFEST.json`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`

## Comparison Anchors

- `BATCH_A2MID_axis0_bookkeep_slice_anchor__v1/A2_2_REFINED_CANDIDATES__v1.md`
- `BATCH_sims_axis0_traj_corr_suite_family__v1/MANIFEST.json`
- `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`

## Dependency Notes

- This reduction depends on the parent batch for:
  - the one-file orphan shell
  - the `SEQ01`-baseline plus `SEQ02-04` delta contract
  - the hidden `T1` / `T2` lattice axis
  - the strongest perturbation point at `T1_REV_BELL_CNOT_R1_SEQ04`
  - the separation from the earlier local trajectory suite
  - the separation from repo-top descendants `V4` and `V5`
  - the catalog-visible / evidence-omitted seam
- The prior bookkeeping orphan reduction is used only as a sequencing and non-merge anchor so this batch stays separate from the earlier axis0 bookkeeping slice.
- The earlier local trajectory suite manifest is used only as a contract-comparison anchor for the non-merge rule against the current orphan.
- The sims evidence-boundary reduction is used only as an outer visibility anchor so catalog presence is not retold as evidence admission.
- No reread of raw result JSON or runner code was needed because the parent batch already preserved the delta-storage contract, hidden lattice, no-runner-anchor rule, and family-separation seams needed for this pass.
