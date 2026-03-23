# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_test_real_a1_001_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why This Parent
- `BATCH_archive_surface_deep_archive_test_real_a1_001__v1` was the next adjacent compact archive-side packet after the now-covered `TEST_DET_*` sibling pair
- it had no existing controller-facing child reduction
- its value is sharply controller-facing:
  - keep one-step packet transport separate from any invented queued continuation
  - keep `REAL_A1` naming separate from replay attribution and empty inbox lineage
  - keep summary/state finality separate from the only event endpoint without reconstructing a missing sequence ledger
  - keep clean packet counters separate from parked promotion debt
  - keep SIM kill-signal residue and snapshot pending evidence separate from final state bookkeeping

## Why This Reduction Goal
- bounded goal:
  - isolate controller-usable fences for one-step execution shape, lineage-label nonauthority, final-hash authority layering, missing-ledger nonreconstruction, parked-debt visibility, and packet/snapshot evidence outrunning final state aggregation
- excluded for now:
  - reopening broader archive siblings beyond `TEST_REAL_A1_001`
  - treating the run name as proof of real-LLM authorship
  - synthesizing a missing `sequence_state.json`
  - treating zero parked packets as semantic closure
  - treating empty state bookkeeping fields as proof that the SIM returns were harmless or fully consumed

## Deferred Alternatives
- `BATCH_archive_surface_deep_archive_test_real_a1_002__v1`
  - next adjacent archive packet after `TEST_REAL_A1_001`, but weaker as the immediate next move because `TEST_REAL_A1_001` closes the nearer sibling first
