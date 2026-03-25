# A2_UPDATE_NOTE__A1_BRANCH_GROUP_VISIBILITY_AND_AUDIT_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2
Date: 2026-03-15
Role: preserve the planner-core patch that makes family-branch grouping explicit on emitted branches and controller-auditable

## Scope

This note records one bounded runtime-core patch after:
- non-rescue branch lineage became explicit
- branch parentage became visible and controller-auditable
- single-primary-root topology was restored for family-slice non-rescue branches

It is a `DERIVED_A2` continuity surface for:
- live branch-group visibility on emitted A1 family branches
- the controller audit rule that checks that visible grouping matches actual emitted grouping

It does not rewrite owner doctrine.

## Why this patch mattered

Before this patch:
- family-slice runs already emitted:
  - `BRANCH_ID`
  - `PARENT_BRANCH_ID`
  - `FEEDBACK_REFS`
- controller audit could already check:
  - visible parentage
  - root ids
  - child counts

But branch grouping itself was still implicit.

That left a gap:
- the family topology was cleaner
- but the emitted branches still did not explicitly show which target-family cluster they belonged to

This was weaker than the owner/doctrine surfaces that already talk in terms of:
- target clusters
- candidate clusters
- term-family grouping

Grounding surfaces checked during this patch:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/01_REQUIREMENTS_LEDGER.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/PROMOTION_BINDING_v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_CONSOLIDATION_PREPACK_JOB__v1.md`

## Why no new family-slice grouping hint object was added

The docs support:
- grouping language
- cluster language
- family-shaped branch obligations

But they still do not give a clean owner-defined family-slice field for:
- branch grouping hints as an explicit contract object

So the right move here was:
- make live emitted grouping explicit
- audit it
- avoid inventing a new slice doctrine field early

## What changed

Live planner file:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`

New emitted field:
- `BRANCH_GROUP`

Current live behavior:
- the main baseline branch for the current family target gets a stable branch group
- prerequisite atomic baseline branches inherit that same branch group
- non-rescue alternatives inherit that same branch group
- rescue branches also inherit that same branch group when they are emitted for the same family target

Current branch-group shape:
- family-slice mode:
  - `BG_FAMILY_<family_id_or_kind>_<goal_term>`
- compatibility mode:
  - `BG_TRACK_<goal_track>_<goal_term>`

New self-audit surfaces:
- `branch_group_map`
- `branch_groups_used`

## Controller audit impact

Audit file:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

New live audit check:
- `AUTORATCHET_FAMILY_SLICE_BRANCH_GROUPS_VISIBLE`

What it checks:
- if explicit branch candidates are present, every branch candidate is group-tagged
- visible self-audit group map matches the actually emitted branch group map
- visible self-audit group set matches the actually emitted group set

Important detail:
- older minimal controller-report fixtures with no explicit branch candidates are still allowed to pass
- real emitted branch sets with missing or stale grouping now fail this check

## Focused regressions

Planner/runtime:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`

Updated expectations:
- tested family-slice baseline branch emits `BRANCH_GROUP`
- tested atomic prerequisite branch inherits the same `BRANCH_GROUP`
- self-audit now reports the expected `branch_groups_used`

Controller audit:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`

Updated expectations:
- visible branch-group metadata passes when it matches actual emitted grouping
- stale or incoherent visible grouping can now fail independently of parentage

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
- family-branch grouping is no longer only implicit in planner code
- emitted branches now carry a visible grouping surface
- controller audit can compare visible grouping to actual emitted grouping
- the live family topology is now described by:
  - lineage
  - parentage
  - root/child counts
  - branch grouping

What is still not done:
- branch grouping is still live policy, not an owner-defined family-slice grouping object
- if owner docs later define explicit grouping hints, this live policy may need to be re-homed into the slice contract

## Next best seam

Stay in the planner/runtime core.

Most likely next move:
1. inspect whether any remaining family-branch clustering rules are still planner-global beyond the visible `BRANCH_GROUP` surface
2. only promote explicit family-slice grouping hints if owner docs support them cleanly
3. otherwise keep tightening live emitted visibility and audit instead of inventing new doctrine
