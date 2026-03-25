# A2_UPDATE_NOTE__A2_CONTROLLER_LAUNCH_SPINE_REFRESH_HELPER__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the step where the compact A2 controller launch spine became a normal active refresh action instead of a one-off build command

## Scope

New helper:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/refresh_active_current_a2_controller_launch_spine.py`

Focused regression:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a2_controller_launch_spine.py`

Patched read surface:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/71_A2_CONTROLLER_LAUNCH_PACKET__v1.md`

## What changed

Before this step:
- the compact controller launch spine could be built
- but it still lived as a one-off lower tool invocation

Now there is a normal active refresh helper that:
- rebuilds the current launch spine from the current packet, gate result, send-text companion, and handoff
- can also refresh the companion GraphML and emitted schema

## Verification

Focused compile:
- `python3 -m py_compile system_v3/tools/refresh_active_current_a2_controller_launch_spine.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a2_controller_launch_spine.py`

Focused suite:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a2_controller_launch_spine.py`

Result:
- `Ran 2 tests ... OK`

Current smoke:
- `python3 system_v3/tools/refresh_active_current_a2_controller_launch_spine.py --spec-graph-python /home/ratchet/Desktop/Codex Ratchet/.venv_spec_graph/bin/python --emit-graphml --emit-schema`

Observed result:
- current launch spine refreshed successfully
- current GraphML refreshed successfully
- current schema refreshed successfully

## Current interpretation

The controller-side compact launch spine is now operational:
- not just a generated object
- but a normal repo-held active refresh action

## Next seam

The next useful move was the A1 worker launch packet local stack, and that seam is now also in progress/completed in:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_WORKER_LAUNCH_PACKET_LOCAL_SPEC_OBJECT_STACK__2026_03_15__v1.md`
