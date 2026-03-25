# A2_UPDATE_NOTE__A1_CONTROLLER_DEMOTES_LEGACY_GOAL_PROFILE_MODE__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the controller-side reset that treats goal-profile autoratchet runs as legacy/manual-review mode instead of a normal clean control path

## Scope

This note is bounded to the direct A1 control surfaces around autoratchet:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_autoratchet_controller_result.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_wiggle_control_cycle.py`

Focused regressions:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py`

## What changed

### 1) Controller result now demotes legacy goal-profile runs

`build_a1_autoratchet_controller_result.py` now treats:
- `goal_source != "family_slice"`

as:
- `legacy_goal_profile_mode = true`
- `controller_decision = MANUAL_REVIEW_REQUIRED`
- `controller_decision_reason = legacy_goal_profile_mode`

This means the controller no longer treats bare profile-driven autoratchet campaigns as a normal clean continuation/stop surface.

### 2) Audit report now exposes legacy-vs-family-slice mode

`run_a1_autoratchet_cycle_audit.py` now emits:
- `goal_source`
- `legacy_goal_profile_mode`

so the audit surface itself preserves the distinction between:
- family-slice-controlled runs
- legacy profile-controlled runs

### 3) Control-cycle result now forwards that distinction

`run_a1_wiggle_control_cycle.py` now includes:
- `goal_source`
- `legacy_goal_profile_mode`
- `family_slice_expected`

in its emitted control-cycle result payload.

## Meaning

This is a controller-law reset, not a lower-loop truth change.

The effect is:
- family-slice-driven autoratchet remains the clean intended path
- legacy goal-profile autoratchet may still run
- but it no longer presents as a normal controller-clean path

That is a better fit for the broader reset:
- bounded A2-derived family slices should define active A1 planning intent
- profile ladders are still present in code, but they are now demoted at the controller layer

## Verification

Compile:
- `python3 -m py_compile system_v3/tools/build_a1_autoratchet_controller_result.py system_v3/tools/run_a1_autoratchet_cycle_audit.py system_v3/tools/run_a1_wiggle_control_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py`
- result:
  - `Ran 8 tests ... OK`

## Next seam

Best next move:
- decide whether `run_a1_wiggle_control_cycle.py` should go one step further and require `--family-slice-json` by default, with an explicit compatibility override for legacy profile mode
- or freeze the controller demotion here and return to deeper planner/orchestrator rewrites in:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/autoratchet.py`
