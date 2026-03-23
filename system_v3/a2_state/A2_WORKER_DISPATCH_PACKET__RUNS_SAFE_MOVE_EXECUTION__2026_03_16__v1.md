# A2_WORKER_DISPATCH_PACKET__RUNS_SAFE_MOVE_EXECUTION__2026_03_16__v1

Status: ACTIVE OPERATOR SURFACE / NONCANON
Date: 2026-03-16
Owner: current `A2` controller
Role: exact bounded `A2_WORKER` dispatch packet for executing only the already-cleared safe moves in `system_v3/runs`

## Dispatch identity

- `dispatch_id: A2_WORKER__RUNS_SAFE_MOVE_EXECUTION__2026_03_16__v1`
- `thread_class: A2_WORKER`
- `model: GPT-5.4 Medium`
- `BOOT_SURFACE: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `ROLE_LABEL: A2H Archived State`
- `ROLE_TYPE: A2_HIGH_ARCHIVED_STATE`
- `ROLE_SCOPE: one bounded pass to execute only the already-cleared safe moves for runs cleanup`

## Source artifacts

- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_WORKER_DISPATCH_PACKET__RUNS_CLEANUP_PLAN__2026_03_15__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/processed/2026-03-16/A2_WORKER__RUNS_CLEANUP_PLAN__2026_03_15__v1__return.txt`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runs`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/archive`

## BOUNDED_SCOPE

Run one bounded pass that:
- archives exactly `system_v3/runs/RUN_LLM_LANE_SMOKE_02`
- quarantines only the exact `.DS_Store` files explicitly named in the prior runs cleanup plan
- writes one small manifest note of what was moved

Do not:
- move any other run family
- infer new candidates
- delete anything
- touch A2 intake, A2 state, or specs

## EXPECTED_OUTPUTS

- exact move execution for the already-cleared candidates only
- one small manifest note under `work/audit_tmp` listing moved paths
- one raw returned result file written by the worker itself into:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__RUNS_SAFE_MOVE_EXECUTION__2026_03_16__v1__return.txt`
- one raw closeout staging text file written by the worker itself into:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__RUNS_SAFE_MOVE_EXECUTION__2026_03_16__v1.txt`

## Exact prompt to send

```text
Use $safe-run-maintenance.

Use the current A2 boot:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md

Run one bounded A2_HIGH_ARCHIVED_STATE pass only.

dispatch_id: A2_WORKER__RUNS_SAFE_MOVE_EXECUTION__2026_03_16__v1
ROLE_LABEL: A2H Archived State
ROLE_TYPE: A2_HIGH_ARCHIVED_STATE
ROLE_SCOPE: one bounded pass to execute only the already-cleared safe moves for runs cleanup

Use only these artifacts:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_WORKER_DISPATCH_PACKET__RUNS_CLEANUP_PLAN__2026_03_15__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/processed/2026-03-16/A2_WORKER__RUNS_CLEANUP_PLAN__2026_03_15__v1__return.txt
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runs
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/archive

Task:
- archive exactly system_v3/runs/RUN_LLM_LANE_SMOKE_02
- quarantine only the exact .DS_Store files explicitly named in the prior cleanup plan
- write one small manifest note under work/audit_tmp listing moved paths

Rules:
- do not move any other run family
- do not infer new candidates
- do not delete anything
- do not touch A2 intake, A2 state, or specs
- stop after one bounded pass

Before your final answer:
- write the exact final closeout body to:
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__RUNS_SAFE_MOVE_EXECUTION__2026_03_16__v1__return.txt
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__RUNS_SAFE_MOVE_EXECUTION__2026_03_16__v1.txt
- if the folders do not exist, create them
- do not ask the operator to save, paste back, or carry files
- if you cannot self-save, report that exact blocker and stop
```

## STOP_RULE

Stop after the exact cleared moves only.
