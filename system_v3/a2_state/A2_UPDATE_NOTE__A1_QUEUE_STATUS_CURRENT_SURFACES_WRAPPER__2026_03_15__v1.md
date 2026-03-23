# A2_UPDATE_NOTE__A1_QUEUE_STATUS_CURRENT_SURFACES_WRAPPER__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the bridge where one machine-readable `A1_QUEUE_STATUS_PACKET_v1` can now be rendered into the repo-held current-note shape instead of leaving the current queue note hand-maintained

## Scope

New queue-current surfaces tools:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/render_a1_queue_status_current_note_from_packet.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/prepare_a1_queue_status_surfaces.py`

Focused regression:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py`

Doc touch-up:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`

Concrete sample current surfaces:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS_PACKET__CURRENT_NO_WORK__2026_03_15__v1.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS__CURRENT__NO_WORK__2026_03_15__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS_PACKET__CURRENT_READY_SUBSTRATE__2026_03_15__v1.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS__CURRENT__READY_SUBSTRATE__2026_03_15__v1.md`

## Problem

The repo now had:
- a machine-readable queue-status packet
- queue-status validation
- queue-status packet examples

But the current repo-held queue note shape was still separate.

So the active controller answer could still drift between:
- the packet
- the current note

even though they were describing the same queue decision.

## What changed

`render_a1_queue_status_current_note_from_packet.py` now:
- reads one validated `A1_QUEUE_STATUS_PACKET_v1`
- renders the repo-held current-note shape
- preserves the current answer block
- expands ready-path fields when the queue is ready
- expands missing items when the queue is blocked

`prepare_a1_queue_status_surfaces.py` now:
- builds the queue-status packet
- renders the current note from it
- supports both:
  - explicit `NO_WORK`
  - ready-from-family-slice packet or bundle

## Meaning

This does not yet make the active current queue note fully automatic.

But it closes the shape gap:
- one packet can now drive one current-note render

So the controller no longer has to keep those two surfaces in sync by hand.

## Verification

Focused regression:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py`

Result:
- `Ran 5 tests ... OK`

Syntax:
- `python3 -m py_compile system_v3/tools/render_a1_queue_status_current_note_from_packet.py system_v3/tools/prepare_a1_queue_status_surfaces.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py`

Concrete sample generation:
- `python3 system_v3/tools/prepare_a1_queue_status_surfaces.py --no-work-reason 'no bounded A1 family slice is currently prepared' --out-json '/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS_PACKET__CURRENT_NO_WORK__2026_03_15__v1.json' --out-note '/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS__CURRENT__NO_WORK__2026_03_15__v1.md'`
- `python3 system_v3/tools/prepare_a1_queue_status_surfaces.py --family-slice-json '/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json' --family-slice-schema-json '/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json' --model 'GPT-5.4 Medium' --dispatch-id 'A1_DISPATCH__CURRENT_READY_SUBSTRATE__2026_03_15__v1' --preparation-mode bundle --out-dir '/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/current_queue_ready_bundle__substrate__2026_03_15__v1' --out-json '/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS_PACKET__CURRENT_READY_SUBSTRATE__2026_03_15__v1.json' --out-note '/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_QUEUE_STATUS__CURRENT__READY_SUBSTRATE__2026_03_15__v1.md'`

Observed result:
- both packet and note are produced together
- the `NO_WORK` sample renders the same answer shape as the existing active note
- the ready sample renders the ready-path fields instead of forcing a hand-written explanatory note

## Next seam

The next actual controller decision is policy:
- whether the active owner-like current note should eventually be refreshed from this wrapper
- and what exact selector decides which family slice becomes the current live ready answer when more than one bounded slice exists
