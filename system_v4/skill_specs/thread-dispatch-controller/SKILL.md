---
name: thread-dispatch-controller
description: Launch bounded fresh-thread worker lanes for the Codex Ratchet system with stable role labels, explicit scope, boot inputs, expected outputs, and handoff into monitoring/closeout. Use when the controller needs to spawn or correct a worker lane instead of continuing work in the current thread.
---

# Thread Dispatch Controller

Use this skill when the controller needs to start a bounded worker lane.

## Core rules

- Do not spawn just because parallelism is available.
- Prefer auditing or correcting existing lanes before spawning more.
- Every worker must have:
  - `ROLE_LABEL`
  - `ROLE_TYPE`
  - `ROLE_SCOPE`
- Launch bounded lanes only.
- Every launched lane must already have:
  - expected outputs
  - a stop condition
  - a handoff path into `thread-run-monitor` and `thread-closeout-auditor`

## Owner surfaces

- `system_v3/specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md`
- `system_v3/a2_state/THREAD_CLOSEOUT_AUDIT_AND_NEXT_BATCH_PLAN__v1.md`
- `system_v4/skill_specs/thread-run-monitor/SKILL.md`
- `system_v4/skill_specs/thread-closeout-auditor/SKILL.md`

## Stable role labels

Preferred worker labels from the controller surface:

- `Controller Master`
- `A2H Upgrade Docs`
- `A2H Archived State`
- `A2H Sims`
- `A2H Refined Fuel Non-Sims`
- `A2M Promotion Review`
- `A2M Contradiction Reprocess`
- `A1 Rosetta Bridge`
- `A1 Cartridge Judge`
- `A1 Strategy Audit`

Use stable role labels that describe role and scope, not transient backlog state.

## Minimum boot set

Default controller boot set for spawning decisions:

- `system_v3/specs/07_A2_OPERATIONS_SPEC.md`
- `system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
- `system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
- `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
- `system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
- `system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`
- `system_v3/specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md`

## Spawn triggers

Spawn or correct a lane only when one of these is true:

- entropy overload
- ratchet plateau / problem state
- promotion pressure
- a weak lane needs bounded correction instead of continuation

## Workflow

1. Confirm that spawning is justified under the controller triggers.
2. Prefer correction of an existing weak lane before creating a redundant new one.
3. Select the worker class and stable role label.
4. Define:
   - exact scope
   - exact boot files
   - exact expected outputs
   - exact bounded stop condition
5. Emit the worker launch packet or prompt with:
   - `ROLE_LABEL`
   - `ROLE_TYPE`
   - `ROLE_SCOPE`
   - boot set
   - output contract
6. Route the new lane to:
   - `thread-run-monitor` once it has run for a while
   - `thread-closeout-auditor` when it crosses the useful stopping boundary

## Guardrails

- Do not launch vague “explore more” lanes.
- Do not spawn overlapping duplicates without a correction reason.
- Do not omit expected outputs or stop condition.
- Do not rely on hidden chat memory as the lane’s only boot.
- If no bounded spawn reason exists, recommend no-spawn directly.
