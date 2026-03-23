# A2_UPDATE_NOTE__A1_ACTIVE_QUEUE_NOTE_REFRESH_POLICY_GUARD__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the policy guard where the active current human-readable A1 queue note remains opt-in for refresh, while the active queue packet refresh stays the default path

## Scope

Patched wrapper:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/refresh_active_current_a1_queue_state.py`

Focused regression:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a1_queue_state.py`

## What changed

The active refresh wrapper already:
- refreshed the active current queue packet from the active current registry
- wrote one preview note by default

It now also supports an explicit guarded path for the active human-readable current note:
- `--active-current-note <path>`
- `--write-active-current-note`

Without that explicit flag:
- the wrapper stays preview-only for the human-readable note

With that explicit flag:
- the wrapper renders the active current note from the active queue packet

## Meaning

This keeps the policy split deliberate:
- machine-readable active queue packet refresh is the default controller path
- human-readable active current note rewrite is still opt-in

So the repo now has:
- a stable active machine-readable source of current queue state
- a preview path for human-readable note refresh
- a deliberate opt-in path if the operator wants the human-readable current note rewritten too

## Verification

Focused suite:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a1_queue_state.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a2_controller_send_text_from_packet.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_candidate_registry.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_current_a1_queue_status_from_candidates.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py`

Result:
- `Ran 15 tests ... OK`

The new regression locks:
- preview-only refresh still works
- explicit active-current-note write works only when asked

## Next seam

The next real question is controller policy:
- should the active current human-readable note continue as an operator summary
- or should the repo eventually treat the machine-readable packet as the true current queue surface and the note as a rendered view
