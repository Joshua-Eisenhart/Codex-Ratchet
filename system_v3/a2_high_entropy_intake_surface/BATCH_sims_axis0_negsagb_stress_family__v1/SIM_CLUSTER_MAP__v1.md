# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_axis0_negsagb_stress_family__v1`
Extraction mode: `SIM_AXIS0_NEGSAGB_STRESS_PASS`

## Cluster A
- cluster label:
  - core source pair
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_negsagb_stress.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_negsagb_stress.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one runner
  - one paired result
  - one local SIM_ID
- tension anchor:
  - the family executes a full search yet stores a zero best score

## Cluster B
- cluster label:
  - search-grid contract
- members:
  - axis3 sign sweep
  - cycle sweep
  - gamma / p / q sweep
  - entangler sweep
  - entangle repetition sweep
  - entangle-position sweep
- family role:
  - executable search space carried by the runner
- executable-facing read:
  - total search width `= 3456`
  - early stop threshold `>= 0.05`
  - stored run exhausts the full search
- tension anchor:
  - the large search space still fails to find any positive negativity score

## Cluster C
- cluster label:
  - compressed result surface
- members:
  - `best`
  - `records_count`
  - `records_sample`
- family role:
  - stored evidence cluster for the current search run
- executable-facing read:
  - full sweep count is preserved
  - only `1 + 10` records are retained for interpretation
- tension anchor:
  - the result surface is much smaller than the executed search space

## Cluster D
- cluster label:
  - mutual-info baseline comparison
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mutual_info.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_mutual_info.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_mutual_info_family__v1/MANIFEST.json`
- family role:
  - comparison-only baseline cluster
- executable-facing read:
  - much smaller baseline
  - one stored negative event in `512` trials
- tension anchor:
  - the smaller baseline beats the larger sweep on stored negativity appearance

## Cluster E
- cluster label:
  - top-level visibility and campaign continuity
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - deferred next residual pair:
    - `run_axis0_sagb_entangle_seed.py`
    - `results_axis0_sagb_entangle_seed.json`
- family role:
  - comparison-only visibility and backlog-continuity cluster
- executable-facing read:
  - catalog lists the family
  - evidence pack omits the local SIM_ID
  - next residual pair remains out of batch
- tension anchor:
  - local evidence, catalog presence, and repo-top admission do not align

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B shows the true search width
- Cluster C shows how heavily the stored output compresses that search
- Cluster D preserves the smaller-but-stronger negativity baseline comparison
- Cluster E preserves visibility and campaign continuity without broadening the batch
