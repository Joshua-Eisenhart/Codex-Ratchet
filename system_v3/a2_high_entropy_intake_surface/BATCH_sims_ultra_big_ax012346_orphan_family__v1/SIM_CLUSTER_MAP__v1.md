# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_ultra_big_ax012346_orphan_family__v1`
Extraction mode: `SIM_ULTRA_BIG_AX012346_ORPHAN_PASS`

## Cluster A
- cluster label:
  - core orphan family
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra_big_ax012346.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one compact result-only ultra macro surface
  - no runner admitted as a source member
- tension anchor:
  - the family is macro-structured but remains a single orphan result surface

## Cluster B
- cluster label:
  - two-sequence axis0 parameter core
- members:
  - `axis0_params`
  - `SEQ01`
  - `SEQ02`
  - `axis0_cycles`
  - `axis0_trials`
  - `entangle_reps`
  - `terrain_params`
- family role:
  - executable parameter shell for the trajectory branch
- executable-facing read:
  - only `SEQ01` and `SEQ02` are stored
  - terrain parameters are fixed at `0.01`
- tension anchor:
  - the file is called ultra-big, but its explicit sequence shell is smaller than the earlier ultra3 orphan

## Cluster C
- cluster label:
  - axis0 trajectory summary branch
- members:
  - `sign-1_ent0`
  - `sign-1_ent1`
  - `sign1_ent0`
  - `sign1_ent1`
  - `BELL`
  - `GINIBRE`
  - `MI_mean`
  - `SAgB_mean`
  - `negfrac_mean`
- family role:
  - compact trajectory summary layer
- executable-facing read:
  - Bell keeps nonzero negativity across both sequences
  - Ginibre negativity stays zero throughout
  - `SEQ02` is consistently stronger than `SEQ01` in Bell MI
- tension anchor:
  - the branch exposes sign and entanglement-repeat labels, but sequence is the stronger stored split

## Cluster D
- cluster label:
  - entanglement-repeat seam
- members:
  - `ent0`
  - `ent1`
  - machine-precision invariance
- family role:
  - runtime-expectation seam inside the trajectory branch
- executable-facing read:
  - declared `entangle_reps = 2`
  - stored metrics are nearly invariant across repeat labels
- tension anchor:
  - metadata promises a repeat axis that the stored summaries barely express

## Cluster E
- cluster label:
  - topology4 summary branch
- members:
  - `EC_AD`
  - `EC_FX`
  - `EO_AD`
  - `EO_FX`
  - `lin_err_mean`
  - `CTRL_comm_deltaH_*`
  - `TEST_nonc_deltaH_*`
- family role:
  - topology-facing summary layer
- executable-facing read:
  - adaptive families are the only nonlinear ones
  - fixed families are effectively linear
  - EC and EO keep distinct control-axis behavior
- tension anchor:
  - topology4 is not one uniform proof surface; it contains two orthogonal splits

## Cluster F
- cluster label:
  - ultra3 separation anchor
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_ultra3_full_geometry_stage16_axis0_orphan_family__v1/MANIFEST.json`
- family role:
  - comparison-only prior ultra orphan anchor
- executable-facing read:
  - current orphan trades ultra3's berry-flux/stage16 shell for topology4 summary metrics
- tension anchor:
  - both are ultra result-only orphans, but they are not the same bounded family

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B and Cluster C define the two-sequence axis0 summary contract
- Cluster D preserves the near-inert entanglement-repeat seam
- Cluster E preserves the adaptive-vs-fixed and EC-vs-EO topology splits
- Cluster F keeps the ultra3 separation explicit while closing the result-only orphan strip
