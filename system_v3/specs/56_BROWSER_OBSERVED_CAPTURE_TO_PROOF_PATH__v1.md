# BROWSER_OBSERVED_CAPTURE_TO_PROOF_PATH__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for bounded browser-assisted Codex continuation

## Purpose

This note defines the one-command wrapper path from:
- real observed Codex worker-thread values

through:
- `BROWSER_CODEX_THREAD_CAPTURE_RECORD_v1`
- `BROWSER_CODEX_THREAD_TARGET_v1`
- browser helper validation / proof output

It exists because the browser continuation chain already has:
- observed-capture schema
- capture helper
- capture-to-target helper
- browser helper validation

But still lacks one bounded wrapper that runs those three steps as a single operator action.

## Wrapper role

The wrapper:
1. receives one sender packet plus one set of observed thread values
2. writes one capture record
3. converts that record into one browser target packet
4. runs the browser helper
5. emits one proof packet

It does not:
- bypass sender validation
- bypass target validation
- authorize blind send
- fabricate live observation

## Required inputs

The wrapper must receive:
- one valid `AUTO_GO_ON_SENDER_PACKET_v1`
- one output directory
- one workspace root
- one composer-ready hint
- one real observed:
  - thread id
  - thread class
  - thread title
  - thread route
  - visible verification text
  - composer-ready state
  - observed timestamp
  - capture method
  - source note

## Required outputs

The wrapper must emit into one output directory:
- `browser_capture_record.json`
- `browser_target_packet.json`
- `browser_go_on_proof_packet.json`

## Hard rules

1. `NO_FAKE_CAPTURE`
- observed thread values must be operator- or Playwright-derived, not guessed

2. `NO_SEND_WITHOUT_SENDER`
- no sender packet means no wrapper run

3. `NO_PRO_THREAD_USE`
- wrapper remains Codex-thread-only

4. `HELPER_CHAIN_ONLY`
- wrapper must rely on existing helper logic for record creation, target conversion, and proof emission

## Immediate implication

After this note:
- browser-assisted continuation has one practical operator path from real observed thread values to proof packet output
- remaining gap is no longer control chaining
- remaining gap is the first real live observed Codex worker-thread capture
