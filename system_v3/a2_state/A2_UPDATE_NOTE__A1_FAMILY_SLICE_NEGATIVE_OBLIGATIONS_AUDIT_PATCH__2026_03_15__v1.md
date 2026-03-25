# A2_UPDATE_NOTE__A1_FAMILY_SLICE_NEGATIVE_OBLIGATIONS_AUDIT_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the reset step where family-slice negative obligations become visible and auditable in the planner/audit chain

## Scope

Primary files:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

Focused regressions:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- plus the standing controller/runtime focused suite

## Problem

After the family-slice reset work, controller-visible obligations were still mostly:
- family-slice presence
- required lanes
- strategy head visibility
- probe-term declaration

But negative obligations were still weakly surfaced:
- family-slice mode still chose a negative class internally
- the chosen class and the slice’s declared negative expectations were not strongly propagated into planner self-audit
- cycle audit therefore could not tell whether a family-slice run was actually carrying its own declared negative discipline

## What changed

### 1) Planner now derives family-slice negative-class order explicitly

`a1_adaptive_ratchet_planner.py` now adds:
- `_family_slice_negative_classes(...)`

Behavior:
- `negative_emphasis_classes` are considered first
- then `required_negative_classes`
- duplicates are collapsed deterministically

### 2) Family-slice goals now prioritize slice-declared negative emphasis

When `family_slice` is present, `_goal_for_term(...)` now:
- prefers the slice’s ordered negative-class set
- only falls back to old known-goal negative class if the slice declares none

So family-slice-controlled planning now takes its negative class from the slice first, not from older hardcoded goal tables first.

### 3) Planner self-audit now exposes negative obligations

Planner `self_audit` now includes:
- `family_slice_required_negative_classes`
- `goal_negative_class`

That means the emitted strategy now makes the family-slice negative surface visible to controller-side auditing.

### 4) Cycle audit now checks negative-obligation visibility

`run_a1_autoratchet_cycle_audit.py` now adds checks for:
- `AUTORATCHET_FAMILY_SLICE_NEGATIVE_CLASSES_VISIBLE`
- `AUTORATCHET_FAMILY_SLICE_GOAL_NEGATIVE_CLASS_VISIBLE`

So family-slice obligations are no longer treated as satisfied by lanes and head visibility alone.

## Meaning

This is a real reset improvement because family-slice mode is supposed to carry family-local negative discipline explicitly.

After this patch:
- the slice’s negative emphasis is used in planning
- the strategy exposes it
- the cycle audit verifies it

That still does not make the full planner fully doctrine-aligned.
But it removes another silent place where active family meaning could still disappear into legacy planner behavior.

## Verification

Compile:
- `python3 -m py_compile system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py system_v3/tools/run_a1_autoratchet_cycle_audit.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`
- result:
  - `Ran 38 tests ... OK`

## Next seam

Best next move:
- inspect the hardcoded minimal math-surface templates still reused inside family-slice planning
- decide which part of those templates should become family-slice-controlled or at least compatibility-only, instead of silently remaining universal planner law
