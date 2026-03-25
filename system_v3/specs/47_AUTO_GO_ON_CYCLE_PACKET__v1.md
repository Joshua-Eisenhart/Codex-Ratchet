# AUTO_GO_ON_CYCLE_PACKET__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for auto-`go on` execution input normalization

## Purpose

This note defines the single invocation packet consumed by:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_auto_go_on_cycle_from_packet.py`

It exists to remove long manual CLI flag assembly from the auto-`go on` control path.

## Role

This is not:
- a returned thread result
- a sender packet
- a closeout packet

It is the one-shot execution input for the raw-text -> normalized-result -> runner cycle.

## Required fields

Every packet must include:

1. `schema`
- exactly:
  - `AUTO_GO_ON_CYCLE_PACKET_v1`

2. `reply_text`
- absolute path to one raw returned thread text file

3. `target_thread_id`
- exact target thread identifier

4. `thread_class`
- exactly one of:
  - `A2_WORKER`
  - `A1_WORKER`
  - `A2_CONTROLLER`

5. `boot_surface`
- exact boot surface path for the returned thread

6. `source_decision_record`
- exact repo path to the decision/summary record for this pass

7. `expected_return_shape`
- one-line expected minimum return shape after one more bounded pass

8. `out_dir`
- absolute output directory for:
  - normalized result JSON
  - runner output JSON

## Optional fields

Optional but useful:
- `fallback_role`
- `fallback_scope`
- `continuation_count`

## Hard rules

1. `ONE_PACKET_PER_RETURN`
- one returned thread text file maps to one cycle packet

2. `ABSOLUTE_PATHS_ONLY`
- all path-bearing fields must be absolute paths

3. `NO_EMBEDDED_THREAD_TEXT`
- the raw returned thread text stays in the file at `reply_text`
- this packet only points to it

4. `OUT_DIR_REQUIRED`
- packet execution must always write both machine-readable outputs into `out_dir`

## Template path

Template:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_derived_indices_noncanonical/auto_go_on_cycle_packet_template_v1.json`

## Immediate implication

After this note:
- the remaining manual step in the auto-`go on` chain is reduced to creating one small packet JSON
- the next helper should consume that packet directly
