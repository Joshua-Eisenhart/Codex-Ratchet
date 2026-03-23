# BROWSER_OBSERVED_CAPTURE_SINK__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for bounded browser-assisted Codex continuation

## Purpose

This note defines the repo-held intake path for real observed Codex worker-thread values
that will later feed:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/54_BROWSER_CODEX_THREAD_CAPTURE_RECORD__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/56_BROWSER_OBSERVED_CAPTURE_TO_PROOF_PATH__v1.md`

It exists so the browser continuation chain stops depending on ad hoc pasted observations.

## Sink role

The sink stores one bounded observation packet for one Codex worker thread.

It is not:
- a proof packet
- a continuation decision
- a target packet

It is the raw observation intake used to create those later artifacts.

## Repo-held paths

Raw observation staging directory:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/browser_thread_observations`

Recommended packet filename pattern:
- `browser_observed_thread__<thread_id>__<YYYYMMDDTHHMMSSZ>.json`

## Required fields

Each raw observation packet must include:

1. `target_thread_id`
2. `thread_class`
- exactly one of:
  - `A2_WORKER`
  - `A1_WORKER`

3. `thread_title_observed`
4. `thread_url_or_route_observed`
5. `visible_verification_text_observed`
6. `composer_ready_observed`
- exactly one of:
  - `YES`
  - `NO`

7. `observed_at`
8. `capture_method`
- exactly one of:
  - `MANUAL_OPERATOR`
  - `PLAYWRIGHT_CAPTURE`

9. `source_note`
- exact repo path to the control note or state surface motivating the capture

10. `workspace_root`
- exact workspace root for later target generation

11. `composer_ready_hint`
- exactly one of:
  - `READY`
  - `UNVERIFIED`

## Hard rules

1. `ONE_PACKET_PER_OBSERVED_THREAD_AT_A_TIME`
- do not mix multiple thread observations into one packet

2. `NO_CONTROLLER_THREADS`
- controller threads are not valid browser continuation targets

3. `NO_PRO_THREADS`
- web UI `Pro` threads are not valid browser continuation targets

4. `NO_GUESSED_VALUES`
- route, title, verification text, and composer state must be observed

5. `SINK_FIRST`
- a real browser continuation attempt should begin from a repo-held observation packet when practical

## Immediate implication

After this note:
- one real observed Codex worker thread can be stored as a stable repo-held intake packet
- the wrapper path can be run from saved observation state instead of ad hoc command assembly
