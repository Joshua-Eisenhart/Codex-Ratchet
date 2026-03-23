# A2_UPDATE_NOTE__WORKER_SELF_SAVE_CLOSEOUT_PROCESS_CORRECTION__2026_03_15__v1

Status: `DERIVED_A2`
Date: 2026-03-15

## What changed

Corrected the external worker launch process so it no longer depends on the operator manually carrying returned files back into the repo.

Updated surfaces:

1. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_WORKER_LAUNCH_HANDOFF__NEXT_TWO_SYSTEM_THREADS__2026_03_15__v1.md`
2. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_WORKER_DISPATCH_PACKET__VALIDATOR_PROVENANCE_HARDENING__2026_03_15__v1.md`
3. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_WORKER_DISPATCH_PACKET__PLANNER_GLOBAL_DEFAULTS_AUDIT__2026_03_15__v1.md`
4. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/THREAD_CLOSEOUT_CAPTURE_QUICKSTART__v1.md`

## Correct rule

For bounded external worker lanes:

- the worker should self-save its exact final closeout body into:
  - `work/audit_tmp/parallel_codex_worker_returns/<dispatch_id>__return.txt`
  - `work/audit_tmp/thread_closeout_packets/<dispatch_id>.txt`
- the operator should only launch the worker and wait for the bounded reply
- the controller can later ingest the saved closeout staging text into the closeout sink

## Why

The earlier launch wording incorrectly made the operator the transport layer for worker returns. That is not the intended shared-workspace process and creates avoidable friction plus capture risk.

## Consequence

The current two-thread batch is still valid, but the prompts should now be launched with the self-save instructions, not the old manual carry-back assumption.
