# A2_UPDATE_NOTE__A1_QUEUE_SURFACE_LOCAL_SPEC_OBJECT_STACK__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the first local spec-object representation for the live A1 queue candidate registry and live A1 queue-status packet

## Scope

New local-stack object/model surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_queue_surface_models.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_a1_queue_surfaces_pydantic.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a1_queue_surfaces_graph.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/emit_a1_queue_surface_pydantic_schemas.py`

Focused regression:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_surface_pydantic_stack.py`

Patched read surface:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`

Current live inputs used for proof:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json`

Generated graph exports:
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.graphml`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.graphml`

Generated queue-surface schemas:
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_CANDIDATE_REGISTRY_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS_PACKET_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`

## What changed

Before this step:
- the local spec-object stack only had a real model for `A2_TO_A1_FAMILY_SLICE_v1`
- the live queue registry and live queue-status packet still existed only as hand-written JSON plus plain validators

Now the live queue surfaces also have:
- Pydantic object models
- local-stack audits
- GraphML export
- Pydantic-derived schema emit

Interpretation:
- the current queue layer is now part of the same local `Pydantic + JSON + NetworkX + GraphML` direction
- the current repo-held queue state can be inspected as objects and as graph projections instead of only as flat JSON

## Verification

Focused compile:
- `python3 -m py_compile system_v3/tools/a1_queue_surface_models.py system_v3/tools/audit_a1_queue_surfaces_pydantic.py system_v3/tools/export_a1_queue_surfaces_graph.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_surface_pydantic_stack.py`

Focused suite:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_surface_pydantic_stack.py`

Result:
- `Ran 5 tests ... OK`

Current registry audit:
- `'.venv_spec_graph/bin/python' system_v3/tools/audit_a1_queue_surfaces_pydantic.py --registry-json /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json`

Observed result:
- `candidate_count = 0`
- `has_selected_family_slice = false`
- graph shape = `1 node / 0 edges`

Current queue packet audit:
- `'.venv_spec_graph/bin/python' system_v3/tools/audit_a1_queue_surfaces_pydantic.py --packet-json /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json`

Observed result:
- `queue_status = NO_WORK`
- `has_ready_surface = false`
- graph shape = `2 nodes / 1 edge`

Current graph exports:
- `'.venv_spec_graph/bin/python' system_v3/tools/export_a1_queue_surfaces_graph.py --registry-json /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json --out-graphml /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.graphml`
- `'.venv_spec_graph/bin/python' system_v3/tools/export_a1_queue_surfaces_graph.py --packet-json /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json --out-graphml /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.graphml`

Current schema emit:
- `'.venv_spec_graph/bin/python' system_v3/tools/emit_a1_queue_surface_pydantic_schemas.py --registry-schema-out /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_CANDIDATE_REGISTRY_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json --queue-packet-schema-out /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS_PACKET_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`

## Current interpretation

The live current queue state is still simple right now:
- current candidate registry is empty
- current queue packet is `NO_WORK`

But that simplicity is now explicit and machine-readable through the local spec-object stack.

That is useful because the queue/controller layer is no longer just consuming objectified family slices.
It can now also objectify the live queue decision surfaces themselves.

## Next seam

The next useful move is to decide whether the queue candidate registry and current queue packet should get the same emitted-schema helper treatment as the family slice, or whether the current audit/export layer is enough for now.
