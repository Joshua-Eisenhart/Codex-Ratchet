# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_test_det_b_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why This Parent
- `BATCH_archive_surface_deep_archive_test_det_b__v1` was the next adjacent compact archive-side sibling after the already reduced `RUN_SIGNAL_0005_bundle` and `TEST_DET_A` packets
- it had no existing controller-facing child reduction
- its value is sharply controller-facing:
  - keep executed transport and queued continuation visibly separate
  - keep summary/state finality separate from the last executed event endpoint
  - keep replay-authored transport lineage separate from both inbox residue and empty strategy-packaging residue
  - keep the staged strategy-family progression visible without promoting it into executed proof
  - keep clean packet transport separate from promotion closure and fail-closed exhaustion

## Why This Reduction Goal
- bounded goal:
  - isolate controller-usable fences for executed-versus-queued state, final-hash authority layering, transport-only replay lineage, packaging-residue nonauthority, staged family progression, and fail-closed semantic debt
- excluded for now:
  - reopening broader archive siblings beyond `TEST_DET_B`
  - treating the third strategy packet as executed history
  - treating the empty `a1_strategies 2/` directory as a real surface
  - treating zero parked packets as semantic closure
  - treating family progression as proof of completed third-step success

## Deferred Alternatives
- `BATCH_archive_surface_deep_archive_test_real_a1_001__v1`
  - next adjacent archive packet after the `TEST_DET_*` sibling pair, but weaker as the immediate next move because `TEST_DET_B` is the closer controlled comparison to `TEST_DET_A`
