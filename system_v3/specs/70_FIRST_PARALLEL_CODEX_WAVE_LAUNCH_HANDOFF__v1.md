# FIRST_PARALLEL_CODEX_WAVE_LAUNCH_HANDOFF__v1

Status: DRAFT / NONCANON / ACTIVE OPERATOR SURFACE
Date: 2026-03-11
Owner: current `A2` controller

## Purpose

This note is the final idiot-proof operator handoff for the first parallel Codex wave.

It tells the operator exactly:
- how many threads to open
- which model to use
- what to paste into `W1`
- what to do with `C0`
- when to stop

## Launch now

Open now:
- `1` new Codex worker thread for `W1`

Keep open:
- this current thread as `C0`

Do not open now:
- `W2`
- `A1`

## Slot map

`C0`
- this current thread
- class:
  - `A2_CONTROLLER`
- role:
  - monitor `W1`
  - wait for `W1` result to be written into the shared worker-result sink
  - evaluate result using:
    - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/69_FIRST_PARALLEL_CODEX_WAVE_C0_EVALUATION_PACKET__v1.md`

`W1`
- one new Codex thread
- model:
  - `GPT-5.4 Medium`
- class:
  - `A2_WORKER`
- role:
  - `A2_HIGH_REFINERY_PASS__REFINEDFUEL_RUN_NOW_WAVE_1`

## Exact instructions for launching `W1`

1. Open `1` new Codex thread
2. Set model to `GPT-5.4 Medium`
3. Paste the exact prompt below
4. Send it once
5. Wait for the result
6. Do **not** send `go on` inside `W1` unless the result explicitly says:
   - `NEXT_STEP = ONE_MORE_BOUNDED_A2_PASS_NEEDED`
   - and gives one exact next bounded step
7. Save the full returned `W1` result into:
   - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_HIGH_REFINERY_PASS__REFINEDFUEL_RUN_NOW_WAVE_1__A2_WORKER__return.txt`
8. Return to `C0`

## Exact prompt for `W1`

```text
Use $ratchet-a2-a1.

Use the current A2 boot:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md

Run one bounded A2_HIGH_REFINERY_PASS only.

Role label:
- A2_HIGH_REFINERY_PASS__REFINEDFUEL_RUN_NOW_WAVE_1

Use only these artifacts:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/REFINEDFUEL_REVISIT_ROUTING_PASS__2026_03_11__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_refinedfuel_constraints_entropy_term_conflict__v1
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_refinedfuel_constraints_term_conflict__v1
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_refinedfuel_constraints_entropy_source_map__v1
- /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_refinedfuel_constraints_source_map__v1

Task:
- process only the exact refinedfuel wave-1 RUN_NOW set
- classify and reduce what is still live/useful in this wave
- produce one bounded revisit result only

Rules:
- A2 only
- no A1 work
- no broad cleanup
- no new lanes
- no canon claims
- no contradiction smoothing
- stop after one bounded refinedfuel wave-1 pass

Required final output:
1. ROLE_AND_SCOPE
2. WHAT_YOU_READ
3. WHAT_YOU_UPDATED
4. REFINEDFUEL_WAVE_RESULT
- one short paragraph on the exact result of this wave
5. NEXT_STEP
Choose exactly one:
- STOP
- ONE_MORE_BOUNDED_A2_PASS_NEEDED
6. IF_ONE_MORE_PASS
Only if needed:
- one exact next bounded A2 step
7. CLOSED_STATEMENT
- one sentence saying whether this worker thread should now stop
```

## Exact instructions for `C0` after `W1` returns

When `W1` returns:
1. stay in this current thread
2. confirm the sink artifact exists at:
   - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_HIGH_REFINERY_PASS__REFINEDFUEL_RUN_NOW_WAVE_1__A2_WORKER__return.txt`
3. use:
   - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/69_FIRST_PARALLEL_CODEX_WAVE_C0_EVALUATION_PACKET__v1.md`
4. evaluate the sink-held `W1` result into exactly one:
   - `STOP_NOW`
   - `SEND_ONE_GO_ON`
   - `ROUTE_TO_CLOSEOUT`
   - `MANUAL_REVIEW_REQUIRED`

## Stop condition

This launch handoff ends when:
- `W1` has been launched
- or the operator decides not to launch it

The wave itself ends only after:
- `W1` returns
- and `C0` evaluates that result

## Do not do now

Do not:
- launch `W2`
- launch `A1`
- launch a Pro thread as part of this wave
- send multiple `go on`s in advance
