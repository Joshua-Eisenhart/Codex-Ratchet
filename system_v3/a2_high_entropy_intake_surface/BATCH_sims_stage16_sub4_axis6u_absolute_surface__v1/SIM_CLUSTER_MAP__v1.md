# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_stage16_sub4_axis6u_absolute_surface__v1`
Extraction mode: `SIM_STAGE16_SUB4_AXIS6U_ABSOLUTE_PASS`

## Cluster A
- cluster label:
  - standalone Stage16 absolute baseline surface
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_sub4_axis6u.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_stage16_sub4_axis6u.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one runner
  - one paired result
  - `16` Stage16 cells with absolute `vn_entropy_*` and `purity_*` summaries
- tension anchor:
  - local SIM_ID exists, but top-level evidence admission prefers sibling descendants instead

## Cluster B
- cluster label:
  - mixed-axis6 baseline consumer family
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_axis6_mix_control.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_stage16_axis6_mix_control.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_stage16_axis6_mix_sweep.py`
- family role:
  - comparison-only family that consumes the same Stage16 baseline
- executable-facing read:
  - control reuses one `rho0` for paired mixed-vs-uniform comparison
  - sweep expands to `MIX_A`, `MIX_B`, and `MIX_R`
- tension anchor:
  - near-identity to the control `U_*` baseline does not merge Cluster B into this batch

## Cluster C
- cluster label:
  - top-level Stage16 descendant delta surfaces
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- family role:
  - comparison-only descendant/provenance cluster
- executable-facing read:
  - same stage lattice is preserved
  - output contract is delta-only
  - V4 and V5 are byte-identical to each other
- tension anchor:
  - current local runner hash `98464a84...` is not the code hash admitted by the top-level evidence pack for these descendants

## Cluster D
- cluster label:
  - adjacent terrain-only next family
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_terrain8_sign_suite.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_terrain8_sign_suite.json`
- family role:
  - boundary-check cluster for the next raw-order batch
- executable-facing read:
  - sign-by-terrain suite
  - no Stage16 outer / inner loop split
  - no four-operator stack
- tension anchor:
  - adjacency in raw order does not justify merging a terrain-only suite into the Stage16 baseline batch

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B uses Cluster A as a baseline anchor but remains a separate mixed-axis6 family
- Cluster C shows that top-level evidence admits sibling Stage16 descendants while omitting the local Cluster A SIM_ID
- Cluster D starts the next bounded family in raw folder order
