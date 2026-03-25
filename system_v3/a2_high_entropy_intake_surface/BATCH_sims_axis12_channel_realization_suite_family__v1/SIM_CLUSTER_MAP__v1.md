# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_axis12_channel_realization_suite_family__v1`
Extraction mode: `SIM_AXIS12_CHANNEL_REALIZATION_SUITE_PASS`

## Cluster A
- cluster label:
  - core source pair
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_channel_realization_suite.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_channel_realization_suite.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one runner
  - one paired result
  - one local SIM_ID
- tension anchor:
  - the local suite is small and fixed-parameter even though the repo-top descendant under the same runner hash is much broader

## Cluster B
- cluster label:
  - axis12 edge partition
- members:
  - `SEQ01`
  - `SEQ02`
  - `SEQ03`
  - `SEQ04`
  - `SENI`
  - `NESI`
- family role:
  - coarse axis12 structural contract carried by the runner
- executable-facing read:
  - `SEQ01/SEQ02` form the no-edge pair
  - `SEQ03/SEQ04` form the double-edge pair
- tension anchor:
  - identical edge flags do not force identical endpoint metrics within each pair

## Cluster C
- cluster label:
  - signed endpoint realization surface
- members:
  - `axis3_1_SEQ01` through `axis3_1_SEQ04`
  - `axis3_-1_SEQ01` through `axis3_-1_SEQ04`
  - `vn_entropy_mean`
  - `purity_mean`
- family role:
  - stored endpoint behavior cluster
- executable-facing read:
  - plus sign always lowers entropy and raises purity relative to minus sign
  - `SEQ02` is best on both entropy and purity under both signs
- tension anchor:
  - sign effect is globally directional, but edge flags still fail to determine full ordering

## Cluster D
- cluster label:
  - repo-top descendant and evidence seam
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_S_SIM_AXIS12_CHANNEL_REALIZATION_V4.json`
  - shared runner hash `5e6358240110019fd266675f9ff1e520c7822114a811d597b630a62aa9efd6f5`
- family role:
  - comparison-only evidence and descendant cluster
- executable-facing read:
  - repo-top admission exists for `V4`
  - the local suite SIM_ID is omitted
  - `V4` is a grid scan rather than the current fixed-parameter snapshot
- tension anchor:
  - code-hash continuity coexists with SIM_ID and surface-shape divergence

## Cluster E
- cluster label:
  - campaign continuity and residual separation
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_traj_corr_suite_family__v1/MANIFEST.json`
  - deferred next residual pair:
    - `run_axis12_seq_constraints.py`
    - `results_axis12_seq_constraints.json`
  - adjacent runner-only surfaces:
    - `run_axis12_harden_triple_v1.py`
    - `run_axis12_harden_v2_triple.py`
- family role:
  - comparison-only continuity and backlog cluster
- executable-facing read:
  - the current paired-family campaign continues
  - runner-only harden surfaces remain out of batch
  - the next paired family stays deferred
- tension anchor:
  - raw adjacency does not override residual class separation

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B shows the coarse axis12 edge partition
- Cluster C shows the signed endpoint realization ordering
- Cluster D preserves the local-suite-vs-`V4` descendant seam
- Cluster E preserves campaign continuity without collapsing runner-only and paired residual classes together
