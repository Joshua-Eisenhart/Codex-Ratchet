# A2_UPDATE_NOTE__A1_CONTROLLER_QUEUE_AUTO_PYDANTIC_POLICY__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the controller-facing validation-policy shift where the active current `a1?` queue path now defaults to `auto`, meaning local Pydantic when the local stack exists and JSON schema fallback otherwise

## Scope

Patched tools:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_launch_packet_from_family_slice.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/prepare_a1_launch_bundle_from_family_slice.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a1_queue_status_packet.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/prepare_a1_queue_status_surfaces.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/prepare_current_a1_queue_status_from_candidates.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/refresh_active_current_a1_queue_state.py`

Patched controller-facing read surfaces:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a2_controller_send_text_from_packet.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/71_A2_CONTROLLER_LAUNCH_PACKET__v1.md`

Focused regressions:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_worker_launch_packet_from_family_slice.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_launch_bundle_from_family_slice.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_current_a1_queue_status_from_candidates.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a1_queue_state.py`

## What changed

Before this step:
- the lower compilers and the controller-facing wrappers could use `local_pydantic`
- but the operator-facing policy still read like explicit opt-in local-stack mode

Now:
- the controller-facing queue path defaults to `--family-slice-validation-mode auto`
- `auto` resolves to `local_pydantic` when the provided local stack exists
- otherwise it falls back to `jsonschema`

That means the current queue path is now:
- local-stack friendly when the repo-local spec-object stack is present
- still compatibility-safe when it is absent

Important policy boundary:
- this is a controller-facing validation policy shift
- it does not change the emitted queue packet shape
- it does not make the normal repo interpreter depend on the local venv

## Verification

Focused suite:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_worker_launch_packet_from_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_launch_bundle_from_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_current_a1_queue_status_from_candidates.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a1_queue_state.py`

Result:
- `Ran 24 tests ... OK`

Direct `auto` packet proof:
- `python3 system_v3/tools/build_a1_worker_launch_packet_from_family_slice.py --family-slice-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json --family-slice-schema-json /tmp/missing_family_slice_schema.json --model 'GPT-5.4 Medium' --dispatch-id 'A1_DISPATCH__AUTO_PYDANTIC_PROOF__2026_03_15__v1' --family-slice-validation-mode auto --spec-graph-python /Users/joshuaeisenhart/Desktop/Codex Ratchet/.venv_spec_graph/bin/python --out-json /tmp/a1_packet_auto_pydantic_proof.json`

Observed result:
- succeeded even with a missing schema path
- so `auto` correctly selected `local_pydantic`

Direct controller-facing `auto` proof:
- `python3 system_v3/tools/refresh_active_current_a1_queue_state.py --candidate-registry-json /tmp/a1_active_queue_pydantic_registry.json --queue-status-packet-json /tmp/a1_active_queue_auto_packet.json --preview-note /tmp/a1_active_queue_auto_preview.md --family-slice-schema-json /tmp/missing_family_slice_schema.json --spec-graph-python /Users/joshuaeisenhart/Desktop/Codex Ratchet/.venv_spec_graph/bin/python --model 'GPT-5.4 Medium' --dispatch-id 'A1_DISPATCH__ACTIVE_QUEUE_REFRESH_AUTO_PROOF__2026_03_15__v1' --preparation-mode packet --out-dir /tmp/a1_active_queue_auto_ready`

Observed result:
- `candidate_count = 1`
- selected family slice = active staged substrate scaffold slice
- queue packet + preview note were created
- controller-facing refresh succeeded under default `auto` policy even with a missing schema path

## Current interpretation

This is the first controller-facing policy where the repo can prefer the local spec-object stack without making it a brittle hard dependency.

That is a useful middle state because:
- the local stack gets exercised through real queue/controller flows
- fallback behavior still exists when the local stack is absent
- the operator-facing read surfaces now describe the actual default

## Next seam

The next useful move is to decide whether the same `auto` policy should become the preferred default for more family-slice preparation paths outside the active current queue flow, or whether queue-first is the right stop point for now.
