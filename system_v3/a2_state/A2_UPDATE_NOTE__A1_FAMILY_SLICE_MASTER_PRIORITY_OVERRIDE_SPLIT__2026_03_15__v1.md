# A2_UPDATE_NOTE__A1_FAMILY_SLICE_MASTER_PRIORITY_OVERRIDE_SPLIT__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the reset step where the old `qit_master_conjunction` priority override stays compatibility-only instead of silently applying inside family-slice planning

## Scope

Primary file:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`

Focused regressions:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py`
- plus the standing cycle-audit family-slice suite

## Problem

`build_strategy_from_state(...)` still contained a compatibility-era global law:
- if `qit_master_conjunction` was present in the goal set
- and its prerequisite terms were canonical
- the planner could override the currently selected goal and promote `qit_master_conjunction`

That behavior made sense for legacy refined-fuel compatibility runs.
But it was still active for family-slice mode too, which meant:
- a bounded A2-provided family slice could choose its own goal ordering
- then a hidden planner-global compatibility rule could still replace that choice

So family-slice planning still had one more silent inheritance seam from the old laddered planner.

## What changed

### 1) Master-goal promotion is now compatibility-only

The `qit_master_conjunction` priority override now runs only when `family_slice` is absent.

That means:
- compatibility/profile scaffolds keep their old whole-system promotion behavior
- family-slice-controlled runs stay with the goal chosen by the normal family-slice path

### 2) Planner now exposes goal-priority provenance

Planner `self_audit` now includes:
- `goal_priority_source`

Current values surfaced are:
- `next_goal`
- `goals_tail_fallback`
- `compatibility_master_override`

So the old hidden promotion rule is now explicit instead of invisible.

## Meaning

This is another real rewrite-first improvement:
- compatibility scaffolds may still use the old refined-fuel master witness shortcut
- family slices no longer inherit that shortcut
- planner output now says whether a compatibility override actually changed the goal choice

That keeps family-slice runs closer to the bounded A2 handoff instead of letting the planner quietly re-impose older whole-system campaign intent.

## Verification

Compile:
- `python3 -m py_compile system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- result:
  - `Ran 36 tests ... OK`

## Next seam

Best next move:
- inspect the remaining family-slice/global-default junctions in `build_strategy_from_state(...)`
- especially hardcoded SIM tier / branch-template defaults that still act as universal law even when family-slice mode is active
