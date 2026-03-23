# A2_UPDATE_NOTE__A1_FAMILY_SLICE_LOCAL_PYDANTIC_INTEROP_BRIDGE__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the first compatibility-safe bridge where existing family-slice packet/bundle/queue compilers can optionally validate through the local Pydantic stack without turning the live runtime into a hard Pydantic/venv dependency

## Scope

Patched tools:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_launch_packet_from_family_slice.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/prepare_a1_launch_bundle_from_family_slice.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a1_queue_status_packet.py`

Focused regressions:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_worker_launch_packet_from_family_slice.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_launch_bundle_from_family_slice.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py`

Observed smoke output:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS_PACKET__SUBSTRATE_BASE_SCAFFOLD__PYDANTIC_SMOKE__2026_03_15__v1.json`

## What changed

Before this patch:
- the local spec-object stack existed under `.venv_spec_graph`
- but the normal family-slice packet/bundle/queue compilers still only knew the hand-written JSON schema path

Now those tools can be told to use the local stack explicitly:
- `--family-slice-validation-mode jsonschema`
- `--family-slice-validation-mode local_pydantic`

Important policy:
- default remains `jsonschema`
- local Pydantic is opt-in

That means:
- current repo/runtime behavior does not silently change
- but the new local stack can now be exercised through real A1 preparation paths

## Important implementation boundary

One real macOS issue showed up in the bridge path:
- resolving `.venv_spec_graph/bin/python` collapses the symlink back to the base Homebrew interpreter
- inherited `__PYVENV_LAUNCHER__` / `PYTHONEXECUTABLE` can also make the child process behave like the parent interpreter

So the packet compiler now:
- preserves the venv launcher path instead of resolving it
- scrubs `__PYVENV_LAUNCHER__`
- scrubs `PYTHONEXECUTABLE`

Without that, `local_pydantic` looked correct at the CLI surface but actually imported broken system-site `pydantic`.

## Verification

Focused compile:
- `python3 -m py_compile system_v3/tools/build_a1_worker_launch_packet_from_family_slice.py system_v3/tools/prepare_a1_launch_bundle_from_family_slice.py system_v3/tools/build_a1_queue_status_packet.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_worker_launch_packet_from_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_launch_bundle_from_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py`

Focused suite:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_worker_launch_packet_from_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_launch_bundle_from_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py`

Result:
- `Ran 9 tests ... OK`

Direct local-Pydantic packet smoke:
- `python3 system_v3/tools/build_a1_worker_launch_packet_from_family_slice.py --family-slice-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json --model 'GPT-5.4 Medium' --dispatch-id 'A1_DISPATCH__DIRECT_PYDANTIC_SMOKE__2026_03_15__v1' --family-slice-validation-mode local_pydantic --spec-graph-python /Users/joshuaeisenhart/Desktop/Codex Ratchet/.venv_spec_graph/bin/python --out-json /tmp/a1_packet_direct_pydantic_smoke.json`

Direct local-Pydantic queue smoke:
- `python3 system_v3/tools/build_a1_queue_status_packet.py --family-slice-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json --model 'GPT-5.4 Medium' --dispatch-id 'A1_DISPATCH__QUEUE_PACKET_PYDANTIC_SMOKE__2026_03_15__v1' --preparation-mode packet --family-slice-validation-mode local_pydantic --spec-graph-python /Users/joshuaeisenhart/Desktop/Codex Ratchet/.venv_spec_graph/bin/python --out-dir /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/queue_status_packet__substrate_base_scaffold__pydantic_smoke__2026_03_15__v1 --out-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS_PACKET__SUBSTRATE_BASE_SCAFFOLD__PYDANTIC_SMOKE__2026_03_15__v1.json`

Observed result:
- packet compiler succeeded under `local_pydantic`
- queue-status compiler succeeded under `local_pydantic`
- generated queue-status packet remained valid and pointed at one real ready packet surface

## Next seam

The next useful move is still bounded:
- add one current-family-slice consumer that can use `local_pydantic` in `auto` or explicit-controller mode
- while leaving default runtime/controller behavior on the compatibility-safe path until interpreter policy is decided
