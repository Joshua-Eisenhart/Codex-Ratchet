# A2_UPDATE_NOTE__A1_WORKER_LAUNCH_RELOAD_ARTIFACT_ROUTING_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the worker-launch routing patch that makes A1 launch packets carry the clean live/historical A1 reload surfaces explicitly instead of relying on mixed owner docs alone

## Scope

Patched A1 worker launch tools:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/create_a1_worker_launch_packet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_a1_worker_launch_packet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_send_text_from_packet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_worker_launch_from_packet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_launch_handoff.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_codex_thread_launch_handoff.py`

Patched A1 launch-shape specs:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/34_A1_READY_PACKET__v1.md`

Focused regression:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_packet.py`

Target reload surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md`

## Problem

The repo already had the cleaner live/historical A1 split, and the boot/handoff docs already pointed to it.

But the actual A1 worker launch packet path still only carried:
- `required_a1_boot`
- `source_a2_artifacts`

That meant generated launch packets, send text, gate results, and handoffs still depended on the mixed boot plus ambient operator interpretation, instead of carrying the bounded A1 reload surfaces explicitly.

## What changed

### 1) Launch packet shape

`A1_WORKER_LAUNCH_PACKET_v1` now supports:
- `a1_reload_artifacts`

Creator behavior:
- `create_a1_worker_launch_packet.py` now accepts repeated `--a1-reload-artifact`
- values must be absolute existing paths

Validation behavior:
- `validate_a1_worker_launch_packet.py` now validates `a1_reload_artifacts` when present
- `prompt_to_send` must visibly contain them when they are declared

### 2) Send text / gate / handoff propagation

`build_a1_worker_send_text_from_packet.py` now emits:
- `a1_reload_artifacts:`
  - `<path>`

when the packet carries them.

`run_a1_worker_launch_from_packet.py` and `build_a1_worker_launch_handoff.py` now preserve:
- `a1_reload_artifacts`

`validate_codex_thread_launch_handoff.py` now treats those reload artifacts as part of the A1 send-text integrity contract when present.

### 3) Launch-shape docs

`32_A1_QUEUE_STATUS_SURFACE__v1.md` now says ready packets should carry:
- `a1_reload_artifacts` when live/historical A1 reload guidance is needed

and distinguishes them from:
- `source_a2_artifacts`

`34_A1_READY_PACKET__v1.md` now includes:
- `a1_reload_artifacts` in the required-field shape
- `77` and `78` in the ready-packet template
- prompt guidance saying declared reload artifacts must be carried into the prompt

## Meaning

The A1 read-side split is now routed through the actual worker-launch machinery, not only through higher-level docs.

So new A1 launch packets can explicitly carry:
- the live packet/profile read
- the historical branch/wiggle read

without confusing those with:
- the boot surface
- A2 fuel artifacts

## Verification

Syntax:
- `python3 -m py_compile system_v3/tools/create_a1_worker_launch_packet.py system_v3/tools/validate_a1_worker_launch_packet.py system_v3/tools/build_a1_worker_send_text_from_packet.py system_v3/tools/run_a1_worker_launch_from_packet.py system_v3/tools/build_a1_worker_launch_handoff.py system_v3/tools/validate_codex_thread_launch_handoff.py system_v3/tools/prepare_codex_launch_bundle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_packet.py`

Focused regression:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_packet.py`

Result:
- `Ran 2 tests ... OK`

What the new test locks:
- repeated `--a1-reload-artifact` CLI args are preserved in the packet
- packet validation succeeds and requires prompt visibility
- send text contains the reload-artifact section
- gate result and handoff preserve the same paths
- handoff validation checks the send-text markers
- old-style packets without `a1_reload_artifacts` still remain valid

## Next seam

The next useful move is to update any active A1 launch-packet exemplars or bundle generators that should now include `77` and `78` by default, so the cleaner routing becomes normal output instead of only newly available output.
