# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_terrain8_sign_suite_family__v1`
Extraction mode: `SIM_TERRAIN8_SIGN_SUITE_PASS`

## Cluster A
- cluster label:
  - terrain-only sign suite
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_terrain8_sign_suite.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_terrain8_sign_suite.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one terrain-only repeated-cycle runner
  - one paired result with eight summary metrics
- tension anchor:
  - the local SIM_ID is not repo-top admitted even though related Terrain8 language exists elsewhere

## Cluster B
- cluster label:
  - top-level Terrain8 naming/provenance seam
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_topology4_channelfamily_suite_v2.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- family role:
  - comparison-only terrain-naming anchor
- executable-facing read:
  - terrain language appears under an Axis12 / Topology4 family with a different runner hash and a `16`-cell result surface
- tension anchor:
  - shared `Terrain8` naming does not make Cluster B the same family as Cluster A

## Cluster C
- cluster label:
  - adjacent macro bundle boundary
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra2_axis0_ab_stage16_axis6.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra2_axis0_ab_stage16_axis6.json`
- family role:
  - next raw-order macro family boundary
- executable-facing read:
  - mixed `stage16`, `axis0_ab`, and `axis12` composite surface
- tension anchor:
  - adjacency in raw order does not justify merging a macro bundle into the terrain-only suite

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B shows the main evidence/provenance contradiction: Terrain8 at repo-top refers to a different family
- Cluster C marks the next bounded family in folder order
