# SOURCE DEPENDENCY MAP

- batch id:
  - `BATCH_A2MID_hygiene_artifact_closure_split__v1`
- extraction mode:
  - `A2_MID_REFINEMENT_PASS`
- output status:
  - `PROPOSAL_ONLY / NONCANON / CONTRADICTION-PRESERVING`

## Parent dependency

- primary parent batch:
  - `BATCH_sims_hygiene_residue_artifacts__v1`
- parent artifacts used:
  - `MANIFEST.json`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`

## Comparison anchors

- `BATCH_A2MID_prove_foundation_witness_boundaries__v1`
  - used to preserve the immediate proof-to-hygiene handoff without backdating closure into the proof family
- `BATCH_A2MID_sims_residual_coverage_split__v1`
  - used to keep residual-class closure, direct source coverage, and source-class completion as separate layers
- `BATCH_sims_axis12_topology4_channelfamily_suite_v2_orphan_surface__v1`
  - used as the later closure-correction anchor so this hygiene reduction does not falsely universalize the parent batch's completion claim

## Non-dependencies preserved as boundaries

- no raw `core_docs` reread was needed
- no active `A2-1` surface was consulted or mutated
- no runtime execution or new sim result generation was performed
