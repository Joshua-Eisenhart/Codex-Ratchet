# A2_UPDATE_NOTE__RUN_REAL_LOOP_SOFT_RECOVERY_WARNING__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the soft-policy upgrade for compatibility-path recovery on the real-loop strict runner and bridge

## Scope

This note is bounded to warning behavior only.

Patched surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_real_loop.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_real_loop_bridge_from_work.py`

Focused regressions:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_recovery_cycle.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_bridge_from_work.py`

## What changed

### 1) Machine-readable warning in strict runner output

When `run_real_loop.py` is invoked with:
- `--allow-reconstructed-artifacts`

the emitted result now includes:
- `warnings = ["COMPATIBILITY_RECOVERY_PATH_USED"]`

alongside the existing `recovery_invocation` metadata that points to the preferred recovery entrypoint.

### 2) Bridge-layer stderr guidance

When `run_real_loop_bridge_from_work.py` is invoked with:
- `--allow-reconstructed-artifacts`

it now emits a warning directing the caller to:
- `system_v3/tools/run_real_loop_recovery_bridge_from_work.py`

## Meaning

This is still a soft policy:
- compatibility path continues to work
- no caller is refused yet

But the path is no longer silent:
- machine readers can detect it
- bridge users get explicit guidance

## Verification

Compile:
- `python3 -m py_compile system_v3/tools/run_real_loop.py system_v3/tools/run_real_loop_bridge_from_work.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_recovery_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_bridge_from_work.py`

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_recovery_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_bridge_from_work.py`
- result:
  - `Ran 7 tests ... OK`

## Next seam

Best next move:
- decide whether controller-facing tools should escalate compatibility-path recovery to `WARN`/`MANUAL_REVIEW_REQUIRED`
- or keep the present soft warning until more live callers have migrated
