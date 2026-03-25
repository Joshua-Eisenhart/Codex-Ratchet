# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_axis0_traj_corr_suite_v2_orphan_family__v1`
Extraction mode: `SIM_AXIS0_TRAJ_CORR_SUITE_V2_ORPHAN_PASS`

## Cluster A
- cluster label:
  - core orphan family
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_traj_corr_suite_v2.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one large result-only orphan surface
  - no runner admitted as a source member
- tension anchor:
  - source membership is one orphan surface even though it clearly belongs near the earlier trajectory-correlation family

## Cluster B
- cluster label:
  - seq01 baseline lattice
- members:
  - `32` absolute base entries
  - `SEQ01`
  - `MI_traj_mean`
  - `SAgB_traj_mean`
  - `neg_SAgB_frac_traj`
- family role:
  - absolute baseline layer
- executable-facing read:
  - all base entries are `SEQ01`
  - strongest base MI sits on `T1_REV_BELL_CZ_R1_SEQ01`
- tension anchor:
  - the file stores absolutes only for one sequence while claiming a four-sequence family

## Cluster C
- cluster label:
  - seq02-04 delta lattice
- members:
  - `96` delta entries
  - `SEQ02`
  - `SEQ03`
  - `SEQ04`
  - `dMI`
  - `dLam`
  - `dNegFrac`
  - `dSAgB`
- family role:
  - relative-change layer
- executable-facing read:
  - deltas dominate the stored surface
  - strongest absolute delta response is on `T1_REV_BELL_CNOT_R1_SEQ04`
- tension anchor:
  - the file privileges relative sequence change over full absolute reporting

## Cluster D
- cluster label:
  - hidden and explicit lattice axes
- members:
  - `T1`
  - `T2`
  - `FWD`
  - `REV`
  - `BELL`
  - `GINIBRE`
  - `CNOT`
  - `CZ`
  - `R1`
  - `R2`
- family role:
  - executable lattice scaffold
- executable-facing read:
  - one axis is hidden only in key prefixes
  - direction, init, gate, and repetition are explicit in keys
- tension anchor:
  - key-encoded axes outstrip what top-level metadata admits

## Cluster E
- cluster label:
  - local family and descendant separation
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_traj_corr_suite_family__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_traj_corr_suite.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json`
- family role:
  - comparison-only family-seam cluster
- executable-facing read:
  - current orphan is neither the earlier local suite nor either repo-top compressed descendant
- tension anchor:
  - family resemblance exists without contract equivalence

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B and Cluster C show the seq01-baseline-plus-deltas contract
- Cluster D shows the hidden `T1`/`T2` axis and the wider gate/repetition lattice
- Cluster E preserves separation from both the earlier local family and the repo-top descendants
