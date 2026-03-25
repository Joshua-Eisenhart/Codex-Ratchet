# A2_WORKER_DISPATCH_PACKET__DOCS_INTEGRATE_GRAPH_AND_PROVENANCE__2026_03_15__v1

Status: ACTIVE OPERATOR SURFACE / NONCANON
Date: 2026-03-15
Owner: current `A2` controller
Role: exact bounded `A2_WORKER` dispatch packet for integrating new graph/provenance tooling into core system docs

## Dispatch identity

- `dispatch_id: A2_WORKER__DOCS_INTEGRATE_GRAPH_AND_PROVENANCE__2026_03_15__v1`
- `thread_class: A2_WORKER`
- `model: GPT-5.4 Medium`
- `BOOT_SURFACE: /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `ROLE_LABEL: A2H Upgrade Docs`
- `ROLE_TYPE: A2_HIGH_UPGRADE_DOCS`
- `ROLE_SCOPE: one bounded pass to integrate the new graph subset tools and provenance validation changes into core specs only`

## Source artifacts

- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/compile_first_controller_a1_launch_subset_graph.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/refresh_first_controller_a1_launch_subset_graph.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_first_controller_a1_launch_subset_graph.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_a1_worker_launch_packet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_a1_queue_status_packet.py`

## BOUNDED_SCOPE

Run one bounded pass that:
- integrates the new graph subset tooling and provenance validation changes into the core specs listed above
- updates only the minimum necessary sections

Do not:
- change code
- widen into new tooling
- touch runs or A2 intake maintenance
- refactor unrelated spec sections

## EXPECTED_OUTPUTS

- one bounded set of doc edits in the listed specs only
- one bounded `A2_UPDATE_NOTE` only if a real source-bound delta exists
- one `NEXT_STEP` value:
  - `STOP`
  - `ONE_MORE_BOUNDED_A2_PASS_NEEDED`
- one raw returned result file written by the worker itself into:
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__DOCS_INTEGRATE_GRAPH_AND_PROVENANCE__2026_03_15__v1__return.txt`
- one raw closeout staging text file written by the worker itself into:
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__DOCS_INTEGRATE_GRAPH_AND_PROVENANCE__2026_03_15__v1.txt`

## CLOSEOUT_ROUTE

- `thread-run-monitor`
- `thread-closeout-auditor`
- `closeout-result-ingest`

## CONTINUATION_POLICY

- `AUTO_GO_ON_ALLOWED = NO`

## Exact prompt to send

```text
Use $ratchet-a2-a1.

Use the current A2 boot:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md

Run one bounded A2_HIGH_UPGRADE_DOCS pass only.

dispatch_id: A2_WORKER__DOCS_INTEGRATE_GRAPH_AND_PROVENANCE__2026_03_15__v1
ROLE_LABEL: A2H Upgrade Docs
ROLE_TYPE: A2_HIGH_UPGRADE_DOCS
ROLE_SCOPE: one bounded pass to integrate the new graph subset tools and provenance validation changes into core specs only

Use only these artifacts:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/tools/compile_first_controller_a1_launch_subset_graph.py
- /home/ratchet/Desktop/Codex Ratchet/system_v3/tools/refresh_first_controller_a1_launch_subset_graph.py
- /home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_first_controller_a1_launch_subset_graph.py
- /home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_a1_worker_launch_packet.py
- /home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_a1_queue_status_packet.py

Task:
- integrate the new graph subset tooling and provenance validation changes into the core specs listed above
- update only the minimum necessary sections

Rules:
- do not change code
- do not widen into new tooling
- do not touch runs or A2 intake maintenance
- stop after one bounded pass

Before your final answer:
- write the exact final closeout body to:
  - /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__DOCS_INTEGRATE_GRAPH_AND_PROVENANCE__2026_03_15__v1__return.txt
  - /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__DOCS_INTEGRATE_GRAPH_AND_PROVENANCE__2026_03_15__v1.txt
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
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__DOCS_INTEGRATE_GRAPH_AND_PROVENANCE__2026_03_15__v1__return.txt
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__DOCS_INTEGRATE_GRAPH_AND_PROVENANCE__2026_03_15__v1.txt
```

## STOP_RULE

Stop after one bounded doc integration pass.
