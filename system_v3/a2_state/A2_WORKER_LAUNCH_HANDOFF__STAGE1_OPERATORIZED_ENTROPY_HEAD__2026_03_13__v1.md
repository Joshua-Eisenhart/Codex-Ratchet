# A2_WORKER_LAUNCH_HANDOFF__STAGE1_OPERATORIZED_ENTROPY_HEAD__2026_03_13__v1

Status: ACTIVE OPERATOR SURFACE / NONCANON
Date: 2026-03-13
Owner: current `A2` controller
Role: final idiot-proof launch handoff for the current Stage-1 operatorized entropy head worker

## Launch now

Open now:
- `1` new Codex worker thread for `W1`

Keep open:
- the current controller thread as `C0`

Do not open now:
- `W2`
- `A1`

## Slot map

`C0`
- this current thread
- class:
  - `A2_CONTROLLER`
- role:
  - wait for the `W1` result in the shared worker-result sink
  - route the result through monitor / closeout if needed
  - decide the next exact bounded move

`W1`
- one new Codex thread
- model:
  - `GPT-5.4 Medium`
- class:
  - `A2_WORKER`
- role:
  - `A2H Refined Fuel Non-Sims`
- dispatch packet:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_WORKER_DISPATCH_PACKET__STAGE1_OPERATORIZED_ENTROPY_HEAD__2026_03_13__v1.md`

## Exact instructions for launching `W1`

1. Open `1` new Codex thread
2. Set model to `GPT-5.4 Medium`
3. Paste the exact prompt from:
   - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_WORKER_DISPATCH_PACKET__STAGE1_OPERATORIZED_ENTROPY_HEAD__2026_03_13__v1.md`
4. Send it once
5. Wait for the bounded result
6. Do not send `go on` unless the returned result explicitly says:
   - `NEXT_STEP = ONE_MORE_BOUNDED_A2_PASS_NEEDED`
   - and gives one exact next bounded step
7. Save the full returned `W1` result into:
   - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_HIGH_REFINERY_PASS__STAGE1_OPERATORIZED_ENTROPY_HEAD__2026_03_13__v1__A2_WORKER__return.txt`
8. Return to `C0`

## Stop condition

This launch handoff ends when:
- `W1` has been launched
- or the operator decides not to launch it

The wave ends only after:
- `W1` returns
- and `C0` decides the next exact bounded move
