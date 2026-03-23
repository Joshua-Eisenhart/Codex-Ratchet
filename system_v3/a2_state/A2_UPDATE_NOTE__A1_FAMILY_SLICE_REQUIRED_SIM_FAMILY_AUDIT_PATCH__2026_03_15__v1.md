# A2_UPDATE_NOTE__A1_FAMILY_SLICE_REQUIRED_SIM_FAMILY_AUDIT_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the reset step where family-slice-required SIM families become visible and auditable in the planner/controller path

## Scope

Primary runtime/audit files:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

Focused regressions:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`

Nearby controller chain safety pass:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py`

## Problem

Even after the family-slice SIM hook ownership patch, one controller-visible SIM surface was still weak:
- family slices already declared `sim_hooks.required_sim_families`
- but planner self-audit did not expose the actual emitted SIM families
- and cycle audit did not check whether the emitted strategy actually satisfied the declared required SIM family set

So `required_sim_families` existed in the contract, but still acted more like documentation than a checked runtime surface.

## What changed

### 1) Planner self-audit now exposes both declared and used SIM families

`a1_adaptive_ratchet_planner.py` now adds:
- `family_slice_required_sim_families`
- `sim_families_used`

`sim_families_used` is derived from emitted `SIM_SPEC` items, not from family-slice prose.

### 2) Cycle audit now checks required family visibility

`run_a1_autoratchet_cycle_audit.py` now checks:
- `AUTORATCHET_FAMILY_SLICE_REQUIRED_SIM_FAMILIES_VISIBLE`

Rule:
- the family-slice-declared required SIM family set must be a subset of the emitted strategy’s visible `sim_families_used`

This keeps the controller path from treating declared family requirements as satisfied unless the strategy surface actually shows them.

## Meaning

This is another small but real reduction of hidden planner inheritance.

After this patch:
- family slices no longer just declare required SIM families
- the emitted strategy exposes the SIM families it actually uses
- the cycle audit enforces that required family visibility

This does not yet mean family slices control SIM family selection itself.
It means the controller path can now see and audit the currently emitted family set instead of trusting declaration-only metadata.

## Verification

Focused planner/audit/controller suite:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py`
- result:
  - `Ran 40 tests ... OK`

Syntax:
- `python3 -m py_compile ...` passed for the touched planner/audit/test files

## Next seam

Best next move:
- decide whether family slices should start owning SIM family selection itself
- or whether current selection stays planner-global but controller-audited

If reset continues deeper, the next likely targets are:
- family-owned SIM family selection
- remaining universal operator-id defaults on emitted branches
