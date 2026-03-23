# A2_WORKER_DISPATCH_PACKET__INTAKE_COLD_CLUSTER_PLAN__2026_03_15__v1

Status: ACTIVE OPERATOR SURFACE / NONCANON
Date: 2026-03-15
Owner: current `A2` controller
Role: exact bounded `A2_WORKER` dispatch packet for the next cold-cluster intake plan (no moves)

## Dispatch identity

- `dispatch_id: A2_WORKER__INTAKE_COLD_CLUSTER_PLAN__2026_03_15__v1`
- `thread_class: A2_WORKER`
- `model: GPT-5.4 Medium`
- `BOOT_SURFACE: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `ROLE_LABEL: A2H Archived State`
- `ROLE_TYPE: A2_HIGH_ARCHIVED_STATE`
- `ROLE_SCOPE: one bounded pass to identify the next cold intake cluster for quarantine planning (no moves)`

## Source artifacts

- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/run_maintenance_reports/SYSTEM_V3_A2_HIGH_ENTROPY_INTAKE_SHORTLIST__2026_03_15.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/run_maintenance_reports/SYSTEM_V3_A2_HIGH_ENTROPY_INTAKE_RETENTION_POLICY_DRAFT__2026_03_15.md`

## BOUNDED_SCOPE

Run one bounded pass that:
- identifies one next cold intake family/cluster suitable for quarantine planning
- produces one repo-held plan note with explicit candidate list and rationale
- makes no filesystem moves

Do not widen into:
- actual quarantine moves
- intake index rewrites
- owner-memory edits
- runtime code changes

## EXPECTED_OUTPUTS

- one bounded plan note under `work/audit_tmp/run_maintenance_reports/`
- exact files read
- one `NEXT_STEP` value:
  - `STOP`
  - `ONE_MORE_BOUNDED_A2_PASS_NEEDED`
- one raw returned result file written by the worker itself into:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__INTAKE_COLD_CLUSTER_PLAN__2026_03_15__v1__return.txt`
- one raw closeout staging text file written by the worker itself into:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__INTAKE_COLD_CLUSTER_PLAN__2026_03_15__v1.txt`

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

Run one bounded A2_HIGH_ARCHIVED_STATE pass only.

dispatch_id: A2_WORKER__INTAKE_COLD_CLUSTER_PLAN__2026_03_15__v1
ROLE_LABEL: A2H Archived State
ROLE_TYPE: A2_HIGH_ARCHIVED_STATE
ROLE_SCOPE: one bounded pass to identify the next cold intake cluster for quarantine planning (no moves)

Use only these artifacts:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/run_maintenance_reports/SYSTEM_V3_A2_HIGH_ENTROPY_INTAKE_SHORTLIST__2026_03_15.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/run_maintenance_reports/SYSTEM_V3_A2_HIGH_ENTROPY_INTAKE_RETENTION_POLICY_DRAFT__2026_03_15.md

Task:
- identify one next cold intake family/cluster suitable for quarantine planning
- produce one repo-held plan note with explicit candidate list and rationale
- make no filesystem moves

Rules:
- no actual quarantine moves
- no intake index rewrites
- no owner-memory edits
- no runtime code changes
- stop after one bounded pass

Before your final answer:
- write the exact final closeout body to:
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__INTAKE_COLD_CLUSTER_PLAN__2026_03_15__v1__return.txt
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__INTAKE_COLD_CLUSTER_PLAN__2026_03_15__v1.txt
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
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__INTAKE_COLD_CLUSTER_PLAN__2026_03_15__v1__return.txt
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__INTAKE_COLD_CLUSTER_PLAN__2026_03_15__v1.txt
```

## STOP_RULE

Stop after one bounded intake cold-cluster plan pass.
