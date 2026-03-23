# A2_UPDATE_NOTE__A1_PLANNING_MODE_METADATA_PROPAGATION__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the propagation of planner/orchestrator planning-mode metadata through A1 audit/controller surfaces

## Scope

This note is bounded to:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/autoratchet.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a1_autoratchet_controller_result.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a1_wiggle_control_cycle.py`

Focused regressions:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`

## What changed

### 1) Autoratchet campaign summary now names compatibility profile identity

`autoratchet.py` now writes:
- `planning_mode`
- `legacy_goal_profile_mode`
- `compatibility_goal_profile`

into campaign summary output.

So profile-driven compatibility mode is no longer only implied by:
- `goal_source = goal_profile`

It now carries an explicit planning-mode identity.

### 2) Audit report now preserves that identity

`run_a1_autoratchet_cycle_audit.py` now forwards:
- `planning_mode`
- `compatibility_goal_profile`

alongside:
- `goal_source`
- `legacy_goal_profile_mode`

### 3) Controller result now preserves that identity

`build_a1_autoratchet_controller_result.py` now forwards:
- `planning_mode`
- `compatibility_goal_profile`

into controller-readable result packets.

### 4) Control-cycle wrapper now emits that identity too

`run_a1_wiggle_control_cycle.py` now includes:
- `planning_mode`
- `compatibility_goal_profile`

in its emitted result payload.

## Meaning

The reset distinction is now preserved across the whole direct-control chain:
- planner/orchestrator chooses family-slice vs compatibility scaffold
- audit sees it
- controller result sees it
- top control-cycle payload sees it

That makes it much harder for later tooling to collapse:
- family-slice-controlled runs
- compatibility profile scaffolds

into the same undifferentiated “A1 run” bucket.

## Verification

Compile:
- `python3 -m py_compile system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tools/autoratchet.py system_v3/tools/run_real_loop.py system_v3/tools/run_a1_autoratchet_cycle_audit.py system_v3/tools/build_a1_autoratchet_controller_result.py system_v3/tools/run_a1_wiggle_control_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`
- result:
  - `Ran 33 tests ... OK`

## Next seam

Best next move:
- leave the controller metadata propagation alone
- return to the remaining substantive planner drift:
  - profile ladders still define the actual compatibility scaffold content
  - witness/residue/head ordering still lives partly in hardcoded tables instead of fully in bounded family-slice inputs
