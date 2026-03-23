# A2_UPDATE_NOTE__RUN_REAL_LOOP_COMPATIBILITY_RECOVERY_SIGNAL__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the soft-deprecation / compatibility-path signal for recovery invoked through `run_real_loop.py`

## Scope

This note is bounded to the compatibility decision only.

Patched surface:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_real_loop.py`

Focused regression:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`

## What changed

When `run_real_loop.py` is invoked with:
- `--allow-reconstructed-artifacts`

the emitted machine-readable result now includes:
- `recovery_invocation.recovery_invocation_mode = compatibility_flag`
- `recovery_invocation.compatibility_recovery_flag_used = true`
- `recovery_invocation.preferred_recovery_entrypoint = .../system_v3/tools/run_real_loop_recovery_cycle.py`

When the strict runner is used without recovery:
- `recovery_invocation.recovery_invocation_mode = strict_default`
- `compatibility_recovery_flag_used = false`

## Meaning

This does not break existing callers.

It does make the compatibility choice explicit in the returned payload, so:
- controllers can detect that recovery is happening through the old flag path
- future operator surfaces can steer toward the dedicated recovery entrypoint
- deprecation can happen later without losing visibility now

## Verification

Compile:
- `python3 -m py_compile system_v3/tools/run_real_loop.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_recovery_cycle.py`

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_recovery_cycle.py`
- result:
  - `Ran 5 tests ... OK`

## Next seam

Best next move:
- decide whether controllers/bridges should start warning or refusing on compatibility-flag recovery
- or keep the current soft signal until more callers have been migrated
