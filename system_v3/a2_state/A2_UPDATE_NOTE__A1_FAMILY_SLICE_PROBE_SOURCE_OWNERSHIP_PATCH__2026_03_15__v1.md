# A2_UPDATE_NOTE__A1_FAMILY_SLICE_PROBE_SOURCE_OWNERSHIP_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the reset step where family-slice probe selection stops silently inheriting the old planner-global probe ladder

## Scope

Primary files:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

Focused regressions:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py`

## Problem

Family-slice mode already owned:
- required probe terms
- probe-term overrides
- term SIM tiers

But planner behavior still had one hidden inheritance seam:
- if no explicit override matched the current goal, probe selection could still collapse into the planner-global `_probe_term_for_goal(...)` ladder
- controller audit could see the selected probe term, but not whether it came from family-slice-owned context or from the old global ladder

That meant family-slice runs could still look healthy while quietly inheriting legacy probe policy.

## What changed

### 1) Planner now exposes probe-source ownership

`a1_adaptive_ratchet_planner.py` now returns both:
- `goal_probe_term`
- `goal_probe_source`

Family-slice probe sources are now explicit:
- `family_slice_override`
- `family_slice_goal_term`
- `family_slice_component_available`
- `family_slice_component_declared`
- `family_slice_declared_available`
- `family_slice_declared_fallback`

Only if none of the slice-owned routes work does the planner fall back to:
- `global_default`

### 2) Family-slice probe selection now prefers slice-declared probe context before global fallback

When a family slice is present, `_family_slice_probe_term_for_goal(...)` now prefers, in order:
- explicit slice override
- goal term if it is itself a declared probe term
- declared probe components from the goal
- declared probe candidates from family admissibility + primary terms + declared probe list

So the old global probe ladder is now the last fallback, not an invisible co-owner of family-slice probe choice.

### 3) Cycle audit now rejects hidden global-default probe selection

`run_a1_autoratchet_cycle_audit.py` now adds:
- `AUTORATCHET_FAMILY_SLICE_GOAL_PROBE_SOURCE_OWNED`

That check only passes when the visible probe source is one of the family-slice-owned sources above.

So family-slice runs can no longer satisfy controller audit if they silently used `global_default` probe selection.

## Meaning

This closes another real inheritance seam in the rewrite-first core:
- family-slice mode is less governed by hidden global planner law
- the emitted strategy now says where probe selection came from
- controller audit can distinguish family-owned probe choice from legacy fallback

This does not remove the global fallback entirely.
It makes it visible, bounded, and auditable instead of invisible.

## Verification

Compile:
- `python3 -m py_compile system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py system_v3/tools/run_a1_autoratchet_cycle_audit.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py`
- result:
  - `Ran 34 tests ... OK`

## Next seam

Best next move:
- inspect remaining universal planner/operator defaults that still act inside family-slice mode
- especially any still-hidden fallback laws that influence branch-template or operator selection without being surfaced into planner self-audit and controller audit
