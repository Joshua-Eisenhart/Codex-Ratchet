# BROWSER_CODEX_THREAD_TARGET_CAPTURE__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for bounded browser-assisted Codex continuation

## Purpose

This note defines the first practical capture step for:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/51_BROWSER_CODEX_THREAD_TARGET__v1.md`

It exists because the browser continuation chain is now specified through:
- sender packet
- proof packet
- target packet
- helper validation
- Playwright bridge plan

But there is still no small bounded helper that turns known thread metadata into a valid:
- `BROWSER_CODEX_THREAD_TARGET_v1`

without hand-editing JSON.

## Capture role

`BROWSER_CODEX_THREAD_TARGET_CAPTURE` is a bounded metadata capture step.

It does not:
- decide whether a thread may continue
- send `go on`
- interpret thread results
- run Playwright

It only creates one valid browser target packet from one known Codex worker thread description.

## Required capture fields

Every capture step must provide:

1. `TARGET_THREAD_ID`
- exact thread id

2. `THREAD_CLASS`
- exactly one of:
  - `A2_WORKER`
  - `A1_WORKER`

3. `WORKSPACE_ROOT`
- exact workspace root for the thread

4. `THREAD_TITLE_HINT`
- short visible thread title or title fragment

5. `THREAD_URL_OR_ROUTE`
- exact route if known
- else `NONE`

6. `VISIBLE_VERIFICATION_TEXT`
- one visible marker used to confirm the right thread before send

7. `COMPOSER_READY_HINT`
- one short note describing the expected ready-to-send composer state

8. `SOURCE_CAPTURE_RECORD`
- exact repo path to the note or record that justified this capture

9. `TARGET_STATUS`
- exactly one of:
  - `READY`
  - `STALE`
  - `UNVERIFIED`

## Hard rules

1. `NO_IMPLICIT_READY`
- `READY` may only be emitted if the capture step has enough information to support it

2. `NO_CONTROLLER_CLASS`
- controller threads may not be captured with this surface

3. `NO_PRO_CLASS`
- external `Pro` threads may not be captured with this surface

4. `ROUTE_HONESTY`
- if no route is actually known, `THREAD_URL_OR_ROUTE` must be `NONE`

5. `CAPTURE_IS_NOT_SEND`
- this packet alone does not authorize browser send

## Intended helper

The first helper for this surface should:
- accept the required fields as CLI arguments
- normalize them into `BROWSER_CODEX_THREAD_TARGET_v1`
- reject invalid class/status combinations
- write one JSON packet only

## Immediate implication

After this note:
- the browser continuation path no longer depends on handwritten target JSON
- the next gap is no longer capture mechanics, but real target acquisition and later execution
