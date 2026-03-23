# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_axis0_mutual_info_family__v1`
Extraction mode: `SIM_AXIS0_MUTUAL_INFO_PASS`

## Cluster A
- cluster label:
  - core source pair
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mutual_info.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_mutual_info.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one runner
  - one paired result
  - one local SIM_ID
- tension anchor:
  - the family is locally complete and even escapes its own kill gate, but still lacks repo-top evidence admission

## Cluster B
- cluster label:
  - compact baseline metric contract
- members:
  - `SAB_mean`
  - `SA_mean`
  - `SB_mean`
  - `MI_mean`
  - `MI_min`
  - `MI_max`
  - `SAgB_mean`
  - `SAgB_min`
  - `SAgB_max`
  - `neg_SAgB_frac`
- family role:
  - internal metric cluster carried by the one stored result surface
- executable-facing read:
  - no branch decomposition
  - no terrain decomposition
  - one compact negativity summary across all `512` trials
- tension anchor:
  - the stored negative-entropy tail is real, but only at a one-in-512 scale

## Cluster C
- cluster label:
  - adjacent negativity-stress next family
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_negsagb_stress.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_negsagb_stress.json`
- family role:
  - comparison-only next-family cluster for boundary setting
- executable-facing read:
  - large sweep over thousands of parameter records
  - best stored negativity score remains zero
- tension anchor:
  - the larger stress search does not outperform the current baseline on stored negativity appearance

## Cluster D
- cluster label:
  - top-level visibility and campaign continuity
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_mi_discrim_branches_ab_family__v1/MANIFEST.json`
- family role:
  - comparison-only visibility and campaign-continuity cluster
- executable-facing read:
  - catalog lists the family
  - evidence pack omits the local SIM_ID and kill token
  - prior residual batch points here as the next pair
- tension anchor:
  - local evidence, kill-gate logic, catalog presence, and repo-top admission do not align

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B captures the compact one-shot MI/entropy baseline contract
- Cluster C preserves the exact boundary against the search-style stress family
- Cluster D preserves visibility and residual campaign continuity without broadening the batch
