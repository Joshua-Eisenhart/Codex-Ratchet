# SOURCE DEPENDENCY MAP

- batch id: `BATCH_A2MID_axis12_channelgrid_control_nonlinearity__v1`
- extraction mode: `A2_MID_REFINEMENT_PASS`
- promotion status: `PROPOSAL_ONLY_NONCANON`
- raw source reread needed: `no`

## Parent Batch

- parent batch id: `BATCH_sims_axis12_topology4_channelgrid_family__v1`
- parent files used:
  - `MANIFEST.json`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`

## Comparison Anchors

- `BATCH_A2MID_axis12_topology4_admission_contract_split__v1/A2_2_REFINED_CANDIDATES__v1.md`
- `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`

## Dependency Notes

- This reduction depends on the parent batch for:
  - the clean local runner/result pairing
  - the explicit `n_test` vs `n_ctrl` contract
  - the stored `AD` vs `FX` nonlinearity split
  - the topology4 quadrant metric asymmetry
  - the paired-family completion boundary
- The previous topology4 seam refinement is used only as a boundary anchor so this batch does not get merged back into the neighboring terrain8 admission seam.
- The sims evidence-boundary refinement is used only as an outer admission anchor so local pairing quality does not get confused with repo-top evidence admission.
- No reread of raw sim runners or result JSON was needed because the parent batch already preserved the clean pair, sign contract, nonlinearity split, omission/admission asymmetry, and class-completion notes.
