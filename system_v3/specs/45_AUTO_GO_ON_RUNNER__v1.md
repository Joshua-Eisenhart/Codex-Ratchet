# AUTO_GO_ON_RUNNER__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for bounded continuation runner design

## Purpose

This note defines the first runnable control-loop design that consumes:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/44_AUTO_GO_ON_SENDER_PACKET__v1.md`

It sits after:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/41_AUTO_GO_ON_RULE__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/42_AUTO_GO_ON_APPLICATOR__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/43_AUTO_GO_ON_EXECUTION_PATH__v1.md`

This note answers:
- what the runner does
- what the runner does not do
- how one bounded continuation cycle executes
- what remains manual versus later automatable

## Runner role

The runner is the control-loop stage that:
1. takes a returned thread result
2. routes it through the applicator
3. produces a sender packet if continuation is allowed
4. executes the allowed send path
5. waits for the next bounded return

It is not a swarm manager.
It handles one continuation decision at a time.

## Current live runner mode

Current live mode:
- `RUNNER_MODE__MANUAL_SEND`

Meaning:
- the runner may produce the sender packet
- the operator still performs the actual send

Future modes:
- `RUNNER_MODE__CODEX_ASSISTED_SEND`
- `RUNNER_MODE__BROWSER_AUTOMATED_SEND`

## Inputs

Minimum runner inputs:
- one captured thread result
- one stable thread identifier
- current continuation count
- current thread class

Optional but useful:
- closeout sink packet
- explicit thread platform metadata

## Runner outputs

The runner emits exactly one of:
- `RUNNER_OUTPUT__STOP`
- `RUNNER_OUTPUT__CLOSEOUT`
- `RUNNER_OUTPUT__MANUAL_REVIEW`
- `RUNNER_OUTPUT__SENDER_PACKET`

## Execution cycle

### Step 1: capture

Read one returned thread result.

If the result is not captured in a usable form:
- emit `RUNNER_OUTPUT__MANUAL_REVIEW`

### Step 2: apply continuation rule

Run:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/42_AUTO_GO_ON_APPLICATOR__v1.md`

Decision must be exactly one of:
- `SEND_ONE_GO_ON`
- `STOP_NOW`
- `ROUTE_TO_CLOSEOUT`
- `MANUAL_REVIEW_REQUIRED`

### Step 3: map decision to runner output

If decision = `STOP_NOW`:
- emit `RUNNER_OUTPUT__STOP`

If decision = `ROUTE_TO_CLOSEOUT`:
- emit `RUNNER_OUTPUT__CLOSEOUT`

If decision = `MANUAL_REVIEW_REQUIRED`:
- emit `RUNNER_OUTPUT__MANUAL_REVIEW`

If decision = `SEND_ONE_GO_ON`:
- build:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/44_AUTO_GO_ON_SENDER_PACKET__v1.md`
- emit `RUNNER_OUTPUT__SENDER_PACKET`

### Step 4: execute send path

Current live path:
- `RUNNER_MODE__MANUAL_SEND`

Execution:
1. emit sender packet
2. operator sends exactly:
   - `go on`
3. runner waits for the next bounded return

### Step 5: recapture

When the next bounded return arrives:
- increment continuation count
- re-enter the cycle from Step 1

## Hard rules

1. `ONE_RETURN_AT_A_TIME`
- runner processes one returned thread result at a time

2. `ONE_SEND_AT_A_TIME`
- runner emits at most one sender packet per cycle

3. `NO_FREE_CHAINING`
- if continuation count reaches the hard ceiling from:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/41_AUTO_GO_ON_RULE__v1.md`
- runner must stop and require manual review

4. `NO_PRO_RUNNER`
- this runner does not currently execute continuation for external `Pro` threads

## Current implementation status

What exists now:
- policy
- applicator
- execution path
- sender packet
- runner design

What does not exist yet:
- executable program or browser layer that runs this automatically

## Immediate implication

After this note:
- the full continuation loop is now designed end-to-end

Remaining gap:
- implementation

So the system now has the complete control design for auto-`go on`,
but not yet the executable tool that enacts it.

