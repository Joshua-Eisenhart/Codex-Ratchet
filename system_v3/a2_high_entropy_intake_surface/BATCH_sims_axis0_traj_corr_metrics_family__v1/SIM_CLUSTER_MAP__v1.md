# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_axis0_traj_corr_metrics_family__v1`
Extraction mode: `SIM_AXIS0_TRAJ_CORR_METRICS_PASS`

## Cluster A
- cluster label:
  - core source pair
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_traj_corr_metrics.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_traj_corr_metrics.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one runner
  - one paired result
  - one local SIM_ID
- tension anchor:
  - one family stores two init regimes with materially different trajectory-negativity behavior

## Cluster B
- cluster label:
  - dual-init branch contract
- members:
  - `GINIBRE`
  - `BELL`
  - `SEQ01`
  - `SEQ02`
  - `entangle_reps = 1`
  - `trials = 256`
  - `cycles = 64`
- family role:
  - executable branch contract carried by the runner
- executable-facing read:
  - same sequence pair
  - same noise and axis settings
  - different starting-state regimes
- tension anchor:
  - the branch-order effect flips sign across init modes instead of staying globally aligned

## Cluster C
- cluster label:
  - trajectory-functional result contract
- members:
  - `MI_traj_mean`
  - `MI_lambda_fit`
  - `SAgB_traj_mean`
  - `SAgB_neg_frac_traj`
  - init-specific sequence deltas
- family role:
  - stored evidence cluster for the current dual-init run
- executable-facing read:
  - Bell keeps nonzero negativity incidence across the trajectory
  - Ginibre keeps zero negativity incidence across the trajectory
  - all final `SAgB` means remain positive
- tension anchor:
  - trajectory negativity and final-state positivity coexist inside the same stored surface

## Cluster D
- cluster label:
  - top-level visibility and campaign continuity
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_sagb_entangle_seed_family__v1/MANIFEST.json`
  - deferred next residual pair:
    - `run_axis0_traj_corr_suite.py`
    - `results_axis0_traj_corr_suite.json`
- family role:
  - comparison-only visibility and backlog-continuity cluster
- executable-facing read:
  - catalog lists the family
  - evidence pack omits the local SIM_ID
  - the next residual pair remains out of batch
- tension anchor:
  - local evidence, catalog presence, and repo-top admission do not align

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B shows the same sequence pair run under two init regimes
- Cluster C shows that trajectory-level negativity behavior diverges even though final `SAgB` stays positive
- Cluster D preserves visibility and campaign continuity without broadening the batch
