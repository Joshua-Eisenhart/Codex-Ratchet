# A2_UPDATE_NOTE__A2_CONTROLLER_LAUNCH_HANDOFF_LOCAL_SPEC_OBJECT_STACK__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the first local spec-object representation for the live A2 controller launch handoff and record the stale send-text hash closure on the current handoff surface

## Scope

New local-stack surfaces:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a2_controller_launch_handoff_models.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/audit_a2_controller_launch_handoff_pydantic.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/export_a2_controller_launch_handoff_graph.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/emit_a2_controller_launch_handoff_pydantic_schema.py`

Focused regression:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_controller_launch_handoff_pydantic_stack.py`

Patched read surface:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/71_A2_CONTROLLER_LAUNCH_PACKET__v1.md`

Current live input used for proof:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__2026_03_12__v1.json`

Generated artifacts:
- GraphML:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__2026_03_12__v1.graphml`
- Pydantic schema:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_LAUNCH_HANDOFF_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`

## What changed

Before this step:
- the current controller handoff existed as JSON plus the generic launch-handoff validator
- but there was no local object/audit/export/schema layer for the controller-specific handoff surface

A real issue also surfaced:
- the current handoff stored `send_text_sha256` no longer matched the current send text

So this step did two things:
1. added the controller-handoff local spec-object stack
2. regenerated the current handoff from the current packet + current send text so the active hash-linked surface is no longer stale

## Verification

Focused compile:
- `python3 -m py_compile system_v3/tools/a2_controller_launch_handoff_models.py system_v3/tools/audit_a2_controller_launch_handoff_pydantic.py system_v3/tools/export_a2_controller_launch_handoff_graph.py system_v3/tools/emit_a2_controller_launch_handoff_pydantic_schema.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_controller_launch_handoff_pydantic_stack.py`

Current-handoff refresh:
- `python3 system_v3/tools/build_a2_controller_launch_handoff.py --packet-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.json --send-text /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_SEND_TEXT__CURRENT__2026_03_12__v1.md --out-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__2026_03_12__v1.json`

Observed result:
- current handoff send-text hash updated to the current send-text file

Focused suite:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_controller_launch_handoff_pydantic_stack.py`

Result:
- `Ran 3 tests ... OK`

Current audit:
- `'.venv_spec_graph/bin/python' system_v3/tools/audit_a2_controller_launch_handoff_pydantic.py --handoff-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__2026_03_12__v1.json`

Observed result:
- `thread_class = A2_CONTROLLER`
- `role_type = A2_CONTROLLER`
- graph shape = `13 nodes / 12 edges`
- `operator_step_count = 6`
- `monitor_mode = direct_controller_result_read`
- `closeout_mode = manual_controller_stop`

Current graph export:
- `'.venv_spec_graph/bin/python' system_v3/tools/export_a2_controller_launch_handoff_graph.py --handoff-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__2026_03_12__v1.json --out-graphml /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__2026_03_12__v1.graphml`

Current schema emit:
- `'.venv_spec_graph/bin/python' system_v3/tools/emit_a2_controller_launch_handoff_pydantic_schema.py --out-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_LAUNCH_HANDOFF_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`

## Current interpretation

The controller boot trio is now objectified across:
- launch packet
- launch gate result
- launch handoff

That means the active controller launch/control seam now has a local object path end to end before the human-facing send text.

## Next seam

The next useful move is to pause and consolidate this new controller-side object spine, or if continuing immediately, objectify the controller send-text surface as a bounded derived companion rather than as authority.
