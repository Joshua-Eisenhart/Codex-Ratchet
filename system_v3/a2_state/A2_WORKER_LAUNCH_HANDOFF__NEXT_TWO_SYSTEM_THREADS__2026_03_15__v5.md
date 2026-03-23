# A2_WORKER_LAUNCH_HANDOFF__NEXT_TWO_SYSTEM_THREADS__2026_03_15__v5

Status: ACTIVE OPERATOR SURFACE / NONCANON
Date: 2026-03-15
Owner: current `A2` controller
Role: exact launch handoff for the next two justified system threads after the fourth successful self-save worker batch

## Launch now

Open now:
- `2` new Codex worker threads: `W9`, `W10`

Keep open:
- the current controller thread as `C0`

Do not open now:
- any third worker

Reason:
- the last batch completed cleanly and was ingested
- the next highest-leverage seams are:
  - runs bloat cleanup planning (archive-first, no deletions)
  - A2 intake bloat triage and de-bloat planning

## Slot map

`C0`
- this current thread
- class:
  - `A2_CONTROLLER`
- role:
  - wait for both worker returns in the shared worker-result sink
  - ingest worker self-saved closeout staging artifacts
  - route each through monitor / closeout if needed
  - decide whether one more bounded batch is justified

`W9`
- one new Codex thread
- model:
  - `GPT-5.4 Medium`
- class:
  - `A2_WORKER`
- role:
  - `A2H Archived State`
- dispatch packet:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_WORKER_DISPATCH_PACKET__RUNS_CLEANUP_PLAN__2026_03_15__v1.md`

`W10`
- one new Codex thread
- model:
  - `GPT-5.4 Medium`
- class:
  - `A2_WORKER`
- role:
  - `A2H Refined Fuel Non-Sims`
- dispatch packet:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_WORKER_DISPATCH_PACKET__A2_INTAKE_BLOAT_TRIAGE__2026_03_15__v1.md`

## Exact instructions for launching

### Launch `W9`

1. Open `1` new Codex thread
2. Set model to `GPT-5.4 Medium`
3. Paste the exact prompt from:
   - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_WORKER_DISPATCH_PACKET__RUNS_CLEANUP_PLAN__2026_03_15__v1.md`
4. Send it once
5. Wait for the bounded result
6. Do not manually save or carry back files
7. The worker must self-save its own raw return and closeout staging file into:
   - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__RUNS_CLEANUP_PLAN__2026_03_15__v1__return.txt`
   - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__RUNS_CLEANUP_PLAN__2026_03_15__v1.txt`

### Launch `W10`

1. Open `1` new Codex thread
2. Set model to `GPT-5.4 Medium`
3. Paste the exact prompt from:
   - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_WORKER_DISPATCH_PACKET__A2_INTAKE_BLOAT_TRIAGE__2026_03_15__v1.md`
4. Send it once
5. Wait for the bounded result
6. Do not manually save or carry back files
7. The worker must self-save its own raw return and closeout staging file into:
   - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__A2_INTAKE_BLOAT_TRIAGE__2026_03_15__v1__return.txt`
   - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_closeout_packets/A2_WORKER__A2_INTAKE_BLOAT_TRIAGE__2026_03_15__v1.txt`

## Stop condition

This launch handoff ends when:
- `W9` and `W10` have both been launched
- or the operator decides not to launch them

The wave ends only after:
- both workers self-save their closeout artifacts and return
- and `C0` decides the next exact bounded move
