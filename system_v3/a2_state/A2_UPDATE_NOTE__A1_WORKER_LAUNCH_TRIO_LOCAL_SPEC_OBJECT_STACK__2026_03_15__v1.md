# A2_UPDATE_NOTE__A1_WORKER_LAUNCH_TRIO_LOCAL_SPEC_OBJECT_STACK__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the local spec-object stack for the rest of the A1 worker launch trio on the staged family-slice launch-bundle path

## Scope

New local-stack surfaces:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a1_worker_launch_gate_result_models.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/audit_a1_worker_launch_gate_result_pydantic.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/export_a1_worker_launch_gate_result_graph.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/emit_a1_worker_launch_gate_result_pydantic_schema.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a1_worker_send_text_companion_models.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_send_text_companion.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/audit_a1_worker_send_text_companion_pydantic.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/export_a1_worker_send_text_companion_graph.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/emit_a1_worker_send_text_companion_pydantic_schema.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a1_worker_launch_handoff_models.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/audit_a1_worker_launch_handoff_pydantic.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/export_a1_worker_launch_handoff_graph.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/emit_a1_worker_launch_handoff_pydantic_schema.py`

Focused regressions:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_gate_result_pydantic_stack.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_send_text_companion_pydantic_stack.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_handoff_pydantic_stack.py`

Patched read surface:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/34_A1_READY_PACKET__v1.md`

Staged proof packet family:
- packet:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1/A1_WORKER_LAUNCH_PACKET__A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1.json`
- gate result:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1/A1_WORKER_LAUNCH_PACKET__A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1__GATE_RESULT.json`
- send text:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1/A1_WORKER_LAUNCH_PACKET__A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1__SEND_TEXT.md`
- handoff:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1/A1_WORKER_LAUNCH_PACKET__A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1__HANDOFF.json`

Generated companion:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_SEND_TEXT_COMPANION__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

Generated artifacts:
- GraphML:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_GATE_RESULT__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_SEND_TEXT_COMPANION__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_HANDOFF__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml`
- Pydantic schemas:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_GATE_RESULT_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_SEND_TEXT_COMPANION_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_HANDOFF_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`

## What changed

Before this step:
- the A1 worker launch packet had the first local object stack
- but the rest of the A1 launch trio was still only raw bundle JSON / markdown

Now the staged family-slice launch-bundle path also has:
- gate-result local object validation
- send-text companion objectification
- handoff local object validation

Important interpretation:
- this is still staged proof on the family-slice launch-bundle sample path
- it is not claiming there is one active current A1 worker launch trio owner surface

## Verification

Focused compile:
- `python3 -m py_compile system_v3/tools/a1_worker_launch_gate_result_models.py system_v3/tools/a1_worker_send_text_companion_models.py system_v3/tools/a1_worker_launch_handoff_models.py system_v3/tools/build_a1_worker_send_text_companion.py system_v3/tools/audit_a1_worker_launch_gate_result_pydantic.py system_v3/tools/export_a1_worker_launch_gate_result_graph.py system_v3/tools/emit_a1_worker_launch_gate_result_pydantic_schema.py system_v3/tools/audit_a1_worker_send_text_companion_pydantic.py system_v3/tools/export_a1_worker_send_text_companion_graph.py system_v3/tools/emit_a1_worker_send_text_companion_pydantic_schema.py system_v3/tools/audit_a1_worker_launch_handoff_pydantic.py system_v3/tools/export_a1_worker_launch_handoff_graph.py system_v3/tools/emit_a1_worker_launch_handoff_pydantic_schema.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_gate_result_pydantic_stack.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_send_text_companion_pydantic_stack.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_handoff_pydantic_stack.py`

Current companion build:
- `'.venv_spec_graph/bin/python' system_v3/tools/build_a1_worker_send_text_companion.py --packet-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1/A1_WORKER_LAUNCH_PACKET__A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1.json --send-text /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1/A1_WORKER_LAUNCH_PACKET__A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1__SEND_TEXT.md --out-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_SEND_TEXT_COMPANION__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

Focused suite:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_gate_result_pydantic_stack.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_send_text_companion_pydantic_stack.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_handoff_pydantic_stack.py`

Result:
- `Ran 9 tests ... OK`

Current audits:
- gate result:
  - `'.venv_spec_graph/bin/python' system_v3/tools/audit_a1_worker_launch_gate_result_pydantic.py --gate-result-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1/A1_WORKER_LAUNCH_PACKET__A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1__GATE_RESULT.json`
  - observed:
    - `thread_class = A1_WORKER`
    - `mode = PROPOSAL_ONLY`
    - graph shape = `9 nodes / 8 edges`
    - `status = LAUNCH_READY`
    - `target_a1_role = A1_PROPOSAL`
- send-text companion:
  - `'.venv_spec_graph/bin/python' system_v3/tools/audit_a1_worker_send_text_companion_pydantic.py --companion-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_SEND_TEXT_COMPANION__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`
  - observed:
    - `thread_class = A1_WORKER`
    - `mode = PROPOSAL_ONLY`
    - graph shape = `10 nodes / 9 edges`
    - `target_a1_role = A1_PROPOSAL`
    - `read_path_count = 7`
- handoff:
  - `'.venv_spec_graph/bin/python' system_v3/tools/audit_a1_worker_launch_handoff_pydantic.py --handoff-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1/A1_WORKER_LAUNCH_PACKET__A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1__HANDOFF.json`
  - observed:
    - `thread_class = A1_WORKER`
    - `mode = PROPOSAL_ONLY`
    - graph shape = `5 nodes / 4 edges`
    - `role_type = A1_PROPOSAL`
    - `operator_step_count = 6`

## Current interpretation

The staged family-slice A1 launch-bundle path now has a bounded local object spine across:
- packet
- gate result
- send-text companion
- handoff

That makes the worker launch side much closer to the controller-side object path, even though it is still anchored on staged sample outputs rather than one live current owner surface.

## Next seam

The next useful move is probably a compact staged A1 worker launch spine companion, mirroring the controller launch spine and giving the family-slice worker bundle one machine-readable coherence object instead of four separate staged surfaces.
