# A2_UPDATE_NOTE__A1_SIM_FAMILY_OPERATOR_MAP_AUDIT_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the reset step where the live SIM-family-to-operator mapping becomes explicit and controller-auditable instead of remaining hidden in planner branch templates

## Scope

Primary runtime/audit files:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

Focused regressions:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`

Nearby controller chain safety pass:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py`

## Problem

After the SIM-family ownership patch, one more live law was still hidden:
- planner branch templates encoded a fixed mapping from SIM family to `operator_id`
- controller-visible surfaces only showed deduplicated `operator_ids_used[]`
- there was no direct way to see which operator actually drove each emitted SIM family

So a family/operator drift could still happen without a clear controller-grade signal.

## Grounding

This patch is grounded in existing live and control-plane surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/ENUM_REGISTRY_v1.md`
  - canonical operator enum includes:
    - `OP_BIND_SIM`
    - `OP_REPAIR_DEF_FIELD`
    - `OP_MUTATE_LEXEME`
    - `OP_REORDER_DEPENDENCIES`
    - `OP_NEG_SIM_EXPAND`
    - `OP_INJECT_PROBE`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_REPAIR_OPERATOR_MAPPING_v1.md`
  - defines bounded operator allowlists by failure class
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_request_to_codex_prompt.py`
  - explicitly narrates the current live family/operator mapping:
    - `BASELINE -> OP_BIND_SIM`
    - `BOUNDARY_SWEEP -> OP_REPAIR_DEF_FIELD`
    - `PERTURBATION -> OP_MUTATE_LEXEME`
    - `COMPOSITION_STRESS -> OP_REORDER_DEPENDENCIES`
    - `ADVERSARIAL_NEG -> OP_NEG_SIM_EXPAND`

So the right next step was not to invent a new operator ontology.
It was to make the current live mapping explicit and auditable.

## What changed

### 1) Planner self-audit now exposes `sim_family_operator_map`

`a1_adaptive_ratchet_planner.py` now derives:
- `sim_family_operator_map`

from emitted `SIM_SPEC` items, keyed by family.

This is a controller-visible map of:
- `family -> [operator_id ...]`

for the actually emitted strategy, not inferred prose.

### 2) Cycle audit now checks visibility and canonical live mapping

`run_a1_autoratchet_cycle_audit.py` now defines the current live family/operator defaults:
- `BASELINE -> OP_BIND_SIM`
- `BOUNDARY_SWEEP -> OP_REPAIR_DEF_FIELD`
- `PERTURBATION -> OP_MUTATE_LEXEME`
- `COMPOSITION_STRESS -> OP_REORDER_DEPENDENCIES`
- `ADVERSARIAL_NEG -> OP_NEG_SIM_EXPAND`

And for family-slice runs it now checks:
- `AUTORATCHET_FAMILY_SLICE_SIM_FAMILY_OPERATOR_MAP_VISIBLE`
- `AUTORATCHET_FAMILY_SLICE_SIM_FAMILY_OPERATOR_MAP_CANONICAL`

So the controller path can now see both:
- whether every required family has a visible operator mapping
- whether the emitted map still matches the current live branch-template law

## Meaning

This patch does not yet make family slices own operator selection.

What it does is:
- remove another hidden planner-only law
- make the live family/operator map explicit in strategy self-audit
- make controller audit fail if that map silently drifts

So the system is now in a better place to answer the next deeper question honestly:
- should operator selection remain a fixed live canonical map
- or should family slices eventually own that too

## Verification

Focused planner/audit/controller suite:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py`
- result:
  - `Ran 41 tests ... OK`

Syntax:
- `python3 -m py_compile ...` passed for the touched planner/audit/test files

## Next seam

Best next move:
- decide whether operator selection should stay fixed and canonical
- or whether bounded family slices should eventually carry family-local operator policy

If reset continues without changing that ownership model, the next likely target is:
- exposing/auditing the remaining branch-template defaults that still live only in planner code
