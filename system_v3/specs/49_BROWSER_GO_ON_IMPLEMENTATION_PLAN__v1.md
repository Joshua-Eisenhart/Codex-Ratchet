# BROWSER_GO_ON_IMPLEMENTATION_PLAN__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for browser-assisted continuation implementation planning

## Purpose

This note turns:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/48_BROWSER_ASSISTED_GO_ON_EXECUTION__v1.md`

into a concrete implementation target.

It defines:
- what the first browser helper must do
- what it must refuse to do
- what inputs and outputs it must use
- what proof it must emit after a send attempt

## Implementation target

The first implementation target is:
- one bounded helper that consumes:
  - `AUTO_GO_ON_SENDER_PACKET_v1`
- and attempts:
  - one browser-assisted `go on` send

It is not a scheduler.
It is not a result interpreter.
It is not a thread monitor.

## Required input

The implementation target must consume one sender packet with all required fields from:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/44_AUTO_GO_ON_SENDER_PACKET__v1.md`

Minimum runtime fields:
- `TARGET_THREAD_ID`
- `THREAD_CLASS`
- `MESSAGE_TO_SEND`
- `EXPECTED_RETURN_SHAPE`
- `STOP_CONDITION`
- `CONTINUATION_COUNT`
- `SOURCE_DECISION_RECORD`
- `BOOT_SURFACE`
- `BOUNDED_SCOPE`

## Required execution steps

1. `LOAD_THREAD`
- open the exact target thread

2. `VERIFY_THREAD`
- confirm visible identity matches `TARGET_THREAD_ID`

3. `VERIFY_CLASS`
- confirm the packet targets only:
  - `A2_WORKER`
  - `A1_WORKER`

4. `VERIFY_MESSAGE`
- confirm `MESSAGE_TO_SEND = go on`

5. `VERIFY_COMPOSER`
- confirm the input surface is ready

6. `SEND`
- send exactly:
  - `go on`

7. `CAPTURE_PROOF`
- emit one proof packet

8. `RETURN`
- stop and hand control back to result capture

## Hard refusals

The first browser helper must refuse to run if:
- thread is controller-class
- thread is external `Pro`
- thread identity cannot be verified
- continuation count exceeds allowed ceiling
- message differs from `go on`
- sender packet is missing required fields

## Proof requirement

Every send attempt must emit a proof packet, whether the send succeeds or fails.

Proof packet status must be exactly one of:
- `SEND_SUCCESS`
- `SEND_BLOCKED`
- `SEND_FAILED`

## Output expectation

The browser helper must not return prose as its primary artifact.

Primary output must be:
- one `BROWSER_GO_ON_PROOF_PACKET_v1`

Optional secondary outputs:
- one screenshot path
- one snapshot path

## Implementation order

1. build proof packet surface
2. build browser helper against sender packet + proof packet only
3. keep execution operator-mediated until proof quality is reliable
4. add one guarded `REAL_SEND_MODE` only after validate-only proof path exists
5. only later integrate with wider automation

## Immediate implication

After this note:
- browser assistance has a concrete first build target
- remaining work is implementation against a strict packet-in / proof-out contract
- live send still requires:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/60_BROWSER_REAL_SEND_MODE__v1.md`
