# A2_UPDATE_NOTE__A1_QUEUE_CANDIDATE_REGISTRY_PATH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the new repo-held candidate-registry path for current A1 queue selection, so the selector can read bounded family-slice candidates from one artifact instead of only from ad hoc command-line lists

## Scope

New registry tools:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/create_a1_queue_candidate_registry.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/validate_a1_queue_candidate_registry.py`

Patched selector:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/prepare_current_a1_queue_status_from_candidates.py`

Focused regressions:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_candidate_registry.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_current_a1_queue_status_from_candidates.py`

Doc touch-up:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`

## Problem

The selector now had a fail-closed decision law.

But it was still reading candidates only from command-line inputs.

That meant the controller still lacked one simple repo-held surface for:
- candidate family slices
- optional explicit selected family slice

## What changed

`create_a1_queue_candidate_registry.py` now emits one:
- `A1_QUEUE_CANDIDATE_REGISTRY_v1`

with:
- `candidate_family_slice_jsons`
- `selected_family_slice_json`

`validate_a1_queue_candidate_registry.py` now checks:
- absolute existing paths
- duplicate candidates
- selected-not-in-candidates drift

`prepare_current_a1_queue_status_from_candidates.py` now accepts:
- `--candidate-registry-json`

and uses:
- registry candidates
- registry selected family slice

unless a direct selected family slice is explicitly supplied as an override.

## Meaning

This is the first repo-held candidate substrate for the current A1 queue selector.

The selector can now be driven by:
- zero or more bounded family slices in one registry
- one explicit selected slice when needed

instead of reconstructing candidate state only from direct command arguments.

## Verification

Focused regressions:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_candidate_registry.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_current_a1_queue_status_from_candidates.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py`

Result:
- `Ran 10 tests ... OK`

Syntax:
- `python3 -m py_compile system_v3/tools/create_a1_queue_candidate_registry.py system_v3/tools/validate_a1_queue_candidate_registry.py system_v3/tools/prepare_current_a1_queue_status_from_candidates.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_candidate_registry.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_current_a1_queue_status_from_candidates.py`

The regressions lock:
- registry validity
- registry-selected candidate use
- retained multi-candidate ambiguity guard

## Next seam

The next likely controller seam is whether there should be one active current registry surface in `a2_state`, so the selector can read the live candidate set from a stable current packet instead of a temporary draft path.
