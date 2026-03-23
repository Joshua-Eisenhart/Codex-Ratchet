# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_ultra_axis0_ab_axis6_sweep_family__v1`
Extraction mode: `SIM_ULTRA_AXIS0_AB_AXIS6_SWEEP_PASS`

## Cluster A
- cluster label:
  - final ultra sweep shell
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra_axis0_ab_axis6_sweep.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra_axis0_ab_axis6_sweep.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one runner
  - one paired result
  - Stage16 plus Axis0 AB sweep shell
- tension anchor:
  - final raw-order family still lacks repo-top evidence admission

## Cluster B
- cluster label:
  - stage16 sweep branch
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra_axis0_ab_axis6_sweep.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra_axis0_ab_axis6_sweep.json`
- family role:
  - bundled Stage16 sweep strip
- executable-facing read:
  - `48` keys
  - strongest cells stay Se-focused
  - effect scale is larger than the corresponding `ultra4` Stage16 branch
- tension anchor:
  - same keyset as `ultra4` does not mean same values or same surrounding family

## Cluster C
- cluster label:
  - axis0_ab mixed-record sweep branch
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra_axis0_ab_axis6_sweep.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra_axis0_ab_axis6_sweep.json`
- family role:
  - bundled Axis0 AB sweep strip
- executable-facing read:
  - `32` absolute `SEQ01` baselines
  - `96` delta records for `SEQ02` through `SEQ04`
- tension anchor:
  - absolute and delta records coexist inside one map

## Cluster D
- cluster label:
  - ultra4 full-stack comparison anchor
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra4_full_stack.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra4_full_stack.json`
- family role:
  - preceding full-stack expansion anchor
- executable-facing read:
  - same Stage16 / Axis0 keysets
  - adds geometry and Axis12 layers that the current family drops
- tension anchor:
  - current sweep is a narrowing of the ultra strip, not the same bounded family as the full stack

## Cross-Cluster Read
- Clusters B and C are internal layers of one in-batch final ultra sweep family
- Cluster D is comparison-only and explains why the current batch is narrower than `ultra4`
- no later raw-order `simpy/` family remains after Cluster A
