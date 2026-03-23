# SCALE_UP_ENVELOPE__2026_03_11__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL NOTE
Date: 2026-03-11
Role: current safe scale envelope for `A2`, `A1`, and external `Pro` lanes

## Purpose

This note answers one bounded controller question:

- how big can the system safely go **right now**?

It does **not** declare the system ready for broad free expansion.
It sets the current allowed concurrency envelope using the actual current state:

- current boot chain exists
- current `A1` dispatch chain exists
- current external `Pro` returns are still local-pack / scaffold heavy
- current large-scale external source coverage is still incomplete

## Current read

Ready now:
- bounded `A2` controller and worker passes
- bounded run-folder cleanup / archive-prep passes
- bounded `A2` family routing passes
- bounded external `Pro` research waves
- bounded `A1` runs from explicit queue status / handoff

Not ready now:
- large unconstrained `A2` swarms
- many simultaneous `Pro` lanes feeding straight into `A2`
- broad parallel `A1` family generation
- large ratchet campaigns over many unrelated families at once
- attractor-basin claims from volume alone
- strong engine / QIT validity claims from current external packets

## Allowed concurrency now

### `A2` Codex threads

Allowed now:
- `1` active `A2` controller thread
- plus up to `2` bounded `A2` worker threads if they are non-overlapping

So the current safe `A2` ceiling is:
- `3` total Codex `A2` threads

Conditions:
- each thread must have a proper `A2` boot
- each thread must have one bounded role
- each thread must stop after one bounded pass
- no duplicate family overlap without an explicit comparison purpose

Blocked now:
- `4+` concurrent `A2` Codex threads
- overlapping high-entropy family swarms
- broad “finish all A2-high” sweeps

### External `Pro` threads

Allowed now:
- `1` to `3` tightly bounded `Pro` research lanes at once

Preferred pattern:
- `1` primary run
- optional `2` secondary non-overlapping lanes

Conditions:
- each lane must have a distinct packet family or source-family scope
- every return must be audited before any `A2` reduction
- local-pack/scaffold-only returns do not count as scale proof

Blocked now:
- `4+` live `Pro` lanes at once
- overlapping prompts against the same packet family
- assuming downloadable zip success equals substantive coverage

### `A1` Codex threads

Allowed now:
- `0` or `1` active `A1` thread

Conditions:
- `A1` starts only from:
  - `READY_FROM_NEW_A2_HANDOFF`
  - `READY_FROM_EXISTING_FUEL`
  - `READY_FROM_A2_PREBUILT_BATCH`
- `A1` runs one bounded role only:
  - `A1_ROSETTA`
  - `A1_PROPOSAL`
  - `A1_PACKAGING`

Blocked now:
- multiple simultaneous `A1` proposal threads
- free-running `A1`
- `A1` directly mining raw source mass

## Current safe combined operating envelope

Safe now:
- `1` main `A2` controller
- up to `2` bounded extra `A2` worker passes
- up to `3` bounded `Pro` lanes
- at most `1` active `A1` thread, and only when explicitly ready

This means the current safe total live upper-loop envelope is:
- about `5` to `7` bounded threads/lane executions

Only if:
- boots are loaded
- roles are separated
- returns are audited before promotion
- no lane duplication is introduced

## Expansion triggers

The system may scale beyond the above envelope only after all of these improve:

1. `Pro` returns become source-bearing rather than mostly scaffold/local-pack
2. `A1` queueing and handoff are used successfully in live runs
3. `A2` refresh/dispatch loop remains stable under repeated bounded cycles
4. no hidden-memory drift or Desktop-procedure drift recurs
5. run-folder and `A2`-high family cleanup remain controlled under load

## Immediate implication

Current answer to “are we ready to run big ones and at scale?” is:

- `No` for true big-scale operation
- `Yes` for controlled bounded scale-up

The current system should scale by:
- more **bounded waves**
- not by broad uncontrolled multiplication
