# A2_UPDATE_NOTE__A1_BUNDLE_QUEUE_LAUNCH_SPINE_PROMOTION__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the bounded rule that bundle-ready A1 queue packets should carry the staged worker launch spine

## Scope

Patched bundle/queue tools:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/prepare_a1_launch_bundle_from_family_slice.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a1_queue_status_packet.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/validate_a1_queue_status_packet.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a1_queue_surface_models.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/render_a1_queue_status_current_note_from_packet.py`

Patched tests:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_launch_bundle_from_family_slice.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a1_queue_state.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_surface_pydantic_stack.py`

Patched read surfaces:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/34_A1_READY_PACKET__v1.md`

## What changed

Before this step:
- bundle prep stopped at packet + gate result + send text + handoff
- the queue packet could point at `ready_bundle_result_json`
- but there was no compact staged worker-spine pointer on the ready queue surface

Now:
- `prepare_a1_launch_bundle_from_family_slice.py` also emits:
  - `send_text_companion_json`
  - `launch_spine_json`
- bundle-mode queue packets now carry:
  - `ready_launch_spine_json`
- packet-only queue packets stay clean and keep:
  - `ready_launch_spine_json = ""`

Interpretation:
- bundle readiness now has one compact machine-readable staged reload surface
- packet-only readiness does not pretend to have bundle-only staged companions

## Validation rule

Manual validator and local Pydantic model now agree:
- if `ready_surface_kind == A1_LAUNCH_BUNDLE`, `ready_launch_spine_json` must exist
- if `ready_surface_kind == A1_WORKER_LAUNCH_PACKET`, `ready_launch_spine_json` must stay empty

The human-readable current queue note now renders `ready_launch_spine_json` when present.

## Verification

Focused compile:
- `python3 -m py_compile system_v3/tools/prepare_a1_launch_bundle_from_family_slice.py system_v3/tools/build_a1_queue_status_packet.py system_v3/tools/validate_a1_queue_status_packet.py system_v3/tools/a1_queue_surface_models.py system_v3/tools/render_a1_queue_status_current_note_from_packet.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_launch_bundle_from_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a1_queue_state.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_surface_pydantic_stack.py`

Focused bundle/queue suite:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_launch_bundle_from_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a1_queue_state.py`

Result:
- `Ran 16 tests ... OK`

Focused local queue-surface stack:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_surface_pydantic_stack.py`

Result:
- `Ran 6 tests ... OK`

## Current interpretation

This closes a small but real queue-shape gap:
- bundle mode now exposes the staged worker spine directly
- the queue/current-note path can reload the compact staged launch object without chasing separate companion paths first

This does not yet promote any staged bundle into the live current queue automatically.
It only makes the bundle-ready queue surface shape richer and more explicit when bundle prep is selected.

## Next seam

The next useful move is to decide whether bundle-mode queue packets should also carry a direct send-text companion pointer, or whether the staged launch spine is the right compact stop point.
