# A2_UPDATE_NOTE__A1_CURRENT_QUEUE_SELECTOR_FAIL_CLOSED__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the fail-closed selector step where the controller can now derive the current A1 queue answer from zero, one, or many family-slice candidates without inventing a hidden ranking

## Scope

New selector wrapper:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/prepare_current_a1_queue_status_from_candidates.py`

Focused regression:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_current_a1_queue_status_from_candidates.py`

Patched process/routing surfaces:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/THREAD_AND_AUTOMATION_PROCESS_FLOWS__2026_03_11__v1.md`

## Problem

The queue-status packet layer and current-note wrapper now existed.

But the selector policy was still missing.

So there was still no actual tool saying:
- zero candidate family slices -> `NO_WORK`
- one candidate family slice -> ready
- many candidate family slices -> explicit selection required or stop

Without that, the controller still risked reintroducing hidden ranking by memory or vibes.

## What changed

`prepare_current_a1_queue_status_from_candidates.py` now wraps the queue-status/current-note surfaces layer.

It implements one bounded fail-closed selector:
- if zero candidates exist, it emits `NO_WORK`
- if exactly one candidate exists, it selects it
- if many candidates exist, it requires one explicit `--selected-family-slice-json`
- otherwise it stops with `ambiguous_family_slice_candidates`

Then it reuses:
- `prepare_a1_queue_status_surfaces.py`

to build the machine-readable queue packet and the current-note render from the chosen outcome.

## Meaning

This is the first actual current-queue selector, even though it is still a simple controller wrapper.

The key part is not sophistication.
The key part is that it does **not** invent policy when many bounded candidates exist.

It either:
- has no work
- has exactly one work item
- or demands an explicit choice

## Verification

Focused regression:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_current_a1_queue_status_from_candidates.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py`

Result:
- `Ran 8 tests ... OK`

Syntax:
- `python3 -m py_compile system_v3/tools/prepare_current_a1_queue_status_from_candidates.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_current_a1_queue_status_from_candidates.py`

The regression locks:
- no-candidate fallback to `NO_WORK`
- one-candidate automatic selection
- multi-candidate fail-closed ambiguity

## Next seam

The next controller choice is whether there should now be one repo-held current candidate registry for bounded family slices, so this selector can read candidates from a stable artifact instead of only command-line inputs.
