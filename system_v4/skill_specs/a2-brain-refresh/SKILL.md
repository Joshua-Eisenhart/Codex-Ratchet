---
name: a2-brain-refresh
description: Run the Codex Ratchet A2-brain-first refresh loop in the correct order. Use when active repo changes, user corrections, tool/spec shifts, or new evidence mean A2 may be stale and A2 understanding surfaces need bounded refresh before A1 work or broader routing.
---

# A2 Brain Refresh

Use this skill when A2 may be stale relative to the active repo or the current user correction.

## Core rules

- A2 refresh happens before new A1 derivation.
- Preserve contradictions; do not smooth them away.
- Treat A2 as noncanon understanding and control memory, not earned state.
- Do not jump directly from new input to A1/A0 without refreshed A2.
- If A2 is stale relative to active system changes, broader work pauses.

## Active owner surfaces

- `system_v3/specs/07_A2_OPERATIONS_SPEC.md`
- `system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
- `system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md`
- `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
- `system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
- `system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
- `system_v3/a2_state/SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md`

## Read order

1. Current user correction or task signal
2. Changed active system surfaces
3. Changed tools/contracts
4. New run evidence
5. Current active A2 control surfaces
6. `A2_TO_A1` handoff surface

## Required outputs

- `A2_UPDATE_NOTE`
- bounded append-safe updates to active A2 surfaces when justified
- `A2_TO_A1_IMPACT_NOTE`
- `OFF_PROCESS_FLAGS` when the A2-first loop was bypassed or drifted

## Workflow

1. Check whether the task includes any of:
   - new user correction
   - changed active docs
   - changed tools/contracts
   - new run evidence
   - pending A1 work
2. Read only the active surfaces needed for the affected scope.
3. Classify touched surfaces:
   - active system surface
   - active low-touch/reference surface
   - alias/migration scaffolding
   - `work/` prototype/test spillover
   - external archive/retention
4. Detect stale-A2 vs active-repo drift.
5. Emit a bounded A2 update note or patch the active A2 surfaces if the change is clearly source-anchored.
6. Record A2-to-A1 impact explicitly.
7. If the loop was bypassed, emit an off-process flag and stop broader routing.

## Guardrails

- Do not treat document-local canon labels as earned truth.
- Do not let derived helper surfaces outrank active owner surfaces.
- Do not read high-entropy material when the task is only active-surface refresh.
- Do not mutate lower-loop or runtime truth from this skill.
- Keep updates append-first and source-bound.
- If no real A2 delta exists, say so directly instead of forcing a rewrite.
