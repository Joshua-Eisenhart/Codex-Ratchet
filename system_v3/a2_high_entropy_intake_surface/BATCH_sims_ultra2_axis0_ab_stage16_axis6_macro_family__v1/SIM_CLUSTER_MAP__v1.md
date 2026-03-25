# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_ultra2_axis0_ab_stage16_axis6_macro_family__v1`
Extraction mode: `SIM_ULTRA2_MACRO_BUNDLE_PASS`

## Cluster A
- cluster label:
  - ultra2 macro shell
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra2_axis0_ab_stage16_axis6.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra2_axis0_ab_stage16_axis6.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one runner
  - one paired result
  - three bundled subfamilies
- tension anchor:
  - local macro existence is stronger than its current repo-top evidence admission

## Cluster B
- cluster label:
  - bundled Stage16 branch
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra2_axis0_ab_stage16_axis6.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra2_axis0_ab_stage16_axis6.json`
- family role:
  - internal Stage16 delta strip inside the macro shell
- executable-facing read:
  - `48` keys
  - strongest cells are Se-focused
- tension anchor:
  - the Stage16 branch is only one part of the macro result, not the whole family

## Cluster C
- cluster label:
  - bundled Axis0 AB branch
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra2_axis0_ab_stage16_axis6.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra2_axis0_ab_stage16_axis6.json`
- family role:
  - internal Axis0 AB delta strip inside the macro shell
- executable-facing read:
  - `16` keys
  - all stored values are delta records
- tension anchor:
  - small Axis0 deltas coexist with the bundled Stage16 and Axis12 branches without separate file boundaries

## Cluster D
- cluster label:
  - bundled Axis12 branch
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra2_axis0_ab_stage16_axis6.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra2_axis0_ab_stage16_axis6.json`
- family role:
  - internal constraint-count strip inside the macro shell
- executable-facing read:
  - `8` counts
  - hidden `SEQ03` / `SEQ04` participation beyond the stored `seqs` field
- tension anchor:
  - the `seqs` field is not exhaustive for this branch

## Cluster E
- cluster label:
  - ultra4 next-family expansion
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra4_full_stack.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra4_full_stack.json`
- family role:
  - next raw-order macro family boundary
- executable-facing read:
  - adds berry flux
  - expands `seqs` to `4`
  - expands `axis0_ab` to `128` keys
- tension anchor:
  - same macro direction does not imply the same bounded family

## Cross-Cluster Read
- Clusters B, C, and D are internal branches of one in-batch macro family
- Cluster E begins the next family expansion in raw folder order
- the batch should be read as one composite shell with three bundled subfamilies rather than as one narrow sim
