# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_test_resume_001_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why This Parent
- `BATCH_archive_surface_deep_archive_test_resume_001__v1` was the next adjacent compact archive-side packet after the now-covered `TEST_REAL_A1_002` sibling
- it had no existing controller-facing child reduction
- its value is sharply controller-facing:
  - keep the zero-work external-handoff stop separate from any invented lower-loop execution
  - keep duplicate step-1 save requests separate from missing-step storytelling
  - keep active-runtime path leakage separate from archive-local packet authority
  - keep sequence-only header drift separate from payload progression
  - keep generic sample strategy scaffolding separate from run-specific outer hash and lexical-shell residue

## Why This Reduction Goal
- bounded goal:
  - isolate controller-usable fences for zero-work boundary handling, duplicate outbound request restraint, provenance leakage nonauthority, sequence-only packet drift, and sample-scaffold nonpromotion
- excluded for now:
  - reopening broader archive siblings beyond `TEST_RESUME_001`
  - treating two save requests as a hidden second executed step
  - treating runtime-path leakage as live authority
  - treating sequence `2` as real payload advancement
  - treating the run-specific outer hash as proof the inner strategy payload is earned

## Deferred Alternatives
- `BATCH_archive_surface_deep_archive_test_state_transition_chain_a__v1`
  - next adjacent archive packet after `TEST_RESUME_001`, but weaker as the immediate next move because `TEST_RESUME_001` closes the nearer sibling first
