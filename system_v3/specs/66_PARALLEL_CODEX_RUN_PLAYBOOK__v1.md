# PARALLEL_CODEX_RUN_PLAYBOOK__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller

## Purpose

This note turns the current slot model, boot chain, `A1` queue, and auto-`go on` chain into one concrete operator playbook for bounded parallel Codex work.

It answers:
- what the first safe parallel Codex wave looks like
- what each slot should do
- what may not overlap
- when `A1` is allowed to start
- how continuation and closeout are handled

This is not a broad swarm plan.
It is the current bounded runbook.

## Governing surfaces

This playbook assumes and extends:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/30_A2_TO_A1_HANDOFF_CONTRACT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/34_A1_READY_PACKET__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/40_PARALLEL_CODEX_THREAD_CONTROL__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/41_AUTO_GO_ON_RULE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/42_AUTO_GO_ON_APPLICATOR__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/66_PARALLEL_CODEX_RUN_PLAYBOOK__v1.md`

## Current safe live layout

Current allowed upper-loop layout:
- `C0`: exactly one `A2_CONTROLLER`
- `W1`: zero or one bounded `A2_WORKER`
- `W2`: zero or one second bounded non-overlapping `A2_WORKER`
- `A1`: zero or one dispatch-governed `A1_WORKER`

Hard ceiling:
- `4` live Codex threads total

## First bounded parallel wave

The first safe wave should use these slots in this order:

### Slot C0
Class:
- `A2_CONTROLLER`

Boot:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`

Current responsibilities:
- own `CURRENT_EXECUTION_STATE`
- monitor all worker slots
- evaluate `a1?`
- capture closeout / continuation decisions

### Slot W1
Class:
- `A2_WORKER`

Boot:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`

Recommended first bounded role now:
- `A2_HIGH_REFINERY_PASS` on the exact `RUN_NOW` refinedfuel set from:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/REFINEDFUEL_REVISIT_ROUTING_PASS__2026_03_11__v1.md`

### Slot W2
Class:
- `A2_WORKER`

Boot:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`

Recommended first bounded role now:
- external return preparation / source-packet preparation only
- or remain empty if no clearly non-overlapping A2 task exists

Blocked overlap:
- must not run the same refinedfuel family pass as `W1`
- must not silently become controller

### Slot A1
Class:
- `A1_WORKER`

Boot:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md`

Start condition:
- only if current queue status is one of:
  - `READY_FROM_NEW_A2_HANDOFF`
  - `READY_FROM_EXISTING_FUEL`
  - `READY_FROM_A2_PREBUILT_BATCH`

Current read:
- do not start `A1` automatically
- use only when `a1?` emits a valid current ready packet

## Launch order

Use this exact order:

1. keep `C0` active
2. launch `W1` only
3. check whether a real non-overlapping `W2` exists
4. check `a1?`
5. launch `A1` only if queue status is ready

Default bias:
- prefer `C0 + W1`
- add `W2` only if clearly separate
- add `A1` last

## Required per-thread packet

Every launched thread must have:
- `THREAD_CLASS`
- `BOOT_SURFACE`
- `BOUNDED_SCOPE`
- `EXPECTED_OUTPUTS`
- `STOP_RULE`
- `CONTINUATION_POLICY`

Minimum continuation policy values:
- `AUTO_GO_ON_ALLOWED = NO` by default unless later thread result qualifies under:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/41_AUTO_GO_ON_RULE__v1.md`

## Continuation handling

When a worker thread returns:

1. capture the raw result
2. normalize it if needed
3. apply:
   - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/42_AUTO_GO_ON_APPLICATOR__v1.md`
4. if result is:
   - `SEND_ONE_GO_ON`
     - send exactly `go on`
     - only once
   - `STOP_NOW`
     - free the slot
   - `ROUTE_TO_CLOSEOUT`
     - run closeout capture
   - `MANUAL_REVIEW_REQUIRED`
     - hold for controller review

## A1 handling

`A1` does not run because there is generally “lots of fuel.”
It runs only when current controller state emits one actual dispatch packet.

Current allowed question:
- `a1?`

Current allowed outputs:
- `A1_QUEUE_STATUS: NO_WORK`
- one current `A1_READY_PACKET`

`A1` may not:
- free-run beside `A2`
- invent its own fuel base
- treat legacy engine language as direct term heads

## Closeout path

Every non-controller slot must be routable through:
- `thread-run-monitor`
- `thread-closeout-auditor`
- `closeout-result-ingest`

No worker thread should be left as a live ambiguous lane after its bounded pass completes.

## Current recommended first live configuration

Right now the best actual bounded parallel configuration is:
- `C0` = active controller
- `W1` = refinedfuel run-now A2 pass
- `W2` = empty unless a clearly non-overlapping return-capture or packet-prep pass exists
- `A1` = empty until `a1?` returns ready

This is the current recommended start state, not maximum occupancy.

## Stop rule

This playbook remains valid until one of these changes:
- the slot ceiling changes
- `A1` queue semantics change
- automatic continuation moves beyond one bounded `go on`
- real browser-assisted continuation becomes live

Until then:
- use this note as the actual bounded runbook
- not just as a descriptive summary
