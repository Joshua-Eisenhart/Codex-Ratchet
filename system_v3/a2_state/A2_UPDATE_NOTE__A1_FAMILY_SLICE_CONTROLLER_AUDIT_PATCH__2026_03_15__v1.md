# A2_UPDATE_NOTE__A1_FAMILY_SLICE_CONTROLLER_AUDIT_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the follow-on patch where family-slice obligations entered cycle audit and controller stop/continue logic

## Scope

This note records the next reset step after the planner/runtime family-slice patch.

It is bounded to:
- cycle audit visibility of family-slice obligations
- controller result handling of family-slice obligation failures
- focused regression coverage

## Patched files

Audit:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

Controller result:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_autoratchet_controller_result.py`

Tests:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py`

## What changed

### 1) Cycle audit

`run_a1_autoratchet_cycle_audit.py` now inspects the latest emitted strategy ZIP and compares it against the family-slice file recorded in `campaign_summary.json` when:
- `goal_source == family_slice`

New family-slice checks include:
- family-slice JSON path present
- family-slice id present
- campaign family-slice id matches loaded family-slice id
- latest strategy ZIP present
- latest strategy `inputs.family_slice_id` matches campaign family-slice id
- latest strategy self-audit exposes required lanes from the family slice
- latest strategy self-audit exposes strategy-head terms from the family slice
- family-slice SIM probe-term obligations are declared

The audit now emits:
- `goal_source`
- `family_slice_expected`
- `family_slice_id`
- `family_slice_json`
- `family_slice_obligations_status`
- `latest_strategy_zip_path`

### 2) Controller result

`build_a1_autoratchet_controller_result.py` now reads:
- `family_slice_expected`
- `family_slice_id`
- `family_slice_obligations_status`

and will not stop on generic semantic gate pass if:
- family-slice obligations are expected
- but family-slice obligations did not pass

In that case:
- `controller_decision = MANUAL_REVIEW_REQUIRED`
- `controller_decision_reason = family_slice_obligations_failed`

## Verification

Compile:
- `python3 -m py_compile ...` passed

Focused tests:
- `python3 -m unittest ...` passed
- result:
  - `Ran 21 tests ... OK`

New regression points:
- audit fails when family-slice metadata in the latest strategy ZIP mismatches the recorded family slice
- controller does not stop on semantic-gate pass when family-slice obligations are marked failed

## Meaning

This patch reduces one specific reset risk:
- controller/audit no longer treat generic semantic pass as sufficient when a family-slice campaign has extra bounded obligations

It still does not complete the doctrinal reset.
But it closes the first obvious controller blind spot after introducing family-slice input.

## Next seam

Best next move:
- either push family-slice awareness into `run_real_loop.py` only after its fail-closed split
- or tighten the audit further so it checks more of the emitted branch-family structure instead of only family-slice metadata visibility
