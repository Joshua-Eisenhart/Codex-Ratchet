# AUTO_GO_ON_APPLICATOR__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for bounded continuation execution

## Purpose

This note defines the first execution surface that applies:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/41_AUTO_GO_ON_RULE__v1.md`

It answers:
- what a returned thread result must be checked against
- when one automatic `go on` is actually sent
- when the thread must stop
- when the thread must route to closeout
- when manual controller review is required

This is still a control surface, not a bot by itself.

## Inputs

The applicator works on one returned thread result at a time.

Minimum input set:
- `THREAD_CLASS`
- `ROLE_AND_SCOPE`
- `WHAT_YOU_READ`
- `WHAT_YOU_UPDATED`
- `NEXT_STEP`
- `IF_ONE_MORE_PASS`
- current continuation count since last manual review

If any required input is missing:
- route to `MANUAL_REVIEW`

## Output decisions

The applicator may emit exactly one of:

1. `SEND_ONE_GO_ON`
2. `STOP_NOW`
3. `ROUTE_TO_CLOSEOUT`
4. `MANUAL_REVIEW_REQUIRED`

## Execution order

### Step 1: class gate

Read `THREAD_CLASS`.

If:
- `A2_CONTROLLER`
then:
- output `MANUAL_REVIEW_REQUIRED`

If:
- `A2_WORKER`
- or `A1_WORKER`
continue

If class is missing or unknown:
- output `MANUAL_REVIEW_REQUIRED`

### Step 2: metadata gate

Check presence of:
- `NEXT_STEP`
- `ROLE_AND_SCOPE`
- `WHAT_YOU_READ`
- `WHAT_YOU_UPDATED`

If `NEXT_STEP = ONE_MORE_BOUNDED_PASS_NEEDED`, also require:
- `IF_ONE_MORE_PASS`

If any required field is missing:
- output `ROUTE_TO_CLOSEOUT`

### Step 3: stop gate

If:
- `NEXT_STEP = STOP`
then:
- output `STOP_NOW`

### Step 4: bounded-step gate

If `NEXT_STEP = ONE_MORE_BOUNDED_PASS_NEEDED`, check that `IF_ONE_MORE_PASS` includes:
- one exact bounded step
- exact touched files or artifact families
- one exact stop condition

If not:
- output `ROUTE_TO_CLOSEOUT`

### Step 5: block-case gate

Check for blocked conditions from:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/41_AUTO_GO_ON_RULE__v1.md`

If any blocked condition is true:
- output `ROUTE_TO_CLOSEOUT`

### Step 6: ceiling gate

If continuation count since last manual review is already `1` or more:
- output `MANUAL_REVIEW_REQUIRED`

### Step 7: role purity gate

For `A1_WORKER`:
- role must remain one of:
  - `A1_ROSETTA`
  - `A1_PROPOSAL`
  - `A1_PACKAGING`
- and must not switch role mid-thread

For `A2_WORKER`:
- scope must remain inside bounded A2 worker work

If role purity fails:
- output `ROUTE_TO_CLOSEOUT`

### Step 8: final decision

If all gates pass:
- output `SEND_ONE_GO_ON`

## Required emitted continuation text

If decision = `SEND_ONE_GO_ON`:
- emit exactly:

```text
go on
```

No added prose.

## Required routing text

If decision = `STOP_NOW`:
- do not send `go on`
- mark the thread stopped in controller state

If decision = `ROUTE_TO_CLOSEOUT`:
- route to:
  - `thread-closeout-auditor`

If decision = `MANUAL_REVIEW_REQUIRED`:
- do not continue automatically
- return the exact gating reason

## Controller summary fields

Every applicator pass should record:
- `THREAD_CLASS`
- `DECISION`
- `REASON`
- `CONTINUATION_COUNT`
- `AUTO_GO_ON_ALLOWED`

## Immediate implication

After this note:
- the system has both:
  - continuation policy
  - continuation application logic

Still missing:
- an actual sender/runner that executes the `SEND_ONE_GO_ON` decision without manual operator action

