# A2_UPDATE_NOTE__A1_ACTIVE_QUEUE_REFRESH_WRAPPER__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the controller-facing wrapper that refreshes the active current A1 queue packet from the active current candidate registry, so `a1?` has a one-command active refresh path instead of a multi-tool chain

## Scope

New wrapper:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/refresh_active_current_a1_queue_state.py`

Focused regression:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a1_queue_state.py`

Patched routing surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a2_controller_send_text_from_packet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/71_A2_CONTROLLER_LAUNCH_PACKET__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`

## What changed

The repo already had the lower-level chain:
- candidate registry
- selector
- queue packet builder
- current-note renderer

But the controller still had to reconstruct that chain mentally.

`refresh_active_current_a1_queue_state.py` now gives one controller-facing command with defaults for:
- active current candidate registry
- active current queue packet
- one preview note path

So the bounded `a1?` action can now refresh the live machine-readable queue answer directly from the active current registry.

## Verification

Focused suite:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a1_queue_state.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a2_controller_send_text_from_packet.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_candidate_registry.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_current_a1_queue_status_from_candidates.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py`

Result:
- `Ran 14 tests ... OK`

Active wrapper run:
- `python3 system_v3/tools/refresh_active_current_a1_queue_state.py`

Observed result:
- refreshed `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json`
- rendered preview note at `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS__CURRENT__ACTIVE_REFRESH_PREVIEW__2026_03_15__v1.md`
- preserved current `NO_WORK` because the active current registry is still empty

## Next seam

The next real decision is policy, not plumbing:
- whether the active current human-readable queue note should eventually be refreshed from this wrapper too
- or remain a manually curated operator summary with the machine-readable packet/registry as companions
