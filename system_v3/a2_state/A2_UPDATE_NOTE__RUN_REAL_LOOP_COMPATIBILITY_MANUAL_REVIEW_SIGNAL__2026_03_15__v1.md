# A2_UPDATE_NOTE__RUN_REAL_LOOP_COMPATIBILITY_MANUAL_REVIEW_SIGNAL__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the controller-grade escalation for legacy compatibility-path recovery on the real-loop strict runner

## Scope

This note is bounded to distinguishing:
- the preferred dedicated recovery entrypoint
- the legacy compatibility recovery flag on the strict runner

Patched surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_real_loop.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_real_loop_recovery_cycle.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_real_loop_bridge_from_work.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/22_RUN_SURFACE_TEMPLATE_AND_SCAFFOLDER_CONTRACT.md`

Focused regressions:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_recovery_cycle.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_bridge_from_work.py`

## What changed

### 1) Preferred recovery entrypoint is now distinguishable

`run_real_loop_recovery_cycle.py` no longer arrives at `run_real_loop.main()` looking identical to:
- `run_real_loop.py --allow-reconstructed-artifacts`

It now injects:
- `--recovery-invocation-source dedicated_recovery_entrypoint`

so the preferred recovery path is not mislabeled as the legacy compatibility path.

### 2) Legacy compatibility-path recovery now carries controller-grade review metadata

When `run_real_loop.py` is invoked through:
- `--allow-reconstructed-artifacts`

without the dedicated recovery entrypoint marker, the emitted result now includes:
- `controller_review_required = true`
- `controller_review_decision = "MANUAL_REVIEW_REQUIRED"`
- `controller_review_reason = "compatibility_recovery_path_used"`

This keeps:
- lower-loop runtime result truth

separate from:
- controller/operator decision truth

so the run can still report its actual gate/sprawl outcome without pretending the legacy recovery path is controller-clean.

### 3) Bridge warning is stronger

`run_real_loop_bridge_from_work.py` now prefixes the old compatibility-path warning with:
- `MANUAL_REVIEW_REQUIRED`

to make the operator consequence visible even when a caller only sees bridge stderr.

## Meaning

The policy is now:
- preferred recovery path: explicit recovery entrypoint, no legacy-path marker
- legacy compatibility path: still works, but is controller-visible as manual-review-required

This is a better fit for the recent reset:
- strict/default runtime stays fail-closed
- explicit recovery remains available
- old compatibility recovery is no longer just a soft warning

## Verification

Compile:
- `python3 -m py_compile system_v3/tools/run_real_loop.py system_v3/tools/run_real_loop_recovery_cycle.py system_v3/tools/run_real_loop_bridge_from_work.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_recovery_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_bridge_from_work.py`

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_recovery_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop_bridge_from_work.py`
- result:
  - `Ran 10 tests ... OK`

## Next seam

Best next move:
- audit any controller or orchestration surfaces that consume `run_real_loop.py` output and make them respect:
  - `controller_review_required`
  - `controller_review_decision`
- then decide whether the legacy compatibility path should eventually become refusal-only outside explicitly waived maintenance flows
