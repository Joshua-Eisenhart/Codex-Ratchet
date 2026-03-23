# BROWSER_CAPTURE_RECORD_TO_TARGET__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for bounded browser-assisted Codex continuation

## Purpose

This note defines the bounded conversion step from:
- `BROWSER_CODEX_THREAD_CAPTURE_RECORD_v1`

to:
- `BROWSER_CODEX_THREAD_TARGET_v1`

It exists because the browser path now has:
- observed capture records
- target packet schema
- helper-side target validation

But still lacks one controlled conversion rule that maps observation into:
- `READY`
- `UNVERIFIED`
- `STALE`

without ad hoc manual judgment.

## Conversion role

This conversion step:
- reads one observed capture record
- adds the missing stable thread metadata
- emits one browser target packet

It does not:
- authorize send by itself
- replace helper-side validation
- interpret continuation policy

## Required additional inputs

The capture record already provides:
- thread id
- thread class
- observed title
- observed route
- verification text
- composer readiness
- source note

The conversion step must also receive:

1. `WORKSPACE_ROOT`
- exact workspace root

2. `COMPOSER_READY_HINT`
- one short send-surface hint for later verification

## Status mapping rules

1. emit `READY` only if all are true:
- `COMPOSER_READY_OBSERVED = YES`
- `THREAD_URL_OR_ROUTE_OBSERVED != NONE`
- `THREAD_TITLE_OBSERVED` is nonempty
- `VISIBLE_VERIFICATION_TEXT_OBSERVED` is nonempty

2. emit `UNVERIFIED` if:
- route is missing
- or composer was not ready
- or any required observed field is missing

3. emit `STALE` only by explicit operator override
- never by default inference
- and explicit override may not promote an otherwise unready capture to `READY`

## Hard rules

1. `NO_UPGRADE_WITHOUT_ROUTE`
- `NONE` route may not become `READY`

2. `NO_UPGRADE_WITHOUT_COMPOSER`
- `COMPOSER_READY_OBSERVED = NO` may not become `READY`

2a. `READY_REQUIRES_OBSERVED_COMPOSER_FIELD`
- emitted target packets must carry the observed composer-ready state
- helper-side validation must reject `READY` targets unless:
  - `COMPOSER_READY_OBSERVED = YES`

3. `NO_GUESSED_TEXT`
- observed title and verification text must pass through unchanged

4. `SOURCE_LOCK`
- `SOURCE_CAPTURE_RECORD` in the emitted target packet must point back to the capture record used

## Immediate implication

After this note:
- one real observed capture can be turned into one valid browser target packet
- the next browser gap is no longer capture conversion, but live target acquisition and later send execution
