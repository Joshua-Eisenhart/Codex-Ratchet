# A2_UPDATE_NOTE__A1_WORKER_LAUNCH_PACKET_LOCAL_SPEC_OBJECT_STACK__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the first local spec-object representation for the A1 worker launch-packet surface on the family-slice-aligned path

## Scope

New local-stack surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_worker_launch_packet_models.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_a1_worker_launch_packet_pydantic.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a1_worker_launch_packet_graph.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/emit_a1_worker_launch_packet_pydantic_schema.py`

Focused regression:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_packet_pydantic_stack.py`

Patched read surface:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/34_A1_READY_PACKET__v1.md`

Current staged proof input:
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_PACKET__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

Generated artifacts:
- GraphML:
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_PACKET__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml`
- Pydantic schema:
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_PACKET_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`

## What changed

Before this step:
- the A1 worker launch packet had creator/validator/gate/handoff tooling
- but it did not yet have the same local Pydantic / GraphML / schema layer the controller and queue surfaces now have

Now the packet surface has a bounded local spec-object stack too.

Important interpretation:
- this does not promote staged draft packets into active owner surfaces
- it adds a machine-readable audit/export/schema layer around the existing packet shape

## Verification

Focused compile:
- `python3 -m py_compile system_v3/tools/a1_worker_launch_packet_models.py system_v3/tools/audit_a1_worker_launch_packet_pydantic.py system_v3/tools/export_a1_worker_launch_packet_graph.py system_v3/tools/emit_a1_worker_launch_packet_pydantic_schema.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_packet_pydantic_stack.py`

Focused suite:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_packet_pydantic_stack.py`

Result:
- `Ran 3 tests ... OK`

Current audit:
- `'.venv_spec_graph/bin/python' system_v3/tools/audit_a1_worker_launch_packet_pydantic.py --packet-json /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_PACKET__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

Observed result:
- `thread_class = A1_WORKER`
- `mode = PROPOSAL_ONLY`
- graph shape = `11 nodes / 10 edges`
- `target_a1_role = A1_PROPOSAL`
- `source_a2_artifact_count = 4`
- `a1_reload_artifact_count = 2`

Current graph export:
- `'.venv_spec_graph/bin/python' system_v3/tools/export_a1_worker_launch_packet_graph.py --packet-json /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_PACKET__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json --out-graphml /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_PACKET__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml`

Current schema emit:
- `'.venv_spec_graph/bin/python' system_v3/tools/emit_a1_worker_launch_packet_pydantic_schema.py --out-json /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_PACKET_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`

## Current interpretation

The next layer above the controller-side spine is no longer plain ad hoc packet JSON only.

The family-slice-aligned A1 worker launch packet now has:
- creator/validator/gate path
- family-slice compiler path
- local Pydantic audit
- local GraphML export
- local schema emit

## Next seam

The next useful move is probably the rest of the A1 worker launch trio:
- A1 worker gate result
- A1 worker send-text companion
- A1 worker handoff
