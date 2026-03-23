# SOURCE DEPENDENCY MAP

- batch id: `BATCH_A2MID_axis12_harden_v2_control_rewrite__v1`
- extraction mode: `A2_MID_REFINEMENT_PASS`
- promotion status: `PROPOSAL_ONLY_NONCANON`
- raw source reread needed: `no`

## Parent Batch

- parent batch id: `BATCH_sims_axis12_harden_v2_result_orphan_triplet__v1`
- parent files used:
  - `MANIFEST.json`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`

## Comparison Anchors

- `BATCH_A2MID_axis12_harden_v1_signal_control_split__v1/A2_2_REFINED_CANDIDATES__v1.md`
- `BATCH_A2MID_axis12_harden_runner_contract_seams__v1/A2_2_REFINED_CANDIDATES__v1.md`
- `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`

## Dependency Notes

- This reduction depends on the parent batch for:
  - the bounded three-surface `v2` result-only shell
  - the base-channel continuity plus weak-row drift packet
  - the near-zero `altchan_v2` collapse packet
  - the dynamic mostly inverted `negctrl_label_v2` control packet
  - the compressed row-only schema boundary
  - the catalog-vs-evidence omission seam
- The `v1` A2-mid reduction is used only as a version-seam anchor so the successor packet keeps continuity with `v1` without being collapsed back into it.
- The runner-contract refinement is used only as a producer-side anchor so this result-only batch stays separate from the earlier runner-only strip.
- The sims evidence-boundary refinement is used only as an outer visibility anchor so catalog filename mentions are not retold as evidence-pack admission.
- No reread of raw result JSON or raw runner code was needed because the parent batch already preserved the successor contract, the control rewrite, the compressed schema limits, and the visibility seam.
