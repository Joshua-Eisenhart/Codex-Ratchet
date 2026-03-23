# PARALLEL_CODEX_WORKER_RESULT_SINK__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-12
Owner: current `A2` controller

## Purpose

This note defines the shared repo-held sink for returned parallel Codex worker results.

It removes the need to paste worker results back into the controller thread when the
threads already share the same workspace.

## Sink location

Raw worker result staging directory:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns`

## Required file convention

Each returned worker result should be saved as one plain-text file:

- `<dispatch_id>__<thread_class>__return.txt`

Example:
- `A2_HIGH_REFINERY_PASS__REFINEDFUEL_RUN_NOW_WAVE_1__A2_WORKER__return.txt`

## Minimum required contents

The saved worker return must contain the full returned bounded result, including:
- `ROLE_AND_SCOPE`
- `WHAT_YOU_READ`
- `WHAT_YOU_UPDATED`
- task-specific result section
- `NEXT_STEP`
- `IF_ONE_MORE_PASS` when applicable
- `CLOSED_STATEMENT`

## Controller rule

`C0` should prefer the sink artifact over pasted chat text when both exist.

If no sink artifact exists:
- controller may temporarily fall back to pasted text
- but the wave is considered procedurally incomplete

## Stop rule

This surface only defines the sink path and file convention.
It does not itself evaluate the result.
