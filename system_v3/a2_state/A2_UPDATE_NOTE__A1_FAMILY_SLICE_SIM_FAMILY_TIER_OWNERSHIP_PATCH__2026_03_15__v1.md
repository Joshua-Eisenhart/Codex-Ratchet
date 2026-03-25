# A2_UPDATE_NOTE__A1_FAMILY_SLICE_SIM_FAMILY_TIER_OWNERSHIP_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the reset step where family slices can own SIM-family branch tiers instead of silently inheriting the planner's hardcoded family-tier defaults

## Scope

Primary runtime files:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

Contract/model files:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a2_to_a1_family_slice_models.py`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

Focused regressions:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`

## Problem

After the earlier family-slice reset work, one more planner-global law was still active inside family-slice mode:
- `BOUNDARY_SWEEP`
- `PERTURBATION`
- `ADVERSARIAL_NEG`
- `COMPOSITION_STRESS`

all still inherited hardcoded branch tiers inside the planner.

That meant:
- family slices could own goal tiers and probe terms
- but family-specific branch pressure still used hidden planner-owned SIM-family tier defaults

So the planner still had another non-obvious way to override family-local campaign shape.

## What changed

### 1) Family slice contract now supports `sim_family_tiers`

`sim_hooks` can now carry an optional:
- `sim_family_tiers`

This was added to:
- the draft JSON schema
- the local Pydantic model
- the active staged substrate scaffold slice

### 2) Planner now uses family-owned SIM-family tiers when present

`a1_adaptive_ratchet_planner.py` now:
- reads `sim_hooks.sim_family_tiers`
- validates family names and tier tokens
- uses those family-owned tiers for family-slice-controlled branch SIMs

This applies to:
- main family alternatives
- graveyard-first adversarial expansion
- graveyard-recovery rescue branches

If a family slice does not declare them, the previous planner defaults still remain as compatibility/default fallback.

### 3) Planner now surfaces visible family-tier usage

Planner `self_audit` now includes:
- `family_slice_sim_family_tiers`
- `sim_family_tier_map`

So the emitted strategy now shows:
- what the slice declared
- what tiers were actually emitted per SIM family

### 4) Cycle audit now checks the visible family-tier map

`run_a1_autoratchet_cycle_audit.py` now adds:
- `AUTORATCHET_FAMILY_SLICE_SIM_FAMILY_TIERS_VISIBLE`

That means controller audit can now detect:
- missing visible SIM-family tier data
- family-slice tier declarations that never reached emitted SIM specs

## Meaning

This is another rewrite-first improvement in the active A1 core:
- family slices now own one more part of branch behavior
- hidden planner SIM-family tier defaults are reduced
- controller audit can see and verify the visible family-tier map

It does not remove all planner-global branch template law.
But it closes another silent inheritance seam inside family-slice mode.

## Verification

Focused runtime tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py`
- result:
  - `Ran 37 tests ... OK`

Local contract/model tests:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`
- result:
  - `Ran 3 tests ... OK`

Direct local audit:
- `'.venv_spec_graph/bin/python' system_v3/tools/audit_a2_to_a1_family_slice_pydantic.py --family-slice-json /home/ratchet/Desktop/Codex\ Ratchet/system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`
- result:
  - `valid: true`

## Next seam

Best next move:
- inspect the remaining branch-template defaults still acting inside family-slice mode
- especially hardcoded rescue/graveyard structural shape that is still planner-owned even after probe, goal-priority, and SIM-family tier ownership were surfaced
