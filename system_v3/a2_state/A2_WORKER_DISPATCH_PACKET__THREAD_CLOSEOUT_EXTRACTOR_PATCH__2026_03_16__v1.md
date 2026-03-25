# A2_WORKER_DISPATCH_PACKET__THREAD_CLOSEOUT_EXTRACTOR_PATCH__2026_03_16__v1

Status: ACTIVE OPERATOR SURFACE / NONCANON
Date: 2026-03-16
Owner: current `A2` controller
Role: exact bounded `A2_WORKER` dispatch packet for making closeout extraction accept the current worker closeout format

## Dispatch identity

- `dispatch_id: A2_WORKER__THREAD_CLOSEOUT_EXTRACTOR_PATCH__2026_03_16__v1`
- `thread_class: A2_WORKER`
- `model: GPT-5.4 Medium`
- `BOOT_SURFACE: /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `ROLE_LABEL: Controller Master`
- `ROLE_TYPE: A2_CONTROLLER`
- `ROLE_SCOPE: one bounded pass to patch thread closeout extraction so NEXT_STEP-format worker returns ingest cleanly`

## Source artifacts

- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/extract_thread_closeout_packet.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/append_thread_closeout_packet.py`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__RUNS_CLEANUP_PLAN__2026_03_15__v1.txt`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__A2_INTAKE_BLOAT_TRIAGE__2026_03_15__v1.txt`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__DOCS_INTEGRATE_GRAPH_AND_PROVENANCE__2026_03_15__v1.txt`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__A2_STATE_BLOAT_AUDIT__2026_03_15__v1.txt`

## BOUNDED_SCOPE

Run one bounded pass that:
- patches the extractor to accept the current `ROLE_AND_SCOPE` / `ACTION_CHOSEN` / `WHAT_YOU_UPDATED` / `TESTS_RUN` / `RESULT` / `NEXT_STEP` / `CLOSED_STATEMENT` shape
- adds focused regression coverage

Do not:
- redesign the packet schema
- change the append tool contract
- widen into unrelated controller tooling

## EXPECTED_OUTPUTS

- one bounded extractor patch
- one focused test
- one raw returned result file written by the worker itself into:
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__THREAD_CLOSEOUT_EXTRACTOR_PATCH__2026_03_16__v1__return.txt`
- one raw closeout staging text file written by the worker itself into:
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__THREAD_CLOSEOUT_EXTRACTOR_PATCH__2026_03_16__v1.txt`

## Exact prompt to send

```text
Use $thread-closeout-auditor.

Use the current A2 boot:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md

Run one bounded controller-tooling pass only.

dispatch_id: A2_WORKER__THREAD_CLOSEOUT_EXTRACTOR_PATCH__2026_03_16__v1
ROLE_LABEL: Controller Master
ROLE_TYPE: A2_CONTROLLER
ROLE_SCOPE: one bounded pass to patch thread closeout extraction so NEXT_STEP-format worker returns ingest cleanly

Use only these artifacts:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/tools/extract_thread_closeout_packet.py
- /home/ratchet/Desktop/Codex Ratchet/system_v3/tools/append_thread_closeout_packet.py
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__RUNS_CLEANUP_PLAN__2026_03_15__v1.txt
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__A2_INTAKE_BLOAT_TRIAGE__2026_03_15__v1.txt
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__DOCS_INTEGRATE_GRAPH_AND_PROVENANCE__2026_03_15__v1.txt
- /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__A2_STATE_BLOAT_AUDIT__2026_03_15__v1.txt

Task:
- patch the extractor to accept the current ROLE_AND_SCOPE / ACTION_CHOSEN / WHAT_YOU_UPDATED / TESTS_RUN / RESULT / NEXT_STEP / CLOSED_STATEMENT shape
- add focused regression coverage

Rules:
- do not redesign the packet schema
- do not change the append tool contract
- do not widen into unrelated controller tooling
- stop after one bounded pass

Before your final answer:
- write the exact final closeout body to:
  - /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__THREAD_CLOSEOUT_EXTRACTOR_PATCH__2026_03_16__v1__return.txt
  - /home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__THREAD_CLOSEOUT_EXTRACTOR_PATCH__2026_03_16__v1.txt
- if the folders do not exist, create them
- do not ask the operator to save, paste back, or carry files
- if you cannot self-save, report that exact blocker and stop
```

## STOP_RULE

Stop after extractor compatibility and one focused regression.
