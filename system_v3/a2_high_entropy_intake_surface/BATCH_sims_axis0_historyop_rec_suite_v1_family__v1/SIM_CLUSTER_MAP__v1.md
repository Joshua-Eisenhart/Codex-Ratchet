# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_axis0_historyop_rec_suite_v1_family__v1`
Extraction mode: `SIM_AXIS0_HISTORYOP_REC_SUITE_PASS`

## Cluster A
- cluster label:
  - core source pair
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_historyop_rec_suite_v1.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_historyop_rec_suite_v1.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one runner
  - one paired result
  - four internal reconstruction cases
- tension anchor:
  - the family is locally complete as a runner/result pair but still lacks repo-top evidence-pack admission

## Cluster B
- cluster label:
  - exact-vs-lossy reconstruction case split
- members:
  - `S_SIM_AXIS0_HISTORYOP_REC_ID_V1`
  - `S_SIM_AXIS0_HISTORYOP_REC_MARG_V1`
  - `S_SIM_AXIS0_HISTORYOP_REC_MIX_V1`
  - `S_SIM_AXIS0_HISTORYOP_REC_SCR_V1`
- family role:
  - internal case cluster carried inside the one stored result surface
- executable-facing read:
  - all four cases share the same:
    - terrain sequences
    - trial and cycle counts
    - axis3 sign split
    - init-mode split
  - only reconstruction policy changes across the case cluster
- tension anchor:
  - MI trajectory summaries stay fixed while reconstruction error rises sharply across the lossy cases

## Cluster C
- cluster label:
  - top-level visibility anchors
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- family role:
  - comparison-only visibility and admission cluster
- executable-facing read:
  - the catalog lists the runner and result family
  - the evidence pack does not list any of the four local SIM_IDs
- tension anchor:
  - catalog presence and repo-top evidence admission diverge

## Cluster D
- cluster label:
  - residual campaign continuity
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
  - deferred next residual pair:
    - `run_axis0_mi_discrim_branches.py`
    - `results_axis0_mi_discrim_branches.json`
- family role:
  - boundary-check cluster for the residual backlog campaign
- executable-facing read:
  - the closure batch explains why this pair is being processed now
  - the next residual pair stays out of this batch
- tension anchor:
  - residual prioritization should proceed pair-by-pair rather than collapsing multiple leftover families into one batch

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B explains the internal structure of the result surface
- Cluster C separates catalog visibility from top-level evidence visibility
- Cluster D preserves backlog continuity without broadening the batch boundary
