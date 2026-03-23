# A2_UPDATE_NOTE__A1_BRANCH_PARENTAGE_VISIBILITY_AND_AUDIT_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2
Date: 2026-03-15
Role: preserve the planner-core patch that makes live non-rescue branch parentage/grouping explicit and controller-auditable without inventing a new family-slice topology object

## Scope

This note records one bounded runtime-core patch after:
- non-rescue branch lineage fields were made real on emitted family branches
- controller audit started checking actual non-rescue branch lineage coverage

It is a `DERIVED_A2` continuity surface for:
- explicit parentage/grouping visibility on non-rescue branches
- controller audit coverage over parentage/grouping coherence

It does not rewrite owner doctrine or promote a new owner contract.

## Why this patch mattered

Before this patch:
- branch lineage fields existed on the main family branch set
- but the parentage/grouping policy behind those fields still lived as hidden planner-local behavior
- a fresh reader could not tell, from emitted strategy self-audit alone:
  - which branches were roots
  - which branches were children of the current primary baseline branch
  - whether the visible branch-parentage story was internally coherent

There was also not enough owner-doc support yet to safely invent a new family-slice branch-topology object.

So the right next move was:
- make the live parentage/grouping policy explicit
- audit it
- postpone any new topology object until doctrine justifies it

## What changed

### Planner

Live planner file:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`

New self-audit surfaces:
- `branch_parentage_map`
- `root_branch_ids`
- `branch_child_counts`

These are derived from actual emitted non-rescue `SIM_SPEC` items.

Current live policy that is now visible:
- baseline / bootstrap branches are roots
  - `PARENT_BRANCH_ID = NONE`
- non-rescue alternatives attach to the current primary baseline branch
- graveyard-first extra adversarial negative branches attach to the main adversarial negative branch

This does not claim that the policy is final doctrine.
It only makes the live policy visible and replayable.

### Controller audit

Audit file:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

New check:
- `AUTORATCHET_FAMILY_SLICE_BRANCH_PARENTAGE_VISIBLE`

The audit now checks:
- actual emitted non-rescue branch parentage map
- visible self-audit parentage map
- root-branch visibility
- child-count visibility
- internal coherence:
  - every non-root parent must resolve to another visible non-rescue branch id
  - roots must be explicit

This turns branch parentage/grouping from hidden local behavior into an exposed live-law surface.

## Focused regressions

Planner/runtime:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`

Updated:
- self-audit now proves:
  - branch parentage map visibility
  - root branch visibility
  - child-count visibility
- expected boundary branch parentage is checked against the current primary baseline branch

Controller audit:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`

Updated:
- passing family-slice audit fixtures now expose matching:
  - `branch_parentage_map`
  - `root_branch_ids`
  - `branch_child_counts`
- added a new failure regression where self-audit parentage is incoherent even though the strategy contains a valid visible branch

## Verification

Focused runtime/controller tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- result: `Ran 45 tests ... OK`

Focused local spec-object test:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`
- result: `Ran 4 tests ... OK`

## Current judgment

This is a real runtime-core improvement.

What is better now:
- the live branch parentage/grouping policy is visible
- controller audit can reject incoherent parentage/grouping stories
- a fresh thread can inspect the live branch-parentage law without reading planner code first

What is still not done:
- this is still a visible live policy, not an explicit family-slice-owned topology object
- alternative-branch parentage remains deterministic local policy rather than declared slice data

## Next best seam

Stay in the planner/runtime core.

Most likely next move:
1. inspect whether alternative-branch grouping or parentage should become an explicit family-slice hint surface
2. only promote that if the owner/docs support it cleanly; otherwise keep exposing live policy without inventing new doctrine
