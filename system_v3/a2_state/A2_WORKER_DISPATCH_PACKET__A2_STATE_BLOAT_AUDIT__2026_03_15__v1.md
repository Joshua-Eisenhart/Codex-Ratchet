# A2_WORKER_DISPATCH_PACKET__A2_STATE_BLOAT_AUDIT__2026_03_15__v1

Status: ACTIVE OPERATOR SURFACE / NONCANON
Date: 2026-03-15
Owner: current `A2` controller
Role: exact bounded `A2_WORKER` dispatch packet for A2 state bloat audit and consolidation planning

## Dispatch identity

- `dispatch_id: A2_WORKER__A2_STATE_BLOAT_AUDIT__2026_03_15__v1`
- `thread_class: A2_WORKER`
- `model: GPT-5.4 Medium`
- `BOOT_SURFACE: /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `ROLE_LABEL: A2M Contradiction Reprocess`
- `ROLE_TYPE: A2_M_CONTRADICTION_REPROCESS`
- `ROLE_SCOPE: one bounded pass to audit A2 state bloat and propose a safe consolidation plan only`

## Source artifacts

- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md`

## BOUNDED_SCOPE

Run one bounded pass that:
- audits A2 state bloat (redundant update notes, duplicate surfaces, stale snapshots)
- proposes a safe consolidation plan and classification rules

Do not:
- delete or move any files
- touch runs or A2 intake maintenance
- change doctrine, core specs, or queue design
- widen into A1 work

## EXPECTED_OUTPUTS

- one bounded A2 state bloat audit report (text only)
- one safe consolidation plan with clear classification rules
- one bounded `A2_UPDATE_NOTE` only if a real source-bound delta exists
- one `NEXT_STEP` value:
  - `STOP`
  - `ONE_MORE_BOUNDED_A2_PASS_NEEDED`
- one raw returned result file written by the worker itself into:
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__A2_STATE_BLOAT_AUDIT__2026_03_15__v1__return.txt`
- one raw closeout staging text file written by the worker itself into:
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__A2_STATE_BLOAT_AUDIT__2026_03_15__v1.txt`

## CLOSEOUT_ROUTE

- `thread-run-monitor`
- `thread-closeout-auditor`
- `closeout-result-ingest`

## CONTINUATION_POLICY

- `AUTO_GO_ON_ALLOWED = NO`

## Exact prompt to send

```text
Use $ratchet-a2-a1.
Use $a2-a1-memory-admission-guard for any proposed consolidation rules.

Use the current A2 boot:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md

Run one bounded A2_M_CONTRADICTION_REPROCESS pass only.

dispatch_id: A2_WORKER__A2_STATE_BLOAT_AUDIT__2026_03_15__v1
ROLE_LABEL: A2M Contradiction Reprocess
ROLE_TYPE: A2_M_CONTRADICTION_REPROCESS
ROLE_SCOPE: one bounded pass to audit A2 state bloat and propose a safe consolidation plan only

Use only these artifacts:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md

Task:
- audit A2 state bloat (redundant update notes, duplicate surfaces, stale snapshots)
- propose a safe consolidation plan and classification rules

Rules:
- do not delete or move any files
- do not work on runs or A2 intake maintenance
- do not change doctrine, core specs, or queue design
- stop after one bounded pass

Before your final answer:
- write the exact final closeout body to:
  - /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__A2_STATE_BLOAT_AUDIT__2026_03_15__v1__return.txt
  - /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__A2_STATE_BLOAT_AUDIT__2026_03_15__v1.txt
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
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__A2_STATE_BLOAT_AUDIT__2026_03_15__v1__return.txt
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__A2_STATE_BLOAT_AUDIT__2026_03_15__v1.txt
```

## STOP_RULE

Stop after one bounded A2 state bloat audit pass.
