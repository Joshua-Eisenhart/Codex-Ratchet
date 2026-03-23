# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_sim_suite_v2_successor_bundle__v1`
Extraction mode: `SIM_SUITE_V2_SUCCESSOR_BUNDLE_PASS`

## Cluster A
- cluster label:
  - successor bundle spine
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_sim_suite_v2_full_axes.py`
- family role:
  - one current successor bundle that emits seven descendant surfaces
- executable-facing read:
  - one current runner hash
  - one local evidence pack
  - seven result writes from `main()`
- tension anchor:
  - repo-top evidence attribution does not use this current runner hash for any emitted descendant

## Cluster B
- cluster label:
  - dedicated-runner-attributed descendants
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json`
- family role:
  - descendants emitted by the bundle but evidenced under dedicated current runner hashes
- executable-facing read:
  - result files belong to this bundle’s emission set
- evidence-facing read:
  - Topology4, Axis4, and Axis0 currently point to dedicated current scripts outside the bundle
- tension anchor:
  - emitted-here does not mean evidenced-here

## Cluster C
- cluster label:
  - cross-bundle and foreign-hash descendants
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V3.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_NEGCTRL_AXIS0_NOENT_V1.json`
- family role:
  - descendants whose repo-top evidence points to the prior bundle hash, the mega hash, an all-zero hash, or a cross-family leading-space hash
- executable-facing read:
  - all four are emitted here
- evidence-facing read:
  - none points back to the current successor bundle hash
- tension anchor:
  - provenance is strongest where it is least intuitively local to the bundle

## Cluster D
- cluster label:
  - predecessor comparison seam
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_sim_suite_v1.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V2.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json`
- family role:
  - bounded predecessor anchors for version and producer-path comparison
- executable-facing read:
  - `sim_suite_v1` remains a separate earlier bundle
- theory-facing read:
  - Stage16 and Negctrl preserve value-level continuity while Axis0 shifts contract materially from V4 to V5
- tension anchor:
  - successor status does not uniformly imply new payloads or cleaner provenance

## Cross-Cluster Read
- `run_sim_suite_v2_full_axes.py` is a coherent executable bundle but not a coherent current evidence producer
- provenance breaks into four modes:
  - dedicated current runner attribution
  - prior-bundle attribution
  - mega-script attribution
  - malformed or foreign attribution
- the strongest batch-level read is “successor emitter with externalized provenance,” not “current canonical producer”
