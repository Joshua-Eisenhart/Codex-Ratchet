# SOURCE DEPENDENCY MAP

- batch id: `BATCH_A2MID_axis12_harden_runner_contract_seams__v1`
- extraction mode: `A2_MID_REFINEMENT_PASS`
- promotion status: `PROPOSAL_ONLY_NONCANON`
- raw source reread needed: `no`

## Parent Batch

- parent batch id: `BATCH_sims_axis12_harden_runner_strip__v1`
- parent files used:
  - `MANIFEST.json`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`

## Comparison Anchors

- `BATCH_A2MID_sims_residual_coverage_split__v1/A2_2_REFINED_CANDIDATES__v1.md`
- `BATCH_A2MID_axis12_channelgrid_control_nonlinearity__v1/A2_2_REFINED_CANDIDATES__v1.md`
- `BATCH_sims_axis12_harden_v1_result_orphan_triplet__v1/MANIFEST.json`

## Dependency Notes

- This reduction depends on the parent batch for:
  - the two-runner harden strip shell
  - the six declared but deferred output surfaces
  - the repo-top omission boundary
  - the `v1` to `v2` contract delta
  - the shared `sim_evidence_pack.txt` overwrite hazard
- The residual coverage split is used only as a class-boundary anchor so runner-only work does not get flattened into direct source coverage or full residual closure.
- The final paired-family reduction is used only as the handoff anchor showing that runner-only work starts after the paired-family campaign ends.
- The `v1` orphan-triplet manifest is used only as a next-pass anchor confirming that the deferred outputs reopen later as result-only surfaces rather than being admitted here.
- No reread of raw runner scripts or result JSON was needed because the parent batch already preserved the producer-strip contract, residual-class split, and visibility seams needed for this pass.
