# BROWSER_OBSERVED_PACKET_TO_PLAYWRIGHT_PROOF_PATH__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for packet-driven Playwright browser continuation

## Purpose

This note defines the packet-driven wrapper path from:
- one staged browser observation packet under the sink
- one valid `AUTO_GO_ON_SENDER_PACKET_v1`

through:
- `BROWSER_CODEX_THREAD_CAPTURE_RECORD_v1`
- `BROWSER_CODEX_THREAD_TARGET_v1`
- `BROWSER_GO_ON_PLAYWRIGHT_PLAN_v1`
- `BROWSER_GO_ON_PROOF_PACKET_v1`

It exists so the browser continuation chain can run from one repo-held observation
packet directly into the Playwright plan/execution path, instead of stopping at the
older helper-only proof wrapper.

## Wrapper role

The wrapper:
1. receives one valid sender packet
2. receives one staged observed-thread packet from the sink
3. writes one capture record
4. writes one browser target packet
5. emits one Playwright plan
6. executes that plan
7. emits one proof packet

It does not:
- bypass sender validation
- bypass target validation
- bypass plan validation
- authorize blind send
- fabricate observation fields

## Required inputs

The wrapper must receive:
- one valid `AUTO_GO_ON_SENDER_PACKET_v1`
- one valid sink packet matching:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/57_BROWSER_OBSERVED_CAPTURE_SINK__v1.md`
- one output directory
- one plan mode:
  - `validate_only`
  - `real_send_once`

## Required outputs

The wrapper must emit into one output directory:
- `browser_capture_record.json`
- `browser_target_packet.json`
- `browser_go_on_playwright_plan.json`
- `browser_go_on_proof_packet.json`
- optionally:
  - `browser_go_on_command_log.json`

## Hard rules

1. `SINK_PACKET_FIRST`
- the wrapper starts from one staged observation JSON, not scattered arguments

2. `PLAN_CHAIN_ONLY`
- the wrapper must route through:
  - target creation
  - Playwright plan emission
  - Playwright execution

3. `NO_HELPER_SHORTCUT`
- the wrapper may not bypass the Playwright plan/execution layer by falling back
  to helper-only proof generation

4. `CODEX_ONLY`
- external `Pro` threads remain excluded

5. `REAL_SEND_STAYS_GATED`
- `real_send_once` still requires the explicit real-send gate at execution time

## Immediate implication

After this note:
- the packet-driven browser path has a stable end-to-end Playwright wrapper
- remaining gap is no longer wrapper design
- it is:
  - first live observed worker-thread packet
  - and later one bounded real-send attempt
