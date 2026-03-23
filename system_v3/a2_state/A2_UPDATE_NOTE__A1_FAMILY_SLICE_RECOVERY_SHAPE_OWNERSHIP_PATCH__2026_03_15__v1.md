# A2_UPDATE_NOTE__A1_FAMILY_SLICE_RECOVERY_SHAPE_OWNERSHIP_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the reset step where family slices can own graveyard-recovery width and recovery-family shape instead of silently inheriting the planner's fixed rescue template

## Scope

Primary runtime files:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

Contract/model files:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a2_to_a1_family_slice_models.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

Focused regressions:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`

## Problem

Even after the earlier family-slice ownership patches, graveyard-recovery still had two hidden planner-global laws:
- rescue source width was fixed at `6`
- recovery branches always used the same rescue family set when enabled:
  - `BOUNDARY_SWEEP`
  - `PERTURBATION`
  - `COMPOSITION_STRESS`

So family-slice mode still inherited planner-owned rescue shape even when the family slice already carried explicit graveyard and rescue policy.

## What changed

### 1) Family slice contract now supports bounded recovery-shape ownership

The contract/model now supports:
- `rescue_start_conditions.max_rescue_sources`
- `sim_hooks.recovery_sim_families`

This was added to:
- the local Pydantic model
- the draft JSON schema
- the active staged substrate scaffold slice

### 2) Planner now uses family-owned recovery width and family set

In `graveyard_recovery`, `a1_adaptive_ratchet_planner.py` now:
- uses `max_rescue_sources` instead of a hardcoded `6`
- uses `recovery_sim_families` instead of always emitting the full fixed rescue family set

Supported recovery families stay bounded to the currently implemented rescue families:
- `BOUNDARY_SWEEP`
- `PERTURBATION`
- `COMPOSITION_STRESS`

If a family slice does not declare them, the previous planner defaults still remain as fallback.

### 3) Planner now surfaces visible recovery-shape metadata

Planner `self_audit` now includes:
- `family_slice_recovery_sim_families`
- `family_slice_rescue_source_limit`
- `rescue_sim_families_used`
- `rescue_source_count`

So emitted strategy output now shows:
- what the family slice declared
- what rescue family subset was actually used
- how many rescue sources were actually consumed

### 4) Cycle audit now checks recovery-shape visibility

`run_a1_autoratchet_cycle_audit.py` now adds:
- `AUTORATCHET_FAMILY_SLICE_RECOVERY_SIM_FAMILIES_VISIBLE`
- `AUTORATCHET_FAMILY_SLICE_RESCUE_SOURCE_LIMIT_VISIBLE`

That means controller audit can now detect:
- hidden rescue-family drift
- hidden rescue-width drift
- over-width rescue expansion

## Meaning

This closes another planner-owned branch-template seam in family-slice mode:
- family slices can now own recovery width
- family slices can now own rescue-family shape
- controller audit can see and validate the resulting recovery metadata

This does not yet make all graveyard/recovery structure family-owned.
But it removes another silent compatibility-era rescue template from the active family-slice path.

## Verification

Focused runtime tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py`
- result:
  - `Ran 38 tests ... OK`

Local contract/model tests:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`
- result:
  - `Ran 3 tests ... OK`

Direct local audit:
- `'.venv_spec_graph/bin/python' system_v3/tools/audit_a2_to_a1_family_slice_pydantic.py --family-slice-json /Users/joshuaeisenhart/Desktop/Codex\ Ratchet/system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`
- result:
  - `valid: true`

## Next seam

Best next move:
- inspect the remaining graveyard-first structural defaults still acting inside family-slice mode
- especially the extra adversarial branch shape and any still-hidden fixed branch-count assumptions that are not yet family-owned or surfaced in controller audit
