# A2_UPDATE_NOTE__RUN_REAL_LOOP_STRICT_FAIL_CLOSED_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the strict-by-default `run_real_loop.py` repair so reload does not lose the phantom-verification reset seam

## Scope

This note is bounded to the `run_real_loop.py` strictification pass.

It does not retune A1 doctrine.
It only records the fail-closed split between:
- default runtime execution
- explicit recovery/reconstruction mode

## Patched files

Runtime loop:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_real_loop.py`

Focused regression:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`

## What changed

### 1) Strict mode is now the default

`run_real_loop.py` now exposes:
- `--allow-reconstructed-artifacts`

Without that flag, the loop no longer synthesizes runtime artifacts by default.

### 2) Reconstruction helpers now report mode explicitly

The helper surfaces for:
- export reports
- events
- graveyard records
- SIM evidence packs
- tapes

now emit mode/status summaries such as:
- `PRESERVED_EXISTING`
- `STRICT_NO_RECONSTRUCTION`
- `MISSING_CANONICAL_EVENTS`
- `MISSING_CANONICAL_GRAVEYARD_RECORDS`
- `VISIBLE_IN_SIM_ZIPS_ONLY`
- `RECONSTRUCTED_FROM_*`

### 3) Missing canonical artifacts now stop the loop before gates

When strict mode sees missing required runtime artifacts, the loop returns:
- `status = FAIL`
- `stage = MISSING_REQUIRED_RUNTIME_ARTIFACTS`

and exits before:
- phase gate pipeline
- sprawl guard

The currently enforced required strict artifacts are:
- canonical events
- canonical graveyard records

### 4) Export-record split handling was repaired

`_extract_export_records(...)` now correctly preserves split `export_block_*.txt` surfaces without using the old tuple shape.

## Verification

Compile:
- `python3 -m py_compile system_v3/tools/run_real_loop.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`
- result:
  - `Ran 2 tests ... OK`

Covered regressions:
- split export-block sequences remain readable after the dict-shape conversion
- strict mode fails closed before gate execution when canonical events and graveyard records are missing

## Meaning

This closes the most immediate phantom-verification seam in `run_real_loop.py`:
- the loop no longer quietly reconstructs required artifacts in default mode and then validates the run with those reconstructions

Recovery-mode reconstruction still exists, but it is now explicit and operator-opt-in.

## Next seam

Best next move:
- review whether more artifact classes should become strict-required
- then continue shrinking `run_real_loop.py` so repair/recovery behavior is separated even more clearly from default runtime execution
