# A2_UPDATE_NOTE__A1_FAMILY_SLICE_RESCUE_LINEAGE_FIELD_OWNERSHIP_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2
Date: 2026-03-15
Role: preserve the planner-core patch that turns family-slice rescue lineage from a declared obligation into actual emitted rescue-branch fields plus controller-audited coverage

## Scope

This note records one bounded runtime-core patch after:
- scaffold rescue multiplicity was made family-slice-owned
- rescue linkage became visible in planner self-audit

It is a `DERIVED_A2` continuity surface for:
- actual rescue-branch lineage field emission
- controller audit coverage over emitted rescue items instead of only mirrored self-audit claims

It does not rewrite owner doctrine.

## Why this patch mattered

Before this patch:
- the family slice could declare lineage requirements such as:
  - `branch_id`
  - `parent_branch_id`
  - `feedback_refs`
  - `rescue_linkage`
- planner self-audit could repeat that declaration
- rescue branches only reliably emitted `RESCUE_LINKAGE`

So rescue lineage was only half-real:
- the contract was visible
- the actual emitted rescue branches did not satisfy the full declared lineage shape

That left the A1 family-slice path weaker than the stated family model in:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a1_state/A1_TARGET_FAMILY_MODEL__v1.md`

## What changed

### Planner

Live planner file:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`

New behavior:
- family-slice rescue branches now emit declared lineage fields when the slice requires them
- this applies to:
  - scaffold rescue branches
  - graveyard-recovery rescue branches

Emitted rescue lineage fields now include:
- `BRANCH_ID`
- `PARENT_BRANCH_ID`
- `FEEDBACK_REFS`
- `RESCUE_LINKAGE`

Grounded shape used:
- scaffold rescue:
  - `BRANCH_ID = rescue branch id`
  - `PARENT_BRANCH_ID = current positive branch id`
  - `FEEDBACK_REFS = [rescue evidence token]`
  - `RESCUE_LINKAGE = scaffold linkage token`
- graveyard recovery:
  - `BRANCH_ID = rescue branch id`
  - `PARENT_BRANCH_ID = recovered graveyard source id`
  - `FEEDBACK_REFS = [graveyard rescue token, rescue evidence token]`
  - `RESCUE_LINKAGE = graveyard linkage token`

Planner self-audit now also exposes:
- `rescue_lineage_fields_used`

That field is derived from actual emitted rescue items, not from the family-slice declaration alone.

### Controller audit

Audit file:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

New behavior:
- rescue-lineage checks now inspect actual emitted rescue branches
- the audit no longer treats rescue-lineage visibility as satisfied merely because:
  - the family slice declared it
  - self-audit repeated it
  - a rescue linkage token existed

`AUTORATCHET_FAMILY_SLICE_RESCUE_LINEAGE_VISIBLE` now requires:
- declared rescue-lineage mode is visible
- rescue branches exist up to the visible `RESCUER` count
- each visible rescue branch satisfies the declared lineage field set

## Focused regressions

Planner/runtime:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`

Added/updated expectations:
- scaffold rescue branches expose:
  - `BRANCH_ID`
  - `PARENT_BRANCH_ID`
  - `FEEDBACK_REFS`
  - `RESCUE_LINKAGE`
- graveyard-recovery rescue branches expose the same lineage set
- planner self-audit exposes:
  - `rescue_lineage_fields_used`

Controller audit:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`

Updated:
- passing family-slice audit fixture now includes an actual rescue branch carrying the declared lineage fields
- failing rescue-lineage fixture still proves the audit rejects missing rescue-lineage coverage

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
- rescue lineage is no longer only a declared family-slice contract
- rescue branches now carry the declared lineage fields themselves
- controller audit now checks actual rescue-branch lineage coverage

What is still not done:
- lineage is still represented through deterministic emitted fields on strategy items, not a separate first-class branch object store
- primary/alternative/non-rescue lineage is still less explicit than rescue lineage

## Next best seam

Stay in the planner/runtime core.

Most likely next move:
1. audit whether any remaining non-rescue branch lineage or branch-shape rules still bypass explicit family-slice ownership
2. especially check whether primary/alternative/negative branches should start surfacing the same lineage field discipline now that rescue branches do
