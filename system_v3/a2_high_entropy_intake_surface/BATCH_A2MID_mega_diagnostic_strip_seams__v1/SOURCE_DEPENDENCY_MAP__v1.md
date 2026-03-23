# SOURCE DEPENDENCY MAP

- batch id:
  - `BATCH_A2MID_mega_diagnostic_strip_seams__v1`
- extraction mode:
  - `A2_MID_REFINEMENT_PASS`
- output status:
  - `PROPOSAL_ONLY / NONCANON / CONTRADICTION-PRESERVING`

## Parent dependency

- primary parent batch:
  - `BATCH_sims_mega_sims_diagnostic_strip__v1`
- parent artifacts used:
  - `MANIFEST.json`
  - `SIM_CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_SIM_DISTILLATES__v1.md`
  - `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`

## Comparison anchors

- `BATCH_A2MID_ultra_big_seq_topology_split__v1`
  - used to preserve the explicit handoff out of the final result-only orphan lane and into the diagnostic strip
- `BATCH_A2MID_sims_residual_coverage_split__v1`
  - used to keep direct source membership, local evidence visibility, and residual prioritization separated
- `BATCH_sims_prove_foundation_proof_family__v1`
  - used only as the adjacent proof-family boundary so the stochastic diagnostic strip is not merged into deterministic witness logic

## Non-dependencies preserved as boundaries

- no raw `core_docs` reread was needed
- no active `A2-1` surface was consulted or mutated
- no runtime execution or result generation was performed
