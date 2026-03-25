# A2_UPDATE_NOTE__A1_FAMILY_SLICE_REQUIRED_SIM_FAMILY_OWNERSHIP_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the reset step where family-slice required SIM families become enforced planner inputs instead of declaration-only audit metadata

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

The earlier SIM-family audit patch made `required_sim_families` visible and checked.
But the planner still did not actually treat the family slice as the authority for SIM family selection.

The remaining hidden law was:
- planner-global branch templates still unconditionally emitted the old stress-family set
- `required_sim_families` was audited, but not yet used as a validated planner input

That left one more planner-global doctrine seam in place.

## Grounding

This step follows explicit doctrine, not a new invention:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/01_REQUIREMENTS_LEDGER.md`
  - `RQ-056` requires stress families:
    - `BASELINE`
    - `BOUNDARY_SWEEP`
    - `PERTURBATION`
    - `ADVERSARIAL_NEG`
    - `COMPOSITION_STRESS`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/06_SIM_EVIDENCE_AND_TIERS_SPEC.md`
  - repeats the same required family set
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_EXECUTABLE_DISTILLATION_UPDATE__SOURCE_BOUND_v2.md`
  - says A1 prepares structures anticipating that same five-family set

So the right reset move here was not to invent a new SIM-family ontology.
It was to make the validated family slice own the existing doctrinal family set.

## What changed

### 1) Family-slice validation now enforces the doctrinal stress-family set

`a1_adaptive_ratchet_planner.py` now defines:
- `REQUIRED_STRESS_SIM_FAMILIES`
- `_family_slice_required_sim_families(...)`

Family-slice semantic validation now fails if:
- any doctrinal required family is missing from `sim_hooks.required_sim_families`
- any unknown SIM family token is present

So `required_sim_families` is now fail-closed instead of advisory.

### 2) Planner now consults the validated family-slice family set

In family-slice mode, planner now derives:
- `sim_family_selection`
- `enabled_sim_families`

from the family slice itself.

That selection is then used to gate emission of:
- the positive `BASELINE` SIM
- `BOUNDARY_SWEEP`
- `PERTURBATION`
- `COMPOSITION_STRESS`
- `ADVERSARIAL_NEG`
- graveyard-first adversarial expansion
- graveyard-recovery rescue boundary / perturb / stress variants

Under valid doctrine-aligned slices, the practical emitted set still matches the required five-family law.
But the authority has moved from hidden planner-global assumption to validated slice input.

### 3) Planner self-audit now preserves family selection more honestly

Self-audit now uses:
- `family_slice_required_sim_families`
- `sim_families_used`

as real ordered/used surfaces rather than purely sorted declaration summaries.

## Meaning

This is a real authority transfer.

After this patch:
- family-slice SIM-family requirements are validated against doctrine
- planner emission consults the family slice
- controller-visible audit still checks what was actually emitted

So SIM family selection is no longer only “planner-global but audited.”
It is now “slice-validated and slice-consulted,” while still preserving the doctrinal five-family requirement.

## Verification

Focused planner/audit/controller suite:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py`
- result:
  - `Ran 41 tests ... OK`

Syntax:
- `python3 -m py_compile ...` passed for the touched planner/audit/test files

## Next seam

Best next move:
- inspect the remaining universal branch-template/operator defaults
- especially:
  - operator-id defaults on emitted structural and negative branches
  - any remaining planner-global branch-template law that family slices still do not own
