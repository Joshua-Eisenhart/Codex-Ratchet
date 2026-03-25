# A2_UPDATE_NOTE__A1_FAMILY_SLICE_PLANNER_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the first live code patch that makes the family-slice reset real in planner/runtime entrypoints

## Scope

This note records the first actual code patch after the family-slice contract/schema work.

It is bounded to:
- planner family-slice input
- autoratchet family-slice pass-through
- control-wrapper family-slice pass-through
- focused regression coverage

It is not an owner-surface doctrine rewrite.

## Patched files

Planner:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`

Autoratchet:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/autoratchet.py`

Direct control wrapper:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_wiggle_control_cycle.py`

Tests:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py`

## What changed

### 1) Planner

The planner now accepts:
- `--family-slice-json`

When present:
- it loads and validates the slice against:
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json`
- slice semantics are guarded for:
  - full-cycle lane presence
  - valid strategy-head presence
  - blocked/witness/residue term exclusion from strategy-head placement
- slice-derived goals outrank `--goal-profile`
- strategy output records family-slice metadata in:
  - `inputs.family_slice_id`
  - `inputs.family_slice_hash`
  - `inputs.family_slice_run_mode`
  - `self_audit.family_slice_present`
  - `self_audit.family_slice_required_lanes`
  - `self_audit.family_slice_strategy_head_terms`

### 2) Autoratchet

`autoratchet.py` now accepts:
- `--family-slice-json`

When present:
- it derives `goal_terms` from the family slice instead of `goal_profile`
- it forwards the same slice to the planner child process
- semantic-gate `required_probe_terms` come from the slice `sim_hooks.required_probe_terms`
- campaign summary now records:
  - `goal_source = family_slice`
  - `family_slice_id`
  - `family_slice_json`
- debate strategy now resolves from family-slice run mode:
  - `SCAFFOLD_PROOF -> balanced`
  - `GRAVEYARD_VALIDITY` upgrades `balanced -> graveyard_first_then_recovery`

### 3) Direct control wrapper

`run_a1_wiggle_control_cycle.py` now accepts:
- `--family-slice-json`

and forwards it to `autoratchet.py`.

## Verification

Compile:
- `python3 -m py_compile ...` passed on the patched tools/tests

Focused tests:
- `python3 -m unittest ...` passed
- result:
  - `Ran 17 tests ... OK`

Most important new checks:
- family-slice goal ordering uses companion floor then strategy head
- blocked strategy head is rejected
- planner CLI family-slice input outranks conflicting `goal-profile`
- autoratchet family-slice probe/gate helpers behave as expected
- control wrapper rejects non-absolute family-slice paths

## Meaning

This is the first live patch where the family-slice reset is no longer only noteware.

It does **not** complete the runtime reset.
But it does move the active seam from:
- profile tuple doctrine

toward:
- explicit bounded A2-derived family input

## Next seam

Best next move:
- tighten `build_a1_autoratchet_controller_result.py` and `run_a1_autoratchet_cycle_audit.py` so controller stop/pass decisions stop depending mainly on generic semantic pass and shallow visibility checks, and start seeing family-slice obligations directly.
