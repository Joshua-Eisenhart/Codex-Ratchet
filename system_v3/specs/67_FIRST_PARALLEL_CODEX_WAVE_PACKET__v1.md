# FIRST_PARALLEL_CODEX_WAVE_PACKET__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller

## Purpose

This note turns the parallel runbook into the first actual bounded launch packet.

It answers:
- what to launch now
- what not to launch now
- what each live slot should do
- what the stop conditions are

This is the first concrete parallel Codex wave.

## Governing surfaces

- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/40_PARALLEL_CODEX_THREAD_CONTROL__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/66_PARALLEL_CODEX_RUN_PLAYBOOK__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/PARALLEL_CODEX_WORKER_RESULT_SINK__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/REFINEDFUEL_REVISIT_ROUTING_PASS__2026_03_11__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_STATUS__CURRENT__2026_03_11__v1.md`

## Current launch decision

Launch now:
- `C0`
- `W1`

Do not launch now:
- `W2`
- `A1`

Reason:
- `W1` has a clear bounded non-overlapping role
- `W2` does not yet have a clearly separate high-value role
- current `A1` queue state is `NO_WORK`

## Slot C0

THREAD_CLASS:
- `A2_CONTROLLER`

BOOT_SURFACE:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`

BOUNDED_SCOPE:
- maintain `CURRENT_EXECUTION_STATE`
- monitor `W1`
- capture continuation/stop results
- evaluate whether `W2` becomes justified
- evaluate whether `a1?` changes from `NO_WORK`

STOP_RULE:
- controller remains live; do not auto-close during this wave

## Slot W1

THREAD_CLASS:
- `A2_WORKER`

BOOT_SURFACE:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`

ROLE_LABEL:
- `A2_HIGH_REFINERY_PASS__REFINEDFUEL_RUN_NOW_WAVE_1`

SOURCE_SURFACE:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/REFINEDFUEL_REVISIT_ROUTING_PASS__2026_03_11__v1.md`

BOUNDED_SCOPE:
- process only the exact `RUN_NOW` refinedfuel wave-1 set:
  - `BATCH_refinedfuel_constraints_entropy_term_conflict__v1`
  - `BATCH_refinedfuel_constraints_term_conflict__v1`
  - `BATCH_refinedfuel_constraints_entropy_source_map__v1`
  - `BATCH_refinedfuel_constraints_source_map__v1`

EXPECTED_OUTPUTS:
- one bounded refinedfuel revisit result
- exact files/artifacts read
- exact files/artifacts updated
- one `NEXT_STEP` value:
  - `STOP`
  - `ONE_MORE_BOUNDED_A2_PASS_NEEDED`
- one raw returned result file written into:
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns`

CONTINUATION_POLICY:
- `AUTO_GO_ON_ALLOWED = NO` unless later thread result qualifies under:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/41_AUTO_GO_ON_RULE__v1.md`

STOP_RULE:
- stop after one bounded wave-1 refinedfuel revisit pass

## Slot W2

Current state:
- `EMPTY`

Launch gate:
- launch only if controller can name one non-overlapping bounded role
- do not duplicate `W1`

## Slot A1

Current state:
- `EMPTY`

Launch gate:
- launch only if:
  - current queue is not `NO_WORK`
  - and a valid ready packet exists under:
    - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/34_A1_READY_PACKET__v1.md`

Current blocker:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_STATUS__CURRENT__2026_03_11__v1.md`

## Launch order

1. keep `C0` active
2. launch `W1`
3. do not launch `W2` unless controller explicitly upgrades state
4. do not launch `A1` unless `a1?` becomes ready

## Wave stop condition

This first parallel wave ends when:
- `W1` returns a bounded result
- controller records:
  - `STOP_NOW`
  - `SEND_ONE_GO_ON`
  - `ROUTE_TO_CLOSEOUT`
  - or `MANUAL_REVIEW_REQUIRED`

At that point, the controller decides whether:
- wave 2 exists
- `W2` is justified
- `A1` is now ready
