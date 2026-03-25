# A2_UPDATE_NOTE__RUN_REAL_LOOP_CONTROLLER_SIGNAL_CONSUMER_HARDENING__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the first downstream consumer hardening for real-loop controller-review signals

## Scope

This note is bounded to:
- the controller-review signal emitted by `run_real_loop.py`
- the first downstream consumer patched to respect that signal

Patched surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_bridge_determinism_pair.py`

Focused regressions:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_bridge_determinism_pair.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_recovery_cycle.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_bridge_from_work.py`

## What changed

`run_bridge_determinism_pair.py` now treats:
- `controller_review_required = true`

on either underlying `run_real_loop.py` result as a determinism-pair failure condition.

This means the pair runner no longer reports clean determinism when one side already says:
- `controller_review_decision = MANUAL_REVIEW_REQUIRED`

It now records:
- `compare.manual_review_required`

and fails the pair report if that signal is present.

## Meaning

The controller-review signal is no longer stranded in the strict runner JSON.

At least one real downstream consumer now respects the distinction between:
- lower-loop pass/fail
- controller/operator review requirement

That makes the recent recovery-path reset more coherent:
- legacy compatibility-path recovery is controller-visible
- first downstream consumer does not ignore that visibility

## Verification

Compile:
- `python3 -m py_compile system_v3/tools/run_bridge_determinism_pair.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_bridge_determinism_pair.py system_v3/tools/run_real_loop.py system_v3/tools/run_real_loop_recovery_cycle.py system_v3/tools/run_real_loop_bridge_from_work.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_recovery_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_bridge_from_work.py`

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_bridge_determinism_pair.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_recovery_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_bridge_from_work.py`
- result:
  - `Ran 13 tests ... OK`

## Next seam

Best next move:
- audit any remaining orchestration helpers that shell out to `run_real_loop.py`
- if they can surface or suppress compatibility-path recovery, make them consume:
  - `controller_review_required`
  - `controller_review_decision`
  - `controller_review_reason`
