# BROWSER_CODEX_THREAD_CAPTURE_RECORD__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for bounded browser-assisted Codex continuation

## Purpose

This note defines the observed capture record that sits before:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/53_BROWSER_CODEX_THREAD_TARGET_CAPTURE__v1.md`

It exists because one real browser target cannot honestly be marked `READY` from guessed values.
The system needs one stable artifact for the observed thread route, title, visible marker,
and composer state before creating the final browser target packet.

## Record role

`BROWSER_CODEX_THREAD_CAPTURE_RECORD_v1` is an evidence-bearing observation record.

It records what was actually seen for one Codex worker thread.

It does not:
- authorize send
- decide continuation policy
- replace the final target packet

It is the capture artifact used to justify:
- `TARGET_STATUS = READY`

## Required fields

Every capture record must include:

1. `TARGET_THREAD_ID`
- exact thread id

2. `THREAD_CLASS`
- exactly one of:
  - `A2_WORKER`
  - `A1_WORKER`

3. `THREAD_TITLE_OBSERVED`
- exact observed thread title or visible title fragment

4. `THREAD_URL_OR_ROUTE_OBSERVED`
- exact observed route or thread address

5. `VISIBLE_VERIFICATION_TEXT_OBSERVED`
- short visible marker used to verify target identity

6. `COMPOSER_READY_OBSERVED`
- exactly one of:
  - `YES`
  - `NO`

7. `OBSERVED_AT`
- timestamp string

8. `CAPTURE_METHOD`
- exactly one of:
  - `MANUAL_OPERATOR`
  - `PLAYWRIGHT_CAPTURE`

9. `SOURCE_NOTE`
- exact repo path to the note or control record that motivated this capture

## Hard rules

1. `NO_CONTROLLER_CAPTURE`
- controller threads are not valid capture targets

2. `NO_PRO_CAPTURE`
- external `Pro` threads are not valid capture targets

3. `OBSERVATION_FIRST`
- `READY` target packets must be justified by one capture record

4. `NO_GUESSED_ROUTE`
- if the route was not observed, this record may not fabricate one

5. `COMPOSER_HONESTY`
- `COMPOSER_READY_OBSERVED = NO` blocks `READY` promotion

## Relationship to the target packet

This record is not the final send target.

The final target packet still lives under:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/51_BROWSER_CODEX_THREAD_TARGET__v1.md`

The capture record exists to justify the final values used there.

## Immediate implication

After this note:
- one real live Codex worker target can be captured as an observed artifact
- the next helper can safely transform that record into a `READY` browser target packet
