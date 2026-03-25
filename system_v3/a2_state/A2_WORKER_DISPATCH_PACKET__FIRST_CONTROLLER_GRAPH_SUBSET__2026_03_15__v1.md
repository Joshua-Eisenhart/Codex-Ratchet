# A2_WORKER_DISPATCH_PACKET__FIRST_CONTROLLER_GRAPH_SUBSET__2026_03_15__v1

Status: ACTIVE OPERATOR SURFACE / NONCANON
Date: 2026-03-15
Owner: current `A2` controller
Role: exact bounded `A2_WORKER` dispatch packet for the first controller/A1 launch graph subset

## Dispatch identity

- `dispatch_id: A2_WORKER__FIRST_CONTROLLER_GRAPH_SUBSET__2026_03_15__v1`
- `thread_class: A2_WORKER`
- `model: GPT-5.4 Medium`
- `BOOT_SURFACE: /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `ROLE_LABEL: A1 Rosetta Bridge`
- `ROLE_TYPE: A1_ROSETTA_BRIDGE`
- `ROLE_SCOPE: one bounded pass to compile the first small controller and A1 launch graph subset from already-objectified current surfaces`

## Source artifacts

- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__FIRST_CONTROLLER_GRAPH_SUBSET_AND_HARDENING_SEQUENCE__2026_03_15__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a2_to_a1_family_slice_graph.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a1_queue_surfaces_graph.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a1_worker_launch_packet_graph.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a1_worker_send_text_companion_graph.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a1_worker_launch_handoff_graph.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a1_worker_launch_spine_graph.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a2_controller_launch_packet_graph.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a2_controller_launch_handoff_graph.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a2_controller_launch_spine_graph.py`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.graphml`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.graphml`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__2026_03_12__v1.graphml`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_LAUNCH_SPINE__CURRENT__2026_03_15__v1.graphml`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_PACKET__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_SEND_TEXT_COMPANION__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_HANDOFF__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_SPINE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_controller_launch_spine_pydantic_stack.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_spine_pydantic_stack.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_surface_pydantic_stack.py`

## BOUNDED_SCOPE

Run one bounded pass that:
- creates one minimal compiled controller/A1 launch graph subset artifact from already-objectified current surfaces
- adds at most one helper tool or one bounded extension to an existing graph/export tool path
- updates only the focused tests needed for that exact graph-subset step

Do not widen into:
- graph DB work
- whole-repo graph compilation
- planner-family doctrine changes
- queue redesign
- intake or run maintenance

## EXPECTED_OUTPUTS

- one bounded graph-subset result
- exact files read
- exact files updated
- focused test commands actually run
- one repo-held compiled graph-subset artifact if a real bounded implementation lands
- one bounded `A2_UPDATE_NOTE` only if a real source-bound delta exists
- one `NEXT_STEP` value:
  - `STOP`
  - `ONE_MORE_BOUNDED_A2_PASS_NEEDED`
- one raw returned result file written by the worker itself into:
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__FIRST_CONTROLLER_GRAPH_SUBSET__2026_03_15__v1__return.txt`
- one raw closeout staging text file written by the worker itself into:
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__FIRST_CONTROLLER_GRAPH_SUBSET__2026_03_15__v1.txt`

## CLOSEOUT_ROUTE

- `thread-run-monitor`
- `thread-closeout-auditor`
- `closeout-result-ingest`

## CONTINUATION_POLICY

- `AUTO_GO_ON_ALLOWED = NO`

## Exact prompt to send

```text
Use $ratchet-a2-a1 and $a2-brain-refresh.

Use the current A2 boot:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md

Run one bounded A1_ROSETTA_BRIDGE pass only.

dispatch_id: A2_WORKER__FIRST_CONTROLLER_GRAPH_SUBSET__2026_03_15__v1
ROLE_LABEL: A1 Rosetta Bridge
ROLE_TYPE: A1_ROSETTA_BRIDGE
ROLE_SCOPE: one bounded pass to compile the first small controller and A1 launch graph subset from already-objectified current surfaces

Use only these artifacts:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__FIRST_CONTROLLER_GRAPH_SUBSET_AND_HARDENING_SEQUENCE__2026_03_15__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a2_to_a1_family_slice_graph.py
- /home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a1_queue_surfaces_graph.py
- /home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a1_worker_launch_packet_graph.py
- /home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a1_worker_send_text_companion_graph.py
- /home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a1_worker_launch_handoff_graph.py
- /home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a1_worker_launch_spine_graph.py
- /home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a2_controller_launch_packet_graph.py
- /home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a2_controller_launch_handoff_graph.py
- /home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a2_controller_launch_spine_graph.py
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.graphml
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.graphml
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__2026_03_12__v1.graphml
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_LAUNCH_SPINE__CURRENT__2026_03_15__v1.graphml
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_PACKET__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_SEND_TEXT_COMPANION__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_HANDOFF__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_SPINE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml
- /home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_controller_launch_spine_pydantic_stack.py
- /home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_spine_pydantic_stack.py
- /home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_surface_pydantic_stack.py

Task:
- create one minimal compiled controller/A1 launch graph subset artifact from already-objectified current surfaces
- add at most one helper tool or one bounded extension to an existing graph/export path
- update only the focused tests needed for that exact graph-subset step

Rules:
- no graph DB work
- no whole-repo graph compilation
- no planner-family doctrine work
- no queue redesign
- no intake or run maintenance
- stop after one bounded pass

Before your final answer:
- write the exact final closeout body to:
  - /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__FIRST_CONTROLLER_GRAPH_SUBSET__2026_03_15__v1__return.txt
  - /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__FIRST_CONTROLLER_GRAPH_SUBSET__2026_03_15__v1.txt
- if the folders do not exist, create them
- do not ask the operator to save, paste back, or carry files
- if you cannot self-save, report that exact blocker and stop

Required final output:
ROLE_AND_SCOPE:
WHAT_YOU_READ:
ACTION_CHOSEN:
- one exact bounded action
- why it beat the alternatives
WHAT_YOU_UPDATED:
TESTS_RUN:
RESULT:
- one short paragraph only
NEXT_STEP:
- STOP
- ONE_MORE_BOUNDED_A2_PASS_NEEDED
IF_ONE_MORE_PASS:
- omit unless needed
- if present, give one exact next bounded A2 action
CLOSED_STATEMENT:
- one sentence only
SELF_SAVED_RETURN_PATHS:
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__FIRST_CONTROLLER_GRAPH_SUBSET__2026_03_15__v1__return.txt
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__FIRST_CONTROLLER_GRAPH_SUBSET__2026_03_15__v1.txt
```

## STOP_RULE

Stop after one bounded first-controller-graph-subset pass.
