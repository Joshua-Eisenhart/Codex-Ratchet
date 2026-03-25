# A2_UPDATE_NOTE__A2_CONTROLLER_LAUNCH_SPINE_LOCAL_SPEC_OBJECT_STACK__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the compact machine-readable launch-spine companion for the active A2 controller boot path

## Scope

New local-stack surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a2_controller_launch_spine_models.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a2_controller_launch_spine.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_a2_controller_launch_spine_pydantic.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a2_controller_launch_spine_graph.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/emit_a2_controller_launch_spine_pydantic_schema.py`

Focused regression:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_controller_launch_spine_pydantic_stack.py`

Patched read surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/71_A2_CONTROLLER_LAUNCH_PACKET__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md`

Current live inputs used for proof:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.json`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_GATE_RESULT__CURRENT__2026_03_12__v1.json`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_SEND_TEXT_COMPANION__CURRENT__2026_03_15__v1.json`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__2026_03_12__v1.json`

Generated current companion:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_SPINE__CURRENT__2026_03_15__v1.json`

Generated artifacts:
- GraphML:
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_LAUNCH_SPINE__CURRENT__2026_03_15__v1.graphml`
- Pydantic schema:
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_LAUNCH_SPINE_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`

## What changed

Before this step:
- the active controller boot path had four objectified pieces
  - launch packet
  - launch gate result
  - send-text companion
  - launch handoff
- but reload still had to stitch them together manually

Now there is one bounded derived launch-spine companion that records:
- the four current artifact paths
- the four artifact hashes
- the send-text path and hash
- shared launch identity fields
- launch-gate status / validity
- queue-helper mode
- handoff role/route summary
- read-path count and operator-step count

Important interpretation:
- this is not a new owner surface
- it is a compact derived controller reload/index companion

## Verification

Focused compile:
- `python3 -m py_compile system_v3/tools/a2_controller_launch_spine_models.py system_v3/tools/build_a2_controller_launch_spine.py system_v3/tools/audit_a2_controller_launch_spine_pydantic.py system_v3/tools/export_a2_controller_launch_spine_graph.py system_v3/tools/emit_a2_controller_launch_spine_pydantic_schema.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_controller_launch_spine_pydantic_stack.py`

Current spine build:
- `'.venv_spec_graph/bin/python' system_v3/tools/build_a2_controller_launch_spine.py --packet-json /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.json --gate-result-json /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_GATE_RESULT__CURRENT__2026_03_12__v1.json --send-text-companion-json /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_SEND_TEXT_COMPANION__CURRENT__2026_03_15__v1.json --handoff-json /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__2026_03_12__v1.json --out-json /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_SPINE__CURRENT__2026_03_15__v1.json`

Observed result:
- current launch spine created successfully
- current `launch_gate_status = LAUNCH_READY`
- current `queue_helper_mode = none`

Focused suite:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_controller_launch_spine_pydantic_stack.py`

Result:
- `Ran 3 tests ... OK`

Current audit:
- `'.venv_spec_graph/bin/python' system_v3/tools/audit_a2_controller_launch_spine_pydantic.py --spine-json /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_SPINE__CURRENT__2026_03_15__v1.json`

Observed result:
- `thread_class = A2_CONTROLLER`
- `mode = CONTROLLER_ONLY`
- graph shape = `17 nodes / 16 edges`
- `launch_gate_status = LAUNCH_READY`
- `allowed_first_action_count = 4`
- `queue_helper_mode = none`

Current graph export:
- `'.venv_spec_graph/bin/python' system_v3/tools/export_a2_controller_launch_spine_graph.py --spine-json /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_SPINE__CURRENT__2026_03_15__v1.json --out-graphml /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_LAUNCH_SPINE__CURRENT__2026_03_15__v1.graphml`

Current schema emit:
- `'.venv_spec_graph/bin/python' system_v3/tools/emit_a2_controller_launch_spine_pydantic_schema.py --out-json /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_LAUNCH_SPINE_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`

## Current interpretation

The active controller boot seam now has a compact local object spine:
- launch packet
- launch gate result
- send-text companion
- launch handoff
- launch spine companion

That means reload no longer has to jump across four current artifacts to check whether the boot path is coherent.

## Next seam

The next useful move is probably not more controller launch fragments. It is either:
- using this compact launch spine inside one higher controller/current-state helper
- or moving the same bounded object treatment into the A2 controller send-text itself or the A1 worker launch trio
