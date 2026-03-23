# SOURCE DEPENDENCY MAP

- batch id: `BATCH_A2MID_axis12_topology4_admission_contract_split__v1`
- extraction mode: `CONTRADICTION_REPROCESS_PASS`
- promotion status: `PROPOSAL_ONLY_NONCANON`
- raw source reread needed: `no`

## Parent Batch

- parent batch id: `BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1`
- parent files used:
  - `MANIFEST.json`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`

## Comparison Anchors

- `BATCH_A2MID_axis12_constraints_v2_surface_split__v1/A2_2_REFINED_CANDIDATES__v1.md`
- `BATCH_A2MID_sims_evidence_boundary__v1/A2_2_REFINED_CANDIDATES__v1.md`

## Source Dependency Notes

- This batch depends on the parent batch for the residual seam framing between:
  - current runner local result: `results_axis12_topology4_channelfamily_suite_v2.json`
  - admitted repo-top surface: `results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`
- This batch uses the prior axis12 constraints refinement only as a boundary anchor for local-surface-vs-descendant admission seams.
- This batch uses the sims evidence-boundary refinement only as a transport/admission anchor for local-vs-top-level evidence separation.
- No `core_docs` reread was required because the parent batch already preserved the needed contract mismatch, admitted-hash linkage, sign-pattern structure, and next-family deferral boundary.
