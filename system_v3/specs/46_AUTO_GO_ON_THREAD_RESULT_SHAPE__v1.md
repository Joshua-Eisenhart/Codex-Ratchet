# AUTO_GO_ON_THREAD_RESULT_SHAPE__v1

Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller for normalized thread-result intake

## Purpose

This note defines the normalized JSON shape consumed by:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/auto_go_on_runner.py`

It exists because current thread returns are still human-oriented text blocks.
The runner needs one stable machine-readable result shape so:
- returned Codex thread outputs
- later closeout packets
- later browser-assisted capture

can be routed through the same continuation helper.

## Role

This shape is not a closeout packet.
It is a continuation-evaluation packet.

It captures exactly the fields needed for:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/41_AUTO_GO_ON_RULE__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/42_AUTO_GO_ON_APPLICATOR__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/45_AUTO_GO_ON_RUNNER__v1.md`

## Required top-level fields

Every normalized packet must include:

1. `schema`
- must be exactly:
  - `AUTO_GO_ON_THREAD_RESULT_v1`

2. `target_thread_id`
- exact target thread identifier

3. `thread_class`
- exactly one of:
  - `A2_WORKER`
  - `A1_WORKER`
  - `A2_CONTROLLER`

4. `role_and_scope`
- object with:
  - `role`
  - `scope`

5. `what_you_read`
- non-empty list of repo-held surfaces or artifacts actually read

6. `what_you_updated`
- list of artifacts updated in the last bounded pass
- may be empty only if the thread explicitly produced bounded no-change work

7. `next_step`
- exactly one of:
  - `STOP`
  - `ONE_MORE_BOUNDED_PASS_NEEDED`

8. `if_one_more_pass`
- object
- required if and only if:
  - `next_step = ONE_MORE_BOUNDED_PASS_NEEDED`
- must include:
  - `next_step`
  - `touches`
  - `stop_condition`

9. `continuation_count`
- integer count since last manual review

10. `source_decision_record`
- exact repo path to the decision/summary record for this pass

11. `boot_surface`
- exact boot used by the target thread

12. `expected_return_shape`
- one-line expected minimum return shape after one more bounded pass

## Optional but useful fields

Optional fields:
- `what_you_updated_is_bounded_no_change`
- `blocked_case_flags`
- `result_summary`
- `thread_platform`
- `captured_utc`

## Hard normalization rules

1. `NO_FREE_TEXT_SUBSTITUTE`
- the runner should not consume raw prose as a substitute for this shape

2. `ROLE_FIELD_CURRENT`
- for `A1_WORKER`, `role_and_scope.role` must be one of:
  - `A1_ROSETTA`
  - `A1_PROPOSAL`
  - `A1_PACKAGING`

3. `A2_CONTROLLER_BLOCKABLE`
- `A2_CONTROLLER` may appear here, but the applicator must still block auto-continue by rule

4. `EMPTY_UPDATES_ALLOWED_ONLY_IF_EXPLICIT`
- an empty `what_you_updated` list is allowed only if the pass explicitly produced bounded no-change work and that is recorded

5. `TOUCHES_MUST_BE_LIST`
- `if_one_more_pass.touches` must always be a list, never free prose

## Template path

The normalized template lives at:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_derived_indices_noncanonical/auto_go_on_thread_result_template_v1.json`

## Immediate implication

After this note:
- the auto-`go on` runner now has a single stable intended input shape

Still missing:
- one extractor/normalizer that turns returned thread prose into this shape automatically

