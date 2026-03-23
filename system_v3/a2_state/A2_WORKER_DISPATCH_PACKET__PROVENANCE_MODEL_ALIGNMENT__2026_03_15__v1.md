# A2_WORKER_DISPATCH_PACKET__PROVENANCE_MODEL_ALIGNMENT__2026_03_15__v1

Status: ACTIVE OPERATOR SURFACE / NONCANON
Date: 2026-03-15
Owner: current `A2` controller
Role: exact bounded `A2_WORKER` dispatch packet for aligning models/schemas with newly stamped validation provenance fields

## Dispatch identity

- `dispatch_id: A2_WORKER__PROVENANCE_MODEL_ALIGNMENT__2026_03_15__v1`
- `thread_class: A2_WORKER`
- `model: GPT-5.4 Medium`
- `BOOT_SURFACE: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `ROLE_LABEL: A2M Promotion Review`
- `ROLE_TYPE: A2_MID_PROMOTION_REVIEW`
- `ROLE_SCOPE: one bounded pass to align Pydantic models and emitted schemas with validation provenance fields added to launch packet/bundle/queue artifacts`

## Source artifacts

- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_launch_packet_from_family_slice.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/prepare_a1_launch_bundle_from_family_slice.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a1_queue_status_packet.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a1_worker_launch_packet_models.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a1_queue_surface_models.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/emit_a1_worker_launch_packet_pydantic_schema.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/emit_a1_queue_surface_pydantic_schemas.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_PACKET_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS_PACKET_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_packet_pydantic_stack.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_surface_pydantic_stack.py`

## BOUNDED_SCOPE

Run one bounded pass that:
- ensures Pydantic models and emitted schemas include the new validation provenance fields
- updates only the focused tests needed for that exact alignment

Do not widen into:
- planner-family doctrine changes
- queue redesign
- graph compiler work
- intake or run maintenance

## EXPECTED_OUTPUTS

- one bounded model/schema alignment result
- exact files read
- exact files updated
- focused test commands actually run
- one bounded `A2_UPDATE_NOTE` only if a real source-bound delta exists
- one `NEXT_STEP` value:
  - `STOP`
  - `ONE_MORE_BOUNDED_A2_PASS_NEEDED`
- one raw returned result file written by the worker itself into:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__PROVENANCE_MODEL_ALIGNMENT__2026_03_15__v1__return.txt`
- one raw closeout staging text file written by the worker itself into:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__PROVENANCE_MODEL_ALIGNMENT__2026_03_15__v1.txt`

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

Run one bounded A2_MID_PROMOTION_REVIEW pass only.

dispatch_id: A2_WORKER__PROVENANCE_MODEL_ALIGNMENT__2026_03_15__v1
ROLE_LABEL: A2M Promotion Review
ROLE_TYPE: A2_MID_PROMOTION_REVIEW
ROLE_SCOPE: one bounded pass to align Pydantic models and emitted schemas with validation provenance fields added to launch packet/bundle/queue artifacts

Use only these artifacts:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_launch_packet_from_family_slice.py
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/prepare_a1_launch_bundle_from_family_slice.py
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a1_queue_status_packet.py
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a1_worker_launch_packet_models.py
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a1_queue_surface_models.py
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/emit_a1_worker_launch_packet_pydantic_schema.py
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/emit_a1_queue_surface_pydantic_schemas.py
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_PACKET_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS_PACKET_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_worker_launch_packet_pydantic_stack.py
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_surface_pydantic_stack.py

Task:
- ensure Pydantic models and emitted schemas include the new validation provenance fields
- update only the focused tests needed for that exact alignment

Rules:
- no planner-family doctrine changes
- no queue redesign
- no graph compiler work
- no intake or run maintenance
- stop after one bounded pass

Before your final answer:
- write the exact final closeout body to:
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__PROVENANCE_MODEL_ALIGNMENT__2026_03_15__v1__return.txt
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__PROVENANCE_MODEL_ALIGNMENT__2026_03_15__v1.txt
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
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__PROVENANCE_MODEL_ALIGNMENT__2026_03_15__v1__return.txt
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__PROVENANCE_MODEL_ALIGNMENT__2026_03_15__v1.txt
```

## STOP_RULE

Stop after one bounded provenance model alignment pass.
