# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_test_state_transition_chain_a_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why This Parent
- `BATCH_archive_surface_deep_archive_test_state_transition_chain_a__v1` was the next adjacent compact archive-side packet after the now-covered `TEST_RESUME_001` sibling
- it had no existing controller-facing child reduction
- its value is sharply controller-facing:
  - keep the two-step executed spine separate from queued third-step residue
  - keep replay attribution separate from `needs_real_llm true`
  - keep counted-step overstatement and final-hash-fed continuation separate from executed completion
  - keep second-step schema-fail correlation separate from stronger causal inflation
  - keep mixed target-lane stall and residue-family noise separate from clean closure or a second branch

## Why This Reduction Goal
- bounded goal:
  - isolate controller-usable fences for executed-versus-queued state, lineage-label contradiction handling, count-layer restraint, schema-fail causal restraint, and stalled-target anti-closure handling
- excluded for now:
  - reopening broader archive siblings beyond `TEST_STATE_TRANSITION_CHAIN_A`
  - treating three counted steps as three executed transitions
  - collapsing replay attribution and `needs_real_llm true` into one label
  - treating the blank target `NEGATIVE_CLASS` as a proven sole cause
  - treating exact duplicate ` 3` files or runtime-path leakage as proof of a second branch

## Deferred Alternatives
- `BATCH_archive_surface_deep_archive_test_state_transition_chain_b__v1`
  - next adjacent archive packet after `TEST_STATE_TRANSITION_CHAIN_A`, but weaker as the immediate next move because `CHAIN_A` closes the nearer sibling first
