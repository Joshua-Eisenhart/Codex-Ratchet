# A2_UPDATE_NOTE__A1_FAMILY_SLICE_SCHEMA_ALIGNMENT_AND_PYDANTIC_REFRESH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the patch that tightens the hand-written family-slice schema to the live SIM-family/SIM-tier law and refreshes the committed generated Pydantic schema artifact

## Scope

Primary contract surfaces:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`

Live model / emit path:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a2_to_a1_family_slice_models.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/emit_a2_to_a1_family_slice_pydantic_schema.py`

Focused regressions:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_worker_launch_packet_from_family_slice.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_launch_bundle_from_family_slice.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`

## Problem

After validator unification, the biggest remaining family-slice contract problem was:
- the hand-written JSON schema still allowed generic uppercase tokens where the live model/runtime used strict SIM-family and SIM-tier sets

That meant the schema path was still looser than the real contract on:
- `required_sim_families`
- `term_sim_tiers`
- `sim_family_tiers`
- `recovery_sim_families`
- `expected_tier_floor`

There was also still a reload drift problem:
- the committed generated Pydantic schema artifact lagged behind the live model

## What changed

### 1) Hand-written family-slice schema is now tighter on SIM-family and SIM-tier law

`A2_TO_A1_FAMILY_SLICE_v1.schema.json` now has explicit defs for:
- `simTierName`
- `requiredStressSimFamilyName`
- `requiredStressSimFamilyList`
- `recoverySimFamilyName`
- `recoverySimFamilyList`

So the manual schema now constrains:
- `required_sim_families`
  - exact stress-family set only
  - `BASELINE`
  - `BOUNDARY_SWEEP`
  - `PERTURBATION`
  - `ADVERSARIAL_NEG`
  - `COMPOSITION_STRESS`
- `term_sim_tiers`
  - values must be one of `T0_ATOM` through `T6_WHOLE_SYSTEM`
- `sim_family_tiers`
  - keys must be required stress-family names
  - values must be known SIM tiers
- `recovery_sim_families`
  - only `BOUNDARY_SWEEP`, `PERTURBATION`, `COMPOSITION_STRESS`
- `expected_tier_floor`
  - must be a known SIM tier

This does not encode every live cross-field rule.
But it removes the biggest remaining “generic token” looseness from the schema path.

### 2) The committed generated Pydantic schema artifact was refreshed

Refreshed file:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`

The fresh emit now includes later-added model fields such as:
- `max_rescue_sources`
- `sim_family_tiers`
- `recovery_sim_families`

### 3) Freshness is now protected by test

`test_a2_to_a1_family_slice_pydantic_stack.py` now compares:
- a fresh emitted schema
- against the committed generated schema artifact

So the repo-held emitted schema cannot silently drift again without failing the local stack test.

## Meaning

The family-slice contract is now materially cleaner:
- the hand-written schema is closer to the live runtime/model law
- the committed generated schema is no longer stale
- the hand-written path now rejects several bad SIM-family/tier shapes before runtime semantics are even consulted

This is still not total contract convergence.
Live cross-field rules remain richer than JSON schema alone.

But the main split-contract seam is now significantly smaller.

## Focused verification

Manual schema still accepts the active staged family slice:
- `python3` + `jsonschema` check against `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`
- result:
  - `valid`

Focused packet/bundle regressions:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_worker_launch_packet_from_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_launch_bundle_from_family_slice.py`
- result:
  - `Ran 11 tests ... OK`

Local Pydantic stack regressions:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_to_a1_family_slice_pydantic_stack.py`
- result:
  - `Ran 4 tests ... OK`

## Next seam

Best next move stays in the real system core:
- keep shrinking remaining planner-global defaults inside family-slice mode
- especially graveyard-first branch-shape inheritance that still behaves like hidden universal law
