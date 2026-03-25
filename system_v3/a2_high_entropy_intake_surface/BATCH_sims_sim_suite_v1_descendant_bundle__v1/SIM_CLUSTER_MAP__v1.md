# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_sim_suite_v1_descendant_bundle__v1`
Extraction mode: `SIM_SUITE_V1_BUNDLE_PASS`

## Cluster A
- cluster label:
  - bundle runner spine
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_sim_suite_v1.py`
- family role:
  - single executable bundle that emits ten descendants across axes 0, 3, 4, 5, 6, 12, and Stage16
- executable-facing read:
  - one `code_hash`
  - one local evidence pack
  - ten result writes from `main()`
- tension anchor:
  - bundle emission is uniform, but repo-top evidence attribution is not

## Cluster B
- cluster label:
  - descendants still aligned to current bundle hash
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS3_WEYL_HOPF_GRID_V1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS6_LR_MULTI_V1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS5_FGA_SWEEP_V1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS5_FSA_SWEEP_V1.json`
- family role:
  - descendants whose repo-top evidence still names the current `run_sim_suite_v1.py` hash
- executable-facing read:
  - direct file membership and evidence alignment are both intact
- theory-facing read:
  - this is the bundle’s cleanest continuity subset
- tension anchor:
  - clean subset continuity can be overgeneralized to the whole bundle

## Cluster C
- cluster label:
  - descendants with diverted repo-top provenance
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_SEQ_CONSTRAINTS_V2.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_CHANNEL_REALIZATION_V4.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V2.json`
- family role:
  - results emitted by the bundle but evidenced at repo-top level under other current script hashes
- executable-facing read:
  - file membership stays inside the bundle
- evidence-facing read:
  - current provenance is split toward dedicated runners or the successor bundle hash
- tension anchor:
  - source membership and top-level evidence producer path diverge

## Cluster D
- cluster label:
  - successor bundle seam
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_sim_suite_v2_full_axes.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V3.json`
- family role:
  - comparison-only successor bundle showing version drift and provenance crossover
- executable-facing read:
  - v2 emits a different result set and not the same bounded bundle membership
- evidence-facing read:
  - one repo-top V2 descendant block already points to the current `run_sim_suite_v2_full_axes.py` hash
- tension anchor:
  - successor-hash crossover exists even where current result versions differ

## Cross-Cluster Read
- this batch is one bundle family, not one uniform current producer lineage
- evidence attribution breaks into three conditions:
  - current-bundle aligned descendants
  - descendants attributed to dedicated runners
  - descendants crossing into successor-bundle hash territory
- theory-facing versus executable-facing split:
  - executable family is coherent at the bundle level
  - evidencing is coherent only in subsets
