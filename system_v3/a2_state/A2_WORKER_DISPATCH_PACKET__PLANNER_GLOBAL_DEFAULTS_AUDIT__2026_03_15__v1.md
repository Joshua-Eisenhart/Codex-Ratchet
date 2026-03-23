# A2_WORKER_DISPATCH_PACKET__PLANNER_GLOBAL_DEFAULTS_AUDIT__2026_03_15__v1

Status: ACTIVE OPERATOR SURFACE / NONCANON
Date: 2026-03-15
Owner: current `A2` controller
Role: exact bounded `A2_WORKER` dispatch packet for remaining planner-global default audit in family-slice mode

## Dispatch identity

- `dispatch_id: A2_WORKER__PLANNER_GLOBAL_DEFAULTS_AUDIT__2026_03_15__v1`
- `thread_class: A2_WORKER`
- `model: GPT-5.4 Medium`
- `BOOT_SURFACE: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `ROLE_LABEL: A1 Strategy Audit`
- `ROLE_TYPE: A1_STRATEGY_AUDIT`
- `ROLE_SCOPE: one bounded audit of remaining planner-global laws inside family-slice mode, with at most one justified patch`

## Source artifacts

- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a2_to_a1_family_slice_models.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/autoratchet.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py`

## BOUNDED_SCOPE

Run one bounded audit that:
- identifies whether any remaining family-slice branch semantics are still encoded only as planner-local universal defaults
- if one real hidden universal law remains, patches at most one such law
- updates only the focused tests needed for that one patch

Do not widen into:
- new family-slice ontology
- broad runtime refactors
- queue/control companion work
- intake cleanup

## EXPECTED_OUTPUTS

- one bounded planner-global audit result
- exact files read
- exact files updated
- focused test commands actually run
- one bounded `A2_UPDATE_NOTE` only if a real source-bound delta exists
- one bounded `A2_TO_A1_IMPACT_NOTE` only if a real proposal-side consequence exists
- one `NEXT_STEP` value:
  - `STOP`
  - `ONE_MORE_BOUNDED_A2_PASS_NEEDED`
- one raw returned result file written by the worker itself into:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__PLANNER_GLOBAL_DEFAULTS_AUDIT__2026_03_15__v1__return.txt`
- one raw closeout staging text file written by the worker itself into:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__PLANNER_GLOBAL_DEFAULTS_AUDIT__2026_03_15__v1.txt`
- no operator copy-back step

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

Run one bounded A1_STRATEGY_AUDIT pass only.

dispatch_id: A2_WORKER__PLANNER_GLOBAL_DEFAULTS_AUDIT__2026_03_15__v1
ROLE_LABEL: A1 Strategy Audit
ROLE_TYPE: A1_STRATEGY_AUDIT
ROLE_SCOPE: one bounded audit of remaining planner-global laws inside family-slice mode, with at most one justified patch

Use only these artifacts:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a2_to_a1_family_slice_models.py
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/autoratchet.py
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py

Task:
- identify whether any remaining family-slice branch semantics are still encoded only as planner-local universal defaults
- if one real hidden universal law remains, patch at most one such law
- update only the focused tests needed for that one patch

Rules:
- no new family-slice ontology
- no broad runtime refactor
- no queue/control companion work
- no intake cleanup
- stop after one bounded pass

Before your final answer:
- write the exact final closeout body to:
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__PLANNER_GLOBAL_DEFAULTS_AUDIT__2026_03_15__v1__return.txt
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__PLANNER_GLOBAL_DEFAULTS_AUDIT__2026_03_15__v1.txt
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
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__PLANNER_GLOBAL_DEFAULTS_AUDIT__2026_03_15__v1__return.txt
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__PLANNER_GLOBAL_DEFAULTS_AUDIT__2026_03_15__v1.txt
```

## STOP_RULE

Stop after one bounded planner-global defaults audit pass.
