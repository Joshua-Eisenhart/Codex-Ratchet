# A2_UPDATE_NOTE__RUN_REAL_LOOP_CONTROLLER_SIGNAL_REPORT_PROPAGATION__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the propagation of real-loop controller-review details into the first downstream pair report

## Scope

This note is bounded to:
- `run_real_loop.py` controller-review fields
- `run_bridge_determinism_pair.py` as the first downstream report surface

Patched surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_bridge_determinism_pair.py`

Focused regressions:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_bridge_determinism_pair.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_recovery_cycle.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_bridge_from_work.py`

## What changed

`run_bridge_determinism_pair.py` previously propagated only:
- `compare.manual_review_required`

It now also preserves per-run manual-review detail objects:
- `compare.manual_review_a`
- `compare.manual_review_b`

Each detail object contains:
- `required`
- `decision`
- `reason`

So the first downstream consumer report now carries the same controller distinction with more fidelity:
- whether review was required
- what decision was requested
- why

## Meaning

The controller-review signal is now:
- emitted by `run_real_loop.py`
- preserved by the determinism-pair consumer
- available to any later report/gate consumer without needing to rediscover it from raw runner JSON

That is better than a bare boolean because later surfaces can distinguish:
- legacy compatibility recovery manual review
- future review-required categories, if more are added

## Verification

Compile:
- `python3 -m py_compile system_v3/tools/run_bridge_determinism_pair.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_bridge_determinism_pair.py`

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_bridge_determinism_pair.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_recovery_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_bridge_from_work.py`
- result:
  - `Ran 14 tests ... OK`

## Next seam

Best next move:
- audit whether any other report builders or controller gates should consume the propagated pair-level manual-review detail
- if not, freeze this seam and return to the broader A1/runtime reset targets
