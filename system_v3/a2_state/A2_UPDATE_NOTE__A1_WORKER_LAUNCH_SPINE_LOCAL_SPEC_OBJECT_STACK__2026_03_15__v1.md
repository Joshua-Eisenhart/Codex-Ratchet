# A2_UPDATE_NOTE__A1_WORKER_LAUNCH_SPINE_LOCAL_SPEC_OBJECT_STACK__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the compact staged A1 worker launch spine companion for the family-slice launch-bundle proof path

## Scope

New local-stack surfaces:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a1_worker_launch_spine_models.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_launch_spine.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/audit_a1_worker_launch_spine_pydantic.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/export_a1_worker_launch_spine_graph.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/emit_a1_worker_launch_spine_pydantic_schema.py`

Focused regression:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_spine_pydantic_stack.py`

Patched read surface:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/34_A1_READY_PACKET__v1.md`

Staged proof inputs:
- packet:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1/A1_WORKER_LAUNCH_PACKET__A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1.json`
- gate result:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1/A1_WORKER_LAUNCH_PACKET__A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1__GATE_RESULT.json`
- send-text companion:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_SEND_TEXT_COMPANION__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`
- handoff:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1/A1_WORKER_LAUNCH_PACKET__A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1__HANDOFF.json`

Generated companion:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_SPINE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

Generated artifacts:
- GraphML:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_SPINE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml`
- Pydantic schema:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_SPINE_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`

## What changed

Before this step:
- the staged A1 worker launch-bundle path had local object validation for:
  - packet
  - gate result
  - send-text companion
  - handoff
- but reload still had to mentally stitch those four staged surfaces together

Now there is one compact staged worker-launch spine companion that records:
- packet / gate / companion / handoff paths
- packet / gate / companion / handoff hashes
- send-text path and hash
- shared launch identity fields
- launch-gate status
- read-path count
- handoff role summary
- monitor-skill binding

Important interpretation:
- this is still staged proof on the family-slice launch-bundle path
- it is not claiming one active current A1 worker launch owner surface exists yet

## Verification

Focused compile:
- `python3 -m py_compile system_v3/tools/a1_worker_launch_spine_models.py system_v3/tools/build_a1_worker_launch_spine.py system_v3/tools/audit_a1_worker_launch_spine_pydantic.py system_v3/tools/export_a1_worker_launch_spine_graph.py system_v3/tools/emit_a1_worker_launch_spine_pydantic_schema.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_spine_pydantic_stack.py`

Current staged spine build:
- `'.venv_spec_graph/bin/python' system_v3/tools/build_a1_worker_launch_spine.py --packet-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1/A1_WORKER_LAUNCH_PACKET__A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1.json --gate-result-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1/A1_WORKER_LAUNCH_PACKET__A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1__GATE_RESULT.json --send-text-companion-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_SEND_TEXT_COMPANION__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json --handoff-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1/A1_WORKER_LAUNCH_PACKET__A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1__HANDOFF.json --out-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_SPINE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

Focused suite:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_spine_pydantic_stack.py`

Result:
- `Ran 3 tests ... OK`

Current audit:
- `'.venv_spec_graph/bin/python' system_v3/tools/audit_a1_worker_launch_spine_pydantic.py --spine-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_SPINE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

Observed result:
- `thread_class = A1_WORKER`
- `mode = PROPOSAL_ONLY`
- graph shape = `6 nodes / 5 edges`
- `launch_gate_status = LAUNCH_READY`
- `target_a1_role = A1_PROPOSAL`
- `read_path_count = 7`

## Current interpretation

The staged family-slice A1 worker launch-bundle path now has the same compact-coherence layer the controller path gained:
- individual objectified launch surfaces
- one compact launch spine that proves they still agree

## Next seam

The next useful move is probably not another launch artifact. It is choosing whether one bounded staged worker-launch spine should be promoted into an active current queue/ready companion path, or whether staged proof should stop here until a real current A1-ready candidate is admitted.
