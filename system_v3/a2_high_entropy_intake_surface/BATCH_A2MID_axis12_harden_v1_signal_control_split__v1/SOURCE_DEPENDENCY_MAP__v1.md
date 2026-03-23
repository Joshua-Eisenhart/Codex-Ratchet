# SOURCE DEPENDENCY MAP

- batch id: `BATCH_A2MID_axis12_harden_v1_signal_control_split__v1`
- extraction mode: `A2_MID_REFINEMENT_PASS`
- promotion status: `PROPOSAL_ONLY_NONCANON`
- raw source reread needed: `no`

## Parent Batch

- parent batch id: `BATCH_sims_axis12_harden_v1_result_orphan_triplet__v1`
- parent files used:
  - `MANIFEST.json`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`

## Comparison Anchors

- `BATCH_A2MID_axis12_harden_runner_contract_seams__v1/A2_2_REFINED_CANDIDATES__v1.md`
- `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`
- `BATCH_sims_axis12_harden_v2_result_orphan_triplet__v1/MANIFEST.json`

## Dependency Notes

- This reduction depends on the parent batch for:
  - the bounded three-surface `v1` result-only shell
  - the live `paramsweep_v1` signal packet
  - the near-max-mixing `altchan_v1` collapse packet
  - the observationally inert `negctrl_swap_v1` control packet
  - the catalog-vs-evidence omission seam
  - the `v2` successor deferral boundary
- The runner-contract refinement is used only as a producer-side anchor so result-only source membership does not get confused with the earlier runner-only strip.
- The sims evidence-boundary refinement is used only as an outer visibility anchor so catalog filename presence does not get retold as evidence-pack admission.
- The `v2` orphan-triplet manifest is used only as a successor boundary anchor so this pass stays inside the `v1` triplet.
- No reread of raw result JSON or runner code was needed because the parent batch already preserved the relevant signal, collapse, control, visibility, and successor-boundary structure.
