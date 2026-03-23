# THREAD_CLOSEOUT_RESULT_SINK__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-09
Role: define the exact repo-held sink for returned thread closeout packets

## 1) Sink path

Returned closeout packets should be captured in:
- `system_v3/a2_derived_indices_noncanonical/thread_closeout_packets.000.jsonl`

Template object lives at:
- `system_v3/a2_derived_indices_noncanonical/thread_closeout_packet_template_v1.json`

This sink is:
- append-only
- noncanon
- controller-facing
- meant for comparison and later ingestion, not direct doctrine mutation

## 2) One-line rule

If a thread returns a closeout audit in chat, convert it into one
`THREAD_CLOSEOUT_PACKET_v1` object and append it as one line in:
- `thread_closeout_packets.000.jsonl`

Do not leave the result only in chat memory.

## 3) Required fields

Each packet must include:
- `schema`
- `captured_utc`
- `source_thread_label`
- `final_decision`
- `thread_diagnosis`
- `role_and_scope`
- `strongest_outputs`
- `keepers`
- `if_one_more_step`
- `risks`
- `handoff_packet`
- `closed_statement`

## 4) Allowed values

`final_decision`:
- `STOP`
- `CONTINUE_ONE_BOUNDED_STEP`
- `CORRECT_LANE_LATER`

`thread_diagnosis`:
- `healthy_but_ready_to_stop`
- `healthy_but_needs_one_bounded_final_step`
- `stalled`
- `duplicate`
- `drifted_off_scope`
- `metadata_polish_only`
- `waiting_on_external_input`

`strongest_outputs[].status`:
- `complete`
- `usable_but_partial`
- `not_actually_reusable`

## 5) Capture discipline

For each returned thread result:
- preserve exact artifact paths when given
- keep `strongest_outputs` bounded
- keep `keepers` bounded
- do not smooth contradictory thread diagnoses together
- one returned thread = one appended packet line

## 6) Controller use

The controller can use this sink to:
- compare lanes
- detect duplicates
- decide stop vs one-more-step vs correction
- choose the next batch wave
- later feed selected results into A2 refresh / A1 derivation

## 7) Next layer

This sink should later be used by:
- `thread closeout auditor` skill
- `thread run monitor`
- `closeout-result-ingest`

Until then, manual capture into this file is the correct repo-held path.

Current manual helper:
- `system_v3/tools/append_thread_closeout_packet.py`
- `system_v3/tools/audit_thread_closeout_packets.py`
- `system_v3/tools/extract_thread_closeout_packet.py`

Shortest operator note:
- `system_v3/a2_state/THREAD_CLOSEOUT_CAPTURE_QUICKSTART__v1.md`
