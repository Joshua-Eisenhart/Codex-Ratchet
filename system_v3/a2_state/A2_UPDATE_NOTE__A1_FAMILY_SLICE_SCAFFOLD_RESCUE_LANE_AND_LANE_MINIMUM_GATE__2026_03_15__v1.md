# A2_UPDATE_NOTE__A1_FAMILY_SLICE_SCAFFOLD_RESCUE_LANE_AND_LANE_MINIMUM_GATE__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2
Date: 2026-03-15
Role: preserve the bounded runtime-core patch that makes the `RESCUER` lane real in scaffold family-slice cycles and upgrades lane minima from visibility-only into an active cycle-audit gate

## Scope

This note records one follow-on patch after the lane-visibility work.

It is a `DERIVED_A2` continuity surface for:
- the new scaffold rescue-lane emission in the live planner
- the stronger controller audit check that lane minima are not only visible but satisfied
- the focused regressions that lock the new runtime behavior

It does not rewrite owner doctrine.

## Why this patch mattered

The earlier lane patch made family lane minima and branch requirements visible, but the live planner still had a doctrinal hole:
- `RESCUER` branches were only emitted in `graveyard_recovery`
- balanced family-slice cycles still had no real rescue lane
- full family cycles therefore remained structurally incomplete even when the contract already declared `RESCUER`

Grounding from the family docs:
- full A1 family cycles should include a `RESCUER` lane
- scaffold runs may use tighter shape
- but scaffold runs still allow minimal rescue attachment, not only graveyard-linked rescue

That made a bounded fix possible without pretending every rescue branch must already be graveyard-sourced.

## What changed

### 1) Scaffold family-slice cycles now emit one real rescue branch

The live planner in:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`

now emits one bounded scaffold rescue branch when:
- a family slice is present
- no graveyard-linked rescue branch was already emitted

This scaffold rescue branch is built from family-local rescue material:
- first allowed recovery SIM family from `sim_hooks.recovery_sim_families`
- first declared `expected_failure_modes[]` entry
- first declared `graveyard_library_terms[]` entry when available

The emitted rescue branch carries explicit rescue metadata:
- `RESCUE_MODE = SCAFFOLD_ATTACHMENT`
- `RESCUE_FAILURE_MODE = <family-declared failure mode>`
- `RESCUE_LIBRARY_TERM = <family graveyard-library term>` when available

This closes the old gap where balanced/scaffold family-slice cycles had no `RESCUER` lane at all.

### 2) Rescue-lane detection now recognizes scaffold rescue markers

Planner-side lane accounting now treats a SIM branch as `RESCUER` when it carries any rescue marker, not only `RESCUE_FROM`.

That means lane accounting now sees:
- graveyard-linked rescue branches
- scaffold-attached rescue branches

The rescue-family visibility helper also now recognizes scaffold rescue branches, so the live self-audit no longer hides that lane.

### 3) Lane minima are now an active controller audit gate

The controller audit in:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

now checks:
- `AUTORATCHET_FAMILY_SLICE_LANE_MINIMUMS_SATISFIED`

This is stronger than the earlier visibility-only step.
The audit now fails when visible `lane_branch_counts` do not meet the family-slice lane minima.

Because scaffold rescue emission now exists, this gate can include `RESCUER` instead of silently exempting it.

## Focused regressions

Planner/runtime:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`

Locked behaviors:
- balanced family-slice mode now emits one scaffold rescue branch
- rescue lane metadata includes declared failure mode and graveyard-library term
- live lane counts now include `RESCUER`

Controller audit:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`

Locked behaviors:
- a coherent family-slice cycle with visible rescue lane passes the lane-minimum gate
- a family-slice cycle that still shows `RESCUER = 0` fails the new lane-minimum satisfaction check

Local spec-object stack:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`

Still passes after the runtime planner/audit change.

## Verification

Focused runtime/controller tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- result: `Ran 42 tests ... OK`

Focused local spec-object test:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`
- result: `Ran 4 tests ... OK`

## Current judgment

This is a real runtime-core improvement.

What is better now:
- full family-slice scaffold cycles no longer silently omit the rescue lane
- lane minima are now checked as live controller-grade obligations, not just displayed metadata
- rescue branch shape is still bounded and family-local rather than invented from thread memory

What is still not done:
- scaffold rescue is still a minimal attachment, not the full graveyard-linked rescue richness expected in validity-heavy runs
- the remaining branch-shape seam is whether scaffold rescue should expand beyond one bounded rescue branch when richer family-local rescue structure is declared

## Next best seam

Stay in the planner/runtime core.

Most likely next move:
1. review whether scaffold rescue should be allowed to emit more than one rescue branch from declared family-local rescue material
2. then tighten any remaining branch-shape defaults that still sit outside explicit family-slice ownership
