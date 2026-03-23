# BROWSER_GO_ON_PLAYWRIGHT_BRIDGE__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for bounded browser-assisted Codex continuation via Playwright

## Purpose

This note defines the first bridge between:
- validated continuation control artifacts
- and a concrete browser execution plan

It exists so the system can move from:
- sender packet
- target packet
- proof packet

to:
- one explicit Playwright execution plan

without improvising browser actions.

## Role

The bridge does not send by itself.

It consumes:
- one `AUTO_GO_ON_SENDER_PACKET_v1`
- one `BROWSER_CODEX_THREAD_TARGET_v1`

and emits:
- one bounded Playwright plan

That plan may be:
- executable
- or explicitly blocked

## Required bridge checks

Before a Playwright plan may be emitted:

1. sender packet must validate
2. target packet must validate
3. `TARGET_STATUS` must be `READY`
4. `THREAD_PLATFORM` must be `CODEX_DESKTOP`
5. `MESSAGE_TO_SEND` must be exactly:
   - `go on`

## Route rule

If:
- `THREAD_URL_OR_ROUTE = NONE`

then the bridge must emit:
- `PLAN_STATUS = BLOCKED`

with detail:
- `missing_thread_route`

## Executable plan minimum

If route data is present, the plan must include:

1. session name
2. target route
3. verification text
4. exact message
5. exact output proof path
6. exact expected post-send stop condition

## Command family

The first plan should target the local Playwright wrapper:
- `/Users/joshuaeisenhart/.codex/skills/playwright/scripts/playwright_cli.sh`

The plan may include:
- `open`
- `snapshot`
- verification step
- send step

But the bridge itself is only required to emit the plan, not execute it.

## Immediate implication

After this note:
- the browser continuation path no longer jumps directly from validation to implementation
- one exact bridge layer now exists between validated packets and a concrete Playwright send plan
