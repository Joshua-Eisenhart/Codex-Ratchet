# A2_UPDATE_NOTE__A1_FAMILY_SLICE_GRAVEYARD_BUDGET_OWNERSHIP_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the patch that makes graveyard-mode strategy budgets family-slice-ownable instead of hidden universal planner law

## Scope

Primary live surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a2_to_a1_family_slice_models.py`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

Focused regressions:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`

## Problem

Even after family-slice ownership patches, one real planner-global law remained:
- `graveyard_first` always budgeted `48 / 64`
- `graveyard_recovery` always budgeted `32 / 48`

Those values were shaping probe pressure and emitted strategy budget even in family-slice mode, but they were not slice-owned or explicitly visible as slice policy.

## What changed

### 1) Family slice can now optionally own graveyard-mode budget

New optional fields under `rescue_start_conditions`:
- `graveyard_first_max_items`
- `graveyard_first_max_sims`
- `graveyard_recovery_max_items`
- `graveyard_recovery_max_sims`

These are now supported in:
- the live local Pydantic model
- the hand-written family-slice schema
- the committed generated Pydantic schema artifact

If omitted:
- the live planner keeps the previous defaults

If present:
- the planner uses the slice-declared values for the matching debate mode

### 2) Planner now emits the active debate-mode budget as visible slice-owned metadata

`a1_adaptive_ratchet_planner.py` now exposes:
- `debate_mode`
- `family_slice_budget_max_items`
- `family_slice_budget_max_sims`
- `family_slice_budget_source`

`family_slice_budget_source` is currently:
- `planner_default`
- or `family_slice_override`

So the active budget is no longer just an implicit branch of planner code.

### 3) Cycle audit now checks the visible budget against the slice

`run_a1_autoratchet_cycle_audit.py` now:
- reads the strategy `budget`
- reads `self_audit.debate_mode`
- derives the expected family-slice budget for that debate mode
- checks both the visible strategy budget and the visible self-audit budget fields

This gives the controller path a real read on whether graveyard-mode budget shaping was slice-owned or defaulted.

## Meaning

This is another real core improvement, not wrapper work:
- one more hidden graveyard-mode planner default moved into the family slice
- the planner and the audit both expose it
- the committed generated schema artifact was refreshed again to stay current

The remaining hardcoded budget law is smaller now.
What still remains is broader hidden branch-shape/budget behavior outside these declared graveyard-mode overrides.

## Focused verification

Planner + audit regressions:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- result:
  - `Ran 36 tests ... OK`

Local Pydantic family-slice stack:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`
- result:
  - `Ran 4 tests ... OK`

## Next seam

Best next move is still in the same layer:
- continue removing remaining hidden planner-global branch shaping inside family-slice mode
- especially any fixed balanced/default budget and any still-unowned branch-count/expansion behavior around graveyard recovery
