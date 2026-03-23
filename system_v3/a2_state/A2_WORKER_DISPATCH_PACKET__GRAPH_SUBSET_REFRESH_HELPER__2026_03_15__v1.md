# A2_WORKER_DISPATCH_PACKET__GRAPH_SUBSET_REFRESH_HELPER__2026_03_15__v1

Status: ACTIVE OPERATOR SURFACE / NONCANON
Date: 2026-03-15
Owner: current `A2` controller
Role: exact bounded `A2_WORKER` dispatch packet for a refresh helper around the first controller/A1 launch graph subset

## Dispatch identity

- `dispatch_id: A2_WORKER__GRAPH_SUBSET_REFRESH_HELPER__2026_03_15__v1`
- `thread_class: A2_WORKER`
- `model: GPT-5.4 Medium`
- `BOOT_SURFACE: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `ROLE_LABEL: A1 Rosetta Bridge`
- `ROLE_TYPE: A1_ROSETTA_BRIDGE`
- `ROLE_SCOPE: one bounded pass to add a refresh helper for the first controller/A1 launch subset graph and one focused test`

## Source artifacts

- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__FIRST_CONTROLLER_GRAPH_SUBSET_AND_HARDENING_SEQUENCE__2026_03_15__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/compile_first_controller_a1_launch_subset_graph.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/export_a2_controller_launch_spine_graph.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/export_a1_queue_surfaces_graph.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/FIRST_CONTROLLER_A1_LAUNCH_SUBSET__CURRENT_AND_SUBSTRATE_BASE__2026_03_15__v1.graphml`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_LAUNCH_SPINE__CURRENT__2026_03_15__v1.graphml`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.graphml`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_controller_launch_spine_pydantic_stack.py`

## BOUNDED_SCOPE

Run one bounded pass that:
- adds a small refresh helper tool that rebuilds the compiled controller/A1 launch subset graph into the fixed spec-drafts path
- adds one focused test that exercises the helper

Do not widen into:
- graph DB work
- whole-repo graph compilation
- planner-family doctrine changes
- queue redesign
- intake or run maintenance

## EXPECTED_OUTPUTS

- one bounded helper tool
- one focused test update
- one bounded `A2_UPDATE_NOTE` only if a real source-bound delta exists
- one `NEXT_STEP` value:
  - `STOP`
  - `ONE_MORE_BOUNDED_A2_PASS_NEEDED`
- one raw returned result file written by the worker itself into:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__GRAPH_SUBSET_REFRESH_HELPER__2026_03_15__v1__return.txt`
- one raw closeout staging text file written by the worker itself into:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__GRAPH_SUBSET_REFRESH_HELPER__2026_03_15__v1.txt`

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
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md

Run one bounded A1_ROSETTA_BRIDGE pass only.

dispatch_id: A2_WORKER__GRAPH_SUBSET_REFRESH_HELPER__2026_03_15__v1
ROLE_LABEL: A1 Rosetta Bridge
ROLE_TYPE: A1_ROSETTA_BRIDGE
ROLE_SCOPE: one bounded pass to add a refresh helper for the first controller/A1 launch subset graph and one focused test

Use only these artifacts:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__FIRST_CONTROLLER_GRAPH_SUBSET_AND_HARDENING_SEQUENCE__2026_03_15__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/compile_first_controller_a1_launch_subset_graph.py
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/export_a2_controller_launch_spine_graph.py
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/export_a1_queue_surfaces_graph.py
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/FIRST_CONTROLLER_A1_LAUNCH_SUBSET__CURRENT_AND_SUBSTRATE_BASE__2026_03_15__v1.graphml
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_CONTROLLER_LAUNCH_SPINE__CURRENT__2026_03_15__v1.graphml
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.graphml
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a2_controller_launch_spine_pydantic_stack.py

Task:
- add a small refresh helper tool that rebuilds the compiled controller/A1 launch subset graph into the fixed spec-drafts path
- add one focused test that exercises the helper

Rules:
- no graph DB work
- no whole-repo graph compilation
- no planner-family doctrine changes
- no queue redesign
- no intake or run maintenance
- stop after one bounded pass

Before your final answer:
- write the exact final closeout body to:
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__GRAPH_SUBSET_REFRESH_HELPER__2026_03_15__v1__return.txt
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__GRAPH_SUBSET_REFRESH_HELPER__2026_03_15__v1.txt
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
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__GRAPH_SUBSET_REFRESH_HELPER__2026_03_15__v1__return.txt
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__GRAPH_SUBSET_REFRESH_HELPER__2026_03_15__v1.txt
```

## STOP_RULE

Stop after one bounded graph subset refresh helper pass.
