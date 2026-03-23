# FIRST_LIVE_BROWSER_THREAD_CAPTURE_PROCEDURE__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for bounded browser-assisted Codex continuation

## Purpose

This note defines the first bounded live procedure for capturing one real Codex worker thread
into the browser-observation sink.

It exists because the browser continuation chain is already executable from:
- one staged observed-thread packet

through:
- capture record
- target packet
- proof packet

But still lacks one explicit operator procedure for the first live capture.

## Scope

This procedure captures exactly one real live Codex worker thread.

It does not:
- send `go on`
- decide continuation policy
- validate the sender packet
- automate browser clicks

It only creates one sink packet suitable for the packet-driven wrapper.

## Target class

The first live capture target must be:
- exactly one `A2_WORKER` or `A1_WORKER`
- not a controller thread
- not a `Pro` thread

Preferred first target:
- one bounded worker thread that already has a known `target_thread_id`
- one visible title fragment
- one visible unique verification line
- one visible ready composer

## Required observed values

The operator must record:

1. `target_thread_id`
2. `thread_class`
3. `thread_title_observed`
4. `thread_url_or_route_observed`
5. `visible_verification_text_observed`
6. `composer_ready_observed`
7. `observed_at`
8. `capture_method`
9. `source_note`
10. `workspace_root`
11. `composer_ready_hint`

## Hard rules

1. `REAL_OBSERVATION_ONLY`
- all values must come from a real visible Codex thread

2. `NO_CONTROLLER_CAPTURE`
- controller threads are excluded

3. `NO_PRO_CAPTURE`
- `Pro` threads are excluded

4. `CAPTURE_ONE_THREAD_ONLY`
- do not combine multiple thread observations in one packet

5. `VISIBLE_VERIFIER_REQUIRED`
- if there is no visible verification text, this procedure must stop without staging a packet

## Output path

The output packet must be written under:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/browser_thread_observations`

Recommended filename:
- `browser_observed_thread__<thread_id>__<YYYYMMDDTHHMMSSZ>.json`

## Immediate next step after capture

Once one real observation packet exists:
1. run the packet-driven wrapper:
   - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_browser_go_on_from_observed_packet.py`
2. use `validate_only`
3. inspect the emitted proof packet

## Stop condition

This procedure stops after one valid observed-thread packet is staged.

If the target cannot be observed cleanly, stop with no packet.
