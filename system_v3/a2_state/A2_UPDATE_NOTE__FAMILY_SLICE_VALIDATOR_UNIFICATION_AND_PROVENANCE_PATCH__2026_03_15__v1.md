# A2_UPDATE_NOTE__FAMILY_SLICE_VALIDATOR_UNIFICATION_AND_PROVENANCE_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the patch that closes the highest-priority split-validator seam on family-slice prep and starts carrying validation provenance through emitted packet/bundle/queue surfaces

## Scope

Primary runtime/prep files:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/family_slice_runtime_validation.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_launch_packet_from_family_slice.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/prepare_a1_launch_bundle_from_family_slice.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/prepare_codex_launch_bundle.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_queue_status_packet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_a1_worker_launch_packet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_a1_queue_status_packet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_worker_launch_packet_models.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_queue_surface_models.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/render_a1_queue_status_current_note_from_packet.py`

Focused regressions:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_worker_launch_packet_from_family_slice.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_launch_bundle_from_family_slice.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_packet_pydantic_stack.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_surface_pydantic_stack.py`

## Problem

The highest-priority recent review finding was:
- family-slice prep/queue surfaces could accept a slice through the manual JSON schema path
- while the live runtime planner would reject the same slice later

This happened because:
- `jsonschema` prep only checked the hand-written schema
- stricter semantic rules lived elsewhere in the runtime/Pydantic path
- emitted artifacts did not record which validator path actually accepted the slice

## What changed

### 1) `jsonschema` prep now also uses live runtime semantics

A new helper:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/family_slice_runtime_validation.py`

now calls the live planner semantic validator.

So `build_a1_worker_launch_packet_from_family_slice.py` no longer treats:
- hand-written JSON schema success

as sufficient by itself.

In `jsonschema` mode it now requires:
- schema validity
- plus the same runtime semantic family-slice checks used by the planner

This closes the highest-priority accept-now / fail-later seam for the launch-packet path.

### 2) Validation provenance is now carried in emitted artifacts

Emitted A1 packet/bundle/queue surfaces now carry:
- `family_slice_validation_requested_mode`
- `family_slice_validation_resolved_mode`
- `family_slice_validation_source`

Current source values:
- `jsonschema_plus_runtime_semantics`
- `local_pydantic_audit`

These now survive through:
- A1 worker launch packet
- Codex launch bundle result for A1 worker packets
- family-slice launch bundle result wrapper
- A1 queue status packet
- current queue note render

### 3) Validators and local Pydantic models now accept/check those provenance fields

The packet and queue validators now:
- validate allowed requested/resolved/source values if present
- reject impossible combinations such as mismatched explicit requested/resolved modes

The local Pydantic object models for:
- A1 worker launch packet
- A1 queue status packet

were widened so the local object stack remains compatible with the new packet shape.

## Meaning

This does not fully unify every validator in the system.
The hand-written JSON schema still needs deeper alignment with the live model.

But the most important system seam is now materially better:
- the default prep path is much less likely to admit a family slice the live runtime will later reject
- emitted ready surfaces now preserve how validation actually happened

That makes queue/launch/controller artifacts more trustworthy and easier to reload/debug.

## Focused verification

Compile:
- `python3 -m py_compile system_v3/tools/family_slice_runtime_validation.py system_v3/tools/build_a1_worker_launch_packet_from_family_slice.py system_v3/tools/validate_a1_worker_launch_packet.py system_v3/tools/a1_worker_launch_packet_models.py system_v3/tools/prepare_codex_launch_bundle.py system_v3/tools/prepare_a1_launch_bundle_from_family_slice.py system_v3/tools/build_a1_queue_status_packet.py system_v3/tools/validate_a1_queue_status_packet.py system_v3/tools/a1_queue_surface_models.py system_v3/tools/render_a1_queue_status_current_note_from_packet.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_worker_launch_packet_from_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_launch_bundle_from_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py`

Focused unittest bundle:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_worker_launch_packet_from_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_launch_bundle_from_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py`
- result:
  - `Ran 17 tests ... OK`

Local Pydantic stack checks:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_packet_pydantic_stack.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_surface_pydantic_stack.py`
- result:
  - `Ran 9 tests ... OK`

## Next seam

Best next move remains:
- align the hand-written family-slice schema with the live model/runtime rules more deeply
- then harden queue bundle integrity so staged companion artifacts must cohere, not merely exist
