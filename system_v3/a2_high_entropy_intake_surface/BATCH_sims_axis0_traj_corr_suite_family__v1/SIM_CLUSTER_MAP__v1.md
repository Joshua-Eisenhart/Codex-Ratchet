# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_axis0_traj_corr_suite_family__v1`
Extraction mode: `SIM_AXIS0_TRAJ_CORR_SUITE_PASS`

## Cluster A
- cluster label:
  - core source pair
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_traj_corr_suite.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_traj_corr_suite.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one runner
  - one paired result
  - one local SIM_ID
- tension anchor:
  - one batch contains a full 32-case lattice rather than a compact two-branch surface

## Cluster B
- cluster label:
  - suite lattice contract
- members:
  - `axis3_sign in {+1, -1}`
  - `init_mode in {GINIBRE, BELL}`
  - `direction in {FWD, REV}`
  - `SEQ01`
  - `SEQ02`
  - `SEQ03`
  - `SEQ04`
- family role:
  - executable lattice carried by the runner
- executable-facing read:
  - four sequences
  - two directions
  - two signs
  - two init modes
- tension anchor:
  - the suite is broad enough that sequence effects become direction-sensitive instead of globally ordered

## Cluster C
- cluster label:
  - Bell vs Ginibre trajectory split
- members:
  - all `BELL` cases
  - all `GINIBRE` cases
  - `MI_traj_mean`
  - `SAgB_traj_mean`
  - `SAgB_neg_frac_traj`
- family role:
  - stored trajectory-behavior cluster
- executable-facing read:
  - Bell keeps nonzero trajectory negativity throughout the suite
  - Ginibre keeps zero trajectory negativity throughout the suite
  - `REV / BELL / SEQ04` is the strongest stored anomaly
- tension anchor:
  - init regime controls whether the suite ever enters negative-conditional-entropy territory in storage

## Cluster D
- cluster label:
  - evidence compression and descendant admission
- members:
  - local evidence delta emitter in `run_axis0_traj_corr_suite.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- family role:
  - comparison-only evidence and descendant cluster
- executable-facing read:
  - local evidence stores only SEQ01-relative deltas
  - repo-top evidence admits `V4` and `V5` descendants under the same code hash
  - the local suite SIM_ID itself is omitted
- tension anchor:
  - code-hash continuity coexists with SIM_ID and output-surface divergence

## Cluster E
- cluster label:
  - campaign continuity
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_traj_corr_metrics_family__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - deferred next residual pair:
    - `run_axis12_channel_realization_suite.py`
    - `results_axis12_channel_realization_suite.json`
- family role:
  - comparison-only continuity and backlog cluster
- executable-facing read:
  - the prior metrics batch hands off into the current suite
  - the next residual pair stays out of batch
- tension anchor:
  - family continuity exists without collapsing adjacent pairs into one batch

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B shows the full sign/init/direction/sequence lattice
- Cluster C shows the persistent Bell-vs-Ginibre split plus the `SEQ04` anomaly
- Cluster D preserves the local-evidence vs repo-top-descendant seam
- Cluster E preserves residual campaign continuity without broadening the batch
