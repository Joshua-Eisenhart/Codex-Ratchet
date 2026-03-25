# A2_UPDATE_NOTE__A1_BUNDLE_QUEUE_SEND_TEXT_COMPANION_PROMOTION__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the bounded rule that bundle-ready A1 queue packets should carry the direct staged send-text companion alongside the staged launch spine

## Scope

Patched queue surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_queue_status_packet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_a1_queue_status_packet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_queue_surface_models.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/render_a1_queue_status_current_note_from_packet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_a1_queue_surfaces_pydantic.py`

Patched tests:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a1_queue_state.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_surface_pydantic_stack.py`

Patched read surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/34_A1_READY_PACKET__v1.md`

## What changed

Before this step:
- bundle-ready queue packets carried `ready_launch_spine_json`
- but they did not also carry the direct send-text-derived companion

Now:
- bundle-ready queue packets also carry `ready_send_text_companion_json`
- packet-only queue packets keep:
  - `ready_send_text_companion_json = ""`
  - `ready_launch_spine_json = ""`

Interpretation:
- the bundle-ready queue surface now exposes both staged bundle-only machine-readable companions
- the direct send-text-derived object is visible without making the controller chase bundle internals first

## Validation rule

Manual validator and local Pydantic model now agree:
- if `ready_surface_kind == A1_LAUNCH_BUNDLE`, require:
  - `ready_bundle_result_json`
  - `ready_send_text_companion_json`
  - `ready_launch_spine_json`
- if `ready_surface_kind == A1_WORKER_LAUNCH_PACKET`, both bundle-only fields must stay empty

The local queue-surface audit now also exposes:
- `has_ready_send_text_companion`
- `has_ready_launch_spine`

## Verification

Focused compile:
- `python3 -m py_compile system_v3/tools/build_a1_queue_status_packet.py system_v3/tools/validate_a1_queue_status_packet.py system_v3/tools/a1_queue_surface_models.py system_v3/tools/render_a1_queue_status_current_note_from_packet.py system_v3/tools/audit_a1_queue_surfaces_pydantic.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a1_queue_state.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_surface_pydantic_stack.py`

Focused queue chain:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a1_queue_state.py`

Result:
- `Ran 13 tests ... OK`

Focused local queue-surface stack:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_surface_pydantic_stack.py`

Result:
- `Ran 6 tests ... OK`

## Current interpretation

The bundle-ready queue packet is now a better compact handoff surface:
- bundle result pointer
- direct send-text companion pointer
- compact staged launch spine pointer

That is enough for the queue/current-note layer to explain the bundle path without reopening raw builder assumptions.

## Next seam

The next useful move is to decide whether the active current queue packet should ever be refreshed into one admitted bundle-ready example in `a2_state`, or whether bundle-ready examples should remain staged/non-active until a real selected candidate exists.
