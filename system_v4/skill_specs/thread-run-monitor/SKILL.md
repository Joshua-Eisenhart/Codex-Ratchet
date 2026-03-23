---
name: thread-run-monitor
description: Diagnose worker-thread health for the Codex Ratchet system and decide when a lane should be handed to closeout instead of continued. Use when fresh-thread worker lanes have run for a while and the controller needs a bounded read on overlong, duplicate, drifted, metadata-polish-only, or waiting-on-external behavior.
---

# Thread Run Monitor

Use this skill when a worker lane may have crossed the useful stopping boundary.

## Core rules

- A worker thread should not continue just because more work is possible.
- One more step is allowed only if it has clear bounded reuse value.
- The monitor does not continue work itself; it diagnoses and routes.
- The monitor should prefer explicit stop law over operator intuition.

## Owner surfaces

- `system_v3/a2_state/THREAD_RUN_DIAGNOSIS_AND_STOP_RULES__v1.md`
- `work/zip_subagents/THREAD_CLOSEOUT_AUDIT_PROMPT__v1.md`
- `system_v3/a2_state/THREAD_CLOSEOUT_AUDIT_AND_NEXT_BATCH_PLAN__v1.md`
- `system_v4/skill_specs/thread-closeout-auditor/SKILL.md`

## Diagnosis classes

- `healthy_but_ready_to_stop`
- `healthy_but_needs_one_bounded_final_step`
- `stalled`
- `duplicate`
- `drifted_off_scope`
- `metadata_polish_only`
- `waiting_on_external_input`

## Allowed controller decisions

- `STOP`
- `CONTINUE_ONE_BOUNDED_STEP`
- `CORRECT_LANE_LATER`

## Stop triggers

- next step is mainly recap or polish
- strongest reusable artifact family is already emitted
- repeated continuation is low-yield symmetry completion
- lane drifted into generic theory talk
- another role/skill/lane covers the work better
- continuation depends more on hidden thread memory than repo-held artifacts
- unresolved remainder is real but not this lane's job

## Workflow

1. Inspect the lane’s current scope and strongest artifacts.
2. Compare the remaining work against the stop triggers.
3. Classify the lane into exactly one diagnosis class.
4. Recommend exactly one decision:
   - `STOP`
   - `CONTINUE_ONE_BOUNDED_STEP`
   - `CORRECT_LANE_LATER`
5. If `STOP` or `CORRECT_LANE_LATER`, hand the lane to `thread-closeout-auditor`.
6. If `CONTINUE_ONE_BOUNDED_STEP`, define:
   - exact next step
   - exact touched files/artifacts
   - exact stop condition after that step

## Guardrails

- Do not let “interesting” override “bounded”.
- Do not recommend continuation without a concrete stop condition.
- Do not invent hidden artifact value that the lane did not actually produce.
- Do not use this skill to reopen or broaden a lane.
- If signals are weak, bias toward stop and audit rather than endless continuation.
