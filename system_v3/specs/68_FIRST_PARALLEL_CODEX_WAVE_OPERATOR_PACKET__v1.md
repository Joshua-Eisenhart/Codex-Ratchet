# FIRST_PARALLEL_CODEX_WAVE_OPERATOR_PACKET__v1

Status: DRAFT / NONCANON / ACTIVE OPERATOR SURFACE
Date: 2026-03-11
Owner: current `A2` controller

## Purpose

This note turns the first parallel Codex wave into one idiot-proof operator handoff.

It answers:
- how many threads to open
- which model to use
- what exact prompt to paste into `W1`
- what to expect back
- when to stop

## Current launch decision

Launch now:
- `C0`
- `W1`

Do not launch now:
- `W2`
- `A1`

Reason:
- `W1` has a clear bounded non-overlapping role
- `W2` is still unjustified
- current `A1` queue state is `NO_WORK`

## Slot map

`C0`
- keep this current `A2` controller thread active
- role:
  - maintain `CURRENT_EXECUTION_STATE`
  - monitor `W1`
  - read `W1` result from the shared worker-result sink
  - decide `STOP / SEND_ONE_GO_ON / ROUTE_TO_CLOSEOUT / MANUAL_REVIEW_REQUIRED`

`W1`
- one new Codex worker thread
- class:
  - `A2_WORKER`
- role label:
  - `A2_HIGH_REFINERY_PASS__REFINEDFUEL_RUN_NOW_WAVE_1`

## Exact operator instructions for `W1`

1. Open `1` new Codex thread
2. Set model to `GPT-5.4 Medium`
3. Paste the exact prompt below
4. Send it once
5. Wait for the bounded result
6. Do **not** send `go on` unless the returned `NEXT_STEP` says:
   - `ONE_MORE_BOUNDED_A2_PASS_NEEDED`
   - and it names one exact next bounded step
7. Save the full returned result into:
   - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_HIGH_REFINERY_PASS__REFINEDFUEL_RUN_NOW_WAVE_1__A2_WORKER__return.txt`
8. After saving, return to `C0`

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

## Expected result shape

The sink-held worker result should make it possible for `C0` to:
- stop the wave cleanly
- send one bounded `go on`
- route the worker to closeout
- or mark manual review required

## Stop rule

This first parallel wave ends when:
- `W1` returns its bounded result
- `C0` records the decision

No `W2` launch and no `A1` launch should happen during this wave unless a fresh explicit controller note changes the state.
