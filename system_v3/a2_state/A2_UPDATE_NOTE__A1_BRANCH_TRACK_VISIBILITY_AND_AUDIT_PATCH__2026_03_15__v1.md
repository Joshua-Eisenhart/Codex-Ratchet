# A2_UPDATE_NOTE__A1_BRANCH_TRACK_VISIBILITY_AND_AUDIT_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2
Date: 2026-03-15
Role: preserve the planner-core patch that makes live family-branch tracks explicit on emitted SIM branches and controller-auditable

## Scope

This note records one bounded runtime-core patch after:
- non-rescue branch lineage became explicit
- branch parentage became visible and auditable
- branch grouping became visible and auditable

It is a `DERIVED_A2` continuity surface for:
- explicit `BRANCH_TRACK` on the emitted family-branch SIM surfaces
- the controller audit rule that checks that visible branch-track metadata matches the actual emitted branch-track map

It does not rewrite owner doctrine.

## Why this patch mattered

Before this patch:
- alternative and rescue SIM branches already emitted `BRANCH_TRACK`
- but the main baseline SIM branch did not
- atomic prerequisite SIM branches also did not, even though their paired `MATH_DEF` surfaces already had a track marker

That left a live asymmetry:
- grouping was now explicit
- parentage was now explicit
- but baseline-vs-support track identity was still partially hidden in planner code

So branch clustering was better than before, but still not fully visible on the emitted SIM branch set.

## What changed

Live planner file:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`

New emitted behavior:
- the main baseline SIM branch now emits:
  - `BRANCH_TRACK = <working_goal.track>`
- atomic prerequisite SIM branches now emit:
  - `BRANCH_TRACK = ATOMIC_TERM_BOOTSTRAP`

New self-audit surfaces:
- `branch_track_map`
- `branch_tracks_used`

So the live family-slice branch story now exposes:
- lineage
- parentage
- grouping
- branch track

on the emitted SIM branch set instead of leaving baseline/support track identity implicit.

## Controller audit impact

Audit file:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

New live audit check:
- `AUTORATCHET_FAMILY_SLICE_BRANCH_TRACKS_VISIBLE`

What it checks:
- if explicit branch candidates are present, every branch candidate is track-tagged
- visible self-audit track map matches the actual emitted branch-track map
- visible self-audit track set matches the actual emitted track set

Important detail:
- older minimal controller fixtures with no explicit branch candidates are still allowed to pass
- real emitted branch sets with missing or stale track metadata now fail this check

## Focused regressions

Planner/runtime:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`

Updated expectations:
- tested family-slice baseline branch emits the family-slice goal track on the SIM branch
- tested atomic prerequisite branch emits `ATOMIC_TERM_BOOTSTRAP`
- self-audit now reports both in `branch_tracks_used`

Controller audit:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`

Updated expectations:
- visible branch-track metadata passes when it matches actual emitted branch tracks
- unrelated failure fixtures now include coherent branch-track metadata so they keep failing for their intended reason

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
- the baseline branch is no longer the one major SIM branch without a visible track
- atomic prerequisite support branches now expose their support-track identity on the SIM side too
- controller audit can compare visible branch-track metadata to the actual emitted branch set

What is still not done:
- branch tracks are still live policy, not an explicit owner-defined branch-topology contract object
- any richer cluster semantics beyond `BRANCH_GROUP` + `BRANCH_TRACK` should still wait for owner-doc support

## Next best seam

Stay in the planner/runtime core.

Most likely next move:
1. inspect whether any remaining family-branch semantics are still only derivable from planner-local naming rules
2. especially check whether the currently emitted branch-role story is still too implicit even after:
   - lineage
   - parentage
   - grouping
   - branch track
3. only add new explicit surfaces if the owner docs support them cleanly
