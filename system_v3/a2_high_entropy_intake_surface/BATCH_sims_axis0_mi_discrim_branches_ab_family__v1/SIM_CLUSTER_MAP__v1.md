# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_axis0_mi_discrim_branches_ab_family__v1`
Extraction mode: `SIM_AXIS0_MI_DISCRIM_BRANCHES_AB_PASS`

## Cluster A
- cluster label:
  - core source pair
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mi_discrim_branches_ab.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_mi_discrim_branches_ab.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one runner
  - one paired result
  - one local SIM_ID
- tension anchor:
  - the family is locally complete as a runner/result pair but still lacks repo-top evidence admission

## Cluster B
- cluster label:
  - compact AB branch-metric contract
- members:
  - `metrics_SEQ01`
  - `metrics_SEQ02`
  - `delta_MI_mean_SEQ02_minus_SEQ01`
  - `delta_SAgB_mean_SEQ02_minus_SEQ01`
  - `delta_negfrac_SEQ02_minus_SEQ01`
- family role:
  - internal metric cluster carried by the one stored result surface
- executable-facing read:
  - both branches keep `neg_SAgB_frac = 0.0`
  - MI becomes materially nonzero
  - `SAgB` still separates the branches
- tension anchor:
  - AB coupling revives MI without producing any negative-end-fraction event

## Cluster C
- cluster label:
  - prior non-AB control sibling
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mi_discrim_branches.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_mi_discrim_branches.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_mi_discrim_branches_family__v1/MANIFEST.json`
- family role:
  - comparison-only control cluster
- executable-facing read:
  - same branch shell and same knobs
  - no explicit AB entangler
  - MI remains at machine-zero scale
- tension anchor:
  - the AB family is a genuine contract change, not a rename

## Cluster D
- cluster label:
  - top-level visibility and campaign continuity
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - deferred next residual pair:
    - `run_axis0_mutual_info.py`
    - `results_axis0_mutual_info.json`
- family role:
  - comparison-only visibility and backlog-continuity cluster
- executable-facing read:
  - catalog lists the AB family
  - evidence pack omits the current local SIM_ID
  - next residual pair remains outside this batch
- tension anchor:
  - local evidence, catalog presence, and repo-top admission do not align

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B captures the compact MI-plus-SAgB result contract
- Cluster C preserves the exact non-AB comparison boundary
- Cluster D preserves visibility and residual campaign continuity without broadening the batch
