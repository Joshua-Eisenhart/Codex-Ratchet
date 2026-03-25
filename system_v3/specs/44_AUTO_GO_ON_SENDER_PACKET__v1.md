# AUTO_GO_ON_SENDER_PACKET__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for bounded continuation send packets

## Purpose

This note defines the exact sender packet used after:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/41_AUTO_GO_ON_RULE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/42_AUTO_GO_ON_APPLICATOR__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/43_AUTO_GO_ON_EXECUTION_PATH__v1.md`

It exists so both:
- current manual operator sending
- later browser automation

use the same exact continuation object.

## Packet role

This packet is the final handoff object between:
- a decision of `SEND_ONE_GO_ON`
- and the actual act of sending:
  - `go on`

It is thread-targeted and single-use.

## Required fields

Every sender packet must include:

1. `TARGET_THREAD_ID`
- exact target thread identity

2. `THREAD_CLASS`
- exactly one of:
  - `A2_WORKER`
  - `A1_WORKER`

3. `MESSAGE_TO_SEND`
- must be exactly:
  - `go on`

4. `EXPECTED_RETURN_SHAPE`
- the minimum result shape expected after this continuation

5. `STOP_CONDITION`
- the exact bounded stop condition expected after this continuation

6. `CONTINUATION_COUNT`
- integer count since last manual review

7. `SOURCE_DECISION_RECORD`
- exact path to the record that produced `SEND_ONE_GO_ON`

8. `BOOT_SURFACE`
- the boot the target thread is running under

9. `BOUNDED_SCOPE`
- one-line restatement of the exact continuation scope

## Hard rules

1. `ONE_PACKET_ONE_SEND`
- each sender packet authorizes one send only

2. `MESSAGE_LOCK`
- `MESSAGE_TO_SEND` may only be:
  - `go on`

3. `NO_CONTROLLER_TARGET`
- this packet may not target an `A2_CONTROLLER`

4. `NO_PRO_TARGET`
- this packet may not target external `Pro` threads

5. `COUNT_LOCK`
- if `CONTINUATION_COUNT >= 1`, no new sender packet may be issued without fresh manual review

## Packet template

```text
AUTO_GO_ON_SENDER_PACKET
TARGET_THREAD_ID: <exact id>
THREAD_CLASS: <A2_WORKER or A1_WORKER>
MESSAGE_TO_SEND: go on
EXPECTED_RETURN_SHAPE: <one short line>
STOP_CONDITION: <one exact stop condition>
CONTINUATION_COUNT: <0 or 1>
SOURCE_DECISION_RECORD: <exact repo path>
BOOT_SURFACE: <exact repo path>
BOUNDED_SCOPE: <one short line>
```

## Current execution path

### Manual operator path

1. applicator returns `SEND_ONE_GO_ON`
2. sender packet is produced
3. operator sends exactly:
- `go on`
4. returned result is captured

### Future browser path

1. applicator returns `SEND_ONE_GO_ON`
2. sender packet is produced
3. browser automation reads packet
4. browser automation sends exactly:
- `go on`
5. returned result is captured

## Block conditions

Do not issue a sender packet if:
- target thread is unclear
- `THREAD_CLASS` is missing or blocked
- `STOP_CONDITION` is vague
- `SOURCE_DECISION_RECORD` is missing
- continuation count is already exhausted

## Immediate implication

After this note:
- the system has the exact final object needed for bounded continuation sending

Still missing:
- an actual runner that consumes this packet automatically

So the remaining gap is now execution tooling, not continuation semantics.

