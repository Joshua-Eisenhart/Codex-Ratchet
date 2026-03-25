# A2_UPDATE_NOTE__A1_FAMILY_SLICE_GRAVEYARD_NEGATIVE_LIMIT_OWNERSHIP_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the patch that makes graveyard-first negative expansion size a family-slice-owned policy instead of a hidden universal planner law

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

Even after the family-slice reset, graveyard-first mode still hid one planner-global law:
- the extra adversarial negative expansion implicitly used every available family negative class

That meant branch-shape pressure was still partially universal instead of slice-owned.

## What changed

### 1) Family slice can now declare graveyard-negative expansion size

New optional field:
- `rescue_start_conditions.graveyard_negative_expansion_limit`

It is now present in:
- the live local Pydantic model
- the hand-written family-slice schema
- the committed generated Pydantic schema artifact

If omitted:
- previous behavior stays intact
- the planner uses the full family negative-class set

If present:
- graveyard-first mode only expands the first `N` ordered family negative classes

### 2) Planner self-audit exposes the new ownership

`a1_adaptive_ratchet_planner.py` now emits:
- `family_slice_graveyard_negative_expansion_limit`
- `graveyard_negative_classes_used`

with the used negative set already shaped by the slice-owned limit.

### 3) Cycle audit now checks the visible limit

`run_a1_autoratchet_cycle_audit.py` now:
- reads the expected slice-owned graveyard expansion limit
- compares it to the strategy self-audit
- compares visible graveyard negative classes against the limit-shaped expected set

So controller-grade reads can now tell whether the planner actually obeyed the slice-owned graveyard expansion policy.

## Meaning

This is a real planner-core improvement:
- one more hidden graveyard-first branch-shape law moved into the family slice
- the planner and the audit both expose it
- the contract artifacts were refreshed so reload surfaces stay current

It is still not the end of planner-global defaults.
But it reduces universal branch shaping inside family-slice mode.

## Focused verification

Planner + audit regressions:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- result:
  - `Ran 35 tests ... OK`

Local Pydantic family-slice stack:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`
- result:
  - `Ran 4 tests ... OK`

## Next seam

Best next move remains in the same layer:
- identify any remaining fixed planner budgets or branch-shape defaults that still act as hidden universal law inside family-slice mode
- especially `graveyard_first` / `graveyard_recovery` budget shaping
