# BROWSER_GO_ON_PROOF_PACKET__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for browser-assisted continuation proof capture

## Purpose

This note defines the proof artifact emitted by browser-assisted continuation execution.

It sits after:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/48_BROWSER_ASSISTED_GO_ON_EXECUTION__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/49_BROWSER_GO_ON_IMPLEMENTATION_PLAN__v1.md`

## Packet role

The proof packet is the minimal repo-holdable evidence that one browser-assisted send attempt:
- succeeded
- was blocked
- or failed

It does not interpret the thread result.
It only records the send attempt.

## Required fields

Every proof packet must include:

1. `TARGET_THREAD_ID`
2. `THREAD_CLASS`
3. `EXECUTION_PATH`
- must be exactly:
  - `PATH_BROWSER_AUTOMATED`

4. `SEND_STATUS`
- exactly one of:
  - `SEND_SUCCESS`
  - `SEND_BLOCKED`
  - `SEND_FAILED`

5. `MESSAGE_SENT`
- must be exactly:
  - `go on`
  - or `NONE` if blocked before send

6. `SENT_AT`
- timestamp or `NONE`

7. `CONTINUATION_COUNT`

8. `SOURCE_SENDER_PACKET`
- exact path to the sender packet used

9. `STOP_CONDITION`
- copied from sender packet

10. `DETAIL`
- one short line only

11. `SCREENSHOT_PATH`
- exact path or `NONE`

12. `SNAPSHOT_PATH`
- exact path or `NONE`

## Hard rules

1. `ONE_PROOF_PER_SEND_ATTEMPT`
- every attempt emits exactly one proof packet

2. `NO_PROSE_ONLY_MODE`
- prose alone is not acceptable proof

3. `MESSAGE_LOCK`
- if `SEND_STATUS = SEND_SUCCESS`, `MESSAGE_SENT` must be:
  - `go on`

4. `BLOCKED_LOCK`
- if `SEND_STATUS = SEND_BLOCKED`, `MESSAGE_SENT` must be:
  - `NONE`

## Packet template

```text
BROWSER_GO_ON_PROOF_PACKET
TARGET_THREAD_ID: <exact id>
THREAD_CLASS: <A2_WORKER or A1_WORKER>
EXECUTION_PATH: PATH_BROWSER_AUTOMATED
SEND_STATUS: <SEND_SUCCESS | SEND_BLOCKED | SEND_FAILED>
MESSAGE_SENT: <go on or NONE>
SENT_AT: <timestamp or NONE>
CONTINUATION_COUNT: <integer>
SOURCE_SENDER_PACKET: <exact repo path>
STOP_CONDITION: <one exact stop condition>
DETAIL: <one short line>
SCREENSHOT_PATH: <exact path or NONE>
SNAPSHOT_PATH: <exact path or NONE>
```

## Immediate implication

After this note:
- the browser-assisted path has a stable proof artifact
- the first implementation can now be judged by packet quality rather than prose summaries
