# AUTO_GO_ON_EXECUTION_PATH__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for bounded continuation execution path

## Purpose

This note defines the first execution path for automatic `go on`.

It sits after:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/41_AUTO_GO_ON_RULE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/42_AUTO_GO_ON_APPLICATOR__v1.md`

This note answers:
- what metadata must exist before `SEND_ONE_GO_ON` can actually be executed
- what the sender path looks like now
- what remains manual
- what later browser automation must eventually do

This note still does not authorize free autonomy.

## Current execution stages

The path now has 4 stages:

1. `RESULT_CAPTURE`
2. `APPLICATOR_DECISION`
3. `SEND_PATH_SELECTION`
4. `EXECUTION_OR_HOLD`

## Stage 1: Result capture

Input must exist as one of:
- repo-held thread result artifact
- normalized closeout packet
- explicit pasted bounded result that can be captured

Required fields:
- `THREAD_CLASS`
- `THREAD_ID` or stable thread label
- `NEXT_STEP`
- `IF_ONE_MORE_PASS` if present
- current continuation count

If capture is incomplete:
- stop at `MANUAL_REVIEW_REQUIRED`

## Stage 2: Applicator decision

Use:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/42_AUTO_GO_ON_APPLICATOR__v1.md`

Output must be exactly one of:
- `SEND_ONE_GO_ON`
- `STOP_NOW`
- `ROUTE_TO_CLOSEOUT`
- `MANUAL_REVIEW_REQUIRED`

## Stage 3: Send-path selection

If applicator output is not `SEND_ONE_GO_ON`:
- do not enter send-path selection

If applicator output is `SEND_ONE_GO_ON`, classify the thread by send path:

### `PATH_MANUAL_OPERATOR`
- current default
- operator sends:
  - `go on`

### `PATH_CODEX_ASSISTED`
- future state
- system prepares:
  - exact target thread
  - exact message text
  - exact expected stop condition
- operator still confirms/send action

### `PATH_BROWSER_AUTOMATED`
- later state only
- browser automation executes the send action against the exact thread target

## Current default path

Right now:
- `PATH_MANUAL_OPERATOR` is the only approved execution path

Meaning:
- the system can decide `SEND_ONE_GO_ON`
- but a human still sends the message

## Required sender metadata

Before any future non-manual sender is allowed, the system must know:
- exact target thread identity
- exact thread class
- exact continuation count
- exact message to send
- exact stop condition expected after that continuation

Minimum sender packet:
- `TARGET_THREAD_ID`
- `THREAD_CLASS`
- `MESSAGE_TO_SEND`
- `EXPECTED_RETURN_SHAPE`
- `STOP_CONDITION`
- `CONTINUATION_COUNT`

## Message text

The only allowed automatic continuation message is:

```text
go on
```

No added explanation.
No added widening.
No side instructions.

## Execution blockers

Even if applicator returns `SEND_ONE_GO_ON`, execution is blocked if:
- target thread identity is unclear
- continuation count is unclear
- expected stop condition is unclear
- thread platform is not reachable by the current send path
- the thread is external `Pro`

## Pro-thread rule

Automatic `go on` does not currently apply to:
- external web UI `Pro` threads

Why:
- current send/return loop for `Pro` is still operator-mediated
- later browser automation may reduce this, but not yet

So current scope of this note is:
- Codex thread continuation first

## Near-term buildout order

1. keep `PATH_MANUAL_OPERATOR` as the live execution path
2. add a repo-held sender packet format later
3. only after that consider browser execution of the send action

## Immediate implication

After this note:
- the system has:
  - continuation policy
  - continuation applicator
  - continuation execution path

Still missing:
- the actual sender packet surface
- the actual browser or app execution layer

So the gap is now narrower:
- not "how should continuation work?"
- but "how is the final send action represented and executed?"

