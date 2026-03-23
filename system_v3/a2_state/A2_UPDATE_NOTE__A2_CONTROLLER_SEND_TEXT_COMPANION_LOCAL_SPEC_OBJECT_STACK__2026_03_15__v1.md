# A2_UPDATE_NOTE__A2_CONTROLLER_SEND_TEXT_COMPANION_LOCAL_SPEC_OBJECT_STACK__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the first local spec-object representation for the A2 controller send-text surface as a bounded derived companion object rather than a second owner surface

## Scope

New local-stack surfaces:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a2_controller_send_text_companion_models.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a2_controller_send_text_companion.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/audit_a2_controller_send_text_companion_pydantic.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/export_a2_controller_send_text_companion_graph.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/emit_a2_controller_send_text_companion_pydantic_schema.py`

Focused regression:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_controller_send_text_companion_pydantic_stack.py`

Patched read surface:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/71_A2_CONTROLLER_LAUNCH_PACKET__v1.md`

Current live inputs used for proof:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_SEND_TEXT__CURRENT__2026_03_12__v1.md`

Generated current companion:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_SEND_TEXT_COMPANION__CURRENT__2026_03_15__v1.json`

Generated artifacts:
- GraphML:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_SEND_TEXT_COMPANION__CURRENT__2026_03_15__v1.graphml`
- Pydantic schema:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_SEND_TEXT_COMPANION_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`

## What changed

Before this step:
- the controller send text existed only as prose plus the hash linkage inside the handoff

Now there is a bounded derived companion object that records:
- source packet
- send-text path + SHA
- governing surfaces
- active context surfaces
- ordered read paths
- queue-helper mode
- required closeout fields
- first-task requirements

Important interpretation:
- this companion is not a new owner surface
- it is a derived machine-readable projection of the send-text surface

## Verification

Focused compile:
- `python3 -m py_compile system_v3/tools/a2_controller_send_text_companion_models.py system_v3/tools/build_a2_controller_send_text_companion.py system_v3/tools/audit_a2_controller_send_text_companion_pydantic.py system_v3/tools/export_a2_controller_send_text_companion_graph.py system_v3/tools/emit_a2_controller_send_text_companion_pydantic_schema.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_controller_send_text_companion_pydantic_stack.py`

Current companion build:
- `python3 system_v3/tools/build_a2_controller_send_text_companion.py --packet-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.json --send-text /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_SEND_TEXT__CURRENT__2026_03_12__v1.md --out-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_SEND_TEXT_COMPANION__CURRENT__2026_03_15__v1.json`

Observed result:
- current companion created successfully
- current `queue_helper_mode = none`
- current companion hash agrees with the regenerated current send text

Focused suite:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_controller_send_text_companion_pydantic_stack.py`

Current audit:
- `'.venv_spec_graph/bin/python' system_v3/tools/audit_a2_controller_send_text_companion_pydantic.py --companion-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_SEND_TEXT_COMPANION__CURRENT__2026_03_15__v1.json`

Observed result:
- `thread_class = A2_CONTROLLER`
- `mode = CONTROLLER_ONLY`
- graph shape = `23 nodes / 22 edges`
- `read_path_count = 9`
- `queue_helper_mode = none`

Current graph export:
- `'.venv_spec_graph/bin/python' system_v3/tools/export_a2_controller_send_text_companion_graph.py --companion-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_SEND_TEXT_COMPANION__CURRENT__2026_03_15__v1.json --out-graphml /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_SEND_TEXT_COMPANION__CURRENT__2026_03_15__v1.graphml`

Current schema emit:
- `'.venv_spec_graph/bin/python' system_v3/tools/emit_a2_controller_send_text_companion_pydantic_schema.py --out-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_SEND_TEXT_COMPANION_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`

Builder/validator drift closure:
- the generic handoff validator required the send-text marker:
  - `You are a fresh A2 controller thread.`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a2_controller_send_text_from_packet.py` now emits that marker
- the active current surfaces were then regenerated:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_SEND_TEXT__CURRENT__2026_03_12__v1.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__2026_03_12__v1.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_SEND_TEXT_COMPANION__CURRENT__2026_03_15__v1.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/launch_bundles/a2_current`
- the generic validator now passes cleanly:
  - `python3 system_v3/tools/validate_codex_thread_launch_handoff.py --launch-handoff-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__2026_03_12__v1.json`
- current observed result:
  - `valid = true`
  - `errors = []`

Focused suite result:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_controller_send_text_companion_pydantic_stack.py`
- `Ran 3 tests ... OK`

## Current interpretation

The controller launch/control seam is now objectified across:
- launch packet
- launch gate result
- send-text companion
- launch handoff

That means the controller boot path now has a bounded local object spine end to end, with the prose send text represented only through a derived companion rather than treated as a new authority surface.

## Next seam

The next useful move is probably not more controller boot objects. It is either:
- consolidating this controller-side object spine into one compact read/index surface
- or starting the same bounded object treatment for the A1 worker launch trio
