# A2_UPDATE_NOTE__RUN_REAL_LOOP_ARTIFACT_STRICTNESS_MAP__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the current strict-required vs projection classification for `run_real_loop.py`

## Scope

This note is bounded to the outer runtime loop artifact classes touched by:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_real_loop.py`

It records which artifact classes are currently treated as:
- strict-required canon inputs
- visible direct-consumer surfaces
- reconstructable recovery projections

## Current classification

### Strict-required canon inputs

These now fail the loop in default strict mode if missing:
- canonical events
- canonical graveyard records

Reason:
- replay pair derivation depends on canonical event logs
- graveyard integrity gate otherwise risks validating reconstructed kill records

### Visible direct-consumer surfaces

These do not need local reconstruction to be usable by the current gate stack:
- export blocks visible in `zip_packets/*_A0_TO_B_EXPORT_BATCH_ZIP.zip`
- SIM evidence visible in `zip_packets/*_SIM_TO_A0_SIM_RESULT_ZIP.zip`

Reason:
- `run_a0_compile_gate.py` already accepts zip-native export blocks
- `run_evidence_ingest_gate.py` already scans SIM result ZIPs directly

So these are not currently in the strict-required fail set.

### Reconstructable recovery projections

These remain recovery-mode projections when:
- `--allow-reconstructed-artifacts`

is explicitly set:
- export compile/dependency/preflight reports
- log event shard from ZIP headers
- graveyard records from runtime state
- SIM evidence pack from SIM manifests or SIM ZIPs
- tapes from visible export blocks

These projections are still useful for:
- operator visibility
- legacy consumers
- bounded recovery/debugging

But they are no longer default truth surfaces.

## Important boundary

Recovery mode does not imply fake completeness.

Example:
- if no canonical SIM evidence exists in manifests or SIM ZIPs
- `run_real_loop.py` now reports `MISSING_CANONICAL_SIM_EVIDENCE`
- instead of pretending recovery happened anyway

So the recovery path is explicit but still fail-aware.

## Verification

Focused tests:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`

Covered now:
- strict mode fails closed on missing canonical events and graveyard records
- recovery mode is visible at top level through:
  - `recovery_mode_active`
  - `reconstructed_artifact_classes`
- recovery mode does not claim reconstructed SIM evidence when no canonical SIM source exists

## Meaning

This is the current minimal fence against phantom verification in `run_real_loop.py`:
- make only the canon inputs strict-required
- allow projections only in explicit recovery mode
- expose reconstruction usage in machine-readable output

## Next seam

Best next move:
- keep shrinking `run_real_loop.py` until repair/recovery behavior can live in a separate helper or entrypoint
- and avoid letting the strict runtime path silently accumulate more projection logic again
