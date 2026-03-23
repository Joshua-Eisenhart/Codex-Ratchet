# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_axis0_boundary_bookkeep_v1_orphan_slice__v1`
Extraction mode: `SIM_AXIS0_BOUNDARY_BOOKKEEP_V1_ORPHAN_SLICE_PASS`

## Cluster A
- cluster label:
  - core orphan slice
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_boundary_bookkeep_v1.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one compact result-only slice
  - no runner or sibling result admitted as source members here
- tension anchor:
  - source membership is one orphan surface even though the slice is semantically anchored to an already-batched sweep family

## Cluster B
- cluster label:
  - sign1 REC1 bookkeeping slice
- members:
  - `BELL_SEQ01`
  - `BELL_SEQ02`
  - `GINIBRE_SEQ01`
  - `GINIBRE_SEQ02`
  - `SEQ01`
  - `SEQ02`
- family role:
  - local payload lattice
- executable-facing read:
  - one sign
  - two sequences
  - two init classes
- tension anchor:
  - BELL shows much larger bookkeeping displacement than GINIBRE while all stored negativity remains zero

## Cluster C
- cluster label:
  - sweep-family overlap
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_boundary_bookkeep_sweep_v2.json`
  - `sign1_BELL_REC1`
  - `sign1_GINIBRE_REC1`
- family role:
  - comparison-only family anchor
- executable-facing read:
  - current orphan matches the sweep family on overlapping mean metrics
  - current orphan stores extra extrema and zero-negativity fields not present in the sweep slice
- tension anchor:
  - the orphan is both derivative of the sweep family and locally enriched relative to the matching slice

## Cluster D
- cluster label:
  - separate axis0 trajectory orphan
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_traj_corr_suite_v2.json`
  - `128` trajectory entries
  - `32` baseline prefixes
  - `96` delta entries
- family role:
  - comparison-only separation anchor
- executable-facing read:
  - broader four-sequence trajectory lattice
  - different metric contract
- tension anchor:
  - catalog adjacency does not make it part of the current boundary/bookkeeping slice

## Cluster E
- cluster label:
  - catalog-only visibility
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_leading_space_runner_result_family__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_traj_corr_suite_family__v1/MANIFEST.json`
- family role:
  - comparison-only visibility and continuity cluster
- executable-facing read:
  - both current and deferred axis0 orphans are catalog-listed
  - neither is admitted in the top-level evidence pack
- tension anchor:
  - filename visibility coexists with evidence-pack omission

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B carries the compact bookkeeping slice itself
- Cluster C shows the exact sweep-family overlap that anchors the orphan
- Cluster D preserves the separation from the deferred trajectory-correlation orphan
- Cluster E preserves catalog-only visibility and residual campaign continuity
