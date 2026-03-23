# A2_UPDATE_NOTE__THREADB_HELPER_ADMISSION_AND_INTAKE_CHAIN_RELEASE__2026_03_15__v1

Status: `DERIVED_A2`
Date: 2026-03-15

## What changed

Two linked changes landed:

1. active A2 now carries the bounded helper:
   - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_THREADB_CONSEQUENCE_SUBSET__SOURCE_BOUND_HELPER__2026_03_15__v1.md`
2. the live intake Thread B chain has been released from `system_v3/a2_high_entropy_intake_surface` into quarantine

## Why

This removes an unnecessarily broad live intake dependency from active A2 while preserving the exact bounded Thread B consequence subset that active A2 still uses.

## Consequence

Active A2 now relies on:
- one bounded helper surface in `a2_state`
- detailed non-owner provenance companions in `work/audit_tmp`

It no longer needs the live intake Thread B chain to remain resident for this concern.

## Retention Result

Moved to quarantine:
1. `BATCH_A2MID_bootpack_thread_b_kernel_gating__v1`
2. `BATCH_A2MID_CONTRADICTION_threadb_kernel_authority__v1`

Destination:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/archive/intake_retention_quarantine/2026-03-15__THREADB_KERNEL_CHAIN__2026_03_15`

## Guardrail

This is still not a doctrine expansion.

The helper preserves:
- bounded consequence subset only
- source-bound meaning
- deliberate non-promotion of Thread B drift specifics
