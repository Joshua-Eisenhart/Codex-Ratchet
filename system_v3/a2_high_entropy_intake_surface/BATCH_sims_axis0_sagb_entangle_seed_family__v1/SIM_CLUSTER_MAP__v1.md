# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_axis0_sagb_entangle_seed_family__v1`
Extraction mode: `SIM_AXIS0_SAGB_ENTANGLE_SEED_PASS`

## Cluster A
- cluster label:
  - core source pair
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_sagb_entangle_seed.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_sagb_entangle_seed.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one runner
  - one paired result
  - one local SIM_ID
- tension anchor:
  - the family is locally complete but still stores zero negativity in both branches

## Cluster B
- cluster label:
  - Bell-seed deterministic branch contract
- members:
  - Bell-state seed with local scramble
  - weak-noise terrain tuple
  - `2` CNOT entangle repetitions
  - `SEQ01`
  - `SEQ02`
- family role:
  - executable branch contract carried by the runner
- executable-facing read:
  - fixed Bell-seed family
  - fixed noise
  - fixed entangle count
  - no search sweep
- tension anchor:
  - random seed scrambling coexists with effectively deterministic stored branch metrics

## Cluster C
- cluster label:
  - compact branch-result contract
- members:
  - `metrics_SEQ01`
  - `metrics_SEQ02`
  - `delta_MI_mean_SEQ02_minus_SEQ01`
  - `delta_SAgB_min_SEQ02_minus_SEQ01`
  - `delta_negfrac_SEQ02_minus_SEQ01`
- family role:
  - stored evidence cluster for the current fixed run
- executable-facing read:
  - both branches keep `neg_SAgB_frac = 0.0`
  - branch deltas remain tiny but nonzero
- tension anchor:
  - the family stores discrimination without any negativity event

## Cluster D
- cluster label:
  - prior negativity-stress comparison
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_negsagb_stress.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_negsagb_stress.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_negsagb_stress_family__v1/MANIFEST.json`
- family role:
  - comparison-only sweep cluster
- executable-facing read:
  - broader search
  - same stored zero-negativity outcome in its best record
- tension anchor:
  - the fixed current family and the prior sweep both stay nonnegative in storage, but for different reasons

## Cluster E
- cluster label:
  - top-level visibility and campaign continuity
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - deferred next residual pair:
    - `run_axis0_traj_corr_metrics.py`
    - `results_axis0_traj_corr_metrics.json`
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
- Cluster B shows the fixed Bell-seed plus repeated-CNOT contract
- Cluster C shows that the stored result is nearly deterministic and still nonnegative
- Cluster D preserves the stress-family contrast without broadening the batch
- Cluster E preserves visibility and campaign continuity without broadening the batch
