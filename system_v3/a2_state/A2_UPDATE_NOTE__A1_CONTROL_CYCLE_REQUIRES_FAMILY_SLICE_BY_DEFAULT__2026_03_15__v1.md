# A2_UPDATE_NOTE__A1_CONTROL_CYCLE_REQUIRES_FAMILY_SLICE_BY_DEFAULT__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the controller-wrapper reset that makes family-slice input the expected default for direct A1 control cycles

## Scope

This note is bounded to:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a1_wiggle_control_cycle.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_WIGGLE_CONTROLLER_LAUNCH_NOTE__2026_03_15__v1.md`

Focused regressions:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`

## What changed

### 1) Control-cycle wrapper now requires family-slice input by default

`run_a1_wiggle_control_cycle.py` now requires:
- `--family-slice-json`

unless the caller explicitly opts into compatibility mode with:
- `--allow-legacy-goal-profile-mode`

Without either, the wrapper fails immediately with:
- `family_slice_json_required_unless_allow_legacy_goal_profile_mode`

### 2) Control-cycle payload now records the policy choice

The emitted control-cycle payload now also includes:
- `legacy_goal_profile_mode_allowed`
- `family_slice_json`

so controller-side inspection can see whether the run was launched through:
- normal family-slice mode
- explicit compatibility override

### 3) Active launch note was retargeted

`A1_WIGGLE_CONTROLLER_LAUNCH_NOTE__2026_03_15__v1.md` now uses:
- `--family-slice-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

in both initial and continuation command examples, and it now states plainly that:
- family-slice input is the normal direct-control path
- legacy profile-only control is compatibility mode only

## Meaning

This is stronger than the previous controller demotion step.

Before:
- legacy goal-profile mode was allowed by default, then demoted after the fact

Now:
- family-slice is the expected controller input
- legacy profile mode requires explicit opt-in
- and still demotes to manual review downstream

That is a better fit for the reset direction:
- bounded A2-derived slices should define active A1 control input
- profile ladders are compatibility scaffolds, not the default controller contract

## Verification

Compile:
- `python3 -m py_compile system_v3/tools/run_a1_wiggle_control_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py`

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- result:
  - `Ran 11 tests ... OK`

## Next seam

Best next move:
- leave the controller-law seam alone for now
- return to deeper planner/orchestrator reset work in:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/autoratchet.py`

Specifically, the next useful patch is likely:
- reduce or isolate the hardcoded profile ladders so compatibility mode is visibly scaffold-only instead of still defining most active planning behavior
