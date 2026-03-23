# AUTO_GO_ON_RULE__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for bounded continuation law

## Purpose

This note defines when a thread may receive an automatic `go on`.

It exists because:
- manual `go on` use is inconsistent
- some bounded continuations are safe
- some continuations cause drift, hidden-memory dependence, or low-yield churn

This note governs:
- Codex upper-loop thread continuation
- later automation for bounded auto-continue

It does not authorize broad autonomy.

## Core rule

Automatic `go on` is allowed only when a thread has already completed one bounded pass and has emitted an explicit bounded continuation contract.

If that contract is missing, blurred, weak, or role-breaking:
- the thread must stop

## Required continuation metadata

A thread is eligible for automatic `go on` only if its result explicitly contains:

1. `NEXT_STEP`
- exactly one of:
  - `STOP`
  - `ONE_MORE_BOUNDED_PASS_NEEDED`

2. `IF_ONE_MORE_PASS`
- required if and only if `NEXT_STEP = ONE_MORE_BOUNDED_PASS_NEEDED`
- must include:
  - one exact bounded step
  - the exact touched files or artifact families
  - one exact stop condition after that step

3. `ROLE_AND_SCOPE`
- must remain compatible with the current thread class and boot

4. `WHAT_YOU_READ`
- enough to show the continuation still rests on repo-held artifacts rather than only hidden thread memory

5. `WHAT_YOU_UPDATED`
- enough to show the previous pass produced real bounded work

If any of these are missing, malformed, or contradictory:
- auto-continue is blocked

## Allowed auto-continue cases

Automatic `go on` is allowed only for:

### `A2_WORKER`
- one more bounded family-routing pass
- one more bounded cleanup-prep pass
- one more bounded delta-consolidation pass
- one more bounded source-capture or return-capture pass

### `A1_WORKER`
- one more bounded role-pure pass
- only if the current result explicitly asks for one more bounded pass
- only if role remains the same:
  - `A1_ROSETTA`
  - or `A1_PROPOSAL`
  - or `A1_PACKAGING`

### `A2_CONTROLLER`
- blocked by default
- controller work should normally be manually directed, not auto-continued

## Blocked auto-continue cases

Automatic `go on` is blocked if any of the following is true:

1. `NEXT_STEP = STOP`
2. the next step is recap, polish, or metadata symmetry completion
3. the thread drifted off role
4. the next step broadens scope instead of finishing one bounded step
5. the next step depends mainly on hidden thread memory
6. the thread already crossed its strongest useful stopping boundary
7. the thread is waiting on external input
8. the thread is duplicate or overlap-prone
9. the thread would blur:
- `A2` with `A1`
- proposal with authority
- external exploratory space with current owner surfaces

## Hard ceiling

No thread may receive more than:
- `1` automatic `go on` in a row

After one automatic continuation:
- the thread must re-emit a fresh continuation contract
- and must be re-evaluated again

So:
- auto-continue never chains freely
- it is always one bounded continuation at a time

## Decision function

Auto-continue is allowed only if all checks pass:

`AUTO_GO_ON_ALLOWED =`
- thread class allowed
- valid continuation metadata present
- no blocked case triggered
- previous pass produced real bounded value
- continuation count for this thread < 1 since last manual review

Otherwise:
- `AUTO_GO_ON_ALLOWED = NO`

## Required automation behavior

Future automation must do this in order:

1. inspect returned thread result
2. extract:
- thread class
- next-step status
- bounded-step contract
- stop condition
3. test against this rule
4. if allowed:
- send exactly one automatic `go on`
5. if not allowed:
- route to:
  - stop
  - closeout
  - or manual controller review

## Interaction with existing control surfaces

This note extends:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/40_PARALLEL_CODEX_THREAD_CONTROL__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/THREAD_AND_AUTOMATION_PROCESS_FLOWS__2026_03_11__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/THREAD_RUN_DIAGNOSIS_AND_STOP_RULES__v1.md`

And is enforced later through:
- `thread-run-monitor`
- `thread-closeout-auditor`
- `closeout-result-ingest`

## Immediate implication

Current system state after this note:
- thread continuation can now be judged by a precise rule
- but no automatic sender exists yet

So this note closes the policy gap, not the execution gap.

