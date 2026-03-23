# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_refinedfuel_nonsims_residual_inventory_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why This Parent
- `BATCH_refinedfuel_nonsims_residual_inventory_closure_audit__v1` was the only live unreduced non-A2MID `A2_2_CANDIDATE` parent on the intake surface at the time of selection
- its value is sharply controller-facing:
  - preserve that broad non-sims refined-fuel source coverage is complete
  - keep the lone hygiene residual from being misread as a real source gap
  - keep multi-coverage distinct from missing coverage
  - shift the queue from new broad extraction toward selective revisit routing
  - keep closure signals from inflating into authority

## Why This Reduction Goal
- bounded goal:
  - isolate controller-usable fences for coverage closure, hygiene-only residual handling, multi-coverage routing, revisit-queue priority, and anti-authority closure discipline
- excluded for now:
  - reopening same-root source-map campaigns
  - treating `.DS_Store` as a new family
  - treating coverage closure as semantic closure
  - treating the closure audit as permission to mutate active A2 or declare canon

## Deferred Alternatives
- none at selection time:
  - this parent was the only live unreduced non-A2MID `A2_2_CANDIDATE` packet on the intake surface
