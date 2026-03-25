# BROWSER_OBSERVED_PACKET_TO_PROOF_PATH__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for bounded browser-assisted Codex continuation

## Purpose

This note defines the packet-driven wrapper path from:
- one staged browser observation packet under the sink

through:
- `BROWSER_CODEX_THREAD_CAPTURE_RECORD_v1`
- `BROWSER_CODEX_THREAD_TARGET_v1`
- browser helper validation / proof output

It exists so the browser continuation chain can run from one repo-held observation JSON
instead of many separate CLI fields.

## Wrapper role

The wrapper:
1. receives one valid sender packet
2. receives one staged observed-thread packet from the sink
3. writes one capture record
4. writes one browser target packet
5. runs the browser helper
6. emits one proof packet

It does not:
- bypass sender validation
- bypass target validation
- authorize blind send
- fabricate observation fields

## Required inputs

The wrapper must receive:
- one valid `AUTO_GO_ON_SENDER_PACKET_v1`
- one valid sink packet matching:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/57_BROWSER_OBSERVED_CAPTURE_SINK__v1.md`
- one output directory
- one helper mode

## Required outputs

The wrapper must emit into one output directory:
- `browser_capture_record.json`
- `browser_target_packet.json`
- `browser_go_on_proof_packet.json`

## Hard rules

1. `SINK_PACKET_FIRST`
- the packet-driven wrapper starts from one staged observation JSON, not scattered arguments

2. `NO_FIELD_REINTERPRETATION`
- values in the staged packet pass through directly into the capture/target generation chain

3. `CODEX_ONLY`
- external `Pro` threads remain excluded

4. `HELPER_CHAIN_ONLY`
- the wrapper must rely on the existing helper chain, not duplicate logic ad hoc

## Immediate implication

After this note:
- the browser continuation chain has a stable repo-held packet path from observed-thread sink packet to proof output
- remaining gap is the first real live observed worker-thread packet and later bounded real-send mode
