# A2_UPDATE_NOTE__A1_FAMILY_SLICE_TRACK_DERIVATION_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the reset step where family-slice-controlled planner goals stop inheriting old known-goal track labels and now derive track identity from the family slice itself

## Scope

Primary runtime file:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`

Focused regressions:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`

## Problem

Even after family-slice mode outranked goal-profile mode, one real drift remained:

- if a term already existed in an older hardcoded goal table,
- `_goal_for_term(...)` would reuse that older `track`,
- so family-slice-controlled planning still inherited policy-flavored identity from historical tuples.

Concrete example:
- `correlation_polarity` could inherit an older axis track
- even when the current planning surface was an entropy family slice

That meant family-slice control was stronger than before, but not yet fully defining its own branch metadata.

## What changed

`a1_adaptive_ratchet_planner.py` now:
- adds `_track_token(...)`
- adds `_family_slice_track(...)`
- changes `_goal_for_term(..., family_slice=...)`

New behavior:
- if a family slice is present, goal `track` is derived from the slice
- old known-goal entries may still contribute default negative-class information
- but they no longer dictate the track identity for family-slice-controlled planning

Example result shape:
- `FAMILY_SLICE_<family_id_or_kind>_<term>`

So family-slice planning now carries family-local track identity instead of silently reusing whichever historical tuple first claimed the term.

## Meaning

This is a real reset improvement because it removes another hidden path where legacy goal tables still defined active A1 semantics.

After this patch:
- compatibility profile mode still exists, but is scaffold-only
- family-slice mode now also owns its own track labels

That makes the family-slice path less like “legacy tables with better routing” and more like a genuinely separate planning mode.

## Verification

Compile:
- `python3 -m py_compile system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tools/autoratchet.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py`

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`
- result:
  - `Ran 36 tests ... OK`

## Next seam

Best next move:
- inspect how much family-slice-controlled planning still inherits old term-local mechanics beyond tracks
- especially:
  - known negative-class defaults
  - known minimal surface templates
  - older target-class naming assumptions in downstream evidence/audit logic
