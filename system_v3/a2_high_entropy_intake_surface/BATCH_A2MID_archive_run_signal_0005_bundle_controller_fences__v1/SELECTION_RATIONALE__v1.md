# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_run_signal_0005_bundle_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why This Parent
- `BATCH_archive_surface_deep_archive_run_signal_0005_bundle__v1` was the richest unresolved archive-side revisit packet on the intake surface at selection time
- it had no existing controller-facing child reduction
- its value is sharply controller-facing:
  - keep historical export-bundle richness visible without treating it as live runtime authority
  - keep sixty-pass alignment separate from semantic promotion closure
  - keep replay determinism separate from replay-final authority
  - keep three-way closure divergence explicit
  - keep packet-lane mismatch and audit-null seams fail-closed

## Why This Reduction Goal
- bounded goal:
  - isolate controller-usable fences for archive-only export-kit scope, promotion-debt visibility, replay-vs-final-hash noncollapse, closure divergence, and fail-closed lineage/audit-null handling
- excluded for now:
  - reopening the whole deep-archive revisit cluster at once
  - treating clean counters as semantic closure
  - treating replay determinism as authority
  - treating naming continuity as byte or lineage continuity
  - treating archive richness as permission to promote current runtime claims

## Deferred Alternatives
- `BATCH_archive_surface_deep_archive_test_det_a__v1`
  - smaller and coherent, but weaker than the bundle as a first archive-side controller packet because it preserves less cross-family retained structure
