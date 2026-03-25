# A2_UPDATE_NOTE__RUN_REAL_LOOP_RECOVERY_ENTRYPOINT__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the dedicated recovery entrypoint added after the `run_real_loop` recovery-module split

## Scope

This note is bounded to the operator-facing entrypoint change only.

It records the addition of:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_real_loop_recovery_cycle.py`

## What changed

Before this patch:
- recovery mode existed mainly as a flag on `run_real_loop.py`

After this patch:
- strict/default path:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_real_loop.py`
- explicit recovery path:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_real_loop_recovery_cycle.py`

The new entrypoint:
- imports `run_real_loop.main`
- forces `--allow-reconstructed-artifacts`
- avoids duplicating the flag if already present

## Verification

Compile:
- `python3 -m py_compile system_v3/tools/run_real_loop.py system_v3/tools/run_real_loop_recovery.py system_v3/tools/run_real_loop_recovery_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_recovery_cycle.py`

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_recovery_cycle.py`
- result:
  - `Ran 5 tests ... OK`

Wrapper regressions:
- injects recovery flag when missing
- does not duplicate recovery flag when already present

## Meaning

This is not the final recovery architecture.

But it is a real reset improvement because:
- strict runtime and recovery runtime now have separate command surfaces
- operator intent is clearer
- future recovery-only policy can evolve without making strict runtime flags carry the full story

## Next seam

Best next move:
- audit callers and notes that still point operators at `run_real_loop.py --allow-reconstructed-artifacts`
- switch them to the dedicated recovery entrypoint where appropriate
