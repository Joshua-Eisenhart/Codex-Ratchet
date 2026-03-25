# A2_UPDATE_NOTE__CONTROLLER_FACING_LOCAL_PYDANTIC_QUEUE_PATH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the first controller-facing queue path where the active current `a1?` refresh flow can now explicitly use the local Pydantic family-slice validator instead of only the hand-written JSON schema path

## Scope

Patched controller-facing helpers:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/prepare_a1_queue_status_surfaces.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/prepare_current_a1_queue_status_from_candidates.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/refresh_active_current_a1_queue_state.py`

Patched controller routing/doc surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a2_controller_send_text_from_packet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/71_A2_CONTROLLER_LAUNCH_PACKET__v1.md`

Focused regressions:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_current_a1_queue_status_from_candidates.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a1_queue_state.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a2_controller_send_text_from_packet.py`

## What changed

Before this patch:
- the lower family-slice prep tools could use `local_pydantic`
- but the controller-facing current-queue wrappers still only knew the older pass-through shape

Now the full current-queue chain accepts:
- `--family-slice-validation-mode local_pydantic`
- `--spec-graph-python /home/ratchet/Desktop/Codex Ratchet/.venv_spec_graph/bin/python`

That means the controller can now do:
- current registry selection
- current queue packet creation
- current queue note render

through the same bounded active refresh path, while explicitly choosing the local spec-object stack.

Default remains:
- `jsonschema`

So this is still compatibility-safe.

## Verification

Focused compile:
- `python3 -m py_compile system_v3/tools/prepare_a1_queue_status_surfaces.py system_v3/tools/prepare_current_a1_queue_status_from_candidates.py system_v3/tools/refresh_active_current_a1_queue_state.py system_v3/tools/build_a2_controller_send_text_from_packet.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_current_a1_queue_status_from_candidates.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a1_queue_state.py`

Focused suite:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_current_a1_queue_status_from_candidates.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a1_queue_state.py`

Result:
- `Ran 12 tests ... OK`

Controller send-text builder check:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a2_controller_send_text_from_packet.py`

Result:
- `Ran 1 test ... OK`

Real controller-facing smoke:
1. created a candidate registry at `/tmp/a1_active_queue_pydantic_registry.json`
2. ran:
   - `python3 system_v3/tools/refresh_active_current_a1_queue_state.py --candidate-registry-json /tmp/a1_active_queue_pydantic_registry.json --queue-status-packet-json /tmp/a1_active_queue_pydantic_packet.json --preview-note /tmp/a1_active_queue_pydantic_preview.md --family-slice-validation-mode local_pydantic --spec-graph-python /home/ratchet/Desktop/Codex Ratchet/.venv_spec_graph/bin/python --model 'GPT-5.4 Medium' --dispatch-id 'A1_DISPATCH__ACTIVE_QUEUE_REFRESH_PYDANTIC_SMOKE__2026_03_15__v1' --preparation-mode packet --out-dir /tmp/a1_active_queue_pydantic_ready`

Observed result:
- `candidate_count = 1`
- selected family slice = staged active substrate scaffold slice
- queue packet + preview note were created
- controller-facing refresh path succeeded under `local_pydantic`

## Current interpretation

This is the first point where the controller-facing `a1?` refresh path can explicitly use the local spec-object stack.

That is a real upgrade because it means:
- the local stack is no longer only a specialist lower-tool path
- the controller can choose it intentionally
- the repo still does not silently force the default runtime interpreter onto the venv

## Next seam

The next useful move is to decide whether the active current queue refresh wrapper should ever default to `local_pydantic` when the local stack is present, or whether keeping it as an explicit controller choice is the better long-term discipline.
