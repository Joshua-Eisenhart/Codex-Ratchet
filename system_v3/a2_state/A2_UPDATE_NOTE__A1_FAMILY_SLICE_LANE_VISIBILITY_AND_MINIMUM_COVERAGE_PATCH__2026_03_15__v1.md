# A2_UPDATE_NOTE__A1_FAMILY_SLICE_LANE_VISIBILITY_AND_MINIMUM_COVERAGE_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2
Date: 2026-03-15
Role: preserve the bounded runtime-core patch that makes family-slice lane minimums and branch requirements visible in planner self-audit and cycle audit, and closes the missing-lane-minimum contract gap in the live family-slice validators

## Scope

This note captures one runtime-core patch in the active A1 family-slice path.

It does not rewrite owner doctrine.
It records a `DERIVED_A2` view of:
- the live model/runtime validation change
- the new planner self-audit visibility
- the new cycle-audit visibility checks
- the focused regressions that lock this seam

## Why this patch mattered

The family-slice contract already carried:
- `lane_minimums{}`
- `primary_branch_requirement`
- `alternative_branch_requirement`
- `negative_branch_requirement`
- `rescue_branch_requirement`

But the live planner/controller path was still not surfacing those fields.
That left a real doctrinal blind spot:
- the contract could declare branch-shape expectations
- the runtime could ignore them silently
- the controller audit had no visible branch-lane accounting to inspect

## What changed

### 1) Live family-slice validators now require lane-minimum coverage

The live Pydantic model in:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a2_to_a1_family_slice_models.py`

now rejects a family slice whose `lane_minimums` do not cover every `required_lanes` entry.

The runtime semantic validator in:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`

now rejects the same gap in the non-Pydantic path.

This closes one more split-contract seam between the shape the family slice claims and the shape the live planner accepts.

### 2) Planner self-audit now exposes family branch-shape metadata

The live planner in:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`

now emits:
- `family_slice_lane_minimums`
- `family_slice_branch_requirements`
- `lane_branch_counts`
- `lane_branch_sim_ids`

Lane branch counts are derived from emitted `SIM_SPEC` branches by live family:
- `STEELMAN` from `BASELINE`
- `BOUNDARY_REPAIR` from `BOUNDARY_SWEEP`
- `ALT_FORMALISM` from `PERTURBATION` and `COMPOSITION_STRESS`
- `ADVERSARIAL_NEG` from `ADVERSARIAL_NEG`
- `RESCUER` from any branch carrying `RESCUE_FROM`

This does **not** yet hard-fail the strategy when visible counts are below the declared minima.
It makes the live branch shape visible first, which was the missing precondition for a harder gate.

### 3) Cycle audit now checks that this branch-shape metadata is visible

The controller audit in:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

now checks:
- `AUTORATCHET_FAMILY_SLICE_LANE_MINIMUMS_VISIBLE`
- `AUTORATCHET_FAMILY_SLICE_BRANCH_REQUIREMENTS_VISIBLE`

These checks currently require:
- family-slice lane minima to be visible in strategy self-audit
- lane branch counts to be present for those lanes
- family branch-requirement strings to be surfaced verbatim

This is a visibility patch, not the final doctrinal completion gate.

## Focused regressions

Planner/runtime tests:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`

Added/updated:
- family-slice semantics now fail when a required lane is missing from `lane_minimums`
- family-slice self-audit now exposes lane minima, branch requirements, and lane branch counts

Cycle-audit tests:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`

Added:
- family-slice audit passes when visible lane minima / branch requirements are present and coherent

Local spec-object stack:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`

Still passes after the lane-minimum coverage rule was added to the live Pydantic model.

## Verification

Focused runtime/controller tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- result: `Ran 40 tests ... OK`

Focused local spec-object test:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`
- result: `Ran 4 tests ... OK`

## Current judgment

This is a real system-core improvement.

What is better now:
- the family slice cannot silently omit lane-minimum coverage and still pass the live validators
- the planner now exposes branch-shape expectations and visible lane counts
- the controller audit can now inspect that shape directly instead of reconstructing it indirectly

What is still not done:
- lane minima are not yet enforced as a hard strategy-satisfaction gate
- `RESCUER` presence is still debate-mode / graveyard-state sensitive
- the next deeper seam is deciding which branch-shape minima can be hard-enforced per mode without overclaiming doctrine

## Next best seam

Stay in the runtime core.

Most likely next move:
1. decide which lane-minimum obligations are truly hard per debate mode
2. especially clarify whether `RESCUER` is required in every cycle or only once rescue-start conditions are live
3. then convert the new visibility layer into a bounded satisfaction gate instead of leaving it as metadata only
