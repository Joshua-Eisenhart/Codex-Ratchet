# BROWSER_CODEX_THREAD_TARGET__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for bounded browser-assisted Codex thread continuation

## Purpose

This note defines the missing target-metadata artifact for browser-assisted `go on` sending.

It exists because:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/browser_go_on_helper.py`
  can validate sender packets and emit proof packets,
- but a real browser send still needs one stable target description for the exact Codex worker thread.

Without this surface, browser execution would still rely on guessed thread identity.

## Packet role

`BROWSER_CODEX_THREAD_TARGET_v1` is the exact target description consumed alongside:
- `AUTO_GO_ON_SENDER_PACKET_v1`

It does not decide whether a thread may continue.
It only identifies where the continuation is allowed to be sent.

## Required fields

Every target packet must include:

1. `TARGET_THREAD_ID`
- exact thread id, matching the sender packet

2. `THREAD_CLASS`
- exactly one of:
  - `A2_WORKER`
  - `A1_WORKER`

3. `THREAD_PLATFORM`
- must be exactly:
  - `CODEX_DESKTOP`

4. `WORKSPACE_ROOT`
- exact workspace root path expected by the thread

5. `THREAD_TITLE_HINT`
- one short visible title hint

6. `THREAD_URL_OR_ROUTE`
- exact addressable route if one exists, else `NONE`

7. `VISIBLE_VERIFICATION_TEXT`
- one short visible string that should appear if the target is correct

8. `COMPOSER_READY_HINT`
- one short description of the expected send surface

9. `SOURCE_CAPTURE_RECORD`
- exact path to the record that produced this target packet

10. `TARGET_STATUS`
- exactly one of:
  - `READY`
  - `STALE`
  - `UNVERIFIED`

## Hard rules

1. `NO_CONTROLLER_TARGET`
- this packet may not target an `A2_CONTROLLER`

2. `NO_PRO_TARGET`
- this packet may not target an external `Pro` thread

3. `ID_LOCK`
- `TARGET_THREAD_ID` must match the paired sender packet

4. `STATUS_LOCK`
- browser send may proceed only if:
  - `TARGET_STATUS = READY`

5. `VERIFICATION_LOCK`
- `VISIBLE_VERIFICATION_TEXT` must be checked before any send attempt

## Packet template

```text
BROWSER_CODEX_THREAD_TARGET
TARGET_THREAD_ID: <exact thread id>
THREAD_CLASS: <A2_WORKER or A1_WORKER>
THREAD_PLATFORM: CODEX_DESKTOP
WORKSPACE_ROOT: <exact workspace root path>
THREAD_TITLE_HINT: <one short title hint>
THREAD_URL_OR_ROUTE: <exact route or NONE>
VISIBLE_VERIFICATION_TEXT: <one short verification string>
COMPOSER_READY_HINT: <one short composer hint>
SOURCE_CAPTURE_RECORD: <exact repo path>
TARGET_STATUS: <READY | STALE | UNVERIFIED>
```

## Relationship to the browser helper

The browser helper must not perform a real send attempt unless both are present:
- one valid `AUTO_GO_ON_SENDER_PACKET_v1`
- one valid `BROWSER_CODEX_THREAD_TARGET_v1`

The sender packet answers:
- should the message be sent

The target packet answers:
- where exactly it may be sent

## Immediate implication

After this note:
- browser-assisted continuation no longer needs to guess Codex thread identity
- the remaining implementation gap is pairing this target packet with the existing helper
