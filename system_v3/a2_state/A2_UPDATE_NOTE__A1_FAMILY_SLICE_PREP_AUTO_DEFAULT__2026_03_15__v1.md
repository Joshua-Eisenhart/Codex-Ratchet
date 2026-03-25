# A2_UPDATE_NOTE__A1_FAMILY_SLICE_PREP_AUTO_DEFAULT__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the follow-through where family-slice packet, bundle, and queue preparation now default to the same `auto` validation policy already used by the controller-facing current-queue path

## Scope

Patched prep tools:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_launch_packet_from_family_slice.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/prepare_a1_launch_bundle_from_family_slice.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_queue_status_packet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/prepare_a1_queue_status_surfaces.py`

Patched read surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/30_A2_TO_A1_HANDOFF_CONTRACT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/34_A1_READY_PACKET__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`

Focused regressions:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_worker_launch_packet_from_family_slice.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_launch_bundle_from_family_slice.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_current_a1_queue_status_from_candidates.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a1_queue_state.py`

## What changed

Before this step:
- the controller-facing active current queue path defaulted to `auto`
- but the lower family-slice packet/bundle/queue prep tools still defaulted to `jsonschema`

Now the prep tools also default to:
- `--family-slice-validation-mode auto`

Interpretation:
- when the local spec-object stack exists, `auto` resolves to `local_pydantic`
- otherwise `auto` resolves to `jsonschema`

So the family-slice preparation path and the current queue path now share one default policy instead of quietly diverging.

## Verification

Focused suite:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_worker_launch_packet_from_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_launch_bundle_from_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_current_a1_queue_status_from_candidates.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a1_queue_state.py`

Result:
- `Ran 27 tests ... OK`

Direct bundle proof under default `auto`:
- `python3 system_v3/tools/prepare_a1_launch_bundle_from_family_slice.py --family-slice-json /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json --family-slice-schema-json /tmp/missing_family_slice_schema_bundle_default.json --model 'GPT-5.4 Medium' --dispatch-id 'A1_DISPATCH__BUNDLE_DEFAULT_AUTO_VERIFY__2026_03_15__v1' --spec-graph-python /home/ratchet/Desktop/Codex Ratchet/.venv_spec_graph/bin/python --out-dir /tmp/a1_bundle_default_auto_verify`

Observed result:
- succeeded even with a missing schema path
- so the bundle-prep default now really uses `auto`

## Current interpretation

This is a small but useful normalization step.

The family-slice prep path now behaves like the controller-facing queue path:
- prefer the local spec-object stack when available
- keep a compatibility fallback when it is not

That makes the object-driven path easier to use consistently without turning the local venv into a hard runtime dependency.

## Next seam

The next useful move is to decide whether the same `auto` policy should be surfaced more explicitly in higher controller launch/process docs, or whether the current handoff/ready/live-packet surfaces are enough for now.
