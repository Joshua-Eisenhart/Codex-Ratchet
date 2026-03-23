# A2_UPDATE_NOTE__RUN_REAL_LOOP_RECOVERY_MODULE_SPLIT__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the structural split between strict runtime execution and recovery/projection helpers for `run_real_loop.py`

## Scope

This note is bounded to the code structure change only.

It records that the recovery/projection machinery has been extracted out of:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_real_loop.py`

into:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_real_loop_recovery.py`

## What moved

The extracted helper module now owns the recovery/projection path for:
- export-record extraction
- reconstructed compile/dependency/preflight reports
- event-log recovery from ZIP headers
- graveyard-record recovery from runtime state
- SIM-evidence-pack recovery
- tape recovery
- reconstructed artifact class reporting

`run_real_loop.py` remains the strict outer runner that:
- initializes the run surface
- runs autoratchet
- computes replay reports
- decides strict failure on missing canonical artifacts
- optionally calls recovery helpers when `--allow-reconstructed-artifacts` is set
- runs the gate pipeline and sprawl guard

## Meaning

This does not yet create a separate recovery entrypoint.

But it is a real structural reset because:
- strict runtime flow is easier to audit
- recovery logic is visibly isolated in code
- future extraction into a separate repair/recovery entrypoint is now much simpler

## Verification

Compile:
- `python3 -m py_compile system_v3/tools/run_real_loop.py system_v3/tools/run_real_loop_recovery.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`
- result:
  - `Ran 3 tests ... OK`

## Next seam

Best next move:
- add one explicit recovery-mode entrypoint or helper wrapper around `run_real_loop_recovery.py`
- so the default runtime path becomes even thinner and recovery behavior stops being primarily flag-driven
