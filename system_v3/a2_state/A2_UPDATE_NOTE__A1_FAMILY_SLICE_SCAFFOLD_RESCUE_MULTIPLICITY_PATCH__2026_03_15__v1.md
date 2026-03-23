# A2_UPDATE_NOTE__A1_FAMILY_SLICE_SCAFFOLD_RESCUE_MULTIPLICITY_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2
Date: 2026-03-15
Role: preserve the bounded runtime-core patch that lets family-slice scaffold rescue expand to the declared `RESCUER.min_branches` instead of always collapsing to one scaffold rescue branch

## Scope

This note records one follow-on planner-core patch after scaffold rescue-lane emission was introduced.

It is a `DERIVED_A2` continuity surface for:
- the new scaffold rescue multiplicity rule in the live planner
- the focused regression that proves `RESCUER.min_branches` can now expand scaffold rescue count

It does not rewrite owner doctrine.

## Why this patch mattered

The prior rescue-lane patch closed the largest doctrinal gap:
- scaffold family-slice cycles now emitted a real rescue branch

But the live scaffold rescue implementation still had one remaining flattening behavior:
- it always emitted at most one scaffold rescue branch
- even when the family slice declared a larger `RESCUER.min_branches`

That meant the runtime could still under-deliver branch diversity relative to the declared family lane shape.

## What changed

The live planner in:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`

now computes scaffold rescue count from:
- declared `lane_minimums["RESCUER"].min_branches`
- minus any rescue branches already emitted

Then it emits that many scaffold rescue branches, bounded by the declared family-local rescue material:
- recovery SIM families from `sim_hooks.recovery_sim_families`
- declared `expected_failure_modes[]`
- declared `graveyard_library_terms[]`

Behavior:
- if `RESCUER.min_branches = 1`, behavior matches the earlier patch
- if `RESCUER.min_branches > 1`, scaffold rescue no longer collapses to one branch
- recovery-family selection cycles through the declared recovery family list
- failure modes and graveyard-library terms are reused deterministically when shorter than the requested rescue count

This keeps the rescue expansion bounded and still family-local.

## Focused regression

Planner/runtime:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`

Added:
- a family-slice scaffold case where `RESCUER.min_branches = 2`
- expected outcome:
  - two scaffold rescue branches are emitted
  - `lane_branch_counts["RESCUER"] = 2`
  - visible rescue SIM families expand from one to two:
    - `BOUNDARY_SWEEP`
    - `PERTURBATION`

The existing controller audit tests still pass after this change.

## Verification

Focused runtime/controller tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- result: `Ran 43 tests ... OK`

Focused local spec-object test:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`
- result: `Ran 4 tests ... OK`

## Current judgment

This is a real runtime-core improvement.

What is better now:
- scaffold rescue no longer hard-caps at one branch
- the live planner can now honor richer declared rescue-lane minima without inventing new doctrine fields
- branch diversity pressure is closer to the actual family contract

What is still not done:
- scaffold rescue multiplicity still reuses declared family-local rescue material deterministically
- it does not yet have a richer family-specified rescue-template object of its own

## Next best seam

Stay in the planner/runtime core.

Most likely next move:
1. audit whether any remaining branch-shape defaults still bypass declared family obligations
2. especially check whether scaffold rescue should ever be restricted by additional family-local rescue structure instead of only lane minima plus declared rescue materials
