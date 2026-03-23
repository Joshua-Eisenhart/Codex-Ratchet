# BROWSER_REAL_SEND_PLAYWRIGHT_BRIDGE__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for guarded real-send Playwright plan emission

## Purpose

This note defines the missing bridge between:
- `REAL_SEND_MODE`
- and one concrete Playwright execution plan

It exists so the browser chain can emit a bounded `real_send_once` plan artifact
without improvising send semantics.

## Role

The bridge does not itself send.

It consumes:
- one valid `AUTO_GO_ON_SENDER_PACKET_v1`
- one valid `BROWSER_CODEX_THREAD_TARGET_v1`
- one valid prior validate-only `BROWSER_GO_ON_PROOF_PACKET_v1`

and emits:
- one `BROWSER_GO_ON_PLAYWRIGHT_PLAN_v1`

with plan mode:
- `validate_only`
- or `real_send_once`

## Required bridge checks

Before a real-send Playwright plan may be emitted:

1. sender packet must validate
2. target packet must validate
3. target status must equal `READY`
4. thread platform must equal `CODEX_DESKTOP`
5. message to send must equal:
   - `go on`
6. prior proof packet must be present
7. prior proof packet must be:
   - `SEND_BLOCKED`
   - `detail = browser_send_not_attempted_validate_only`
8. prior proof packet must match:
   - target thread id
   - thread class
   - continuation count

## Route rule

If:
- `THREAD_URL_OR_ROUTE = NONE`

the bridge must emit:
- `PLAN_STATUS = BLOCKED`

with detail:
- `missing_thread_route`

## Real-send executable plan minimum

If all checks pass, the plan must include:

1. session name
2. target route
3. verification text
4. exact message:
   - `go on`
5. exact proof path
6. exact stop condition
7. exact plan mode:
   - `real_send_once`

## Command family

The first real-send bridge still targets the local Playwright wrapper:
- `/Users/joshuaeisenhart/.codex/skills/playwright/scripts/playwright_cli.sh`

The real-send command family may include:
- `open`
- `snapshot`
- verification step
- send step placeholder

The bridge may emit a placeholder send command description, but it may not claim
that sending already occurred.

## Hard refusals

The bridge must refuse to emit a `READY` real-send plan if:
- prior proof is missing
- prior proof is not validate-only
- target status is not `READY`
- target class is not `A2_WORKER` or `A1_WORKER`
- route is missing
- visible verification text is missing

## Immediate implication

After this note:
- validate-only and real-send plan emission are both packet-defined
- the next implementation step is no longer “invent the real-send plan”
- it is:
  - update the Playwright plan builder to emit guarded `real_send_once` plans
