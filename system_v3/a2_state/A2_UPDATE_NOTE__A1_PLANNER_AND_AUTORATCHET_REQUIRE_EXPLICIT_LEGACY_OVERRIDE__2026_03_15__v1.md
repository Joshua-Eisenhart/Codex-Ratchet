# A2_UPDATE_NOTE__A1_PLANNER_AND_AUTORATCHET_REQUIRE_EXPLICIT_LEGACY_OVERRIDE__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the deeper reset step where planner/orchestrator legacy profile mode stops being implicit and now requires explicit compatibility override

## Scope

This note is bounded to:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/autoratchet.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_real_loop.py`

Focused regressions:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`

## What changed

### 1) Planner now requires family slice unless legacy mode is explicitly allowed

`a1_adaptive_ratchet_planner.py` now requires:
- `--family-slice-json`

unless the caller explicitly opts into compatibility mode with:
- `--allow-legacy-goal-profile-mode`

Without either, planner CLI exits with:
- `family_slice_json_required_unless_allow_legacy_goal_profile_mode`

### 2) Autoratchet now requires the same explicit override

`autoratchet.py` now follows the same rule:
- family-slice path is normal
- goal-profile path is compatibility mode only

It now accepts:
- `--allow-legacy-goal-profile-mode`

and refuses profile-only execution without that override.

### 3) Legacy path is explicitly labeled in planner/orchestrator metadata

Planner `self_audit` now includes:
- `planning_mode = family_slice_controlled | compatibility_profile_scaffold`
- `legacy_goal_profile_mode = true|false`

Autoratchet campaign summary now includes:
- `planning_mode`
- `legacy_goal_profile_mode`

So the legacy scaffold path is no longer just implied by absence of a slice.

### 4) Still-legacy caller now opts in on purpose

`run_real_loop.py` still uses the old profile-driven autoratchet path, but it now passes:
- `--allow-legacy-goal-profile-mode`

So that legacy dependency is explicit instead of silent.

## Meaning

This is the first reset step that reaches below controller wrappers into the active planner/orchestrator layer.

Before:
- family-slice was preferred in wrappers
- but planner/orchestrator still silently treated profile ladders as a normal fallback

Now:
- planner/orchestrator also require explicit compatibility intent
- profile ladders are visibly scaffold-only
- remaining legacy users have to opt in

That does not remove the hardcoded ladders yet.
But it does stop them from presenting as the unmarked normal path.

## Verification

Compile:
- `python3 -m py_compile system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tools/autoratchet.py system_v3/tools/run_real_loop.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py`

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`
- result:
  - `Ran 33 tests ... OK`

## Next seam

Best next move:
- reduce how much the hardcoded profile ladders still define actual planning content
- likely by isolating them further into clearly named compatibility/scaffold helpers and shrinking the active planner path around family-slice inputs

Most likely next edit targets:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/autoratchet.py`
