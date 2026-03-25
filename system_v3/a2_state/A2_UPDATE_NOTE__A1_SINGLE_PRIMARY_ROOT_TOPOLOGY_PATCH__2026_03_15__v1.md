# A2_UPDATE_NOTE__A1_SINGLE_PRIMARY_ROOT_TOPOLOGY_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2
Date: 2026-03-15
Role: preserve the planner-core patch that reduces family-slice non-rescue topology to one explicit primary root instead of many baseline roots

## Scope

This note records one bounded runtime-core patch after:
- non-rescue branch lineage became explicit
- branch parentage/grouping became visible and controller-auditable

It is a `DERIVED_A2` continuity surface for:
- the live family-slice topology correction
- the reason we chose topology correction over inventing a new family-slice parentage hint object

It does not rewrite owner doctrine.

## Why this patch mattered

Before this patch:
- family-slice runs emitted explicit non-rescue branch lineage
- but prerequisite atomic baseline SIM branches still had:
  - `PARENT_BRANCH_ID = NONE`
- the current target baseline branch also had:
  - `PARENT_BRANCH_ID = NONE`

So one family-slice cycle could emit many non-rescue roots.

That was weaker than the family model in:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_TARGET_FAMILY_MODEL__v1.md`

The family model expects:
- one primary branch
- alternatives / negatives / rescue attached around that family

Multiple baseline roots made the live topology look flatter and less family-shaped than intended.

## Why no new family-slice hint object was added yet

I checked the relevant owner/doctrine surfaces.

There is support for:
- explicit lineage fields
- term-family grouping
- negative/rescue attachment to the correct family
- one primary branch plus alternatives/negative/rescue obligations

But there is not yet a clean owner-defined family-slice field for:
- branch parentage hints
- branch grouping topology hints

So the right core move was:
- improve the live emitted topology
- keep it visible and auditable
- avoid inventing new slice doctrine ahead of the docs

## What changed

Live planner file:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`

New behavior in family-slice mode:
- prerequisite atomic baseline SIM branches now attach to the current main target baseline branch
- they no longer become independent non-rescue roots

Current live topology after the patch:
- one primary non-rescue root:
  - current target baseline branch
- prerequisite atomic baseline branches:
  - children of the current primary baseline branch
- non-rescue alternatives:
  - children of the current primary baseline branch
- rescue branches:
  - still handled by the separate rescue-lineage path

This gives the family-slice path a cleaner:
- one-primary-root
- many-attached-support/alternative

shape.

## Visibility / audit impact

Because branch parentage was already made visible, this patch now improves those live surfaces too:
- `branch_parentage_map`
- `root_branch_ids`
- `branch_child_counts`

Effect:
- `root_branch_ids` now collapses to one primary non-rescue root for the tested family-slice case
- child counts on the main primary branch now include:
  - prerequisite atomic baseline support branches
  - non-rescue alternatives

The controller audit in:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

continues to validate that visible parentage matches actual emitted parentage.

## Focused regressions

Planner/runtime:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`

Updated expectations:
- one explicit primary non-rescue root for the tested family-slice case
- prerequisite atomic baseline branch parent points to the main target baseline branch
- main target branch remains the only root
- child counts on the main root increase accordingly

Controller audit:
- existing parentage visibility tests still pass without needing doctrine changes

## Verification

Focused runtime/controller tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- result: `Ran 45 tests ... OK`

Focused local spec-object test:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`
- result: `Ran 4 tests ... OK`

## Current judgment

This is a real planner/runtime-core improvement.

What is better now:
- family-slice non-rescue topology is closer to the stated “one primary branch” family model
- prerequisite baseline support no longer explodes the root set
- visible branch-parentage audit surfaces now describe a cleaner family topology

What is still not done:
- this is still a live-policy correction, not an explicit owner-defined family-slice topology object
- richer family-local grouping hints may still be worth adding later if owner doctrine explicitly supports them

## Next best seam

Stay in the planner/runtime core.

Most likely next move:
1. inspect whether non-rescue alternative grouping is still too flat even after the single-root correction
2. only add a family-slice grouping hint surface if owner/docs support it cleanly
3. otherwise keep tightening visible live policy rather than inventing new doctrine
