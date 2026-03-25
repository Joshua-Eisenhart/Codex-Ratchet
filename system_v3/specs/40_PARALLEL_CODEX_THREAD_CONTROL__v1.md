# PARALLEL_CODEX_THREAD_CONTROL__v1
Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for bounded parallel Codex thread operation

## Purpose

This note defines the first concrete current control surface for parallel Codex threads.

It answers:
- how many Codex upper-loop threads may run at once
- what slot types are allowed
- what may overlap
- what must stay single-owner
- how stop/closeout routing works

This is not broad swarm authorization.
It is the current bounded parallel control law.

## Hard rules

1. `ONE_CONTROLLER_ONLY`
- there is exactly one active `A2` controller thread
- no second thread may silently assume controller authority

2. `WORKER_SLOTS_ONLY`
- extra Codex concurrency is worker-slot concurrency, not controller duplication

3. `NON_OVERLAP_REQUIRED`
- two live Codex worker threads may not target the same family, queue, or cleanup class unless the purpose is an explicit comparison

4. `A1_IS_SEPARATE`
- `A1` does not share a slot with `A2`
- `A1` may run only from valid queue status and handoff

5. `THREADS_ARE_BOOTED`
- every active Codex thread must run from the proper current boot

6. `ONE_BOUNDED_PASS_PER_THREAD`
- each thread performs one bounded pass only
- continuation requires a separate valid stop/continue decision

## Allowed live slot layout now

Current safe Codex upper-loop layout:

### Slot C0: controller
- class: `A2_CONTROLLER`
- count: exactly `1`
- boot:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- allowed work:
  - execution-state updates
  - queue routing
  - handoff readiness
  - bounded control/build/audit notes

### Slot W1: bounded A2 worker
- class: `A2_WORKER`
- count: up to `1`
- boot:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- allowed work:
  - family routing
  - high-entropy revisit
  - cleanup-prep
  - return capture
  - delta consolidation

### Slot W2: second bounded A2 worker
- class: `A2_WORKER`
- count: up to `1`
- boot:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- allowed work:
  - same worker classes as `W1`
- extra rule:
  - must be non-overlapping with `W1`

### Slot A1: optional dispatch-governed A1 thread
- class: `A1_WORKER`
- count: `0` or `1`
- boot:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md`
- allowed work:
  - one bounded `A1_ROSETTA`
  - or one bounded `A1_PROPOSAL`
  - or one bounded `A1_PACKAGING`
- start condition:
  - valid packet from:
    - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/34_A1_READY_PACKET__v1.md`

## Maximum live Codex set now

Allowed at once:
- `1` controller
- `2` bounded A2 workers
- `1` optional A1 worker

So the current hard ceiling is:
- `4` live Codex upper-loop threads total

This does not override the external `Pro` envelope.

## Valid overlap matrix

Allowed:
- controller + one A2 worker
- controller + two non-overlapping A2 workers
- controller + one A2 worker + one A1 worker
- controller + two non-overlapping A2 workers + one A1 worker

Blocked:
- controller + second controller
- two A2 workers on the same packet family without explicit comparison purpose
- A1 without valid queue status
- two simultaneous A1 threads
- A1 plus A2 on the same exact role/fuel packet in a blurred way

## Launch order

When parallel Codex work is used, launch in this order:

1. controller remains primary
2. fill `W1` with the highest-value bounded A2 worker
3. fill `W2` only if another non-overlapping A2 worker clearly exists
4. fill `A1` only if `a1?` returns a real ready packet

Default bias:
- prefer `controller + W1`
- add `W2` only when there is real separation
- add `A1` only when dispatch-ready

## Required per-thread metadata

Every live Codex thread must be classifiable by:
- `THREAD_CLASS`
- `BOOT_SURFACE`
- `BOUNDED_SCOPE`
- `EXPECTED_OUTPUTS`
- `STOP_RULE`
- `CLOSEOUT_ROUTE`

Minimum values:
- `CLOSEOUT_ROUTE = thread-run-monitor -> thread-closeout-auditor -> closeout-result-ingest`

## Stop and closeout routing

Every live non-controller thread must pass through:
1. monitor check
2. closeout audit
3. result capture if useful

If a worker reaches a useful stopping boundary:
- it must stop instead of drifting
- the slot becomes reusable

## Immediate implication

Current gap closed by this note:
- parallel Codex work is no longer just implied by the scale envelope
- the live slot model is now explicit and bounded

Current next gap:
- later auto-go-on / auto-monitor / auto-dispatch still do not exist
- this note defines manual control law first
