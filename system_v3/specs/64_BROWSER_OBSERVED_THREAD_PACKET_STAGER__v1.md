# BROWSER_OBSERVED_THREAD_PACKET_STAGER__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for staging real observed browser-thread packets

## Purpose

This note defines the tiny helper that writes one valid browser observed-thread
packet directly into the repo-held sink.

It exists so the first live browser capture does not require hand-editing JSON.

## Role

The stager consumes bounded observed thread metadata and emits:
- one `browser_observed_thread__<thread_id>__<timestamp>.json`

under:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/browser_thread_observations`

## Required output contract

The staged packet must satisfy:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/57_BROWSER_OBSERVED_CAPTURE_SINK__v1.md`

The stager may not:
- invent controller threads
- invent `Pro` threads
- omit route/title/verification/composer values
- write outside the sink directory by default

## Immediate implication

After this note:
- first live browser capture can start from one command instead of hand-built JSON
- the packet-driven Playwright wrapper can consume a real staged packet more directly
