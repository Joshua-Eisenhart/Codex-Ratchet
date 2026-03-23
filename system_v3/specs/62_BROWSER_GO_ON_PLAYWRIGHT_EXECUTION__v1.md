# BROWSER_GO_ON_PLAYWRIGHT_EXECUTION__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for bounded Playwright execution of browser go-on plans

## Purpose

This note defines the first executable layer after:
- `BROWSER_GO_ON_PLAYWRIGHT_PLAN_v1`

It exists so the system can consume one emitted Playwright plan and either:
- execute it in `validate_only`
- or execute it in guarded `real_send_once`

without improvising command behavior.

## Role

The executor consumes:
- one `BROWSER_GO_ON_PLAYWRIGHT_PLAN_v1`

and emits:
- one `BROWSER_GO_ON_PROOF_PACKET_v1`

It may also emit:
- screenshots
- snapshots
- command logs
- timeout-backed proof packets

## Required execution modes

1. `validate_only`
- open target route
- snapshot
- require the snapshot output to contain the expected verification text
- optionally snapshot again if required by plan
- do not send text
- emit proof packet

2. `real_send_once`
- requires explicit operator enable flag
- open target route
- snapshot
- require the snapshot output to contain the expected verification text before any send
- perform exactly one bounded send:
  - type `go on`
  - press `Enter`
- snapshot after send attempt
- emit proof packet

## Hard rules

1. no execution without a valid `READY` plan
2. no execution if `plan_mode = real_send_once` and explicit send enable is absent
3. no send text other than:
   - `go on`
4. no retry loop
5. no chained sends
6. one proof packet per execution attempt
7. command stall/timeout must still emit a proof packet

## Command mapping

Allowed wrapper commands:
- `open`
- `snapshot`
- `type`
- `press`

The executor may not invent commands outside the plan family.

## Proof behavior

If execution is blocked before any browser action:
- `SEND_STATUS = SEND_BLOCKED`

If a browser command stalls or times out:
- `SEND_STATUS = SEND_FAILED`
- `DETAIL = command_timeout:<command>:<timeout_sec>`

If validate-only completes:
- `SEND_STATUS = SEND_BLOCKED`
- `DETAIL = browser_send_not_attempted_validate_only`

If the snapshot does not contain the expected verification text:
- `SEND_STATUS = SEND_BLOCKED`
- `DETAIL = visible_verification_text_not_found_in_snapshot`

If real-send mode is requested without explicit enable:
- `SEND_STATUS = SEND_BLOCKED`
- `DETAIL = real_send_requires_explicit_enable`

If real-send mode executes browser commands but send is not proven:
- `SEND_STATUS = SEND_FAILED`

If real-send mode executes and send is attempted:
- `SEND_STATUS = SEND_SUCCESS`

## Immediate implication

After this note:
- the Playwright bridge no longer ends at plan emission
- there is now one bounded executor contract for turning a ready plan into a proof packet
