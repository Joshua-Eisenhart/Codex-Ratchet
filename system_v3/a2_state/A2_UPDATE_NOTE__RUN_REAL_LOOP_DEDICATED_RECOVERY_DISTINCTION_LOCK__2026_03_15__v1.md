# A2_UPDATE_NOTE__RUN_REAL_LOOP_DEDICATED_RECOVERY_DISTINCTION_LOCK__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the regression lock that the preferred dedicated recovery path does not inherit the legacy compatibility-path manual-review marker

## Scope

This note is bounded to the distinction between:
- preferred recovery entrypoint usage
- legacy compatibility-path recovery on the strict runner

Focused regression:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`

## What changed

Added a focused integration-style regression around `run_real_loop.main()` that exercises recovery mode with:
- `--allow-reconstructed-artifacts`
- `--recovery-invocation-source dedicated_recovery_entrypoint`

The test locks that the dedicated recovery path:
- returns `status = PASS` in the stubbed recovery scenario
- emits `recovery_invocation.recovery_invocation_mode = dedicated_recovery_entrypoint`
- does not mark `compatibility_recovery_flag_used`
- emits no compatibility warnings
- does not set:
  - `controller_review_required`
  - `controller_review_decision`
  - `controller_review_reason`

## Meaning

This closes the last ambiguity in the recent reset:
- legacy compatibility recovery is controller-review-required
- preferred dedicated recovery is not mislabeled as legacy compatibility recovery

So the code path distinction is now locked at the emitted result level, not only at helper-function level.

## Verification

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_recovery_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_bridge_from_work.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_bridge_determinism_pair.py`

## Next seam

Best next move:
- freeze the `run_real_loop` recovery-policy seam unless a real downstream consumer still ignores the dedicated/legacy distinction
- return to broader A1/runtime reset work if no such consumer appears
