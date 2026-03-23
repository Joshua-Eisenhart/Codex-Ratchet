# BROWSER_REAL_SEND_MODE__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for guarded browser-assisted continuation execution

## Purpose

This note defines the first bounded transition from:
- validate-only browser continuation

to:
- one real browser-assisted send attempt

It exists so the system does not jump from proof-only validation to live sending without
an explicit gating layer.

## Role

`REAL_SEND_MODE` is not the default.

It is a guarded execution mode that may be enabled only for one bounded send attempt after:
1. one valid `AUTO_GO_ON_SENDER_PACKET_v1`
2. one valid `BROWSER_CODEX_THREAD_TARGET_v1`
3. one valid observed-capture path
4. one successful validate-only proof path

## Allowed target scope

The first real-send mode may target only:
- `A2_WORKER`
- `A1_WORKER`

It may not target:
- controller threads
- `Pro` threads
- any thread with uncertain identity

## Required prerequisites

Before `REAL_SEND_MODE` is allowed, all of the following must be true:

1. `VALID_SENDER_PACKET`
- sender packet passes the current sender validation

2. `VALID_TARGET_PACKET`
- target packet passes current target validation

3. `OBSERVED_VERIFICATION_PRESENT`
- visible verification text exists in the observed capture

4. `COMPOSER_READY_OBSERVED`
- the observed capture says the composer is ready

5. `VALIDATE_ONLY_PROOF_PRESENT`
- there is one prior `SEND_BLOCKED` proof packet with detail:
  - `browser_send_not_attempted_validate_only`

6. `CONTINUATION_COUNT_ALLOWED`
- continuation ceiling has not been reached

## Real-send mode behavior

If all prerequisites pass, the first real-send mode may do exactly:

1. `LOAD_THREAD`
2. `VERIFY_THREAD`
3. `VERIFY_COMPOSER`
4. `SEND_EXACT_MESSAGE`
- exactly:
  - `go on`
5. `CAPTURE_PROOF`
6. `STOP`

It may not:
- send any other text
- retry automatically
- chain multiple sends
- continue after send without handing control back to the result-capture path

## Hard refusals

`REAL_SEND_MODE` must refuse to run if:
- there is no validate-only proof packet
- target status is not `READY`
- observed verification text is missing
- composer readiness was inferred rather than observed
- sender/target ids do not match
- the target platform is not `CODEX_DESKTOP`

## Proof requirement

The real-send attempt must emit one and only one proof packet:
- `SEND_SUCCESS`
- `SEND_BLOCKED`
- or `SEND_FAILED`

`SEND_SUCCESS` is allowed only if:
- the browser helper actually attempted the send
- and proof capture completed

## Manual control rule

The first implementation of `REAL_SEND_MODE` remains:
- operator-gated
- single-attempt
- no scheduler integration

That means:
- a human still decides when to invoke the helper
- the helper does not loop
- the helper does not scan for work

## Relationship to existing browser chain

Current chain:
1. observed thread capture
2. capture record
3. target packet
4. sender packet
5. validate-only proof

This note adds:
6. guarded real-send mode
7. real proof packet

## Immediate implication

After this note:
- browser continuation has an explicit live-send gate
- the next implementation step is no longer “make it send somehow”
- it is:
  - add one bounded `real_send_once` mode to the helper under this contract
