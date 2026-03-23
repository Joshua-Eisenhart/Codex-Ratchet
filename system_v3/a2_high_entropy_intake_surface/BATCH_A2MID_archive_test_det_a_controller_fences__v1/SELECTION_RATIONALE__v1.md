# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_test_det_a_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why This Parent
- `BATCH_archive_surface_deep_archive_test_det_a__v1` was the next smaller coherent archive-side revisit packet after the already reduced `RUN_SIGNAL_0005_bundle` bundle
- it had no existing controller-facing child reduction
- its value is sharply controller-facing:
  - keep executed transport and queued continuation visibly separate
  - keep summary/state finality separate from the last executed event endpoint
  - keep replay-authored transport lineage separate from inbox delivery
  - keep clean packet transport separate from promotion closure
  - keep operator exhaustion and schema-fail stopping together with the preserved next-step proposal

## Why This Reduction Goal
- bounded goal:
  - isolate controller-usable fences for executed-versus-queued state, final-hash authority layering, transport-only replay lineage, semantic-debt visibility, and fail-closed exhaustion handling
- excluded for now:
  - reopening adjacent `TEST_DET_B` or `TEST_REAL_A1_*` runs
  - treating the third strategy packet as executed history
  - treating zero parked packets as semantic closure
  - treating the empty inbox as no A1 lineage
  - treating exhaustion as silent truncation

## Deferred Alternatives
- `BATCH_archive_surface_deep_archive_test_det_b__v1`
  - closely related sibling, but still weaker as the immediate next packet because `TEST_DET_A` is the cleaner bounded anchor already named in the controller docs
