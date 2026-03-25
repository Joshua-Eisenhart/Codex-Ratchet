# A2_UPDATE_NOTE__A1_FAMILY_SLICE_SIM_HOOK_OWNERSHIP_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the reset step where family-slice mode now owns term-level SIM hook defaults instead of inheriting universal planner SIM laws

## Scope

Primary runtime/audit files:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

Family-slice contract surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

Focused regressions:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`

## Problem

After the earlier reset steps, family-slice mode already owned:
- routing
- tracks
- negative obligations
- math surfaces
- target-class naming
- graveyard-first negative expansion

But SIM hook behavior was still partly universal:
- `_probe_term_for_goal(...)` still selected probe terms from planner-global law
- `_sim_tier_for_term(...)` still assigned tiers from planner-global law
- cycle audit only checked that probe terms were declared in the slice, not that the emitted strategy actually used the slice-owned SIM choices

So family-slice mode still did not fully own the planner-to-SIM seam.

## What changed

### 1) Family-slice schema now supports explicit SIM ownership

`A2_TO_A1_FAMILY_SLICE_v1` now allows optional `sim_hooks` fields:
- `probe_term_overrides`
- `term_sim_tiers`

The sample substrate slice now includes explicit values for:
- `finite_dimensional_hilbert_space`
- `density_matrix`
- `probe_operator`
- `cptp_channel`
- `partial_trace`

### 2) Planner now prefers family-slice SIM hooks

`a1_adaptive_ratchet_planner.py` now adds:
- `_family_slice_probe_term_override(...)`
- `_family_slice_term_sim_tier(...)`
- `_family_slice_probe_term_for_goal(...)`
- `SIM_TIER_ORDER`
- `_sim_tier_rank(...)`

Behavior:
- if a family slice declares `sim_hooks.probe_term_overrides[goal_term]`, planner uses it
- if a family slice declares `sim_hooks.term_sim_tiers[goal_term]`, planner uses it
- otherwise planner falls back to the older universal defaults

### 3) Family-slice semantic validation now checks the SIM hook contract

Family-slice validation now fails if:
- a probe override is not also declared in `required_probe_terms`
- a probe override points to a non-probe-capable term
- a term-level SIM tier is invalid
- a term-level SIM tier falls below the declared `expected_tier_floor`

### 4) Planner self-audit now exposes actual SIM choices

Planner self-audit now includes:
- `family_slice_declared_probe_terms`
- `family_slice_term_sim_tier_terms`
- `goal_term`
- `goal_probe_term`
- `goal_sim_tier`

So the controller-visible layer can now see the actual emitted SIM choice for the active goal.

### 5) Cycle audit now checks the used probe/tier, not just the declaration

`run_a1_autoratchet_cycle_audit.py` now checks:
- `AUTORATCHET_FAMILY_SLICE_GOAL_PROBE_TERM_VISIBLE`
- `AUTORATCHET_FAMILY_SLICE_GOAL_SIM_TIER_VISIBLE`

Rule:
- the actual probe term must be visible and belong to the slice-declared required probe set
- if the slice declares a term-specific probe override, the actual probe term must match it
- if the slice declares a term-specific SIM tier, the actual goal SIM tier must match it
- otherwise the actual goal SIM tier must still satisfy the declared tier floor

## Meaning

This removes another real planner-global inheritance seam.

After this patch:
- family-slice mode can own term-level probe routing
- family-slice mode can own term-level SIM tier choice
- controller-visible auditing checks the emitted strategy against those slice-owned choices

That still does not mean family slices now own every downstream SIM policy.
But it removes one more hidden universal planner law from the active family-slice path.

## Verification

Focused runtime/audit tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- result:
  - `Ran 26 tests ... OK`

Nearby controller chain safety pass:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py`
- result:
  - `Ran 14 tests ... OK`

Syntax / schema:
- `python3 -m py_compile ...` passed for the touched planner/audit/test files
- `jsonschema.validate(...)` passed for:
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json`
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

## Next seam

Best next move:
- inspect the remaining family-slice inheritance in downstream SIM-side policy
- especially:
  - required SIM family visibility and usage
  - family-owned sim-family selection versus universal defaults
  - any remaining operator-id defaults that still leak planner-global doctrine into family-slice mode
