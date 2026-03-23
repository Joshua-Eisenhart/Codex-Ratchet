# SOURCE DEPENDENCY MAP

- batch id:
  - `BATCH_A2MID_prove_foundation_witness_boundaries__v1`
- extraction mode:
  - `A2_MID_REFINEMENT_PASS`
- output status:
  - `PROPOSAL_ONLY / NONCANON / CONTRADICTION-PRESERVING`

## Parent dependency

- primary parent batch:
  - `BATCH_sims_prove_foundation_proof_family__v1`
- parent artifacts used:
  - `MANIFEST.json`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`

## Comparison anchors

- `BATCH_A2MID_mega_diagnostic_strip_seams__v1`
  - used to preserve the deterministic proof boundary against the preceding stochastic diagnostic strip
- `BATCH_A2MID_sims_residual_coverage_split__v1`
  - used to keep local evidence, top-level visibility, and residual-lane completion as separate layers
- `BATCH_sims_hygiene_residue_artifacts__v1`
  - used only as the next residual boundary so proof-family completion is not retold as total sims-side closure

## Non-dependencies preserved as boundaries

- no raw `core_docs` reread was needed
- no active `A2-1` surface was consulted or mutated
- no runtime execution or new result generation was performed
