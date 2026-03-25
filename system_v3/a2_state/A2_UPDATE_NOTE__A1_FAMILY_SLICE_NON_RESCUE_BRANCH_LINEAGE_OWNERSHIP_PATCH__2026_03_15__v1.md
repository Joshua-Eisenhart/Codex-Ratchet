# A2_UPDATE_NOTE__A1_FAMILY_SLICE_NON_RESCUE_BRANCH_LINEAGE_OWNERSHIP_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2
Date: 2026-03-15
Role: preserve the planner-core patch that extends declared family-slice lineage discipline from rescue branches onto the main non-rescue branch set

## Scope

This note records one bounded runtime-core patch after:
- rescue lineage fields became real on emitted rescue branches
- controller audit started checking actual rescue-lineage coverage

It is a `DERIVED_A2` continuity surface for:
- non-rescue branch lineage field emission
- controller audit coverage over actual non-rescue branch lineage

It does not rewrite owner doctrine.

## Why this patch mattered

Before this patch:
- family slices could declare lineage requirements:
  - `branch_id`
  - `parent_branch_id`
  - `feedback_refs`
  - `rescue_linkage`
- rescue branches now honored that contract
- primary and alternative/non-rescue branches still did not

That left the branch family asymmetrical:
- rescue branches carried explicit lineage
- baseline / alternative / negative branches still relied mostly on implicit IDs and track strings

This was weaker than the family model in:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_TARGET_FAMILY_MODEL__v1.md`

## What changed

### Planner

Live planner file:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`

Family-slice branch lineage is now emitted on non-rescue `SIM_SPEC` branches too.

This now covers:
- baseline SIM branches
- prerequisite atomic bootstrap SIM branches
- boundary repair branches
- perturbation branches
- composition-stress branches
- adversarial negative branches
- graveyard-first extra adversarial negative branches

Emitted non-rescue lineage fields:
- `BRANCH_ID`
- `PARENT_BRANCH_ID`
- `FEEDBACK_REFS`

Grounded shape used:
- baseline / bootstrap primary branches:
  - `BRANCH_ID = branch sim id`
  - `PARENT_BRANCH_ID = NONE`
  - `FEEDBACK_REFS = [required evidence token]`
- non-rescue alternatives:
  - `BRANCH_ID = branch sim id`
  - `PARENT_BRANCH_ID = primary baseline sim id`
  - `FEEDBACK_REFS = [required evidence token]`
- graveyard-first extra negative branches:
  - `BRANCH_ID = extra negative sim id`
  - `PARENT_BRANCH_ID = main adversarial negative branch id`
  - `FEEDBACK_REFS = [required evidence token]`

Planner self-audit now also exposes:
- `branch_lineage_fields_used`

That field is derived from actual emitted non-rescue branch items.

### Controller audit

Audit file:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

New behavior:
- non-rescue branch lineage now has its own actual-branch check
- audit inspects emitted non-rescue `SIM_SPEC` items
- it no longer treats non-rescue lineage as satisfied only because self-audit repeated the family-slice declaration

New check:
- `AUTORATCHET_FAMILY_SLICE_BRANCH_LINEAGE_VISIBLE`

This check now requires:
- expected non-rescue lineage fields are declared
- at least one non-rescue branch is actually visible
- every visible non-rescue branch carries the declared non-rescue lineage fields

Rescue lineage remains a separate check:
- `AUTORATCHET_FAMILY_SLICE_RESCUE_LINEAGE_VISIBLE`

## Focused regressions

Planner/runtime:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`

Added/updated expectations:
- planner self-audit exposes:
  - `branch_lineage_fields_used`
- baseline branches now expose:
  - `BRANCH_ID`
  - `PARENT_BRANCH_ID`
  - `FEEDBACK_REFS`
- non-rescue alternative branches expose the same lineage set

Controller audit:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`

Updated:
- the passing family-slice audit fixture now includes one actual non-rescue baseline branch carrying the declared lineage fields
- the rescue-lineage failure fixture also includes a valid non-rescue branch so the rescue-lineage failure remains isolated to the rescue seam
- the new branch-lineage check is asserted explicitly

## Verification

Focused runtime/controller tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- result: `Ran 44 tests ... OK`

Focused local spec-object test:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`
- result: `Ran 4 tests ... OK`

## Current judgment

This is a real planner/runtime-core improvement.

What is better now:
- lineage discipline is no longer rescue-only
- the main family branch set now carries explicit lineage fields too
- controller audit now checks actual non-rescue branch lineage coverage

What is still not done:
- lineage is still represented through emitted strategy item fields, not a separate first-class branch object store
- primary/alternative/negative branch parentage is deterministic and conservative, not yet derived from a richer family-local branch graph object

## Next best seam

Stay in the planner/runtime core.

Most likely next move:
1. inspect whether any remaining branch-shape rules still live as planner-global defaults rather than explicit family-slice structure
2. especially check whether alternative-branch parentage or branch grouping should become a declared family-slice object instead of deterministic local defaults
